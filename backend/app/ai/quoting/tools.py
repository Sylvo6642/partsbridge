"""Tools for the quote agent. They read ONE seller's offers; the seller is fixed by the server, never by the model."""

import json

import psycopg

TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "check_offers",
        "description": "For each part_id, what this seller has: carried or not, unit price, stock on hand and lead "
                       "time in days.",
        "parameters": {
            "type": "object",
            "properties": {"part_ids": {"type": "array", "items": {"type": "integer"}}},
            "required": ["part_ids"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "find_equivalent",
        "description": "Interchangeable parts from other brands (same physical part) that this seller carries, with "
                       "price, stock and lead time.",
        "parameters": {
            "type": "object",
            "properties": {"part_id": {"type": "integer"}},
            "required": ["part_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def check_offers(conn: psycopg.Connection, seller_id: int, part_ids: list[int]) -> list[dict]:
    rows = conn.execute(
        """select p.id, p.brand, p.part_number, o.unit_price, o.stock_qty, o.lead_time_days
           from parts p left join offers o on o.part_id = p.id and o.seller_id = %s
           where p.id = any(%s) order by p.id""", (seller_id, part_ids),
    ).fetchall()
    return [{"part_id": r[0], "brand": r[1], "part_number": r[2], "carried": r[3] is not None,
             "unit_price": str(r[3]) if r[3] is not None else None, "stock_qty": r[4], "lead_time_days": r[5]}
            for r in rows]


def find_equivalent(conn: psycopg.Connection, seller_id: int, part_id: int) -> list[dict]:
    rows = conn.execute(
        """select p.id, p.brand, p.part_number, o.unit_price, o.stock_qty, o.lead_time_days
           from parts p join offers o on o.part_id = p.id and o.seller_id = %s
           where p.interchange_group = (select interchange_group from parts where id = %s) and p.id <> %s
           order by o.unit_price""", (seller_id, part_id, part_id),
    ).fetchall()
    if not rows:
        return [{"result": "this seller carries no equivalent of that part"}]
    return [{"part_id": r[0], "brand": r[1], "part_number": r[2], "unit_price": str(r[3]), "stock_qty": r[4],
             "lead_time_days": r[5]} for r in rows]


def run_tool(conn: psycopg.Connection, seller_id: int, name: str, arguments_json: str) -> list[dict]:
    try:
        args = json.loads(arguments_json)
        if name == "check_offers":
            return check_offers(conn, seller_id, [int(i) for i in args["part_ids"]][:30])
        if name == "find_equivalent":
            return find_equivalent(conn, seller_id, int(args["part_id"]))
        return [{"error": f"unknown tool {name}"}]
    except Exception as e:  # noqa: BLE001 (the model sees the error and can try again)
        return [{"error": f"{type(e).__name__}: {e}"}]
