"""Generate the synthetic PartsBridge catalog.

Everything here is made up: the brands, sellers, prices and stock levels.
The part-number *formats* follow real industry conventions (a 6205 bearing has a 25 mm bore,
an "A42" V-belt is 42 inches long), so matching a buyer's messy text to a part is a realistic problem.

Three fictional brands make the same physical part under different part numbers.
Parts that are physically interchangeable share an `interchange_group`.

Run from backend/:  python -m scripts.generate_catalog   -> writes data/*.csv
"""

import csv
import json
import random
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from app.part_numbers import normalize_part_number

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SEED = 42

# Premium, mid-range and budget brand. The factor multiplies the base price.
BRANDS = {"Norvik": Decimal("1.15"), "Kanto Seiko": Decimal("1.05"), "Ferrum": Decimal("0.90")}


@dataclass
class Catalog:
    parts: list[dict] = field(default_factory=list)
    sellers: list[dict] = field(default_factory=list)
    offers: list[dict] = field(default_factory=list)


def money(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Each *_groups() function yields one dict per physical part ("interchange group"):
#   group        unique key, e.g. "bearing:6205:sealed"
#   title        short name, e.g. "Deep groove ball bearing"
#   description  plain-English spec line (this is what search will read)
#   specs        structured specs (same for every brand in the group)
#   base_price   price before brand and seller markups
#   numbers      {brand: that brand's part number}

# ---------------------------------------------------------------- bearings
# Deep groove ball bearings: (bore, outer diameter, width) in mm, real ISO dimensions.
BEARING_SIZES = {
    "6000": (10, 26, 8), "6001": (12, 28, 8), "6002": (15, 32, 9), "6003": (17, 35, 10),
    "6004": (20, 42, 12), "6005": (25, 47, 12), "6006": (30, 55, 13), "6007": (35, 62, 14),
    "6008": (40, 68, 15), "6009": (45, 75, 16), "6010": (50, 80, 16),
    "6200": (10, 30, 9), "6201": (12, 32, 10), "6202": (15, 35, 11), "6203": (17, 40, 12),
    "6204": (20, 47, 14), "6205": (25, 52, 15), "6206": (30, 62, 16), "6207": (35, 72, 17),
    "6208": (40, 80, 18), "6209": (45, 85, 19), "6210": (50, 90, 20),
    "6300": (10, 35, 11), "6301": (12, 37, 12), "6302": (15, 42, 13), "6303": (17, 47, 14),
    "6304": (20, 52, 15), "6305": (25, 62, 17), "6306": (30, 72, 19), "6307": (35, 80, 21),
    "6308": (40, 90, 23), "6309": (45, 100, 25), "6310": (50, 110, 27),
}
# sealing type -> (description, price factor, suffix per brand). Each brand writes it differently.
SEALING = {
    "open": ("open (no seals)", 1.00, {"Norvik": "", "Kanto Seiko": "", "Ferrum": ""}),
    "shielded": ("metal shields both sides (ZZ)", 1.15, {"Norvik": "-2Z", "Kanto Seiko": "ZZ", "Ferrum": "-2ZR"}),
    "sealed": ("rubber seals both sides (2RS)", 1.25, {"Norvik": "-2RS1", "Kanto Seiko": "DDU", "Ferrum": "-2RSR"}),
}


def bearing_groups():
    for series, (bore, od, width) in BEARING_SIZES.items():
        for sealing, (label, factor, suffixes) in SEALING.items():
            yield {
                "group": f"bearing:{series}:{sealing}",
                "title": "Deep groove ball bearing",
                "description": f"Deep groove ball bearing, {bore} mm bore x {od} mm outer diameter x "
                               f"{width} mm wide, {label}.",
                "specs": {"series": series, "bore_mm": bore, "outer_diameter_mm": od,
                          "width_mm": width, "sealing": sealing},
                "base_price": (2.0 + od * 0.12 + width * 0.2) * factor,
                "numbers": {brand: series + suffix for brand, suffix in suffixes.items()},
            }


# ---------------------------------------------------------------- belts
# Classical sections (A, B) are sold by inner length in inches; wedge sections (SPA, SPB) by datum length in mm.
BELT_TOP_WIDTH_MM = {"A": 13.0, "B": 17.0, "SPA": 12.7, "SPB": 16.3}


def belt_groups():
    for section, top_width in BELT_TOP_WIDTH_MM.items():
        classical = section in ("A", "B")
        for length in (range(30, 91, 4) if classical else range(1000, 2501, 250)):
            code = f"{section}{length}"
            if classical:
                length_text = f"{length} in inner length ({round(length * 25.4)} mm)"
                base = (3 + length * 0.12) * (1.4 if section == "B" else 1.0)
            else:
                length_text = f"{length} mm datum length"
                base = (4 + length * 0.006) * (1.35 if section == "SPB" else 1.0)
            kind = "Classical V-belt" if classical else "Wedge V-belt"
            yield {
                "group": f"belt:{code}",
                "title": kind,
                "description": f"{kind}, section {section} ({top_width} mm top width), {length_text}.",
                "specs": {"section": section, "length": length, "length_unit": "in" if classical else "mm",
                          "top_width_mm": top_width},
                "base_price": base,
                "numbers": {"Norvik": code, "Kanto Seiko": f"{section}-{length}", "Ferrum": f"FX-{code}"},
            }


# ---------------------------------------------------------------- filters
THREADS = {"UNF34": "3/4-16 UNF", "UN1": "1-12 UN", "M20": "M20x1.5"}


def filter_groups():
    for micron in (3, 10, 25):
        for length in (160, 250, 400):
            yield {
                "group": f"filter:hydraulic:{micron}:{length}",
                "title": "Hydraulic return filter element",
                "description": f"Hydraulic return-line filter element, {micron} micron glass fibre media, "
                               f"{length} mm long.",
                "specs": {"kind": "hydraulic", "micron": micron, "length_mm": length},
                "base_price": 18 + length * 0.05 + (8 if micron == 3 else 0),
                "numbers": {"Norvik": f"HE{length}-{micron}M", "Kanto Seiko": f"KH-{micron:02d}{length}",
                            "Ferrum": f"FR{length}/{micron}"},
            }
    for code, thread in THREADS.items():
        for height in (100, 140):
            yield {
                "group": f"filter:spin-on:{code}:{height}",
                "title": "Spin-on oil filter",
                "description": f"Spin-on oil filter, {thread} thread, {height} mm high, "
                               f"for compressors and gearboxes.",
                "specs": {"kind": "spin-on", "thread": thread, "height_mm": height},
                "base_price": 9 + height * 0.05,
                "numbers": {"Norvik": f"SO-{code}-{height}", "Kanto Seiko": f"KSO{height}{code}",
                            "Ferrum": f"FSO/{code}/{height}"},
            }
    for od, height in ((100, 200), (130, 250), (160, 300)):
        yield {
            "group": f"filter:air:{od}:{height}",
            "title": "Air filter element",
            "description": f"Radial-seal air filter element, {od} mm outer diameter x {height} mm high, "
                           f"for compressor intakes.",
            "specs": {"kind": "air", "outer_diameter_mm": od, "height_mm": height},
            "base_price": 22 + od * 0.1,
            "numbers": {"Norvik": f"AE{od}{height}", "Kanto Seiko": f"KA-{od}-{height}",
                        "Ferrum": f"FA{od}x{height}"},
        }


# ---------------------------------------------------------------- motors
# IEC frame size per power rating: kW -> (2-pole frame, 4-pole frame).
MOTOR_FRAMES = {
    0.37: ("71M", "71M"), 0.55: ("71M", "80M"), 0.75: ("80M", "80M"), 1.1: ("80M", "90S"),
    1.5: ("90S", "90L"), 2.2: ("90L", "100L"), 3.0: ("100L", "100L"), 4.0: ("112M", "112M"),
    5.5: ("132S", "132S"), 7.5: ("132S", "132M"), 11.0: ("160M", "160M"),
}
MOUNTINGS = {"B3": "foot mounted (B3)", "B5": "flange mounted (B5)"}


def motor_groups():
    for kw, frames in MOTOR_FRAMES.items():
        for poles, frame in zip((2, 4), frames):
            for mount, mount_text in MOUNTINGS.items():
                rpm = 2900 if poles == 2 else 1450
                kw_text = f"{kw:g}"  # 3.0 -> "3", 1.5 -> "1.5"
                yield {
                    "group": f"motor:{kw_text}kw:{poles}p:{mount}",
                    "title": "IE3 three-phase motor",
                    "description": f"Three-phase induction motor IE3, {kw_text} kW, {poles}-pole ({rpm} rpm), "
                                   f"IEC frame {frame}, {mount_text}, 400 V 50 Hz.",
                    "specs": {"power_kw": kw, "poles": poles, "speed_rpm": rpm, "frame": frame,
                              "mounting": mount, "efficiency_class": "IE3", "voltage": "400 V 50 Hz"},
                    "base_price": (120 + kw * 55) * (1.08 if mount == "B5" else 1.0),
                    "numbers": {"Norvik": f"NM3-{frame}-{poles}P-{kw_text}KW-{mount}",
                                "Kanto Seiko": f"K3E{round(kw * 100):04d}{poles}{mount}",
                                "Ferrum": f"FM-IE3-{frame}{poles}-{kw_text}-{mount}"},
                }


CATEGORIES = {"bearing": bearing_groups, "belt": belt_groups, "filter": filter_groups, "motor": motor_groups}

# ---------------------------------------------------------------- sellers
SELLERS = [
    {"id": 1, "name": "Apex Industrial Supply", "city": "Houston", "country": "US", "shipping_fee": "25.00",
     "categories": ["bearing", "belt", "filter", "motor"]},
    {"id": 2, "name": "Rhine Bearing & Drive", "city": "Duisburg", "country": "DE", "shipping_fee": "30.00",
     "categories": ["bearing", "belt"]},
    {"id": 3, "name": "Gulf Motion Parts", "city": "Dubai", "country": "AE", "shipping_fee": "35.00",
     "categories": ["motor", "filter"]},
    {"id": 4, "name": "Deccan Power Transmission", "city": "Pune", "country": "IN", "shipping_fee": "15.00",
     "categories": ["bearing", "belt", "motor"]},
    {"id": 5, "name": "Northwind MRO", "city": "Rotterdam", "country": "NL", "shipping_fee": "28.00",
     "categories": ["filter", "bearing"]},
]


def build_catalog(seed: int = SEED) -> Catalog:
    """Build the whole catalog. Same seed -> same catalog, so eval scores stay comparable."""
    rng = random.Random(seed)
    catalog = Catalog()
    base_prices: dict[int, Decimal] = {}

    for category, groups in CATEGORIES.items():
        for g in groups():
            for brand, brand_factor in BRANDS.items():
                part_number = g["numbers"][brand]
                part_id = len(catalog.parts) + 1
                catalog.parts.append({
                    "id": part_id,
                    "brand": brand,
                    "part_number": part_number,
                    "part_number_norm": normalize_part_number(part_number),
                    "category": category,
                    "name": f"{brand} {part_number} {g['title']}",
                    "description": f"{g['description']} Brand: {brand}.",
                    "specs": g["specs"],
                    "interchange_group": g["group"],
                })
                base_prices[part_id] = money(g["base_price"]) * brand_factor

    for seller in SELLERS:
        markup = Decimal(str(rng.uniform(0.95, 1.25)))  # some sellers are cheaper than others
        catalog.sellers.append({k: v for k, v in seller.items() if k != "categories"})
        for part in catalog.parts:
            if part["category"] not in seller["categories"] or rng.random() > 0.6:
                continue  # each seller carries ~60% of the parts in its categories
            in_stock = rng.random() > 0.3
            max_qty = 15 if part["category"] == "motor" else 200
            noise = Decimal(str(rng.uniform(0.97, 1.03)))
            catalog.offers.append({
                "seller_id": seller["id"],
                "part_id": part["id"],
                "unit_price": money(base_prices[part["id"]] * markup * noise),
                "stock_qty": rng.randint(1, max_qty) if in_stock else 0,
                "lead_time_days": rng.randint(1, 3) if in_stock else rng.randint(10, 30),
            })
    return catalog


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, dict) else v for k, v in row.items()})


def main() -> None:
    catalog = build_catalog()
    DATA_DIR.mkdir(exist_ok=True)
    write_csv(DATA_DIR / "parts.csv", catalog.parts)
    write_csv(DATA_DIR / "sellers.csv", catalog.sellers)
    write_csv(DATA_DIR / "offers.csv", catalog.offers)
    groups = {p["interchange_group"] for p in catalog.parts}
    print(f"{len(catalog.parts)} parts in {len(groups)} interchange groups, "
          f"{len(catalog.sellers)} sellers, {len(catalog.offers)} offers -> {DATA_DIR}")


if __name__ == "__main__":
    main()
