# Vendored sonuv-guard runtime

This directory is an exact runtime snapshot of the pre-existing local
`sonuv-guard` project at Git commit `62157c5` (2026-07-14).

- Upstream local source during the competition: `/Users/bill/game/sonuv-guard`
- Included files: the eight tracked Python runtime files under `sonuv_guard/`
- Excluded: tests, build output, data, examples, and untracked files
- Upstream package declaration: MIT (`pyproject.toml`)
- Competition status: pre-existing asset; not claimed as Build Week work

`backend/tests/test_vendor.py` pins SHA-256 hashes for every included file so
the submission cannot silently describe modified code as the upstream snapshot.
