"""The one place that talks to OpenAI.

Every call is timed, priced and logged to llm_calls, so we always know what the AI costs.
"""

import time
from dataclasses import dataclass
from functools import cache
from uuid import UUID, uuid4

from openai import OpenAI
from pydantic import BaseModel

from app.ai import tracing
from app.config import settings

MODEL = "gpt-4o-mini"

# USD per 1 million tokens: (input, output). Check https://openai.com/api/pricing when adding a model.
PRICES = {"gpt-4o-mini": (0.15, 0.60)}


class LLMError(Exception):
    pass


@dataclass
class LLMResult[T: BaseModel]:
    output: T
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int


@cache
def client() -> OpenAI:
    if not settings.openai_api_key:
        raise LLMError("OPENAI_API_KEY is not set in .env")
    return OpenAI(api_key=settings.openai_api_key)


def cost(model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = PRICES[model]
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


def parse[T: BaseModel](*, feature: str, prompt_version: str, instructions: str, input: str, schema: type[T],
                        model: str = MODEL, trace_id: UUID | None = None,
                        user_id: UUID | None = None) -> LLMResult[T]:
    """Ask the model for an answer that fits `schema` (structured output) and log the call."""
    trace_id = trace_id or uuid4()
    log = dict(trace_id=trace_id, user_id=user_id, feature=feature, prompt_version=prompt_version, model=model)
    start = time.perf_counter()
    try:
        response = client().responses.parse(model=model, instructions=instructions, input=input,
                                            text_format=schema, temperature=0)
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000)
        tracing.log_call(**log, input_tokens=0, output_tokens=0, cost_usd=0, latency_ms=latency_ms,
                         ok=False, error=str(e)[:500])
        raise LLMError(f"OpenAI call failed: {e}") from e

    latency_ms = round((time.perf_counter() - start) * 1000)
    tokens_in, tokens_out = response.usage.input_tokens, response.usage.output_tokens
    usd = cost(model, tokens_in, tokens_out)
    parsed = response.output_parsed
    tracing.log_call(**log, input_tokens=tokens_in, output_tokens=tokens_out, cost_usd=usd,
                     latency_ms=latency_ms, ok=parsed is not None,
                     error=None if parsed is not None else "no parsed output (refusal?)")
    if parsed is None:
        raise LLMError("The model returned no structured output (it may have refused).")
    return LLMResult(output=parsed, input_tokens=tokens_in, output_tokens=tokens_out,
                     cost_usd=usd, latency_ms=latency_ms)
