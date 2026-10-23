"""PartsBridge API.

Run from backend/:  uvicorn app.main:app --reload   then open http://127.0.0.1:8000/docs
Login comes on Day 5. Until then this API is for local use only.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.ai.extraction import ExtractedRFQ, ExtractionError, extract
from app.ai.llm import LLMError
from app.db import connect
from app.part_numbers import normalize_part_number

app = FastAPI(title="PartsBridge API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/parts")
def find_parts(part_number: str):
    """Exact part-number lookup (normalized, so '6205 2rs1' finds '6205-2RS1')."""
    with connect() as conn:
        rows = conn.execute(
            "select id, brand, part_number, name, description from parts where part_number_norm = %s",
            (normalize_part_number(part_number),),
        ).fetchall()
    return [dict(zip(("id", "brand", "part_number", "name", "description"), r)) for r in rows]


class ExtractRequest(BaseModel):
    text: str


@app.post("/extract", response_model=ExtractedRFQ)
def extract_parts(body: ExtractRequest):
    """Messy buyer message in, checked parts list out."""
    try:
        return extract(body.text).rfq
    except (LLMError, ExtractionError) as e:
        raise HTTPException(status_code=502, detail=str(e))
