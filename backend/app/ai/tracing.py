"""Write every AI call to the llm_calls table.

Logging must never break the feature: if the database is down, we warn and carry on.
"""

import logging
from uuid import UUID

from app.db import connect

log = logging.getLogger(__name__)


def log_call(*, trace_id: UUID, user_id: UUID | None, feature: str, prompt_version: str, model: str,
             input_tokens: int, output_tokens: int, cost_usd: float, latency_ms: int,
             ok: bool, error: str | None = None) -> None:
    try:
        with connect() as conn:
            conn.execute(
                """insert into llm_calls (trace_id, user_id, feature, prompt_version, model, input_tokens,
                                          output_tokens, cost_usd, latency_ms, ok, error)
                   values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (trace_id, user_id, feature, prompt_version, model, input_tokens, output_tokens,
                 cost_usd, latency_ms, ok, error),
            )
    except Exception as e:  # noqa: BLE001 (tracing is best effort)
        log.warning("could not log llm call: %s", e)
