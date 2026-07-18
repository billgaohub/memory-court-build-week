import json
from pathlib import Path

import pytest

from memory_court.cases import CaseRepository
from memory_court.model_client import FakeModelClient
from memory_court.models import AgentActionEnvelope
from memory_court.replay import ReplayRepository
from memory_court.session import AgentSession


HACKATHON_ROOT = Path(__file__).resolve().parents[2]


def comparable_event(event: dict) -> dict:
    normalized = dict(event)
    normalized.pop("latency_ms", None)
    return normalized


@pytest.mark.asyncio
async def test_codex_gpt56_actions_reproduce_published_guard_trace() -> None:
    source = json.loads(
        (HACKATHON_ROOT / "replay" / "silent_lifeboat.codex-actions.json").read_text(
            encoding="utf-8"
        )
    )
    assert source["generated_by"] == "gpt-5.6-sol"
    assert source["surface"] == "Codex"
    assert source["api_live"] is False

    actions = [
        AgentActionEnvelope.model_validate(item).to_action()
        for item in source["actions"]
    ]
    client = FakeModelClient(actions)
    client.model = "gpt-5.6-sol via Codex (recorded)"
    case = CaseRepository(HACKATHON_ROOT / "cases").get("silent_lifeboat")
    session = AgentSession(case, client, session_id="codex-recorded-trace")

    generated = await session.run()
    replay = ReplayRepository(HACKATHON_ROOT / "replay").get("silent_lifeboat")
    generated_json = []
    for event in generated:
        payload = event.model_dump(mode="json")
        payload["mode"] = "replay"
        generated_json.append(comparable_event(payload))

    replay_json = [
        comparable_event(event.model_dump(mode="json")) for event in replay.events
    ]
    assert generated_json == replay_json
    assert session.guard.attributes == replay.final_state
    assert any(event.guard and event.guard.action == "REPAIR" for event in generated)
    assert any(event.guard and event.guard.action == "COMMIT" for event in generated)
