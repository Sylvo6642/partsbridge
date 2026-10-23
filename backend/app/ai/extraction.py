"""Extraction: turn a buyer's messy message into a checked parts list.

1. The model answers in a fixed shape (structured output, the Pydantic models below).
2. We check the answer with plain code (`problems`).
3. If something is wrong, we ask once more and tell the model what was wrong.
"""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.ai import llm

PROMPT_VERSION = "extraction_v3"
PROMPTS_DIR = Path(__file__).parent / "prompts"


class LineItem(BaseModel):
    part_number: str | None = Field(description="Part number exactly as the buyer wrote it, or null")
    brand: str | None = Field(description="Brand named by the buyer for this part, or null")
    description: str = Field(description="Short description of the part in the buyer's words")
    quantity: int = Field(description="How many units; 1 if not stated")


class ExtractedRFQ(BaseModel):
    line_items: list[LineItem]
    needed_by: str | None = Field(description="When the parts are needed, or null")
    notes: str | None = Field(description="Other details that matter for a quote, or null")


@dataclass
class ExtractionResult:
    rfq: ExtractedRFQ
    attempts: int
    cost_usd: float
    latency_ms: int


class ExtractionError(Exception):
    pass


def load_prompt(version: str) -> str:
    return (PROMPTS_DIR / f"{version}.md").read_text(encoding="utf-8")


def problems(rfq: ExtractedRFQ) -> list[str]:
    """Rules the model's answer must follow. Plain code, not AI."""
    found = []
    for i, item in enumerate(rfq.line_items, start=1):
        if item.quantity < 1:
            found.append(f"line {i}: quantity must be at least 1, got {item.quantity}")
        if not item.description.strip():
            found.append(f"line {i}: description is empty")
    return found


def extract(text: str, *, prompt_version: str = PROMPT_VERSION, trace_id: UUID | None = None,
            user_id: UUID | None = None) -> ExtractionResult:
    trace_id = trace_id or uuid4()
    instructions = load_prompt(prompt_version)
    message = text
    total_cost, total_ms = 0.0, 0

    for attempt in (1, 2):
        result = llm.parse(feature="extraction", prompt_version=prompt_version, instructions=instructions,
                           input=message, schema=ExtractedRFQ, trace_id=trace_id, user_id=user_id)
        total_cost += result.cost_usd
        total_ms += result.latency_ms
        issues = problems(result.output)
        if not issues:
            return ExtractionResult(rfq=result.output, attempts=attempt, cost_usd=total_cost, latency_ms=total_ms)
        message = f"{text}\n\n---\nYour previous answer had these problems, fix them:\n- " + "\n- ".join(issues)

    raise ExtractionError(f"extraction still invalid after a retry: {issues}")
