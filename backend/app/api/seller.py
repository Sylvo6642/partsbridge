"""Seller side: inbox, draft a quote with AI, edit it, submit it. A person approves every quote.

The seller is always the caller's own shop (looked up under RLS), never something the client or the AI chooses.
"""

from decimal import Decimal
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.ai.llm import LLMError
from app.api.rfqs import ai_summary, parts_by_id, rfq_detail
from app.auth import User, current_user
from app.db import as_user
from app.quotes import draft_and_save, reprice

router = APIRouter(tags=["seller"])


def my_shop(conn: psycopg.Connection, user: User) -> int:
    row = conn.execute("select id from sellers where owner_id = %s", (user.id,)).fetchone()
    if not row:
        raise HTTPException(404, "No seller shop for this account")
    return row[0]


@router.get("/seller/inbox")
def inbox(user: User = Depends(current_user)):
    with as_user(user.id) as conn:
        shop = my_shop(conn, user)
        rows = conn.execute(
            """select r.id, r.buyer_name, r.is_sample, r.raw_text, r.needed_by, r.status, r.published_at,
                      (select count(*) from rfq_lines l where l.rfq_id = r.id),
                      (select q.status from quotes q where q.rfq_id = r.id and q.seller_id = %s),
                      (select q.total from quotes q where q.rfq_id = r.id and q.seller_id = %s)
               from rfqs r where r.status <> 'draft' order by r.published_at desc""", (shop, shop),
        ).fetchall()
    keys = ("id", "buyer_name", "is_sample", "raw_text", "needed_by", "status", "published_at", "line_count",
            "my_quote_status", "my_quote_total")
    return [dict(zip(keys, r)) for r in rows]


def my_quote(conn: psycopg.Connection, rfq_id: UUID, shop: int) -> dict | None:
    q = conn.execute(
        """select id, status, subtotal, shipping, total, lead_time_days, notes, ai_trace_id, submitted_at
           from quotes where rfq_id = %s and seller_id = %s""", (rfq_id, shop),
    ).fetchone()
    if not q:
        return None
    lines = conn.execute(
        """select ql.id, ql.rfq_line_id, ql.part_id, ql.quantity, ql.unit_price, ql.line_total, ql.lead_time_days,
                  ql.note, o.stock_qty
           from quote_lines ql join rfq_lines rl on rl.id = ql.rfq_line_id
           left join offers o on o.part_id = ql.part_id and o.seller_id = %s
           where ql.quote_id = %s order by rl.line_no""", (shop, q[0]),
    ).fetchall()
    parts = parts_by_id(conn, [l[2] for l in lines if l[2]])
    return {
        "id": q[0], "status": q[1], "subtotal": q[2], "shipping": q[3], "total": q[4], "lead_time_days": q[5],
        "notes": q[6], "submitted_at": q[8], "ai": ai_summary(q[7]),
        "lines": [{"id": l[0], "rfq_line_id": l[1],
                   "part": {k: v for k, v in parts[l[2]].items() if k != "group"} if l[2] else None,
                   "quantity": l[3], "unit_price": l[4], "line_total": l[5], "lead_time_days": l[6], "note": l[7],
                   "stock_qty": l[8]} for l in lines],
    }


@router.get("/seller/rfqs/{rfq_id}")
def seller_rfq(rfq_id: UUID, user: User = Depends(current_user)):
    with as_user(user.id) as conn:
        shop = my_shop(conn, user)
        detail = rfq_detail(conn, rfq_id)
        if detail["status"] == "draft":
            raise HTTPException(404, "RFQ not found")
        return {**detail, "my_quote": my_quote(conn, rfq_id, shop)}


@router.post("/seller/rfqs/{rfq_id}/draft")
def draft(rfq_id: UUID, user: User = Depends(current_user)):
    """Draft (or redraft) this shop's quote with AI. It stays a draft until the seller submits it."""
    with as_user(user.id) as conn:
        shop = my_shop(conn, user)
        status = conn.execute("select status from rfqs where id = %s", (rfq_id,)).fetchone()
        if not status or status[0] != "published":
            raise HTTPException(409, "This request isn't open for quotes")
        if conn.execute("select 1 from quotes where rfq_id = %s and seller_id = %s and status <> 'draft'",
                        (rfq_id, shop)).fetchone():
            raise HTTPException(409, "You already submitted a quote for this request")
        try:
            draft_and_save(conn, rfq_id, shop, user.id, user_id=user.id, submit=False)
        except LLMError as e:
            raise HTTPException(502, f"The AI step failed: {e}") from e
        return {**rfq_detail(conn, rfq_id), "my_quote": my_quote(conn, rfq_id, shop)}


class QuoteLineEdit(BaseModel):
    id: UUID
    quantity: int = Field(ge=0, le=100000)
    unit_price: Decimal | None = Field(default=None, ge=Decimal("0.01"), le=Decimal("1000000"), decimal_places=2)


class QuoteEdit(BaseModel):
    lines: list[QuoteLineEdit] = []
    notes: str | None = Field(default=None, max_length=1000)


def _own_draft_quote(conn: psycopg.Connection, quote_id: UUID, shop: int) -> UUID:
    row = conn.execute("select rfq_id, status, seller_id from quotes where id = %s", (quote_id,)).fetchone()
    if not row or row[2] != shop:
        raise HTTPException(404, "Quote not found")
    if row[1] != "draft":
        raise HTTPException(409, "This quote was already submitted")
    return row[0]


@router.put("/quotes/{quote_id}")
def edit_quote(quote_id: UUID, body: QuoteEdit, user: User = Depends(current_user)):
    """The seller changes quantities, prices or the note. Every amount is recalculated in code."""
    with as_user(user.id) as conn:
        shop = my_shop(conn, user)
        rfq_id = _own_draft_quote(conn, quote_id, shop)
        reprice(conn, quote_id, {l.id: (l.quantity, l.unit_price) for l in body.lines}, body.notes)
        return {**rfq_detail(conn, rfq_id), "my_quote": my_quote(conn, rfq_id, shop)}


@router.post("/quotes/{quote_id}/submit")
def submit_quote(quote_id: UUID, user: User = Depends(current_user)):
    """The person's approval: only now does the buyer see the quote."""
    with as_user(user.id) as conn:
        shop = my_shop(conn, user)
        rfq_id = _own_draft_quote(conn, quote_id, shop)
        conn.execute("update quotes set status = 'submitted', submitted_at = now() where id = %s", (quote_id,))
        return {**rfq_detail(conn, rfq_id), "my_quote": my_quote(conn, rfq_id, shop)}
