# Memory Court

Memory Court is an auditable autonomous-agent demo built for OpenAI Build Week. GPT-5.6 investigates a memory case, chooses one structured action per turn, and proposes bounded cognitive-state interventions. `sonuv-guard` independently adjudicates every intervention as **COMMIT**, **REPAIR**, **REJECT**, or **FORGET** before any state is applied.

The interface makes the boundary explicit: GPT-5.6 supplies the investigation and proposal; Guard controls structured state execution. Guard does not review or certify the model's natural-language reasoning.

## Judge experience

1. Open the application and select **The Silent Lifeboat**, the competition-period case.
2. If the server has an OpenAI key, choose **Run live audit**. The trace records the exact model ID, actions, latency, validation, Guard outcomes, and state diffs.
3. If live access is unavailable or fails after its bounded retry, the app automatically opens a fixed trace labeled **REPLAY MODE**. Replay never claims that a live model call occurred.
4. Choose **Export audit JSON** to inspect the complete evidence artifact.

No account is required. The public demo is free to test and rate-limits each client to five new live sessions per ten minutes.

## Architecture

```text
Vercel: React + TypeScript + Vite
             |
             v
Railway: FastAPI -> OpenAI Responses API (GPT-5.6)
             |
             v
       schema validation -> sonuv-guard -> committed state + audit event
```

The live loop is deliberately bounded to 8 model calls, 8 events, 3 intervention proposals, and 600 output tokens per call. Each OpenAI request has a 30-second timeout; timeout and rate-limit responses retry once. Sessions live in one API process for one hour. This is a transparent hackathon-grade design, not a distributed production control plane.

## Local setup

Requirements: Python 3.11+, Node.js 22+, and an optional OpenAI API key for live mode.

```bash
git clone https://github.com/bill/memory-court-build-week.git
cd memory-court-build-week

python3 -m venv .venv
. .venv/bin/activate
pip install -e 'backend[test]'

export OPENAI_API_KEY='your server-side key'
export ALLOWED_ORIGINS='http://localhost:5173'
uvicorn memory_court.app:app --app-dir backend --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd frontend
npm ci
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

Without `OPENAI_API_KEY`, `/api/health` reports `live_available=false` and the frontend presents the labeled replay.

## Verification

```bash
bash scripts/verify.sh
```

The gate runs 34 backend tests, frontend interaction tests, TypeScript checking, a production build, vendored-source hashes, and—inside the original source workspace—the upstream 121-test sonuv-guard regression suite.

## GPT-5.6 usage

The backend uses the async OpenAI Python SDK Responses API with `gpt-5.6`, Pydantic structured outputs, low reasoning effort, low verbosity, `store=false`, and a 600-token ceiling. Each response must be exactly one of:

- `inspect_memory`
- `propose_intervention`
- `finalize`

Only `propose_intervention` reaches Guard. Invalid fields, booleans masquerading as integers, out-of-range values, and empty patches are rejected before adjudication.

## Built with Codex

Codex was used to review the original game plan, isolate a standalone architecture, create the approved design specification, implement the backend and frontend test-first, package the pre-existing Guard runtime with provenance hashes, prepare deployment, and run the completion audit. The primary build task ID and commit evidence are recorded in [CODEX_EVIDENCE.md](CODEX_EVIDENCE.md).

## Provenance and scope

The autonomous loop, FastAPI service, React audit console, Silent Lifeboat case, replay system, deployment packaging, tests, and submission materials were created during the competition period. A precise snapshot of pre-existing `sonuv-guard` commit `62157c5` and the pre-existing Last Birthday case are disclosed in [PREEXISTING_VS_NEW.md](PREEXISTING_VS_NEW.md).

## Deployment

- Railway builds `backend/Dockerfile` from the repository root. Configure `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-5.6`, `TRUST_PROXY=true`, and `ALLOWED_ORIGINS`.
- Vercel uses `frontend` as Root Directory, `npm run build` as Build Command, `dist` as Output Directory, and the Railway origin as `VITE_API_BASE_URL`.
- After Vercel assigns the production domain, set that exact origin in Railway's `ALLOWED_ORIGINS` and redeploy.

See [SECURITY.md](SECURITY.md) for the threat boundary and [SUBMISSION.md](SUBMISSION.md) for competition copy.

## License

MIT. See [LICENSE](LICENSE).
