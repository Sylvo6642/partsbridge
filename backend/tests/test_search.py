"""Tests for the plain-code parts of search (no database or OpenAI calls)."""

from app.ai.matching.search import Hit, _codes, rrf


def hit(part_id, method):
    return Hit(part_id, "Norvik", f"P{part_id}", "bearing", "", f"g{part_id}", found_by=[method])


def test_codes_uses_extracted_part_number_when_present():
    assert _codes("6205 sealed bearing", "6205") == ["6205"]


def test_codes_falls_back_to_tokens_with_digits():
    # "x6" has a digit but is too short to be a part number
    assert _codes("need spb2250 belts x6", None) == ["SPB2250"]


def test_rrf_rewards_parts_found_by_several_methods():
    merged = rrf([[hit(1, "keyword"), hit(2, "keyword")], [hit(2, "meaning"), hit(3, "meaning")]])
    assert [h.part_id for h in merged] == [2, 1, 3]
    assert merged[0].found_by == ["keyword", "meaning"]
