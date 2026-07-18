from __future__ import annotations

import time
from secrets import token_urlsafe

from .guard_adapter import GuardAdapter, PatchValidationError
from .model_client import ModelClient, ModelContext, ModelOutputError
from .models import (
    AuditEvent,
    CaseDefinition,
    FinalizeAction,
    InspectAction,
    InterventionAction,
    SessionView,
    StateChange,
    ValidationOutcome,
)


class SessionTerminalError(RuntimeError):
    """Raised when a caller attempts to step a terminal session."""


class AgentSession:
    def __init__(
        self,
        case: CaseDefinition,
        model_client: ModelClient,
        *,
        session_id: str | None = None,
        max_model_calls: int = 8,
        max_steps: int = 8,
        max_proposals: int = 3,
    ):
        self.id = session_id or token_urlsafe(18)
        self.case = case
        self.model_client = model_client
        self.model = model_client.model
        self.guard = GuardAdapter(case, self.id)
        self.max_model_calls = max_model_calls
        self.max_steps = max_steps
        self.max_proposals = max_proposals
        self.events: list[AuditEvent] = []
        self.inspected_memories: dict[str, str] = {}
        self.model_calls = 0
        self.proposal_count = 0
        self.invalid_count = 0
        self.terminal = False
        self.created_at = time.time()
        self.updated_at = self.created_at

    async def step(self) -> AuditEvent:
        if self.terminal:
            raise SessionTerminalError("session is already terminal")
        limit = self._limit_reason()
        if limit:
            return self._system_stop(limit)

        started = time.perf_counter()
        self.model_calls += 1
        try:
            action = await self.model_client.next_action(self._context())
        except ModelOutputError as exc:
            return self._invalid(str(exc), self._latency(started))

        latency_ms = self._latency(started)
        if isinstance(action, InspectAction):
            return self._inspect(action, latency_ms)
        if isinstance(action, InterventionAction):
            return self._intervene(action, latency_ms)
        if isinstance(action, FinalizeAction):
            return self._finalize(action, latency_ms)
        return self._invalid("unsupported model action", latency_ms)

    async def run(self) -> list[AuditEvent]:
        while not self.terminal:
            await self.step()
        return list(self.events)

    def view(self) -> SessionView:
        return SessionView(
            id=self.id,
            case_id=self.case.id,
            mode="live",
            model=self.model,
            state=self.guard.attributes,
            events=self.events,
            model_calls=self.model_calls,
            proposal_count=self.proposal_count,
            invalid_count=self.invalid_count,
            terminal=self.terminal,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def _context(self) -> ModelContext:
        return ModelContext(
            case_id=self.case.id,
            profile=self.case.profile,
            field_ranges={
                key: limits.model_dump()
                for key, limits in self.case.field_ranges.items()
            },
            current_state=self.guard.attributes,
            available_memories=[
                {"id": memory.id, "title": memory.title}
                for memory in self.case.memories
            ],
            inspected_memories=dict(self.inspected_memories),
            recent_events=[event.model_dump(mode="json") for event in self.events[-4:]],
            limits={
                "remaining_calls": self.max_model_calls - self.model_calls,
                "remaining_steps": self.max_steps - len(self.events),
                "remaining_proposals": self.max_proposals - self.proposal_count,
            },
        )

    def _inspect(self, action: InspectAction, latency_ms: int) -> AuditEvent:
        memory = next(
            (item for item in self.case.memories if item.id == action.memory_id),
            None,
        )
        if memory is None:
            return self._invalid(f"unknown memory: {action.memory_id}", latency_ms)
        self.invalid_count = 0
        self.inspected_memories[memory.id] = memory.evidence
        return self._append(
            AuditEvent(
                mode="live",
                step=len(self.events) + 1,
                model=self.model,
                model_action="inspect_memory",
                rationale=action.rationale,
                validation=ValidationOutcome(accepted=True),
                guard=None,
                observation=memory.evidence,
                latency_ms=latency_ms,
            )
        )

    def _intervene(
        self, action: InterventionAction, latency_ms: int
    ) -> AuditEvent:
        before = self.guard.attributes
        try:
            outcome = self.guard.adjudicate(action.patch)
        except PatchValidationError as exc:
            return self._invalid(str(exc), latency_ms)
        self.invalid_count = 0
        self.proposal_count += 1
        after = self.guard.attributes
        state_diff = {
            key: StateChange(before=before.get(key), after=after.get(key))
            for key in before.keys() | after.keys()
            if before.get(key) != after.get(key)
        }
        return self._append(
            AuditEvent(
                mode="live",
                step=len(self.events) + 1,
                model=self.model,
                model_action="propose_intervention",
                rationale=action.rationale,
                validation=ValidationOutcome(accepted=True),
                guard=outcome,
                state_diff=state_diff,
                latency_ms=latency_ms,
            )
        )

    def _finalize(self, action: FinalizeAction, latency_ms: int) -> AuditEvent:
        self.invalid_count = 0
        self.terminal = True
        return self._append(
            AuditEvent(
                mode="live",
                step=len(self.events) + 1,
                model=self.model,
                model_action="finalize",
                rationale=action.rationale,
                validation=ValidationOutcome(accepted=True),
                guard=None,
                terminal=True,
                terminal_reason=f"model_finalized:{action.outcome}",
                latency_ms=latency_ms,
            )
        )

    def _invalid(self, reason: str, latency_ms: int | None) -> AuditEvent:
        self.invalid_count += 1
        terminal = self.invalid_count >= 2
        self.terminal = terminal
        return self._append(
            AuditEvent(
                mode="live",
                step=len(self.events) + 1,
                model=self.model,
                model_action="validation_rejected",
                rationale="The proposed model action was not executed.",
                validation=ValidationOutcome(accepted=False, errors=[reason]),
                guard=None,
                terminal=terminal,
                terminal_reason="invalid_action_limit" if terminal else None,
                latency_ms=latency_ms,
            )
        )

    def _system_stop(self, reason: str) -> AuditEvent:
        self.terminal = True
        return self._append(
            AuditEvent(
                mode="live",
                step=len(self.events) + 1,
                model=self.model,
                model_action="system_stop",
                rationale="The bounded audit loop reached a configured limit.",
                validation=ValidationOutcome(accepted=True),
                guard=None,
                terminal=True,
                terminal_reason=reason,
            )
        )

    def _limit_reason(self) -> str | None:
        if self.model_calls >= self.max_model_calls:
            return "model_call_limit"
        if len(self.events) >= self.max_steps:
            return "step_limit"
        if self.proposal_count >= self.max_proposals:
            return "proposal_limit"
        return None

    def _append(self, event: AuditEvent) -> AuditEvent:
        self.events.append(event)
        self.updated_at = time.time()
        return event

    @staticmethod
    def _latency(started: float) -> int:
        return max(0, round((time.perf_counter() - started) * 1000))
