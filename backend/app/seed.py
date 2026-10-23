"""Set up a new visitor's sandbox workspace, so they can try both sides alone.

- Their own seller shop, stocked with a copy of a bot seller's catalog (prices, stock).
- Three sample RFQs from bot buyers in their seller inbox, ready to quote on.

Runs with the system connection, writing rows with the new user's workspace_id.
"""

from uuid import UUID

import psycopg

TEMPLATE_SELLER_ID = 1  # Apex Industrial Supply carries all four categories

SAMPLE_RFQS = [
    {
        "buyer_name": "Kestrel Mining (bot buyer)",
        "raw_text": "Hi, please quote 20x 6308-2RS1 and 10x 6310-2Z for our conveyor idlers. "
                    "Delivery to our Perth site within 3 weeks.",
        "needed_by": "within 3 weeks",
        "lines": [("Norvik", "6308-2RS1", 20), ("Norvik", "6310-2Z", 10)],
    },
    {
        "buyer_name": "Harbor Foods (bot buyer)",
        "raw_text": "Need 6 x SPA1250 belts and 4 x SPA1500, plus 2 spin-on oil filters SO-UNF34-140 for the "
                    "compressor. Thanks!",
        "needed_by": None,
        "lines": [("Norvik", "SPA1250", 6), ("Norvik", "SPA1500", 4), ("Norvik", "SO-UNF34-140", 2)],
    },
    {
        "buyer_name": "Vela Water Utility (bot buyer)",
        "raw_text": "Replacement motor K3E05504B3 (5.5 kW 4-pole, foot mounted) x1 and hydraulic return "
                    "elements KH-10250 x 4. Urgent, pump station down.",
        "needed_by": "urgent",
        "lines": [("Kanto Seiko", "K3E05504B3", 1), ("Kanto Seiko", "KH-10250", 4)],
    },
]


def seed_workspace(conn: psycopg.Connection, user_id: UUID, email: str) -> None:
    shop_name = email.split("@")[0].replace(".", " ").title() + " Supply (your shop)"
    seller_id = conn.execute(
        "insert into sellers (name, city, country, shipping_fee, owner_id) values (%s, 'Your city', '--', 20.00, %s) "
        "returning id", (shop_name, user_id),
    ).fetchone()[0]
    conn.execute(
        """insert into offers (seller_id, part_id, unit_price, currency, stock_qty, lead_time_days)
           select %s, part_id, unit_price, currency, stock_qty, lead_time_days from offers where seller_id = %s""",
        (seller_id, TEMPLATE_SELLER_ID),
    )
    for sample in SAMPLE_RFQS:
        rfq_id = conn.execute(
            """insert into rfqs (workspace_id, buyer_name, is_sample, raw_text, needed_by, status, published_at)
               values (%s, %s, true, %s, %s, 'published', now()) returning id""",
            (user_id, sample["buyer_name"], sample["raw_text"], sample["needed_by"]),
        ).fetchone()[0]
        for line_no, (brand, part_number, qty) in enumerate(sample["lines"], start=1):
            part_id, description = conn.execute(
                "select id, description from parts where brand = %s and part_number = %s", (brand, part_number)
            ).fetchone()
            conn.execute(
                """insert into rfq_lines (rfq_id, workspace_id, line_no, part_number_raw, brand_raw, description,
                                          quantity, match_status, suggested_part_ids, part_id)
                   values (%s, %s, %s, %s, null, %s, %s, 'matched', %s, %s)""",
                (rfq_id, user_id, line_no, part_number, description.split(". Brand:")[0], qty, [part_id], part_id),
            )
