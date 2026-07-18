from __future__ import annotations

import time
from copy import deepcopy

from .models import CaseDefinition, GuardOutcome
from .vendor.sonuv_guard import CommitEngine, ConstraintRule, Guard, StateStore


class PatchValidationError(ValueError):
    """Raised before Guard when a model patch violates the case contract."""


class GuardAdapter:
    def __init__(self, case: CaseDefinition, session_id: str):
        self.case = case
        self.npc_id = f"{case.id}-{session_id}"
        self.store = StateStore()
        self.engine = CommitEngine(self.store)
        rules = [
            ConstraintRule(
                name=rule.name,
                expression=rule.expression,
                action_on_fail=rule.action,
                repair_delta=rule.repair_delta,
                forget_keys=rule.forget_keys,
            )
            for rule in case.rules
        ]
        self.guard = Guard(rules, recursive=len(rules) > 1)
        self.store.save(
            self.npc_id,
            {
                "npc_id": self.npc_id,
                "version": 1,
                "timestamp": time.time(),
                "attributes": dict(case.initial_state),
            },
        )

    @property
    def state(self) -> dict:
        return self.store.load(self.npc_id)

    @property
    def attributes(self) -> dict[str, int | None]:
        return deepcopy(self.state["attributes"])

    def adjudicate(self, patch: dict[str, int]) -> GuardOutcome:
        self._validate_patch(patch)
        requested = dict(patch)
        current = self.state
        before = current["attributes"]

        result = self.guard.verify(current, requested)
        self.engine.execute(self.npc_id, result)

        after = self.state["attributes"]
        applied = {
            key: after.get(key)
            for key in before.keys() | after.keys()
            if before.get(key) != after.get(key)
        }
        return GuardOutcome(
            action=result.action.name,
            reason=result.reason,
            requested_patch=requested,
            applied_patch=applied,
        )

    def _validate_patch(self, patch: dict[str, int]) -> None:
        if not patch:
            raise PatchValidationError("patch must contain at least one field")
        if len(patch) > 4:
            raise PatchValidationError("patch may contain at most four fields")
        for field_name, value in patch.items():
            if field_name not in self.case.field_ranges:
                raise PatchValidationError(f"unknown field: {field_name}")
            if isinstance(value, bool) or not isinstance(value, int):
                raise PatchValidationError(f"{field_name} must be an integer")
            limits = self.case.field_ranges[field_name]
            if not limits.minimum <= value <= limits.maximum:
                raise PatchValidationError(
                    f"{field_name} must be between {limits.minimum} and {limits.maximum}"
                )
