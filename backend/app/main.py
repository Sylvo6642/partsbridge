"""PartsBridge API.

Run from backend/:  uvicorn app.main:app --port 8010   then open http://127.0.0.1:8010/docs
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.ai.extraction import ExtractedRFQ, ExtractionError, extract
from app.ai.llm import LLMError
from app.ai.matching import search
from app.api import account, rfqs
from app.auth import User, current_user
from app.config import settings
from app.db import as_user

app = FastAPI(title="PartsBridge API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.frontend_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(account.router)
app.include_router(rfqs.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---- developer endpoints (log in required, because they cost money) ----

@app.get("/search", tags=["developer"])
def search_parts(q: str, part_number: str | None = None, limit: int = 10, user: User = Depends(current_user)):
    """Hybrid catalog search: part number + keyword + meaning, merged with RRF."""
    with as_user(user.id) as conn:
        hits = search.hybrid(conn, q, part_number, limit=min(limit, 20))
    return [{**h.__dict__, "score": round(h.score, 4)} for h in hits]


class ExtractRequest(BaseModel):
    text: str


@app.post("/extract", response_model=ExtractedRFQ, tags=["developer"])
def extract_parts(body: ExtractRequest, user: User = Depends(current_user)):
    """Messy buyer message in, checked parts list out (extraction only, no matching)."""
    try:
        return extract(body.text, user_id=user.id).rfq
    except (LLMError, ExtractionError) as e:
        raise HTTPException(status_code=502, detail=str(e))
