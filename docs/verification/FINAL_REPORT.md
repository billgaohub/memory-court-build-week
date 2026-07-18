# Memory Court submission verification report

- Audit time: 2026-07-18 15:27 Asia/Shanghai
- Status: **PUBLIC REPLAY READY; LIVE GPT-5.6 BLOCKED BY API QUOTA**
- Primary Codex task: `019f725e-6f43-78c2-8587-4ad6a3725d9f`
- Source branch code commit: `40d8120f4020db67cb876aa89f7d7ce695c4c8f8`
- Published subtree commit: `7fed520c7f84d89df0f4d1cd9bf4b729f5c142dc`

This report deliberately remains incomplete on one required gate. Railway has a server-side `OPENAI_API_KEY`, the production request now passes the Responses parameter and strict-schema checks, but OpenAI returns `429 insufficient_quota`. No replay event is presented as live-model proof.

## Public artifacts

| Artifact | URL | Evidence |
|---|---|---|
| GitHub | <https://github.com/billgaohub/memory-court-build-week> | PUBLIC; main; MIT detected; standalone subtree only |
| Frontend | <https://memory-court-build-week.vercel.app> | Vercel deployment `dpl_7pLdyf7PYDYxP8zXFkAmrjCGuCnd`; target production; Ready |
| API | <https://memory-court-api-production.up.railway.app> | Railway service `cf859640-8eae-4c81-8ab8-1cb4dda96575` |

## Local gates

Command: `bash scripts/verify.sh`

| Gate | Result |
|---|---|
| Required submission files | PASS |
| Unfilled-marker scan | PASS |
| Backend contracts and Guard adapter | PASS — 35 tests |
| Frontend interaction tests | PASS — 4 tests |
| TypeScript | PASS |
| Vite production build | PASS |
| Upstream sonuv-guard regression | PASS — 121 tests |
| Patch whitespace, excluding byte-exact vendor snapshot | PASS |

## Rendered frontend verification

- Local viewports: 1440×900 and 390×844.
- Production viewport: 1440×900.
- Page title: `Memory Court — GPT-5.6 Audit`.
- Default case: `silent_lifeboat`.
- Public replay mode: exactly one `REPLAY MODE` badge.
- Replay events: 5.
- Live readiness is now advertised because a server-side key is configured; a provider failure still enters labeled replay.
- Browser console: zero warnings and zero errors.
- Interaction: switching from Silent Lifeboat to Last Birthday and restarting replay changed the rendered trace from 5 to 4 events.

## Railway container and API verification

Railway used `/railway.json` with `builder=DOCKERFILE`, `dockerfilePath=backend/Dockerfile`, and `/api/health` as the health path. Latest deployment `1e473ebe-f1bd-42d8-b7a7-c3aefce42856` completed with status `SUCCESS`.

| Public check | Result |
|---|---|
| `GET /api/health` | 200; model `gpt-5.6`; replay and live readiness available |
| `GET /api/cases` | 200; one pre-existing and one competition-period case |
| `GET /api/replays/silent_lifeboat` | 200; top-level and all events use replay mode |
| Vercel-origin CORS preflight | 200; exact production origin returned |
| `POST /api/sessions` with server key | 201; creates `mode=live`, model `gpt-5.6` |
| `POST /api/sessions/{id}/run` | 200; safely terminates as `live_model_unavailable`, allowing labeled replay fallback |
| Recent Railway runtime logs | full server-side exception chain; final provider cause is `429 insufficient_quota`; no credential material |

## Live GPT-5.6 gate

Current evidence contradicts completion of the live gate: production session `9MLXheuOzU30n1Sz-b1XydwP` reached OpenAI after all request/schema fixes, then the provider returned `429 insufficient_quota`. It produced no model action and no Guard ruling.

Required evidence after the entrant enables billing or quota for the OpenAI project behind the deployed key:

1. A new public session runs to terminal without `live_model_unavailable`.
2. At least one returned event has `mode=live`, `model=gpt-5.6`, `model_action=propose_intervention`, and a non-null Guard outcome.
3. The response and logs contain no credential material.
4. Production frontend displays `LIVE · GPT-5.6` and the same executed trace.

## Known demo-grade limits

- Session and rate-limit state are process-local.
- One Railway replica is assumed.
- Replay is a fixed fixture and is never live evidence.
- The API is intentionally unauthenticated and cost-bounded for free judge access.

## Entrant-only actions after technical completion

1. Confirm personal and regional eligibility.
2. Record the supplied 166-second narrated script and upload it to YouTube.
3. Paste the repository, application, video, and primary Codex task ID into Devpost and click final submit.
