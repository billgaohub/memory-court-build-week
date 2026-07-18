# Codex build evidence

## Primary task

- Codex task ID: `019f725e-6f43-78c2-8587-4ad6a3725d9f`
- Build date: 2026-07-18 (Asia/Shanghai)
- Scope: review and replace the original game-extension plan; specify, implement, test, package, deploy, and audit a standalone Build Week application.

This single task contains the approved architecture and visual decisions plus the implementation trail. It should be used as the primary `/feedback` Session ID in the competition form.

## Codex-produced milestones

| Commit | Evidence |
|---|---|
| `79722b0` | Formal independent-app design specification |
| `c20a029` | Test-driven implementation and deployment plan |
| `fbbfc93` | Case contracts, Build Week case, and exact Guard snapshot |
| `f593e00` | Guard adapter with all four adjudication outcomes |
| `8c5efa4` | Bounded GPT-5.6 structured-action loop |
| `7b1a98f` | FastAPI, rate limiting, recovery, replay, and Docker |
| `3733fa4` | React audit console, tests, responsive implementation, and build |
| `6e02cf3` | Submission-ready English materials and verification gate |
| `485fd8d` | Standalone public-repository ignore boundary |
| `358576c` | Railway Docker and health-check configuration |
| `b87f60b` | Server-side provider exception audit without client credential exposure |
| `ac398e1` | Responses API `text.verbosity` compatibility fix |
| `a81d794` | Strict-schema patch-size compatibility fix with runtime validation preserved |
| `40d8120` | Flat strict action envelope accepted by the Responses schema contract |

## Verification performed by Codex

- Backend RED/GREEN cycles and the full deterministic test suite.
- Upstream sonuv-guard 121-test regression run.
- Frontend unit interaction tests, TypeScript check, and production build.
- Playwright desktop and 390px mobile rendering.
- Browser interaction proof for case switching and replay with zero console errors.
- Public GitHub visibility/license check, Railway Docker deployment, Vercel production build, public replay/CORS smoke, and zero-console-error production rendering.
- Source hash verification, unfilled-marker scan, and live-model evidence are recorded by the completion report.
- GPT-5.6 Sol inside Codex generated the six Silent Lifeboat action envelopes in this primary task. `test_codex_replay.py` re-executes them through the production session and Guard adapter and requires an exact replay match.

## Public deployment evidence

- Source: <https://github.com/billgaohub/memory-court-build-week>
- Frontend: <https://memory-court-build-week.vercel.app>
- API: <https://memory-court-api-production.up.railway.app>
- Railway project: `136c52ec-3f62-4cc3-8b97-0354b205da28`
- Railway service: `cf859640-8eae-4c81-8ab8-1cb4dda96575`
- Successful Railway live-request deployment: `1e473ebe-f1bd-42d8-b7a7-c3aefce42856`
- Ready Vercel production deployment: `dpl_7pLdyf7PYDYxP8zXFkAmrjCGuCnd`

## Claim boundary

Codex generated the competition-period extension and hosted the recorded GPT-5.6 Sol investigation. That trace is labeled `mode=replay` and `api_live=false`; the deployed OpenAI API path remains quota-blocked. Codex did not create the pre-existing sonuv-guard runtime or Last Birthday case. Their provenance is disclosed separately.
