# Security and trust boundary

Memory Court is a public hackathon demo. It is designed to make its safety boundary inspectable, not to claim production readiness.

## Protected assets

- `OPENAI_API_KEY` is read only by FastAPI and must be stored as a Railway environment variable.
- The frontend bundle contains only `VITE_API_BASE_URL`; it never receives provider credentials.
- Audit events exclude request headers, credentials, raw provider exceptions, and stack traces.

## Input and execution boundary

- Users select version-controlled case IDs; they cannot upload Python or policy expressions.
- GPT-5.6 produces one Pydantic-discriminated action per turn.
- Intervention patches accept only declared integer fields within case ranges. Python booleans are rejected rather than treated as integers.
- Only validated intervention patches reach sonuv-guard. Inspection, rationale text, and finalization are not represented as Guard-approved.
- State changes occur only from Guard's applied patch.

## Cost and abuse controls

- Five new live sessions per client address per ten-minute fixed window.
- Eight model calls, eight events, three proposals, and 600 output tokens per session.
- Thirty-second provider timeout and one retry for timeout or provider rate limiting.
- `TRUST_PROXY` is disabled locally and enabled only behind Railway's trusted proxy.
- CORS uses explicit local and Vercel origins.

## Known demo limitations

- Sessions and rate-limit counters are process-local and reset on deployment or restart.
- A multi-instance deployment would require shared storage and distributed limiting.
- There is no user authentication, persistent personal data, or user-supplied case execution.
- Replay is deterministic demonstration data, visibly labeled and never accepted as live-model evidence.

## Reporting

Do not submit secrets in a public issue. Use the repository owner's private GitHub contact channel and include the affected route, reproduction steps, and impact without including a real API key.
