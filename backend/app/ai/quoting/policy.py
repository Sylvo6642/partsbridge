"""Quote policy v2: the AI reads the buyer's words, plain code applies the rules.

quoting_v1 let an agent apply the substitution rules with tools: 65% of lines right, 8 substitutions against the
buyer's wish (docs/evals/quoting_v1.md). The rules are fixed and need number comparisons, which is code's job.
The only fuzzy input is language: does the buyer allow another brand? That's one structured-output call.
"""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import psycopg
from pydantic import BaseModel, Field

from app.ai import llm

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


class BuyerPreferences(BaseModel):
    substitutes_allowed: bool = Field(description="False only if the buyer asks for the listed brand only / no substitutes")
    evidence: str = Field(description="The buyer's words this is based on, or empty if they said nothing about it")


def read_preferences(notes: str | None, *, trace_id: UUID | None = None, user_id: UUID | None = None
                     ) -> tuple[BuyerPreferences, llm.LLMResult | None]:
    if not (notes or "").strip():
        return BuyerPreferences(substitutes_allowed=True, evidence=""), None  # nothing to read: no AI call
    result = llm.parse(feature="quoting", prompt_version="quoting_v2",
                       instructions=(PROMPTS_DIR / "quoting_v2.md").read_text(encoding="utf-8"),
                       input=f"Buyer notes: {notes}", schema=BuyerPreferences, trace_id=trace_id, user_id=user_id)
    return result.output, result


@dataclass
class PolicyDecision:
    part_id: int | None
    situation: str
    note: str


def decide_line(conn: psycopg.Connection, seller_id: int, part_id: int, quantity: int,
                substitutes_allowed: bool) -> PolicyDecision:
    rows = conn.execute(
        """select p.id, p.brand, p.part_number, o.stock_qty, o.lead_time_days, o.unit_price
           from parts p join offers o on o.part_id = p.id and o.seller_id = %s
           where p.interchange_group = (select interchange_group from parts where id = %s)
           order by o.unit_price""", (seller_id, part_id),
    ).fetchall()
    requested = next((r for r in rows if r[0] == part_id), None)
    equivalents = [r for r in rows if r[0] != part_id]          # cheapest first
    if requested and requested[3] >= quantity:
        return PolicyDecision(part_id, "requested in stock", "")
    in_stock = [r for r in equivalents if r[3] >= quantity]
    if substitutes_allowed and in_stock:
        r = in_stock[0]
        why = "not stocked here" if not requested else f"only {requested[3]} in stock"
        return PolicyDecision(r[0], "equivalent in stock",
                              f"Equivalent {r[1]} {r[2]} offered from stock (requested brand {why}).")
    if requested:
        return PolicyDecision(part_id, "requested, must be ordered",
                              f"Only {requested[3]} in stock; the rest must be ordered.")
    if substitutes_allowed and equivalents:
        r = equivalents[0]
        return PolicyDecision(r[0], "equivalent, must be ordered",
                              f"Equivalent {r[1]} {r[2]} offered; must be ordered.")
    if equivalents:
        return PolicyDecision(None, "can't supply", "We only carry another brand of this part; you asked for the listed brand only.")
    return PolicyDecision(None, "can't supply", "We don't carry this part.")
