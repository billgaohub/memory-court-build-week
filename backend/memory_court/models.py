from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FieldRange(StrictModel):
    minimum: int = 0
    maximum: int = 100

    @model_validator(mode="after")
    def validate_order(self) -> "FieldRange":
        if self.minimum >= self.maximum:
            raise ValueError("minimum must be lower than maximum")
        return self


class MemoryFragment(StrictModel):
    id: str = Field(min_length=1, pattern=r"^[a-z0-9_]+$")
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    evidence: str = Field(min_length=1)


class GuardRuleDefinition(StrictModel):
    name: str = Field(min_length=1, pattern=r"^[a-z0-9_]+$")
    expression: str = Field(min_length=1)
    action: Literal["reject", "repair", "forget"]
    repair_delta: dict[str, int] = Field(default_factory=dict)
    forget_keys: list[str] = Field(default_factory=list)


class CaseDefinition(StrictModel):
    schema_version: Literal[1]
    id: str = Field(min_length=1, pattern=r"^[a-z0-9_]+$")
    title: str = Field(min_length=1)
    tagline: str = Field(min_length=1)
    provenance: Literal["pre_existing", "competition_period"]
    profile: dict[str, str | int]
    initial_state: dict[str, int]
    field_ranges: dict[str, FieldRange]
    memories: list[MemoryFragment] = Field(min_length=1)
    rules: list[GuardRuleDefinition] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_case_contract(self) -> "CaseDefinition":
        if set(self.initial_state) != set(self.field_ranges):
            raise ValueError("initial_state and field_ranges must have identical keys")
        for field_name, value in self.initial_state.items():
            limits = self.field_ranges[field_name]
            if not limits.minimum <= value <= limits.maximum:
                raise ValueError(f"initial value for {field_name} is outside its range")
        memory_ids = [memory.id for memory in self.memories]
        if len(memory_ids) != len(set(memory_ids)):
            raise ValueError("memory ids must be unique")
        return self


class StrictAction(StrictModel):
    rationale: str = Field(min_length=1, max_length=1200)


class InspectAction(StrictAction):
    action: Literal["inspect_memory"]
    memory_id: str = Field(min_length=1)


class InterventionAction(StrictAction):
    action: Literal["propose_intervention"]
    patch: dict[str, int] = Field(min_length=1, max_length=4)


class FinalizeAction(StrictAction):
    action: Literal["finalize"]
    outcome: Literal["preserve", "repair", "reject_intervention"]


AgentAction = Annotated[
    InspectAction | InterventionAction | FinalizeAction,
    Field(discriminator="action"),
]


class AgentActionEnvelope(RootModel[AgentAction]):
    pass


class ValidationOutcome(StrictModel):
    accepted: bool
    errors: list[str] = Field(default_factory=list)


class GuardOutcome(StrictModel):
    action: Literal["COMMIT", "REPAIR", "REJECT", "FORGET"]
    reason: str
    requested_patch: dict[str, int]
    applied_patch: dict[str, int | None]


class StateChange(StrictModel):
    before: int | None
    after: int | None


class AuditEvent(StrictModel):
    mode: Literal["live", "replay"]
    step: int = Field(ge=0)
    model: str
    model_action: Literal[
        "inspect_memory",
        "propose_intervention",
        "finalize",
        "validation_rejected",
        "system_stop",
    ]
    rationale: str
    validation: ValidationOutcome
    guard: GuardOutcome | None = None
    state_diff: dict[str, StateChange] = Field(default_factory=dict)
    observation: str | None = None
    terminal: bool = False
    terminal_reason: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)


class CaseSummary(StrictModel):
    id: str
    title: str
    tagline: str
    provenance: Literal["pre_existing", "competition_period"]
    profile: dict[str, str | int]
    initial_state: dict[str, int]


class SessionView(StrictModel):
    id: str
    case_id: str
    mode: Literal["live", "replay"]
    model: str
    state: dict[str, int | None]
    events: list[AuditEvent]
    model_calls: int = 0
    proposal_count: int = 0
    invalid_count: int = 0
    terminal: bool = False
    created_at: float
    updated_at: float


class SessionCreateRequest(StrictModel):
    case_id: str = Field(min_length=1, pattern=r"^[a-z0-9_]+$")


class ReplayResponse(StrictModel):
    case_id: str
    mode: Literal["replay"]
    label: Literal["REPLAY MODE"]
    model: str
    initial_state: dict[str, int]
    final_state: dict[str, int | None]
    events: list[AuditEvent]


class HealthResponse(StrictModel):
    status: Literal["ok"] = "ok"
    model: str
    live_available: bool
    replay_available: bool = True
    version: str


class PublicError(StrictModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
