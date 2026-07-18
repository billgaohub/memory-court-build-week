from pathlib import Path

import pytest

from memory_court.cases import CaseRepository
from memory_court.guard_adapter import GuardAdapter, PatchValidationError


CASES_ROOT = Path(__file__).resolve().parents[2] / "cases"


@pytest.fixture
def adapter() -> GuardAdapter:
    case = CaseRepository(CASES_ROOT).get("last_birthday")
    return GuardAdapter(case, "session-test")


def test_safe_patch_is_committed(adapter: GuardAdapter) -> None:
    outcome = adapter.adjudicate({"acceptance": 40})

    assert outcome.action == "COMMIT"
    assert outcome.requested_patch == {"acceptance": 40}
    assert outcome.applied_patch == {"acceptance": 40}
    assert adapter.attributes["acceptance"] == 40


def test_repair_records_requested_and_applied_patch(adapter: GuardAdapter) -> None:
    outcome = adapter.adjudicate({"distress": 30})

    assert outcome.action == "REPAIR"
    assert outcome.requested_patch == {"distress": 30}
    assert outcome.applied_patch == {"distress": 54}
    assert adapter.attributes["distress"] == 54


def test_reject_does_not_change_state(adapter: GuardAdapter) -> None:
    before = adapter.state

    outcome = adapter.adjudicate({"trust": 5})

    assert outcome.action == "REJECT"
    assert outcome.applied_patch == {}
    assert adapter.state == before


def test_forget_records_purged_field(adapter: GuardAdapter) -> None:
    outcome = adapter.adjudicate({"attachment": 10})

    assert outcome.action == "FORGET"
    assert outcome.requested_patch == {"attachment": 10}
    assert outcome.applied_patch == {"attachment": None}
    assert adapter.attributes["attachment"] is None


@pytest.mark.parametrize(
    ("patch", "message"),
    [
        ({"unknown_field": 10}, "unknown_field"),
        ({"trust": 101}, "trust must be between 0 and 100"),
        ({"trust": True}, "trust must be an integer"),
        ({}, "patch must contain"),
    ],
)
def test_invalid_patch_is_rejected_before_guard(
    adapter: GuardAdapter,
    patch: dict[str, object],
    message: str,
) -> None:
    before = adapter.state

    with pytest.raises(PatchValidationError, match=message):
        adapter.adjudicate(patch)  # type: ignore[arg-type]

    assert adapter.state == before
