"""Create and price quotes. Used by the seller API (a person approves) and by bot sellers (auto-submit)."""

from decimal import Decimal
from uuid import UUID, uuid4

import psycopg

from app.ai.quoting.agent import QuoteRequestLine, QuoteResult, draft_quote, price_quote


def rfq_lines_for_quote(conn: psycopg.Connection, rfq_id: UUID) -> list[QuoteRequestLine]:
    rows = conn.execute(
        "select id, part_id, quantity, description from rfq_lines where rfq_id = %s and part_id is not null "
        "order by line_no", (rfq_id,),
    ).fetchall()
    return [QuoteRequestLine(str(r[0]), r[1], r[2], r[3]) for r in rows]


def draft_and_save(conn: psycopg.Connection, rfq_id: UUID, seller_id: int, workspace_id: UUID, *,
                   user_id: UUID | None, submit: bool) -> tuple[UUID, QuoteResult]:
    """Run the quote AI for one seller, price every line in code, and store the quote (replacing a draft)."""
    notes = conn.execute("select coalesce(notes, '') || ' ' || raw_text from rfqs where id = %s",
                         (rfq_id,)).fetchone()[0]
    lines = rfq_lines_for_quote(conn, rfq_id)
    trace_id = uuid4()
    result = draft_quote(conn, seller_id, lines, notes, trace_id=trace_id, user_id=user_id)
    priced = price_quote(conn, seller_id, [(l.line_id, result.decisions[l.line_id].part_id, l.quantity) for l in lines])

    conn.execute("delete from quotes where rfq_id = %s and seller_id = %s and status = 'draft'", (rfq_id, seller_id))
    quote_id = conn.execute(
        """insert into quotes (rfq_id, workspace_id, seller_id, status, subtotal, shipping, total, lead_time_days,
                               notes, ai_trace_id, submitted_at)
           values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, case when %s then now() end) returning id""",
        (rfq_id, workspace_id, seller_id, "submitted" if submit else "draft", priced.subtotal, priced.shipping,
         priced.total, priced.lead_time_days, result.summary, trace_id, submit),
    ).fetchone()[0]
    for line, p in zip(lines, priced.lines):
        conn.execute(
            """insert into quote_lines (quote_id, workspace_id, rfq_line_id, part_id, quantity, unit_price,
                                        line_total, lead_time_days, note)
               values (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (quote_id, workspace_id, line.line_id, p.part_id, p.quantity, p.unit_price, p.line_total,
             p.lead_time_days, result.decisions[line.line_id].note or None),
        )
    return quote_id, result


def reprice(conn: psycopg.Connection, quote_id: UUID, edits: dict[UUID, tuple[int, Decimal | None]],
            notes: str | None) -> None:
    """A person edited quantities or prices: recompute every amount in code."""
    seller_id = conn.execute("select seller_id from quotes where id = %s", (quote_id,)).fetchone()[0]
    rows = conn.execute("select id, part_id, quantity, unit_price from quote_lines where quote_id = %s",
                        (quote_id,)).fetchall()
    chosen, overrides = [], {}
    for line_id, part_id, qty, unit in rows:
        new_qty, new_price = edits.get(line_id, (qty, None))
        chosen.append((str(line_id), part_id, new_qty))
        overrides[str(line_id)] = new_price if new_price is not None else unit
    priced = price_quote(conn, seller_id, chosen, {k: v for k, v in overrides.items() if v is not None})
    for p in priced.lines:
        conn.execute("update quote_lines set quantity = %s, unit_price = %s, line_total = %s, lead_time_days = %s "
                     "where id = %s", (p.quantity, p.unit_price, p.line_total, p.lead_time_days, p.line_id))
    conn.execute("update quotes set subtotal = %s, shipping = %s, total = %s, lead_time_days = %s, "
                 "notes = coalesce(%s, notes) where id = %s",
                 (priced.subtotal, priced.shipping, priced.total, priced.lead_time_days, notes, quote_id))
