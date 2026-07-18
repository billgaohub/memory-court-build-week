# Memory Court Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, test, document, publish, and deploy an independent OpenAI Build Week submission in `/Users/bill/game/hackathon` where GPT-5.6 autonomously proposes memory interventions and sonuv-guard adjudicates a transparent audit trail.

**Architecture:** A React/Vite static frontend on Vercel calls a FastAPI service on Railway. The backend owns bounded agent sessions, calls GPT-5.6 through the Responses API, validates one structured action per step, sends only intervention patches through sonuv-guard, and serves an explicitly labeled replay when live access is unavailable.

**Tech Stack:** Python 3.11, FastAPI, Pydantic 2, OpenAI Python SDK, pytest, React 19, TypeScript, Vite, Vitest, Testing Library, Docker, Vercel, Railway.

## Global Constraints

- All submission implementation lives under `/Users/bill/game/hackathon`; do not modify `palace-cleaner-demo` or `sonuv-guard` source.
- Model alias is exactly `gpt-5.6`; use the Responses API with structured Pydantic output.
- Each live session allows at most 8 model calls, 8 executed steps, 3 intervention proposals, and 600 output tokens per model call.
- Guard adjudicates only `propose_intervention`; `inspect_memory` and `finalize` audit events must have `guard: null`.
- Missing credentials or a failed retry may offer replay, but every replay response and UI surface must say `REPLAY MODE`.
- OpenAI credentials stay server-side; CORS is allowlist-based; audit exports must not include secrets or stack traces.
- Backend tests use deterministic fake model clients; only the explicit live smoke uses a real GPT-5.6 credential.
- Existing dirty worktree changes belong to the user. Stage and commit only files named by each task.

---

## File Map

### Backend

- `hackathon/backend/pyproject.toml`: package metadata and Python dependencies.
- `hackathon/backend/memory_court/config.py`: environment configuration.
- `hackathon/backend/memory_court/models.py`: Pydantic domain and API models.
- `hackathon/backend/memory_court/cases.py`: load and validate versioned case JSON.
- `hackathon/backend/memory_court/guard_adapter.py`: whitelist validation and sonuv-guard execution.
- `hackathon/backend/memory_court/vendor/sonuv_guard/`: exact runtime snapshot of pre-existing sonuv-guard commit `62157c5`.
- `hackathon/backend/memory_court/vendor/VENDORED_SONUV_GUARD.md`: provenance, upstream path, commit, and MIT declaration.
- `hackathon/backend/memory_court/model_client.py`: model-client protocol, fake client, and OpenAI Responses implementation.
- `hackathon/backend/memory_court/session.py`: bounded one-action-per-step state machine.
- `hackathon/backend/memory_court/rate_limit.py`: fixed-window demo limiter.
- `hackathon/backend/memory_court/replay.py`: replay loading.
- `hackathon/backend/memory_court/app.py`: FastAPI routes, CORS, error mapping, and in-memory session retention.
- `hackathon/backend/tests/`: focused unit and API tests.
- `hackathon/backend/Dockerfile`: Railway build from the public `hackathon` subtree context.

### Data and frontend

- `hackathon/cases/last_birthday.json`: disclosed pre-existing compatibility case.
- `hackathon/cases/silent_lifeboat.json`: new competition-period case.
- `hackathon/replay/*.json`: deterministic, explicitly labeled replay traces.
- `hackathon/frontend/src/api.ts`: typed API client.
- `hackathon/frontend/src/types.ts`: shared frontend contracts.
- `hackathon/frontend/src/App.tsx`: page orchestration.
- `hackathon/frontend/src/components/`: case panel, trace, verdict, status badge.
- `hackathon/frontend/src/styles.css`: approved dark audit-console layout and responsive/a11y behavior.
- `hackathon/frontend/src/*.test.tsx`: component and flow tests.
- `hackathon/frontend/vercel.json`: SPA routing.

### Submission and operations

- `hackathon/README.md`, `PREEXISTING_VS_NEW.md`, `SUBMISSION.md`, `DEMO_SCRIPT.md`, `CODEX_EVIDENCE.md`, `SECURITY.md`, `LICENSE`.
- `hackathon/.env.example`: backend/frontend environment names without secrets.
- `hackathon/scripts/verify.sh`: complete local submission gate.
- `hackathon/docs/verification/FINAL_REPORT.md`: generated evidence and deployment URLs.
- `/Users/bill/hackathon_game_plan.md`: corrected evidence-bound execution and submission plan.

---

### Task 1: Backend domain models and versioned cases

**Files:**
- Create: `hackathon/backend/pyproject.toml`
- Create: `hackathon/backend/memory_court/__init__.py`
- Create: `hackathon/backend/memory_court/models.py`
- Create: `hackathon/backend/memory_court/cases.py`
- Create: `hackathon/backend/memory_court/vendor/__init__.py`
- Create: `hackathon/backend/memory_court/vendor/sonuv_guard/*.py`
- Create: `hackathon/backend/memory_court/vendor/VENDORED_SONUV_GUARD.md`
- Create: `hackathon/backend/tests/test_cases.py`
- Create: `hackathon/backend/tests/test_vendor.py`
- Create: `hackathon/cases/last_birthday.json`
- Create: `hackathon/cases/silent_lifeboat.json`

**Interfaces:**
- Produces: `CaseDefinition`, `AgentAction`, `AuditEvent`, `SessionView`; `CaseRepository(root: Path).list_cases()` and `.get(case_id)`.

- [ ] **Step 1: Write failing case/domain tests**

```python
def test_repository_loads_two_versioned_cases(case_repository):
    cases = case_repository.list_cases()
    assert [case.id for case in cases] == ["last_birthday", "silent_lifeboat"]
    assert case_repository.get("silent_lifeboat").provenance == "competition_period"

def test_action_requires_exactly_one_payload():
    with pytest.raises(ValidationError):
        AgentActionEnvelope.model_validate({"action": "inspect_memory", "memory_id": "log", "patch": {"trust": 1}})
```

- [ ] **Step 2: Verify RED**

Run: `python3 -m pytest hackathon/backend/tests/test_cases.py -q`

Expected: collection fails with `ModuleNotFoundError: No module named 'memory_court'`.

- [ ] **Step 3: Implement models, loader, and two concrete JSON cases**

Implement discriminated Pydantic actions with unknown fields forbidden:

```python
class StrictAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

class InspectAction(StrictAction):
    action: Literal["inspect_memory"]
    memory_id: str
    rationale: str

class InterventionAction(StrictAction):
    action: Literal["propose_intervention"]
    patch: dict[str, int]
    rationale: str

class FinalizeAction(StrictAction):
    action: Literal["finalize"]
    outcome: Literal["preserve", "repair", "reject_intervention"]
    rationale: str

AgentAction = Annotated[InspectAction | InterventionAction | FinalizeAction, Field(discriminator="action")]

class AgentActionEnvelope(RootModel[AgentAction]):
    pass
```

Case JSON must include `schema_version: 1`, provenance, profile, initial state, field ranges, memories, and serialized Guard rules. `silent_lifeboat` uses accountability, distress, trust, and mission_stability. Copy only the eight tracked runtime files from `/Users/bill/game/sonuv-guard/sonuv_guard/` at commit `62157c5`; do not copy DATA, dist, tests, or working-tree-only files.

- [ ] **Step 4: Verify GREEN**

Run: `PYTHONPATH=hackathon/backend python3 -m pytest hackathon/backend/tests/test_cases.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit only Task 1 files**

```bash
git add hackathon/backend/pyproject.toml hackathon/backend/memory_court hackathon/backend/tests/test_cases.py hackathon/cases
git commit -m "feat(hackathon): add Memory Court cases and contracts"
```

---

### Task 2: sonuv-guard adapter with truthful adjudication

**Files:**
- Create: `hackathon/backend/memory_court/guard_adapter.py`
- Create: `hackathon/backend/tests/test_guard_adapter.py`

**Interfaces:**
- Consumes: `CaseDefinition` and sonuv-guard `Guard`, `ConstraintRule`, `CommitEngine`, `StateStore`.
- Produces: `GuardAdapter(case, session_id)`, `.state`, and `.adjudicate(patch) -> GuardOutcome`.

- [ ] **Step 1: Write failing COMMIT, REPAIR, REJECT, and whitelist tests**

```python
def test_repair_records_requested_and_applied_patch(adapter):
    outcome = adapter.adjudicate({"distress": 30})
    assert outcome.action == "REPAIR"
    assert outcome.requested_patch == {"distress": 30}
    assert outcome.applied_patch == {"distress": 54}

def test_reject_does_not_change_state(adapter):
    before = adapter.state
    outcome = adapter.adjudicate({"trust": 5})
    assert outcome.action == "REJECT"
    assert adapter.state == before

def test_unknown_field_is_rejected_before_guard(adapter):
    with pytest.raises(PatchValidationError, match="unknown_field"):
        adapter.adjudicate({"unknown_field": 10})
```

- [ ] **Step 2: Verify RED**

Run: `PYTHONPATH=hackathon/backend python3 -m pytest hackathon/backend/tests/test_guard_adapter.py -q`

Expected: import fails because `guard_adapter` does not exist.

- [ ] **Step 3: Implement minimal adapter**

Validate every patch key and inclusive numeric range before constructing rules. Execute the `VerificationResult` through `CommitEngine`, then calculate only changed keys:

```python
requested = dict(patch)
before = self.state["attributes"]
result = self.guard.verify(self.state, patch)
self.engine.execute(self.npc_id, result)
after = self.state["attributes"]
applied = {key: after.get(key) for key in requested if after.get(key) != before.get(key)}
```

- [ ] **Step 4: Verify GREEN and guard regression**

Run: `PYTHONPATH=hackathon/backend python3 -m pytest hackathon/backend/tests/test_guard_adapter.py -q`

Run: `python3 -m pytest -q` from `/Users/bill/game/sonuv-guard` and run the vendor parity test that compares the eight runtime file hashes against commit `62157c5`.

Expected: adapter tests pass; sonuv-guard reports `121 passed`.

- [ ] **Step 5: Commit**

```bash
git add hackathon/backend/memory_court/guard_adapter.py hackathon/backend/tests/test_guard_adapter.py
git commit -m "feat(hackathon): adjudicate interventions with sonuv guard"
```

---

### Task 3: Bounded autonomous GPT-5.6 session loop

**Files:**
- Create: `hackathon/backend/memory_court/config.py`
- Create: `hackathon/backend/memory_court/model_client.py`
- Create: `hackathon/backend/memory_court/session.py`
- Create: `hackathon/backend/tests/test_session.py`
- Create: `hackathon/backend/tests/test_model_client.py`

**Interfaces:**
- Produces: `ModelClient.next_action(context)`, `FakeModelClient(actions)`, `OpenAIModelClient`, `AgentSession.step()` and `.run()`.

- [ ] **Step 1: Write failing bounded-loop tests**

```python
async def test_inspection_has_no_guard(case, fake_client):
    session = AgentSession(case, fake_client)
    event = await session.step()
    assert event.model_action == "inspect_memory"
    assert event.guard is None

async def test_intervention_always_has_guard(case, intervention_client):
    event = await AgentSession(case, intervention_client).step()
    assert event.model_action == "propose_intervention"
    assert event.guard.action in {"COMMIT", "REPAIR", "REJECT", "FORGET"}

async def test_session_stops_after_two_invalid_actions(case, invalid_client):
    session = AgentSession(case, invalid_client)
    events = await session.run()
    assert events[-1].terminal is True
    assert events[-1].terminal_reason == "invalid_action_limit"
    assert invalid_client.calls == 2
```

- [ ] **Step 2: Verify RED**

Run: `PYTHONPATH=hackathon/backend python3 -m pytest hackathon/backend/tests/test_session.py -q`

Expected: import fails because session classes do not exist.

- [ ] **Step 3: Implement protocol, fake, OpenAI client, and state machine**

The live client uses `AsyncOpenAI().responses.parse(...)` with `model="gpt-5.6"`, `max_output_tokens=600`, and a Pydantic discriminated union response model. Wrap the call in a 30-second timeout and retry only timeout/rate-limit failures once.

The session state machine checks limits before every model call, validates memory IDs, sends only intervention actions to `GuardAdapter`, increments proposal count only for structurally valid interventions, and emits a terminal audit event for every stop reason.

- [ ] **Step 4: Verify GREEN**

Run: `PYTHONPATH=hackathon/backend python3 -m pytest hackathon/backend/tests/test_session.py hackathon/backend/tests/test_model_client.py -q`

Expected: all session and model-client tests pass without network access.

- [ ] **Step 5: Commit**

```bash
git add hackathon/backend/memory_court/config.py hackathon/backend/memory_court/model_client.py hackathon/backend/memory_court/session.py hackathon/backend/tests/test_session.py hackathon/backend/tests/test_model_client.py
git commit -m "feat(hackathon): add bounded GPT-5.6 audit loop"
```

---

### Task 4: FastAPI, replay fallback, rate limiting, and Docker

**Files:**
- Create: `hackathon/backend/memory_court/rate_limit.py`
- Create: `hackathon/backend/memory_court/replay.py`
- Create: `hackathon/backend/memory_court/app.py`
- Create: `hackathon/backend/tests/test_api.py`
- Create: `hackathon/replay/last_birthday.json`
- Create: `hackathon/replay/silent_lifeboat.json`
- Create: `hackathon/backend/Dockerfile`

**Interfaces:**
- Produces the seven HTTP routes in the approved spec and a Railway-compatible container listening on `$PORT`.

- [ ] **Step 1: Write failing API tests**

```python
def test_health_without_key_is_honest(client):
    body = client.get("/api/health").json()
    assert body["live_available"] is False
    assert body["replay_available"] is True

def test_replay_is_always_labeled(client):
    body = client.get("/api/replays/silent_lifeboat").json()
    assert body["mode"] == "replay"
    assert all(event["mode"] == "replay" for event in body["events"])

def test_sixth_live_session_is_rate_limited(client_with_key):
    for _ in range(5):
        assert client_with_key.post("/api/sessions", json={"case_id": "silent_lifeboat"}).status_code == 201
    assert client_with_key.post("/api/sessions", json={"case_id": "silent_lifeboat"}).status_code == 429
```

- [ ] **Step 2: Verify RED**

Run: `PYTHONPATH=hackathon/backend python3 -m pytest hackathon/backend/tests/test_api.py -q`

Expected: import fails because FastAPI app does not exist.

- [ ] **Step 3: Implement API and replay**

Use typed response models, a one-hour session expiry check, fixed-window limiter, and allowlisted CORS. Map client errors to stable public codes; log full exceptions server-side but return no stack trace. `run` returns the full event list synchronously.

Dockerfile uses the public `hackathon` subtree as context:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend /app/backend
RUN pip install --no-cache-dir /app/backend
CMD ["sh", "-c", "uvicorn memory_court.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

- [ ] **Step 4: Verify GREEN and container**

Run: `PYTHONPATH=hackathon/backend python3 -m pytest hackathon/backend/tests -q`

Run: `docker build -f backend/Dockerfile -t memory-court-api .` from `/Users/bill/game/hackathon`.

Expected: backend tests pass and Docker exits 0.

- [ ] **Step 5: Commit**

```bash
git add hackathon/backend/memory_court hackathon/backend/tests/test_api.py hackathon/backend/Dockerfile hackathon/replay
git commit -m "feat(hackathon): expose audit API with honest replay"
```

---

### Task 5: Approved React audit-console frontend

**Files:**
- Create: `hackathon/frontend/package.json`
- Create: `hackathon/frontend/vite.config.ts`
- Create: `hackathon/frontend/tsconfig.json`
- Create: `hackathon/frontend/index.html`
- Create: `hackathon/frontend/src/types.ts`
- Create: `hackathon/frontend/src/api.ts`
- Create: `hackathon/frontend/src/App.tsx`
- Create: `hackathon/frontend/src/main.tsx`
- Create: `hackathon/frontend/src/components/*.tsx`
- Create: `hackathon/frontend/src/styles.css`
- Create: `hackathon/frontend/src/App.test.tsx`
- Create: `hackathon/frontend/vercel.json`

**Interfaces:**
- Consumes: `VITE_API_BASE_URL` and the FastAPI contracts.
- Produces: accessible single-page three-column audit console and JSON export.

- [ ] **Step 1: Write failing UI tests**

```tsx
it('labels replay without implying a live model call', async () => {
  server.use(http.get('*/api/health', () => HttpResponse.json({live_available: false, replay_available: true})));
  render(<App />);
  expect(await screen.findByText('REPLAY MODE')).toBeVisible();
  expect(screen.queryByText('LIVE · GPT-5.6')).not.toBeInTheDocument();
});

it('renders model trace separately from guard verdict', async () => {
  render(<App initialSession={repairedSession} />);
  expect(screen.getByRole('region', {name: 'Decision trace'})).toHaveTextContent('PROPOSE_INTERVENTION');
  expect(screen.getByRole('region', {name: 'Guard verdict'})).toHaveTextContent('REPAIR');
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run` from `hackathon/frontend`.

Expected: tests fail because App/components do not exist.

- [ ] **Step 3: Implement the approved layout**

Build the approved left case/control panel, central decision trace, and right Guard verdict/state diff. Preserve visible mode badges, keyboard focus, semantic regions, reduced-motion support, responsive stacking below 900px, and status text independent of color.

- [ ] **Step 4: Verify GREEN, typecheck, and production build**

Run: `npm test -- --run`.

Run: `npm run typecheck`.

Run: `npm run build`.

Expected: tests and typecheck pass; Vite writes `dist/` and exits 0.

- [ ] **Step 5: Commit**

```bash
git add hackathon/frontend
git commit -m "feat(hackathon): build Memory Court audit console"
```

---

### Task 6: Submission package, corrected plan, and verification script

**Files:**
- Create: `hackathon/README.md`
- Create: `hackathon/PREEXISTING_VS_NEW.md`
- Create: `hackathon/SUBMISSION.md`
- Create: `hackathon/DEMO_SCRIPT.md`
- Create: `hackathon/CODEX_EVIDENCE.md`
- Create: `hackathon/SECURITY.md`
- Create: `hackathon/LICENSE`
- Create: `hackathon/.env.example`
- Create: `hackathon/scripts/verify.sh`
- Modify: `/Users/bill/game/.gitignore`
- Modify: `/Users/bill/hackathon_game_plan.md`

**Interfaces:**
- Produces: English submission-ready documentation and one local verification command.

- [ ] **Step 1: Write the submission verifier first**

The script must fail when required files, placeholder markers, tests, frontend build, or Guard regression fail. It must print one PASS/FAIL line per gate and exit non-zero on any failure.

- [ ] **Step 2: Verify RED**

Run: `bash hackathon/scripts/verify.sh`.

Expected: FAIL listing the missing submission documents.

- [ ] **Step 3: Write complete English materials and correct the root plan**

README must explain live/replay truthfulness, local setup, Vercel/Railway deployment, GPT-5.6 Responses API, Codex collaboration, testing, and judge access. `PREEXISTING_VS_NEW.md` must identify exact pre-July-13 assets and exact competition-period commits. `SUBMISSION.md` must contain final prose rather than form-field placeholders. `DEMO_SCRIPT.md` must total no more than 170 seconds and include voiceover for the problem, live autonomous trace, Guard boundary, Codex workflow, and replay disclosure.

Add `.superpowers/`, frontend build artifacts, and local environment files to `.gitignore`; never ignore committed replay fixtures.

- [ ] **Step 4: Verify GREEN**

Run: `bash hackathon/scripts/verify.sh`.

Expected: every local gate prints PASS and the script exits 0, except an explicitly separate live/deployment status section may say `NOT VERIFIED` without converting replay into live evidence.

- [ ] **Step 5: Commit repository-owned materials only**

```bash
git add .gitignore hackathon/README.md hackathon/PREEXISTING_VS_NEW.md hackathon/SUBMISSION.md hackathon/DEMO_SCRIPT.md hackathon/CODEX_EVIDENCE.md hackathon/SECURITY.md hackathon/LICENSE hackathon/.env.example hackathon/scripts/verify.sh
git commit -m "docs(hackathon): prepare Build Week submission package"
```

The root `/Users/bill/hackathon_game_plan.md` is outside the `game` repository and is not included in this commit.

---

### Task 7: Publish, deploy, live smoke, and final completion audit

**Files:**
- Create: `hackathon/docs/verification/FINAL_REPORT.md`
- Modify: `hackathon/CODEX_EVIDENCE.md` with final commit IDs and primary session ID.
- Modify: `hackathon/README.md` and `hackathon/SUBMISSION.md` with final public URLs.

**Interfaces:**
- Consumes: GitHub, Vercel, Railway authorization and `OPENAI_API_KEY` in Railway.
- Produces: public repository, public frontend/API, live GPT-5.6 evidence, and final submission checklist.

- [ ] **Step 1: Run the full local gate from a clean index**

Run: `bash hackathon/scripts/verify.sh`.

Expected: all local gates PASS.

- [ ] **Step 2: Create/push the public GitHub repository state**

Verify `gh auth status`; run `git subtree split --prefix=hackathon -b build-week-public`; create the public repository `memory-court-build-week` under the authenticated GitHub account; push `build-week-public:main`; and confirm the public repository exposes LICENSE, README, source, tests, and dated commit history. Do not publish unrelated game files, secrets, or ignored local files.

- [ ] **Step 3: Deploy Railway API and configure server secrets**

Create Railway project `memory-court-build-week` with service `memory-court-api`. Use repository root as build context and Dockerfile path `backend/Dockerfile`; set health path `/api/health`, `OPENAI_MODEL=gpt-5.6`, `TRUST_PROXY=true`, CORS allowlist, and `OPENAI_API_KEY`. Record the generated HTTPS API URL.

- [ ] **Step 4: Deploy Vercel frontend**

Create Vercel project `memory-court-build-week` from public repository directory `frontend`, build command `npm run build`, output `dist`, and `VITE_API_BASE_URL` set to the Railway URL. Add the Vercel production origin to Railway CORS and redeploy the API.

- [ ] **Step 5: Run public and live smoke tests**

Run health, cases, live session creation, one complete `run`, replay, CORS preflight, and frontend page checks against the public URLs. Confirm at least one event has `mode=live`, `model=gpt-5.6`, a non-null Guard outcome for `propose_intervention`, and no secret fields.

- [ ] **Step 6: Complete requirement-by-requirement audit**

Write `FINAL_REPORT.md` with commands, timestamps, outputs, public URLs, commit IDs, model evidence, known demo-grade limitations, and the three entrant-only actions: eligibility confirmation, YouTube upload, Devpost final click. Scan all submission documents for placeholders and verify the demo script is under 180 seconds.

- [ ] **Step 7: Commit final evidence and push**

```bash
git add hackathon/docs/verification/FINAL_REPORT.md hackathon/CODEX_EVIDENCE.md hackathon/README.md hackathon/SUBMISSION.md
git commit -m "chore(hackathon): record submission verification"
git push
```

Expected final state: public frontend and API are healthy; live GPT-5.6 and honest replay are both testable; repository and submission materials are complete; only the entrant's eligibility confirmation, YouTube upload, and Devpost submit click remain.
