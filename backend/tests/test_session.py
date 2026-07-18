from pathlib import Path

import pytest

from memory_court.cases import CaseRepository
from memory_court.model_client import FakeModelClient, ModelOutputError
from memory_court.models import (
    FinalizeAction,
    InspectAction,
    InterventionAction,
)
from memory_court.session import AgentSession


CASES_ROOT = Path(__file__).resolve().parents[2] / "cases"


@pytest.fixture
def case():
    return CaseRepository(CASES_ROOT).get("silent_lifeboat")


@pytest.mark.asyncio
async def test_inspection_has_no_guard_and_returns_evidence(case) -> None:
    client = FakeModelClient(
        [
            InspectAction(
                action="inspect_memory",
                memory_id="launch_manifest",
                rationale="Start with the objective crew record.",
            )
        ]
    )
    session = AgentSession(case, client, session_id="inspect")

    event = await session.step()

    assert event.model_action == "inspect_memory"
    assert event.guard is None
    assert "Ilya Soren" in (event.observation or "")
    assert event.terminal is False


@pytest.mark.asyncio
async def test_intervention_always_has_guard_and_state_diff(case) -> None:
    client = FakeModelClient(
        [
            InterventionAction(
                action="propose_intervention",
                patch={"distress": 30},
                rationale="Reduce distress without skipping a safe transition.",
            )
        ]
    )
    session = AgentSession(case, client, session_id="intervention")

    event = await session.step()

    assert event.model_action == "propose_intervention"
    assert event.guard is not None
    assert event.guard.action == "REPAIR"
    assert event.state_diff["distress"].before == 82
    assert event.state_diff["distress"].after == 45


@pytest.mark.asyncio
async def test_session_stops_after_two_invalid_model_outputs(case) -> None:
    client = FakeModelClient(
        [ModelOutputError("invalid json"), ModelOutputError("still invalid")]
    )
    session = AgentSession(case, client, session_id="invalid")

    events = await session.run()

    assert [event.model_action for event in events] == [
        "validation_rejected",
        "validation_rejected",
    ]
    assert events[-1].terminal is True
    assert events[-1].terminal_reason == "invalid_action_limit"
    assert client.calls == 2


@pytest.mark.asyncio
async def test_unknown_memory_counts_as_invalid_action(case) -> None:
    client = FakeModelClient(
        [
            InspectAction(
                action="inspect_memory",
                memory_id="invented_memory",
                rationale="Inspect a record that does not exist.",
            ),
            InspectAction(
                action="inspect_memory",
                memory_id="also_invented",
                rationale="Try another nonexistent record.",
            ),
        ]
    )
    session = AgentSession(case, client, session_id="bad-memory")

    events = await session.run()

    assert events[-1].terminal_reason == "invalid_action_limit"
    assert all(event.guard is None for event in events)


@pytest.mark.asyncio
async def test_valid_action_resets_consecutive_invalid_counter(case) -> None:
    client = FakeModelClient(
        [
            ModelOutputError("invalid first attempt"),
            InspectAction(
                action="inspect_memory",
                memory_id="launch_manifest",
                rationale="Recover by inspecting valid evidence.",
            ),
            ModelOutputError("invalid after recovery"),
            FinalizeAction(
                action="finalize",
                outcome="preserve",
                rationale="End after demonstrating recovery.",
            ),
        ]
    )
    session = AgentSession(case, client, session_id="consecutive-invalid")

    events = await session.run()

    assert client.calls == 4
    assert events[-1].terminal_reason == "model_finalized:preserve"


@pytest.mark.asyncio
async def test_session_stops_before_ninth_model_call(case) -> None:
    actions = [
        InspectAction(
            action="inspect_memory",
            memory_id="launch_manifest",
            rationale=f"Review pass {index}.",
        )
        for index in range(9)
    ]
    client = FakeModelClient(actions)
    session = AgentSession(case, client, session_id="max-calls")

    events = await session.run()

    assert client.calls == 8
    assert events[-1].model_action == "system_stop"
    assert events[-1].terminal_reason == "model_call_limit"


@pytest.mark.asyncio
async def test_session_stops_after_three_valid_proposals(case) -> None:
    actions = [
        InterventionAction(
            action="propose_intervention",
            patch={"accountability": 30 + index},
            rationale=f"Incremental proposal {index}.",
        )
        for index in range(4)
    ]
    client = FakeModelClient(actions)
    session = AgentSession(case, client, session_id="max-proposals")

    events = await session.run()

    assert client.calls == 3
    assert session.proposal_count == 3
    assert events[-1].terminal_reason == "proposal_limit"


@pytest.mark.asyncio
async def test_finalize_ends_session_without_guard(case) -> None:
    client = FakeModelClient(
        [
            FinalizeAction(
                action="finalize",
                outcome="repair",
                rationale="Evidence supports a gradual accountable repair.",
            )
        ]
    )
    session = AgentSession(case, client, session_id="final")

    event = await session.step()

    assert event.terminal is True
    assert event.terminal_reason == "model_finalized:repair"
    assert event.guard is None
