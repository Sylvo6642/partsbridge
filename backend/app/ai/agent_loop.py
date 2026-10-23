"""The agent loop shared by every agent (matching, quoting).

1. Send the conversation + tool descriptions to the model.
2. If it asks for tool calls, run them (plain Python) and append the results. Repeat.
3. Stop when the model answers in the requested schema, or after `max_turns` model calls.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID

from pydantic import BaseModel

from app.ai import llm


@dataclass
class LoopResult[T: BaseModel]:
    output: T | None                       # None if the loop hit max_turns
    tool_calls: list[str] = field(default_factory=list)
    tool_outputs: list = field(default_factory=list)
    model_calls: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0


def run_tool_loop[T: BaseModel](*, feature: str, prompt_version: str, instructions: str, message: str,
                                schema: type[T], tools: list[dict], run_tool: Callable[[str, str], object],
                                max_turns: int, trace_id: UUID, user_id: UUID | None) -> LoopResult[T]:
    conversation: list = [{"role": "user", "content": message}]
    result: LoopResult[T] = LoopResult(output=None)
    for _ in range(max_turns):
        step = llm.parse(feature=feature, prompt_version=prompt_version, instructions=instructions,
                         input=conversation, schema=schema, tools=tools, trace_id=trace_id, user_id=user_id)
        result.model_calls += 1
        result.cost_usd += step.cost_usd
        result.latency_ms += step.latency_ms

        calls = [item for item in step.response.output if item.type == "function_call"]
        if not calls:
            result.output = step.output
            return result

        conversation += step.response.output  # keep the model's tool requests in the history
        for call in calls:
            output = run_tool(call.name, call.arguments)
            result.tool_calls.append(f"{call.name}({call.arguments})")
            result.tool_outputs.append(output)
            conversation.append({"type": "function_call_output", "call_id": call.call_id,
                                 "output": json.dumps(output, default=str)})
    return result
