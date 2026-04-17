# Plan — mekongd v0 (Qwen3.6 Local Daemon for CC CLI Cost-Saving)

**Created:** 2026-04-17 10:24 | **Branch:** `feat/mekongd-v0-qwen-daemon`
**Scope:** Monorepo subfolder `packages/mekongd/` (Python, PUBLIC SDK per CLAUDE.md allowlist)
**Research:** [research-260417-1024-qwen36-solo-company.md](../reports/research-260417-1024-qwen36-solo-company.md)

## Goal

Ship MVP v0 of `mekongd` — a local daemon that routes CC CLI subagent calls to Qwen3.6-35B-A3B on M1 Max instead of Anthropic API, cutting bills 4-10x.

## Value Prop

Heavy CC CLI user burns $200-500/mo on Claude API. `mekongd` routes low-stakes subagent work (explore/search/reformat) to local Qwen3.6 (SWE-bench 73.4, 30 tok/s on M1 Max) while keeping Opus for plan/review. Target: $19/mo SaaS or FOSS+Polar donations.

## MVP v0 Scope (SHIP-IN-WEEK)

- Python package `tools/mekongd/` with typer CLI: `mekongd serve|stats|config`
- MLX-based Qwen3.6-35B-A3B loader (Q4 quantization, ~20GB RAM)
- FastAPI proxy with **Anthropic-compat** `/v1/messages` endpoint (primary use case: CC CLI)
- Streaming SSE responses matching Anthropic schema
- Simple regex-based policy router: system prompt patterns → local vs cloud
- SQLite stats: tokens routed local vs cloud, estimated $ saved
- Unit + integration tests (mock MLX for CI)

## OUT OF SCOPE for v0 (YAGNI)

- OpenAI-compat `/v1/chat/completions` (add later if user demand)
- Polar billing integration
- Cloudflare Tunnel deployment
- Multi-tenant / auth
- Fine-tuned routing policy (v0 = regex; later = embeddings)
- Web dashboard (v0 = CLI stats only)

## Phases

| Phase | Scope | Files | Status |
|-------|-------|-------|--------|
| [01](phase-01-scaffold.md) | Package scaffold, CLI, config, stats schema | `packages/mekongd/{pyproject.toml,src/mekongd/*.py}` | ✅ Done |
| [02](phase-02-mlx-proxy.md) | MLX loader + Anthropic-compat `/v1/messages` | `mekongd/{runtime.py,proxy.py,schemas.py}` | ✅ Done |
| [03](phase-03-router-stats.md) | Policy router + stats + tests | `mekongd/{router.py,stats.py}`, `tests/` | ✅ Done |

## Ship Summary (2026-04-17 11:xx)

- 8 Python files, 660 LOC (all <200 lines/file — max 189)
- 5 test files, **22/22 tests pass**
- CLI works: `--version`, `config show`, `stats show`
- Code review: 85% (68/80), **0 critical**, 3 minor non-blocking follow-ups
- Review report: [code-review-260417-1030-mekongd-v0.md](../reports/code-review-260417-1030-mekongd-v0.md)

## Dependencies

- `mlx` + `mlx-lm` (Apple Silicon LLM runtime)
- `fastapi` + `uvicorn` + `sse-starlette` (proxy)
- `typer` + `pydantic` + `pydantic-settings` (CLI + config)
- `httpx` (cloud fallback to Anthropic)
- `anthropic` SDK (optional, for cloud-side types)

## Tech Stack Justification

- **MLX over llama.cpp:** 2x faster on Apple Silicon per benchmark (antekapetanovic.com/blog/qwen3.5-apple-silicon-benchmark/)
- **FastAPI + SSE:** Anthropic Messages API uses SSE streaming — native fit
- **Typer over Click:** consistency with existing Mekong CLI
- **SQLite stats:** zero-config, aligns with existing `src/core/signals/local_store.py` pattern

## Success Criteria

- `mekongd serve` boots, loads Qwen3.6 Q4 (or stub in dev), exposes `/v1/messages`
- `curl` to `/v1/messages` returns Anthropic-compat response
- Router correctly dispatches based on regex policy
- Stats CLI shows tokens + $ saved
- All unit + integration tests pass
- CI gates (G1-G5) green
- PR merged to main

## File Ownership

All files NEW — no conflicts with existing code. Branch isolated. No parallel session risk.

## Risk Register

| Risk | Mitigation |
|------|------------|
| MLX install fails on CI (no Apple Silicon runner) | Mock MLX runtime in tests; skip real-model tests outside Mac runner |
| Qwen3.6 weights 20GB — long download | Do NOT download in CI; use `pytest.mark.requires_model` skip |
| Anthropic API schema drift | Pin `anthropic` SDK version; snapshot-test response shapes |
| Streaming SSE edge cases (truncate, cancel) | Integration tests with fastapi TestClient |
| M1 Pro cannot run Qwen3.6 (remote-only per user rule) | Dev + test on M1 Pro w/ stub; real model runs via SSH to M1 Max |

## Next

Phase 01 → Phase 02 → Phase 03 → Test → Review → Merge.
