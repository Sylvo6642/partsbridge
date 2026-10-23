"""The part-matching agent: one buyer line in, a decision out.

The loop (shared with the quote agent, in app/ai/agent_loop.py):
1. Send the buyer's line + tool descriptions to the model.
2. If the model asks for tool calls, run them and send the results back. Repeat.
3. When the model answers, check the answer with plain code (it may only choose parts the tools returned).

Limits keep it safe and cheap: at most MAX_TURNS model calls per line.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

import psycopg
from pydantic import BaseModel, Field

from app.ai.agent_loop import run_tool_loop
from app.ai.extraction import LineItem
from app.ai.matching.tools import TOOLSETS, run_tool
from app.part_numbers import normalize_part_number

PROMPT_VERSION = "matching_v4"
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
MAX_TURNS = 5


class MatchDecision(BaseModel):
    status: Literal["matched", "needs_choice", "not_found"]
    part_id: int | None = Field(description="The chosen part when status is 'matched', else null")
    candidate_part_ids: list[int] = Field(description="Options for the buyer when status is 'needs_choice'")
    reason: str = Field(description="One short sentence explaining the decision")


@dataclass
class MatchResult:
    decision: MatchDecision
    tool_calls: list[str] = field(default_factory=list)
    model_calls: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    guardrail: str | None = None  # set when plain code had to overrule the model
    settled: str | None = None    # what settle_brand changed, if anything


def describe_line(line: LineItem) -> str:
    return json.dumps({"part_number": line.part_number, "brand": line.brand,
                       "description": line.description, "quantity": line.quantity})


def _part_ids(tool_output: list[dict]) -> set[int]:
    """Every part_id a tool returned (flat rows, or physical parts with brand options)."""
    ids = {p["part_id"] for p in tool_output if "part_id" in p}
    ids |= {o["part_id"] for p in tool_output for o in p.get("options", [])}
    return ids


def check_decision(decision: MatchDecision, seen_ids: set[int]) -> tuple[MatchDecision, str | None]:
    """The model may only choose parts that the tools actually returned. Anything else is downgraded."""
    candidates = [i for i in decision.candidate_part_ids if i in seen_ids]
    if decision.status == "matched" and decision.part_id not in seen_ids:
        return (MatchDecision(status="not_found", part_id=None, candidate_part_ids=candidates,
                              reason="The model chose a part that the catalog search never returned."),
                f"rejected unseen part_id {decision.part_id}")
    if decision.status == "needs_choice" and not candidates:
        return (MatchDecision(status="not_found", part_id=None, candidate_part_ids=[], reason=decision.reason),
                "needs_choice without valid candidates")
    if decision.status != "matched" and decision.part_id is not None:
        decision = decision.model_copy(update={"part_id": None})
    return decision.model_copy(update={"candidate_part_ids": candidates}), None


def settle_brand(conn: psycopg.Connection, line: LineItem, decision: MatchDecision) -> tuple[MatchDecision, str | None]:
    """Plain code, not AI (from matching_v4). The model picks the physical part; code picks the brand option.

    - "needs_choice" between brand options of ONE physical part is really a match.
    - Brand: the one the buyer named; else the one whose part number the buyer wrote; else keep the model's pick.
    """
    note = None
    ids = [decision.part_id] if decision.status == "matched" else decision.candidate_part_ids
    group_of = dict(conn.execute("select id, interchange_group from parts where id = any(%s)", (ids,)).fetchall())
    groups = set(group_of.values())
    if decision.status == "needs_choice":
        # One option per physical part: the model sometimes lists brands of the same part as separate options.
        seen, first_per_group = set(), []
        for i in ids:
            if i in group_of and group_of[i] not in seen:
                seen.add(group_of[i])
                first_per_group.append(i)
        if len(first_per_group) < len(ids):
            decision = decision.model_copy(update={"candidate_part_ids": first_per_group})
            ids = first_per_group
            note = "duplicate brand options removed"
    if decision.status == "needs_choice" and len(groups) == 1:
        decision = decision.model_copy(update={"status": "matched", "part_id": ids[0], "candidate_part_ids": []})
        note = "brand options of one part turned into a match"
    if decision.status != "matched":
        return decision, note
    options = conn.execute(
        "select id, brand, part_number, part_number_norm from parts where interchange_group = %s order by id",
        (groups.pop(),),
    ).fetchall()
    wanted_brand = (line.brand or "").strip().lower()
    written = (line.part_number or "").strip().upper()
    # Most specific first: named brand, then the part number exactly as written ("A-42" is Kanto, "A42" is Norvik,
    # which look the same once normalized), then the normalized part number.
    rules = [lambda o: wanted_brand and o[1].lower() == wanted_brand,
             lambda o: not wanted_brand and written and o[2].upper() == written,
             lambda o: not wanted_brand and written and o[3] == normalize_part_number(written)]
    for rule in rules:
        chosen = next((o for o in options if rule(o)), None)
        if chosen:
            if chosen[0] != decision.part_id:
                decision = decision.model_copy(update={"part_id": chosen[0]})
                note = (note + "; " if note else "") + f"brand set to {chosen[1]}"
            break
    return decision, note


def match_line(conn: psycopg.Connection, line: LineItem, *, prompt_version: str = PROMPT_VERSION,
               trace_id: UUID | None = None, user_id: UUID | None = None) -> MatchResult:
    loop = run_tool_loop(
        feature="matching", prompt_version=prompt_version,
        instructions=(PROMPTS_DIR / f"{prompt_version}.md").read_text(encoding="utf-8"),
        message=f"Buyer line: {describe_line(line)}", schema=MatchDecision, tools=TOOLSETS[prompt_version],
        run_tool=lambda name, args: run_tool(conn, name, args, grouped=prompt_version != "matching_v1"),
        max_turns=MAX_TURNS, trace_id=trace_id or uuid4(), user_id=user_id,
    )
    result = MatchResult(
        decision=MatchDecision(status="not_found", part_id=None, candidate_part_ids=[],
                               reason="The agent did not finish."),
        tool_calls=loop.tool_calls, model_calls=loop.model_calls, cost_usd=loop.cost_usd, latency_ms=loop.latency_ms,
    )
    if loop.output is None:
        result.guardrail = f"stopped after {MAX_TURNS} model calls"
        return result
    seen_ids = set().union(*(_part_ids(o) for o in loop.tool_outputs)) if loop.tool_outputs else set()
    result.decision, result.guardrail = check_decision(loop.output, seen_ids)
    if prompt_version not in ("matching_v1", "matching_v2", "matching_v3"):
        result.decision, result.settled = settle_brand(conn, line, result.decision)
    return result
