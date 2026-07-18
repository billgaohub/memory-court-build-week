# Memory Court submission verification report

- Audit time: 2026-07-18 14:45 Asia/Shanghai
- Status: **PUBLIC REPLAY READY; LIVE GPT-5.6 NOT YET VERIFIED**
- Primary Codex task: `019f725e-6f43-78c2-8587-4ad6a3725d9f`
- Source branch commit: `358576cbbe916058193f66c2872aa39ec0d269c2`
- Published subtree commit: `7fed520c7f84d89df0f4d1cd9bf4b729f5c142dc`

This report deliberately remains incomplete on one required gate: Railway does not yet contain an `OPENAI_API_KEY`, so no replay event is presented as live-model proof.

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
| Backend contracts and Guard adapter | PASS — 34 tests |
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
- Public mode before key configuration: exactly one `REPLAY MODE` badge.
- Replay events: 5.
- Live control: disabled while `live_available=false`.
- Browser console: zero warnings and zero errors.
- Interaction: switching from Silent Lifeboat to Last Birthday and restarting replay changed the rendered trace from 5 to 4 events.

## Railway container and API verification

Railway used `/railway.json` with `builder=DOCKERFILE`, `dockerfilePath=backend/Dockerfile`, and `/api/health` as the health path. Deployment `39735c74-5b69-4add-85c1-3dd6cbdaf33a` completed with status `SUCCESS`.

| Public check | Result |
|---|---|
| `GET /api/health` | 200; model `gpt-5.6`; replay available; live unavailable |
| `GET /api/cases` | 200; one pre-existing and one competition-period case |
| `GET /api/replays/silent_lifeboat` | 200; top-level and all events use replay mode |
| Vercel-origin CORS preflight | 200; exact production origin returned |
| `POST /api/sessions` without key | 503; no fake live session created |
| Recent Railway runtime logs | clean startup and expected 200/404 smoke traffic; no application exception |

## Live GPT-5.6 gate

Current evidence contradicts completion of the live gate: the Railway variable-name audit contains `OPENAI_MODEL` but not `OPENAI_API_KEY`; `/api/health` returns `live_available=false`.

Required evidence after the entrant adds the server-side key:

1. Railway redeployment status `SUCCESS`.
2. `/api/health` returns `live_available=true` and `model=gpt-5.6`.
3. A new public session runs to terminal.
4. At least one returned event has `mode=live`, `model=gpt-5.6`, `model_action=propose_intervention`, and a non-null Guard outcome.
5. The response and logs contain no credential material.
6. Production frontend displays `LIVE · GPT-5.6` and the same executed trace.

## Known demo-grade limits

- Session and rate-limit state are process-local.
- One Railway replica is assumed.
- Replay is a fixed fixture and is never live evidence.
- The API is intentionally unauthenticated and cost-bounded for free judge access.

## Entrant-only actions after technical completion

1. Confirm personal and regional eligibility.
2. Record the supplied 166-second narrated script and upload it to YouTube.
3. Paste the repository, application, video, and primary Codex task ID into Devpost and click final submit.
