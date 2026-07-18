from __future__ import annotations

import asyncio
import json
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from openai import APITimeoutError, AsyncOpenAI, OpenAIError, RateLimitError
from pydantic import ValidationError

from .models import AgentAction, AgentActionEnvelope


SYSTEM_INSTRUCTIONS = """You are the autonomous investigator in Memory Court.
Choose exactly one structured action per turn. Inspect evidence before intervening.
You may only modify the cognitive fields and ranges supplied in the context.
sonuv-guard, not you, decides whether an intervention is committed, repaired,
rejected, or forgotten. Never claim that natural-language text was Guard-verified.
Finalize once the evidence supports a defensible ethical outcome. Keep rationale
specific and concise. Always return every envelope field; use null for fields that
do not belong to the selected action. Encode an intervention patch as a list of
objects with a field name and integer value."""


class ModelOutputError(RuntimeError):
    """Raised when the model does not produce one valid structured action."""


class ModelUnavailableError(ModelOutputError):
    """Raised when a live provider failure should end the live session."""


@dataclass(frozen=True)
class ModelContext:
    case_id: str
    profile: dict[str, str | int]
    field_ranges: dict[str, dict[str, int]]
    current_state: dict[str, int | None]
    available_memories: list[dict[str, str]]
    inspected_memories: dict[str, str]
    recent_events: list[dict[str, Any]]
    limits: dict[str, int]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


class ModelClient(Protocol):
    model: str

    async def next_action(self, context: ModelContext) -> AgentAction: ...


class FakeModelClient:
    model = "fake-model"

    def __init__(self, actions: list[AgentAction | Exception]):
        self._actions = deque(actions)
        self.calls = 0

    async def next_action(self, context: ModelContext) -> AgentAction:
        del context
        self.calls += 1
        if not self._actions:
            raise ModelOutputError("fake model has no action remaining")
        item = self._actions.popleft()
        if isinstance(item, Exception):
            raise item
        return item


class OpenAIModelClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        api_client: Any | None = None,
        model: str = "gpt-5.6",
        timeout_seconds: float = 30.0,
        max_output_tokens: int = 600,
        retry_delay: float = 0.5,
    ):
        if api_client is None and not api_key:
            raise ValueError("OpenAI API key is required for live mode")
        self.client = api_client or AsyncOpenAI(api_key=api_key)
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.retry_delay = retry_delay

    async def next_action(self, context: ModelContext) -> AgentAction:
        for attempt in range(2):
            try:
                response = await asyncio.wait_for(
                    self.client.responses.parse(
                        model=self.model,
                        instructions=SYSTEM_INSTRUCTIONS,
                        input=context.to_json(),
                        text_format=AgentActionEnvelope,
                        max_output_tokens=self.max_output_tokens,
                        reasoning={"effort": "low"},
                        text={"verbosity": "low"},
                        store=False,
                    ),
                    timeout=self.timeout_seconds,
                )
                parsed = response.output_parsed
                if parsed is None:
                    raise ModelOutputError("model returned no parsed action")
                if isinstance(parsed, AgentActionEnvelope):
                    return parsed.to_action()
                return AgentActionEnvelope.model_validate(parsed).to_action()
            except (asyncio.TimeoutError, APITimeoutError, RateLimitError) as exc:
                if attempt == 1:
                    raise ModelUnavailableError(
                        "live model unavailable after retry"
                    ) from exc
                if self.retry_delay:
                    await asyncio.sleep(self.retry_delay)
            except ValidationError as exc:
                raise ModelOutputError("model action failed schema validation") from exc
            except OpenAIError as exc:
                raise ModelUnavailableError("model provider request failed") from exc
        raise ModelUnavailableError("live model unavailable")
