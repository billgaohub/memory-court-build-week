# Competition-period provenance

The repository is a standalone Build Week application, but it intentionally demonstrates a new agent workflow against a disclosed pre-existing policy engine.

## Pre-existing assets

### sonuv-guard runtime

- Source: the independent local `sonuv-guard` repository.
- Snapshot commit: `62157c5`.
- Competition repository location: `backend/memory_court/vendor/sonuv_guard/`.
- The eight Python runtime files are byte-for-byte snapshots. `backend/tests/test_vendor.py` pins every SHA-256 digest so an accidental change fails verification.
- The snapshot is integration material, not claimed as a Build Week invention.

### The Last Birthday case

- Case ID: `last_birthday`.
- Provenance field: `pre_existing`.
- Purpose: compatibility evidence that the new autonomous audit loop can exercise a prior grief-memory rule set.
- The UI labels it **PRE-EXISTING CASE**.

## Created during Build Week

- The **Silent Lifeboat** case and its accountable-memory rule set.
- The bounded GPT-5.6 Responses API agent and one-action structured protocol.
- Schema, field, range, empty-patch, and boolean validation.
- The adapter that submits only structured intervention patches to Guard.
- Per-event audit contracts, requested/applied patch evidence, and state diffs.
- The FastAPI service, one-hour in-memory sessions, CORS allowlist, and fixed-window rate limit.
- The explicitly labeled, version-controlled replay mode and automatic live-failure fallback.
- The React/Vite three-panel audit console and JSON export.
- Docker/Vercel/Railway deployment packaging.
- Backend, frontend, regression, provenance, and submission verification tests.
- Design specification, implementation plan, security notes, demo script, submission copy, and completion report.

## Competition commit history

The standalone implementation begins with these dated commits on 2026-07-18:

- `79722b0` — approved design specification
- `c20a029` — test-driven implementation plan
- `fbbfc93` — cases, contracts, and vendored runtime
- `f593e00` — Guard adjudication adapter
- `8c5efa4` — bounded GPT-5.6 audit loop
- `7b1a98f` — FastAPI, rate limiting, replay, and Docker
- `3733fa4` — React audit console

Later documentation and deployment-evidence commits are recorded in `CODEX_EVIDENCE.md` and the final verification report.
