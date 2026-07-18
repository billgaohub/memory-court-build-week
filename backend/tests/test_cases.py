from pathlib import Path

import pytest
from pydantic import ValidationError

from memory_court.cases import CaseNotFoundError, CaseRepository
from memory_court.models import AgentActionEnvelope


CASES_ROOT = Path(__file__).resolve().parents[2] / "cases"


@pytest.fixture
def repository() -> CaseRepository:
    return CaseRepository(CASES_ROOT)


def test_repository_loads_two_versioned_cases(repository: CaseRepository) -> None:
    cases = repository.list_cases()

    assert [case.id for case in cases] == ["last_birthday", "silent_lifeboat"]
    assert repository.get("last_birthday").provenance == "pre_existing"
    assert repository.get("silent_lifeboat").provenance == "competition_period"


def test_cases_have_valid_initial_state_and_unique_memories(
    repository: CaseRepository,
) -> None:
    for case in repository.list_cases():
        assert set(case.initial_state) == set(case.field_ranges)
        assert len({memory.id for memory in case.memories}) == len(case.memories)
        for field, value in case.initial_state.items():
            limits = case.field_ranges[field]
            assert limits.minimum <= value <= limits.maximum


def test_action_rejects_payload_for_a_different_action() -> None:
    with pytest.raises(ValidationError):
        AgentActionEnvelope.model_validate(
            {
                "action": "inspect_memory",
                "memory_id": "mission_log",
                "rationale": "Inspect objective evidence first.",
                "patch": {"trust": 1},
            }
        )


def test_repository_raises_stable_error_for_unknown_case(
    repository: CaseRepository,
) -> None:
    with pytest.raises(CaseNotFoundError, match="unknown"):
        repository.get("unknown")
