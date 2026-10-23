from collections import defaultdict

from app.part_numbers import normalize_part_number
from scripts.generate_catalog import build_catalog


def test_normalize_part_number():
    assert normalize_part_number("6205-2RS1") == "62052RS1"
    assert normalize_part_number(" 6205 2rs1 ") == "62052RS1"
    assert normalize_part_number("FR250/10") == "FR25010"


def test_same_seed_gives_same_catalog():
    assert build_catalog(seed=7) == build_catalog(seed=7)


def test_part_numbers_are_unique_per_brand():
    parts = build_catalog().parts
    keys = [(p["brand"], p["part_number"]) for p in parts]
    assert len(keys) == len(set(keys))


def test_interchange_groups_have_one_part_per_brand_and_same_specs():
    groups = defaultdict(list)
    for p in build_catalog().parts:
        groups[p["interchange_group"]].append(p)
    for members in groups.values():
        assert len({p["brand"] for p in members}) == 3
        assert all(p["specs"] == members[0]["specs"] for p in members)


def test_offers_point_at_real_parts_and_sellers():
    catalog = build_catalog()
    part_ids = {p["id"] for p in catalog.parts}
    seller_ids = {s["id"] for s in catalog.sellers}
    for o in catalog.offers:
        assert o["part_id"] in part_ids and o["seller_id"] in seller_ids
        assert o["unit_price"] > 0
        assert (o["stock_qty"] == 0) == (o["lead_time_days"] >= 10)  # out of stock -> long lead time


def test_every_part_has_at_least_one_seller():
    catalog = build_catalog()
    offered = {o["part_id"] for o in catalog.offers}
    missing = [p["part_number"] for p in catalog.parts if p["id"] not in offered]
    assert len(missing) < len(catalog.parts) * 0.1  # a few unstocked parts are realistic


def test_open_bearing_text_does_not_contain_the_word_seals():
    # "open (no seals)" made keyword search match "sealed" queries to open bearings (Day 3 eval)
    open_bearings = [p for p in build_catalog().parts if p["interchange_group"].endswith(":open")]
    assert open_bearings and all("seals" not in p["description"] for p in open_bearings)
