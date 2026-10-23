"""The quote agent: an RFQ + one seller in, a draft quote out.

The model decides, per line, WHICH part this seller offers (requested, an equivalent brand, or none) and writes the
notes. It never writes a price: `price_quote` computes every amount from the seller's price list in plain code.
Guardrails (also plain code) reject any part that isn't the requested one or an equivalent, or isn't carried.
"""

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
from pydantic import BaseModel, Field

from app.ai.agent_loop import run_tool_loop
from app.ai.quoting.tools import TOOL_SCHEMAS, run_tool

PROMPT_VERSION = "quoting_v2"  # v1 = the tool-calling agent, kept as the measured baseline
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
MAX_TURNS = 6


@dataclass
class QuoteRequestLine:
    line_id: str
    part_id: int
    quantity: int
    description: str


class LineDecision(BaseModel):
    line_id: str
    part_id: int | None = Field(description="The part this seller offers for the line, or null if it can't supply")
    note: str = Field(description="What the buyer should know about this line, or empty")


class QuoteDraft(BaseModel):
    lines: list[LineDecision]
    summary: str = Field(description="One sentence for the seller")


@dataclass
class QuoteResult:
    decisions: dict[str, LineDecision]
    summary: str
    guardrails: list[str] = field(default_factory=list)
    tool_calls: list[str] = field(default_factory=list)
    model_calls: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0


def describe_request(conn: psycopg.Connection, lines: list[QuoteRequestLine], notes: str | None) -> str:
    rows = dict(conn.execute("select id, brand || ' ' || part_number from parts where id = any(%s)",
                             ([l.part_id for l in lines],)).fetchall())
    return json.dumps({
        "buyer_notes": notes or "",
        "lines": [{"line_id": l.line_id, "requested_part_id": l.part_id, "requested_part": rows.get(l.part_id),
                   "quantity": l.quantity, "description": l.description} for l in lines],
    })


def check_decisions(conn: psycopg.Connection, seller_id: int, lines: list[QuoteRequestLine],
                    draft: QuoteDraft | None) -> tuple[dict[str, LineDecision], list[str]]:
    """Every line gets exactly one decision; offered parts must be the requested part or an equivalent the seller
    carries. Anything else becomes "can't supply" and is reported."""
    given = {d.line_id: d for d in (draft.lines if draft else [])}
    issues, decided = [], {}
    for line in lines:
        d = given.get(line.line_id)
        if d is None:
            issues.append(f"{line.line_id}: no decision from the model")
            decided[line.line_id] = LineDecision(line_id=line.line_id, part_id=None, note="Not quoted.")
            continue
        if d.part_id is not None:
            ok = conn.execute(
                """select 1 from parts p join offers o on o.part_id = p.id and o.seller_id = %s
                   where p.id = %s and p.interchange_group = (select interchange_group from parts where id = %s)""",
                (seller_id, d.part_id, line.part_id),
            ).fetchone()
            if not ok:
                issues.append(f"{line.line_id}: rejected part {d.part_id} (not the requested part or an equivalent "
                              f"this seller carries)")
                d = LineDecision(line_id=line.line_id, part_id=None, note="Can't supply this part.")
        decided[line.line_id] = d
    return decided, issues


def draft_quote(conn: psycopg.Connection, seller_id: int, lines: list[QuoteRequestLine], notes: str | None, *,
                prompt_version: str = PROMPT_VERSION, trace_id: UUID | None = None,
                user_id: UUID | None = None) -> QuoteResult:
    if prompt_version == "quoting_v2":
        return _draft_with_policy(conn, seller_id, lines, notes, trace_id=trace_id, user_id=user_id)
    loop = run_tool_loop(
        feature="quoting", prompt_version=prompt_version,
        instructions=(PROMPTS_DIR / f"{prompt_version}.md").read_text(encoding="utf-8"),
        message=f"RFQ: {describe_request(conn, lines, notes)}", schema=QuoteDraft, tools=TOOL_SCHEMAS,
        run_tool=lambda name, args: run_tool(conn, seller_id, name, args),
        max_turns=MAX_TURNS, trace_id=trace_id or uuid4(), user_id=user_id,
    )
    decisions, issues = check_decisions(conn, seller_id, lines, loop.output)
    if loop.output is None:
        issues.insert(0, f"stopped after {MAX_TURNS} model calls")
    return QuoteResult(decisions=decisions, summary=loop.output.summary if loop.output else "",
                       guardrails=issues, tool_calls=loop.tool_calls, model_calls=loop.model_calls,
                       cost_usd=loop.cost_usd, latency_ms=loop.latency_ms)


def _draft_with_policy(conn: psycopg.Connection, seller_id: int, lines: list[QuoteRequestLine], notes: str | None,
                       *, trace_id: UUID | None, user_id: UUID | None) -> QuoteResult:
    """quoting_v2: one AI call reads the buyer's notes; plain code decides every line (app/ai/quoting/policy.py)."""
    from app.ai.quoting.policy import decide_line, read_preferences

    prefs, call = read_preferences(notes, trace_id=trace_id, user_id=user_id)
    decisions = {}
    for line in lines:
        d = decide_line(conn, seller_id, line.part_id, line.quantity, prefs.substitutes_allowed)
        decisions[line.line_id] = LineDecision(line_id=line.line_id, part_id=d.part_id, note=d.note)
    supplied = sum(d.part_id is not None for d in decisions.values())
    summary = (f"{supplied} of {len(lines)} lines supplied. Substitutes "
               f"{'allowed' if prefs.substitutes_allowed else 'not allowed'}"
               f"{f' (buyer: “{prefs.evidence}”)' if prefs.evidence else ''}.")
    return QuoteResult(decisions=decisions, summary=summary, model_calls=1 if call else 0,
                       cost_usd=call.cost_usd if call else 0.0, latency_ms=call.latency_ms if call else 0)


@dataclass
class PricedLine:
    line_id: str
    part_id: int | None
    quantity: int
    unit_price: Decimal | None
    line_total: Decimal | None
    lead_time_days: int | None
    stock_qty: int | None


@dataclass
class PricedQuote:
    lines: list[PricedLine]
    subtotal: Decimal
    shipping: Decimal
    total: Decimal
    lead_time_days: int | None


def price_quote(conn: psycopg.Connection, seller_id: int, chosen: list[tuple[str, int | None, int]],
                unit_price_overrides: dict[str, Decimal] | None = None) -> PricedQuote:
    """All money, in plain code: prices from the seller's price list (or a price the seller typed in), Decimal math."""
    overrides = unit_price_overrides or {}
    part_ids = [p for _, p, _ in chosen if p is not None]
    offers = {r[0]: r[1:] for r in conn.execute(
        "select part_id, unit_price, stock_qty, lead_time_days from offers where seller_id = %s and part_id = any(%s)",
        (seller_id, part_ids),
    )}
    shipping = conn.execute("select shipping_fee from sellers where id = %s", (seller_id,)).fetchone()[0]
    priced = []
    for line_id, part_id, qty in chosen:
        offer = offers.get(part_id)
        if part_id is None or offer is None:
            priced.append(PricedLine(line_id, None, qty, None, None, None, None))
            continue
        unit = overrides.get(line_id, offer[0])
        lead = offer[2] if offer[1] >= qty else max(offer[2], 10)  # not enough stock: order it in
        priced.append(PricedLine(line_id, part_id, qty, unit, (unit * qty).quantize(Decimal("0.01")), lead, offer[1]))
    subtotal = sum((p.line_total for p in priced if p.line_total is not None), Decimal("0.00"))
    supplied = [p for p in priced if p.part_id is not None]
    return PricedQuote(lines=priced, subtotal=subtotal, shipping=shipping if supplied else Decimal("0.00"),
                       total=subtotal + (shipping if supplied else Decimal("0.00")),
                       lead_time_days=max((p.lead_time_days for p in supplied), default=None))
