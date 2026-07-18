# Memory Court submission verification report

- Audit time: 2026-07-18 15:58 Asia/Shanghai
- Status: **DISCLOSED CODEX GPT-5.6 SUBMISSION ROUTE READY; OPENAI API LIVE BLOCKED BY QUOTA**
- Primary Codex task: `019f725e-6f43-78c2-8587-4ad6a3725d9f`
- Source branch code commit: `757ce2d741dad963843625dfa28f07483f6280b0`
- Published subtree commit: `c8107f16ffc705cde29735e23cba21efeee1cf47`

Railway has a server-side `OPENAI_API_KEY`, and the production request passes the Responses parameter and strict-schema checks, but OpenAI returns `429 insufficient_quota`. The judgeable fallback is now a competition-period GPT-5.6 Sol trace generated inside Codex and reproducibly executed against sonuv-guard. It is disclosed as recorded replay evidence, not API-live proof.

## Public artifacts

| Artifact | URL | Evidence |
|---|---|---|
| GitHub | <https://github.com/billgaohub/memory-court-build-week> | PUBLIC; main; MIT detected; standalone subtree only |
| Frontend | <https://memory-court-build-week.vercel.app> | Vercel production deployment `A5mcG63x5SjDeAUJ7sbP9voYZNsL`; aliased and Ready |
| API | <https://memory-court-api-production.up.railway.app> | Railway service `cf859640-8eae-4c81-8ab8-1cb4dda96575` |

## Local gates

Command: `bash scripts/verify.sh`

| Gate | Result |
|---|---|
| Required submission files | PASS |
| Unfilled-marker scan | PASS |
| Backend contracts and Guard adapter | PASS — 36 tests |
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
- Silent Lifeboat replay events: 6, including Guard `REPAIR` followed by `COMMIT`.
- Live readiness is now advertised because a server-side key is configured; a provider failure still enters labeled replay.
- Visible provenance note: GPT-5.6 Sol inside Codex, executed against sonuv-guard, not through the OpenAI API.
- Browser console: zero warnings and zero errors.
- Interaction: direct replay load rendered 6 events; clicking live reached the quota failure and automatically switched to the same labeled replay.

## Railway container and API verification

Railway used `/railway.json` with `builder=DOCKERFILE`, `dockerfilePath=backend/Dockerfile`, and `/api/health` as the health path. Latest deployment `caae1f66-4280-4d51-a9e8-5046df0cb8fb` completed with status `SUCCESS`.

| Public check | Result |
|---|---|
| `GET /api/health` | 200; model `gpt-5.6`; replay and live readiness available |
| `GET /api/cases` | 200; one pre-existing and one competition-period case |
| `GET /api/replays/silent_lifeboat` | 200; `provenance=codex_gpt_5_6_sol`; `api_live=false`; 6 replay events; Guard actions `REPAIR`, `COMMIT` |
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

## Recorded GPT-5.6 Sol / Codex evidence

- Source: `replay/silent_lifeboat.codex-actions.json`.
- Generator: GPT-5.6 Sol inside Codex, primary task `019f725e-6f43-78c2-8587-4ad6a3725d9f`.
- Disclosure: `api_live=false`; public model label is `gpt-5.6-sol via Codex (recorded)`.
- Execution: the six envelopes run through `AgentSession` and the production sonuv-guard adapter.
- Deterministic result: three inspections, a `REPAIR`, a follow-up `COMMIT`, and `finalize`; final state accountability 82, distress 58, trust 65, mission stability 70.
- Verification: `test_codex_replay.py` requires the regenerated events and final state to match the published fixture exactly.

## Known demo-grade limits

- Session and rate-limit state are process-local.
- One Railway replica is assumed.
- Replay is a fixed fixture and is never live evidence.
- The API is intentionally unauthenticated and cost-bounded for free judge access.
- Whether recorded GPT-5.6 usage inside Codex satisfies the competition's GPT-5.6 requirement is ultimately an organizer/judging interpretation; this package makes the evidence and non-API boundary explicit.
- Public GitHub Actions run `29636573447` passed against subtree commit `c8107f1`.

## Entrant-only actions after technical completion

1. Confirm personal and regional eligibility.
2. Record the supplied 166-second narrated script and upload it to YouTube.
3. Paste the repository, application, video, and primary Codex task ID into Devpost and click final submit.
