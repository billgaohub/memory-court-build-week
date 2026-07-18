# Devpost submission copy

## Project name

Memory Court

## Category

Developer Tools

## Tagline

GPT-5.6 proposes memory interventions. sonuv-guard decides what is allowed to become state.

## Inspiration

Autonomous agents are often demonstrated by showing what they can do. We wanted to make the more difficult boundary visible: what happens when a capable model proposes a sensitive change that should not be executed exactly as requested? Memory Court turns that boundary into a legible, interactive hearing.

## What it does

GPT-5.6 autonomously investigates a case, inspects evidence, and chooses one structured action at a time. When it proposes a cognitive-state intervention, the server validates the patch and passes it to sonuv-guard. Guard can commit it, repair it to a safe transition, reject it, or forget protected state. The UI separates the model's action and rationale from the Guard ruling, requested versus applied values, and the resulting state diff.

Every run produces an exportable audit trail. When a server key is absent or a live request fails after retry, the interface automatically enters a fixed **REPLAY MODE** and clearly states that no live model call occurred.

## How we built it

The application is a React/TypeScript/Vite frontend on Vercel and an independent FastAPI service on Railway. The backend uses the OpenAI Responses API with GPT-5.6 structured outputs. The model may inspect memory, propose an intervention, or finalize. It receives real execution outcomes on the next turn but cannot bypass schema validation or Guard.

The loop is bounded to eight calls and three proposals. API keys remain server-side, live session creation is rate-limited, origins are allowlisted, and session IDs are generated with a cryptographically secure source. The public repository includes deterministic replays, exact hashes for the disclosed pre-existing Guard snapshot, and a one-command local verification gate.

## How we used GPT-5.6

GPT-5.6 is the autonomous investigator. It selects evidence to inspect, proposes typed field changes, reacts to COMMIT/REPAIR/REJECT/FORGET outcomes, and decides when to finalize. We use Pydantic structured parsing, low reasoning effort, a strict token limit, `store=false`, and a bounded retry policy. The trace exposes the model ID and latency for each live action.

## How we used Codex

Codex was the implementation partner for the entire competition extension: evidence-based plan review, independent architecture, product specification, test-first backend and frontend work, browser QA, submission packaging, and deployment verification. The primary task ID is `019f725e-6f43-78c2-8587-4ad6a3725d9f`, and dated commit evidence is included in the repository.

## Challenges

The hardest part was maintaining an honest boundary. Exploration and natural-language reasoning must not appear Guard-certified, so non-intervention events always carry `guard: null`. A repaired proposal must preserve both the model's requested values and Guard's applied values. Finally, fallback had to remain demo-friendly without becoming fake live evidence, which led to a separate replay contract and highly visible mode labeling.

## Accomplishments

- A complete autonomous loop with structured GPT-5.6 actions and real adjudication feedback.
- Audit events that distinguish validation, Guard policy, state execution, and model reasoning.
- Automatic, unmistakable replay fallback without exposing a browser API key.
- Deterministic tests for COMMIT, REPAIR, REJECT, FORGET, invalid actions, limits, provider failure, rate limiting, CORS, UI behavior, and source provenance.
- A standalone repository and deployable Vercel/Railway split.

## What we learned

Auditability is not a log-shaped decoration. It requires precise ownership of each claim: the model proposed, validation accepted, Guard ruled, and the state engine applied. Showing those stages separately made both the system and the demo easier to trust.

## What's next

The current release intentionally uses one API process and in-memory session/rate-limit state. A production version would add a shared session store, distributed rate limiting, signed audit exports, policy version identifiers, and evaluation across a larger adversarial case suite.

## Testing instructions for judges

Open <https://memory-court-build-week.vercel.app> without an account. The competition-period **Silent Lifeboat** case is selected by default. Run a live audit when the green live badge is available, or inspect the gold **REPLAY MODE** trace. Compare the model proposal with the Guard ruling in the right panel, then export the audit JSON. Source and local verification instructions are public at <https://github.com/billgaohub/memory-court-build-week>.
