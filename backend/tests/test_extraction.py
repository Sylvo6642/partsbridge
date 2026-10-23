"""Tests for the plain-code parts of extraction (no OpenAI calls)."""

from app.ai.extraction import ExtractedRFQ, LineItem, problems
from evals.run_extraction import score_case


def item(part_number=None, quantity=1, brand=None, description="part"):
    return LineItem(part_number=part_number, brand=brand, description=description, quantity=quantity)


def test_problems_catches_bad_quantity_and_empty_description():
    rfq = ExtractedRFQ(line_items=[item(quantity=0), item(description="  ")], needed_by=None, notes=None)
    assert problems(rfq) == ["line 1: quantity must be at least 1, got 0", "line 2: description is empty"]


def test_problems_accepts_an_empty_list():
    assert problems(ExtractedRFQ(line_items=[], needed_by=None, notes=None)) == []


def test_score_matches_part_numbers_after_normalizing():
    s = score_case([{"part_number": "6205-2RS1", "brand": None, "quantity": 10}], [item("6205 2rs1", 10)])
    assert s.matched == 1 and s.fully_correct


def test_score_flags_wrong_quantity_and_extra_items():
    s = score_case([{"part_number": "A42", "brand": None, "quantity": 8}], [item("A42", 4), item("B60", 2)])
    assert s.matched == 1 and s.quantity_ok == 0
    assert s.errors == ["A42: quantity 4, expected 8", "extra item 'B60'"]


def test_score_matches_items_without_part_number_by_keywords():
    expected = [{"part_number": None, "brand": None, "quantity": 2, "keywords": ["1.5", "motor"]}]
    s = score_case(expected, [item(None, 2, description="1.5 kW 4 pole motor, foot mounted")])
    assert s.fully_correct
