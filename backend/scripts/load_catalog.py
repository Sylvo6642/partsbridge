"""Load data/*.csv into the database. Safe to re-run: it replaces the catalog each time.

Run from backend/:  python -m scripts.load_catalog
"""

import csv
from pathlib import Path

from app.db import connect

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

TABLES = {  # loaded in this order because offers point at sellers and parts
    "sellers": ["id", "name", "city", "country", "shipping_fee"],
    "parts": ["id", "brand", "part_number", "part_number_norm", "category", "name", "description",
              "specs", "interchange_group"],
    "offers": ["seller_id", "part_id", "unit_price", "stock_qty", "lead_time_days"],
}


def main() -> None:
    with connect() as conn:
        conn.execute("truncate offers, parts, sellers")
        for table, columns in TABLES.items():
            with (DATA_DIR / f"{table}.csv").open(encoding="utf-8") as f:
                rows = [[row[c] for c in columns] for row in csv.DictReader(f)]
            placeholders = ", ".join(["%s"] * len(columns))
            with conn.cursor() as cur:
                cur.executemany(f"insert into {table} ({', '.join(columns)}) values ({placeholders})", rows)
            print(f"{table}: {len(rows)} rows")


if __name__ == "__main__":
    main()
