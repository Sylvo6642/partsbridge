"""The buyer's AI pipeline: pasted text -> extraction -> matching agent for every line (in parallel).

Everything runs as the visitor (`as_user`), so the agent's tools can only see what this visitor may see.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from uuid import UUID, uuid4

from app.ai.extraction import ExtractedRFQ, LineItem, extract
from app.ai.matching.agent import MatchResult, match_line
from app.db import as_user

MAX_LINES = 15  # keeps one request's cost bounded


@dataclass
class AnalyzedRequest:
    rfq: ExtractedRFQ
    matches: list[MatchResult]
    trace_id: UUID
    cost_usd: float


def analyze_request(text: str, user_id: UUID) -> AnalyzedRequest:
    trace_id = uuid4()
    extraction = extract(text, trace_id=trace_id, user_id=user_id)
    lines = extraction.rfq.line_items[:MAX_LINES]

    def match_one(line: LineItem) -> MatchResult:
        with as_user(user_id) as conn:
            return match_line(conn, line, trace_id=trace_id, user_id=user_id)

    with ThreadPoolExecutor(max_workers=5) as pool:
        matches = list(pool.map(match_one, lines))
    cost = extraction.cost_usd + sum(m.cost_usd for m in matches)
    return AnalyzedRequest(rfq=extraction.rfq.model_copy(update={"line_items": lines}), matches=matches,
                           trace_id=trace_id, cost_usd=cost)
