"""Tests for the plain-code guardrails around the matching agent (no OpenAI calls)."""

from app.ai.matching.agent import MatchDecision, _part_ids, check_decision
from app.ai.matching.tools import FILTER_SCHEMA, TOOLSETS


def decision(status, part_id=None, candidates=()):
    return MatchDecision(status=status, part_id=part_id, candidate_part_ids=list(candidates), reason="r")


def test_a_part_the_tools_never_returned_is_rejected():
    checked, guardrail = check_decision(decision("matched", part_id=999), seen_ids={1, 2})
    assert checked.status == "not_found" and checked.part_id is None
    assert guardrail == "rejected unseen part_id 999"


def test_unseen_candidates_are_dropped():
    checked, _ = check_decision(decision("needs_choice", candidates=[1, 999, 2]), seen_ids={1, 2})
    assert checked.candidate_part_ids == [1, 2]


def test_needs_choice_without_valid_candidates_becomes_not_found():
    checked, guardrail = check_decision(decision("needs_choice", candidates=[999]), seen_ids={1})
    assert checked.status == "not_found" and guardrail


def test_part_ids_are_collected_from_flat_and_grouped_tool_output():
    flat = [{"part_id": 1}, {"part_id": 2}]
    grouped = [{"options": [{"part_id": 3}, {"part_id": 4}]}, {"result": "no parts"}]
    assert _part_ids(flat) | _part_ids(grouped) == {1, 2, 3, 4}


def test_tools_never_take_user_or_seller_ids():
    # The model must never be able to choose whose data a tool reads (D-004).
    forbidden = {"user_id", "workspace_id", "seller_id", "buyer_id"}
    for tools in TOOLSETS.values():
        for tool in tools:
            assert not forbidden & set(tool["parameters"]["properties"]), tool["name"]


def test_filter_schema_is_strict_and_requires_every_field():
    params = FILTER_SCHEMA["parameters"]
    assert FILTER_SCHEMA["strict"] and set(params["required"]) == set(params["properties"])
