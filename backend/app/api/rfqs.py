"""Buyer side: paste a request, let the AI build the parts list, check it, publish it, accept a quote.

Every query runs through `as_user`, so Row Level Security limits it to the caller's workspace.
"""

from uuid import UUID

import psycopg
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from app.ai.extraction import ExtractionError
from app.ai.llm import LLMError
from app.ai.pipeline import analyze_request
from app.auth import User, current_user
from app.db import as_user, connect

router = APIRouter(tags=["buyer"])

PART_FIELDS = "id, brand, part_number, description, interchange_group, category, specs"


def _part(row) -> dict:
    return {"part_id": row[0], "brand": row[1], "part_number": row[2],
            "description": row[3].rsplit(" Brand:", 1)[0], "category": row[5], "specs": row[6]}


def parts_by_id(conn: psycopg.Connection, ids: list[int]) -> dict[int, dict]:
    rows = conn.execute(f"select {PART_FIELDS} from parts where id = any(%s)", (ids,)).fetchall()
    return {r[0]: _part(r) | {"group": r[4]} for r in rows}


def brand_options(conn: psycopg.Connection, groups: list[str]) -> dict[str, list[dict]]:
    rows = conn.execute(f"select {PART_FIELDS} from parts where interchange_group = any(%s) order by id",
                        (groups,)).fetchall()
    options: dict[str, list[dict]] = {}
    for r in rows:
        options.setdefault(r[4], []).append(_part(r))
    return options


def ai_summary(trace_id: UUID | None) -> dict | None:
    """What the AI did for one request, from the llm_calls log (read by the system: users can't read the log)."""
    if not trace_id:
        return None
    with connect() as conn:
        rows = conn.execute(
            """select feature, count(*), sum(input_tokens + output_tokens), sum(cost_usd), sum(latency_ms)
               from llm_calls where trace_id = %s group by feature""", (trace_id,),
        ).fetchall()
    if not rows:
        return None
    return {
        "model_calls": sum(r[1] for r in rows),
        "tokens": sum(r[2] for r in rows),
        "cost_usd": float(sum(r[3] for r in rows)),
        "model_time_ms": sum(r[4] for r in rows),
        "by_feature": {r[0]: r[1] for r in rows},
    }


def rfq_detail(conn: psycopg.Connection, rfq_id: UUID) -> dict:
    rfq = conn.execute(
        """select id, buyer_name, is_sample, raw_text, needed_by, notes, status, created_at, published_at, ai_trace_id
           from rfqs where id = %s""", (rfq_id,),
    ).fetchone()
    if not rfq:
        raise HTTPException(404, "RFQ not found")  # also what another workspace's RFQ looks like (RLS)
    lines = conn.execute(
        """select id, line_no, part_number_raw, brand_raw, description, quantity, match_status, match_reason,
                  suggested_part_ids, part_id
           from rfq_lines where rfq_id = %s order by line_no""", (rfq_id,),
    ).fetchall()
    ids = {i for line in lines for i in line[8]} | {line[9] for line in lines if line[9]}
    parts = parts_by_id(conn, list(ids))
    options = brand_options(conn, list({p["group"] for p in parts.values()}))
    keys = ("id", "buyer_name", "is_sample", "raw_text", "needed_by", "notes", "status", "created_at",
            "published_at")
    return {
        **dict(zip(keys, rfq)),
        "ai": ai_summary(rfq[9]),
        "lines": [{
            "id": line[0], "line_no": line[1], "part_number_raw": line[2], "brand_raw": line[3],
            "description": line[4], "quantity": line[5], "match_status": line[6], "match_reason": line[7],
            "part": {k: v for k, v in parts[line[9]].items() if k != "group"} if line[9] else None,
            "suggestions": [{**{k: v for k, v in parts[i].items() if k != "group"},
                             "brand_options": options[parts[i]["group"]]} for i in line[8] if i in parts],
        } for line in lines],
        "quotes": quotes_for(conn, rfq_id),
    }


def quotes_for(conn: psycopg.Connection, rfq_id: UUID) -> list[dict]:
    rows = conn.execute(
        """select q.id, s.name, s.owner_id is not null, q.status, q.subtotal, q.shipping, q.total,
                  q.lead_time_days, q.notes, q.submitted_at,
                  (select count(*) from quote_lines ql where ql.quote_id = q.id and ql.part_id is null)
           from quotes q join sellers s on s.id = q.seller_id
           where q.rfq_id = %s and q.status <> 'draft' order by q.total nulls last""", (rfq_id,),
    ).fetchall()
    keys = ("id", "seller_name", "is_your_shop", "status", "subtotal", "shipping", "total", "lead_time_days",
            "notes", "submitted_at", "lines_not_supplied")
    return [dict(zip(keys, r)) for r in rows]


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=3, max_length=4000)


@router.post("/rfqs/analyze", status_code=201)
def analyze(body: AnalyzeRequest, user: User = Depends(current_user)):
    """The AI step: extract the parts list and match every line. Saves a draft RFQ for the buyer to check."""
    try:
        result = analyze_request(body.text, user.id)
    except (LLMError, ExtractionError) as e:
        raise HTTPException(502, f"The AI step failed: {e}") from e
    if not result.rfq.line_items:
        raise HTTPException(422, "No parts found in that message. Try listing part numbers or descriptions.")
    with as_user(user.id) as conn:
        rfq_id = conn.execute(
            """insert into rfqs (buyer_name, raw_text, needed_by, notes, ai_trace_id)
               values ('You', %s, %s, %s, %s) returning id""",
            (body.text, result.rfq.needed_by, result.rfq.notes, result.trace_id),
        ).fetchone()[0]
        for line_no, (item, match) in enumerate(zip(result.rfq.line_items, result.matches), start=1):
            d = match.decision
            suggested = [d.part_id] if d.status == "matched" and d.part_id else d.candidate_part_ids
            conn.execute(
                """insert into rfq_lines (rfq_id, line_no, part_number_raw, brand_raw, description, quantity,
                                          match_status, match_reason, suggested_part_ids, part_id)
                   values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (rfq_id, line_no, item.part_number, item.brand, item.description, item.quantity, d.status,
                 d.reason, suggested, d.part_id if d.status == "matched" else None),
            )
        detail = rfq_detail(conn, rfq_id)
    return detail


@router.get("/rfqs")
def list_rfqs(user: User = Depends(current_user)):
    with as_user(user.id) as conn:
        rows = conn.execute(
            """select r.id, r.raw_text, r.status, r.created_at,
                      (select count(*) from rfq_lines l where l.rfq_id = r.id),
                      (select count(*) from quotes q where q.rfq_id = r.id and q.status <> 'draft')
               from rfqs r where not r.is_sample order by r.created_at desc""",
        ).fetchall()
    keys = ("id", "raw_text", "status", "created_at", "line_count", "quote_count")
    return [dict(zip(keys, r)) for r in rows]


@router.get("/rfqs/{rfq_id}")
def get_rfq(rfq_id: UUID, user: User = Depends(current_user)):
    with as_user(user.id) as conn:
        return rfq_detail(conn, rfq_id)


def _own_draft(conn: psycopg.Connection, rfq_id: UUID) -> None:
    row = conn.execute("select status, is_sample from rfqs where id = %s", (rfq_id,)).fetchone()
    if not row:
        raise HTTPException(404, "RFQ not found")
    if row[1] or row[0] != "draft":
        raise HTTPException(409, "Only your own draft RFQs can be changed")


class LineUpdate(BaseModel):
    part_id: int | None = None
    quantity: int | None = Field(default=None, ge=1, le=100000)


@router.patch("/rfqs/{rfq_id}/lines/{line_id}")
def update_line(rfq_id: UUID, line_id: UUID, body: LineUpdate, user: User = Depends(current_user)):
    """The buyer picks a part (any brand of a part the AI suggested) or changes the quantity."""
    with as_user(user.id) as conn:
        _own_draft(conn, rfq_id)
        line = conn.execute("select suggested_part_ids from rfq_lines where id = %s and rfq_id = %s",
                            (line_id, rfq_id)).fetchone()
        if not line:
            raise HTTPException(404, "Line not found")
        if body.part_id is not None:
            allowed = conn.execute(
                """select 1 from parts where id = %s and interchange_group in
                   (select interchange_group from parts where id = any(%s))""", (body.part_id, line[0]),
            ).fetchone()
            if not allowed:
                raise HTTPException(400, "Pick one of the suggested parts (any brand)")
            conn.execute("update rfq_lines set part_id = %s where id = %s", (body.part_id, line_id))
        if body.quantity is not None:
            conn.execute("update rfq_lines set quantity = %s where id = %s", (body.quantity, line_id))
        return rfq_detail(conn, rfq_id)


@router.delete("/rfqs/{rfq_id}/lines/{line_id}")
def delete_line(rfq_id: UUID, line_id: UUID, user: User = Depends(current_user)):
    with as_user(user.id) as conn:
        _own_draft(conn, rfq_id)
        conn.execute("delete from rfq_lines where id = %s and rfq_id = %s", (line_id, rfq_id))
        return rfq_detail(conn, rfq_id)


@router.post("/rfqs/{rfq_id}/publish")
def publish(rfq_id: UUID, background: BackgroundTasks, user: User = Depends(current_user)):
    """The buyer confirms the parts list. Every line needs a part; then sellers can quote."""
    with as_user(user.id) as conn:
        _own_draft(conn, rfq_id)
        counts = conn.execute(
            "select count(*), count(part_id) from rfq_lines where rfq_id = %s", (rfq_id,)
        ).fetchone()
        if counts[0] == 0:
            raise HTTPException(400, "Add at least one line")
        if counts[0] != counts[1]:
            raise HTTPException(400, "Choose a part for every line (or remove the line) before publishing")
        conn.execute("update rfqs set status = 'published', published_at = now() where id = %s", (rfq_id,))
        detail = rfq_detail(conn, rfq_id)
    from app.bots import quote_as_bot_sellers  # Day 7: bot sellers answer every published RFQ
    background.add_task(quote_as_bot_sellers, rfq_id, user.id)
    return detail
