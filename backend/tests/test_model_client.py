import asyncio
from types import SimpleNamespace

import pytest
from openai import OpenAIError

from memory_court.model_client import (
    FakeModelClient,
    ModelContext,
    ModelOutputError,
    ModelUnavailableError,
    OpenAIModelClient,
)
from memory_court.models import InspectAction


def context() -> ModelContext:
    return ModelContext(
        case_id="silent_lifeboat",
        profile={"name": "Mara"},
        field_ranges={"trust": {"minimum": 0, "maximum": 100}},
        current_state={"trust": 57},
        available_memories=[{"id": "launch_manifest", "title": "Manifest"}],
        inspected_memories={},
        recent_events=[],
        limits={"remaining_calls": 8, "remaining_proposals": 3},
    )


@pytest.mark.asyncio
async def test_fake_client_returns_one_action_per_call() -> None:
    action = InspectAction(
        action="inspect_memory",
        memory_id="launch_manifest",
        rationale="Inspect the manifest.",
    )
    client = FakeModelClient([action])

    assert await client.next_action(context()) == action
    assert client.calls == 1


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        parsed = kwargs["text_format"].model_validate(
            {
                "action": "inspect_memory",
                "memory_id": "launch_manifest",
                "rationale": "Inspect objective evidence.",
            }
        )
        return SimpleNamespace(output_parsed=parsed)


@pytest.mark.asyncio
async def test_openai_client_uses_gpt56_responses_parse() -> None:
    responses = FakeResponses()
    api_client = SimpleNamespace(responses=responses)
    client = OpenAIModelClient(api_client=api_client, retry_delay=0)

    action = await client.next_action(context())

    assert action.action == "inspect_memory"
    assert responses.calls[0]["model"] == "gpt-5.6"
    assert responses.calls[0]["max_output_tokens"] == 600
    assert responses.calls[0]["store"] is False


class TimeoutThenSuccessResponses(FakeResponses):
    async def parse(self, **kwargs):
        if not self.calls:
            self.calls.append(kwargs)
            raise asyncio.TimeoutError
        return await super().parse(**kwargs)


@pytest.mark.asyncio
async def test_openai_client_retries_timeout_once() -> None:
    responses = TimeoutThenSuccessResponses()
    client = OpenAIModelClient(
        api_client=SimpleNamespace(responses=responses),
        retry_delay=0,
    )

    action = await client.next_action(context())

    assert action.action == "inspect_memory"
    assert len(responses.calls) == 2


class ProviderErrorResponses(FakeResponses):
    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        raise OpenAIError("provider unavailable")


@pytest.mark.asyncio
async def test_openai_client_exposes_stable_error_for_provider_failure() -> None:
    responses = ProviderErrorResponses()
    client = OpenAIModelClient(
        api_client=SimpleNamespace(responses=responses),
        retry_delay=0,
    )

    with pytest.raises(ModelUnavailableError, match="model provider request failed"):
        await client.next_action(context())

    assert len(responses.calls) == 1
