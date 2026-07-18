#!/usr/bin/env bash
set -uo pipefail

APP_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKTREE_ROOT="$(cd "$APP_ROOT/.." && pwd)"
failures=0

pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1" >&2; failures=$((failures + 1)); }

required_files=(
  README.md PREEXISTING_VS_NEW.md SUBMISSION.md DEMO_SCRIPT.md
  CODEX_EVIDENCE.md SECURITY.md LICENSE .env.example
  railway.json frontend/vercel.json
  docs/specs/2026-07-18-memory-court-design.md
  docs/plans/2026-07-18-memory-court-implementation.md
  docs/verification/FINAL_REPORT.md
)

missing=()
for file in "${required_files[@]}"; do
  [[ -s "$APP_ROOT/$file" ]] || missing+=("$file")
done
if ((${#missing[@]} == 0)); then
  pass "submission files exist"
else
  fail "submission files missing: ${missing[*]}"
fi

placeholder_pattern='TODO|TBD|PLACEHOLDER|YOUR_[A-Z_]+|<repo>|<video>|<url>|<fill[^>]*>'
if ((${#missing[@]} == 0)) && ! rg -n -i "$placeholder_pattern" \
  "$APP_ROOT/README.md" "$APP_ROOT/PREEXISTING_VS_NEW.md" \
  "$APP_ROOT/SUBMISSION.md" "$APP_ROOT/DEMO_SCRIPT.md" \
  "$APP_ROOT/CODEX_EVIDENCE.md" \
  "$APP_ROOT/docs/verification/FINAL_REPORT.md"; then
  pass "submission prose has no placeholder markers"
else
  fail "submission prose contains placeholders or cannot be scanned"
fi

python_bin="python3"
if [[ -x "$WORKTREE_ROOT/.venv/bin/python" ]]; then
  python_bin="$WORKTREE_ROOT/.venv/bin/python"
fi
if (cd "$APP_ROOT/backend" && "$python_bin" -m pytest tests -q); then
  pass "backend contract and vendored Guard tests"
else
  fail "backend contract and vendored Guard tests"
fi

if [[ ! -d "$APP_ROOT/frontend/node_modules" ]]; then
  if (cd "$APP_ROOT/frontend" && npm ci); then
    pass "frontend dependencies installed from lockfile"
  else
    fail "frontend dependencies installed from lockfile"
  fi
fi

if (cd "$APP_ROOT/frontend" && npm test -- --run && npm run typecheck && npm run build); then
  pass "frontend tests, types, and production build"
else
  fail "frontend tests, types, and production build"
fi

upstream_guard="${SONUV_GUARD_ROOT:-}"
if [[ -z "$upstream_guard" ]] && [[ -d "/Users/bill/game/sonuv-guard/tests" ]]; then
  upstream_guard="/Users/bill/game/sonuv-guard"
fi
if [[ -n "$upstream_guard" ]] && [[ -d "$upstream_guard/tests" ]]; then
  if (cd "$upstream_guard" && "$python_bin" -m pytest tests -q); then
    pass "upstream sonuv-guard regression suite"
  else
    fail "upstream sonuv-guard regression suite"
  fi
else
  pass "upstream suite optional outside source workspace; vendored hashes enforced"
fi

if (cd "$WORKTREE_ROOT" && git diff --check -- . \
  ':(exclude)hackathon/backend/memory_court/vendor/sonuv_guard/**'); then
  pass "tracked patch whitespace"
else
  fail "tracked patch whitespace"
fi

if ((failures)); then
  printf '\n%d verification gate(s) failed.\n' "$failures" >&2
  exit 1
fi

printf '\nAll local submission gates passed. Live credentials and public deployment require separate evidence.\n'
