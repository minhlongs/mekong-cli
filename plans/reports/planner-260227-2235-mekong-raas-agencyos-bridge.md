# Planner Report: Mekong-CLI RaaS Bridge to AgencyOS

**Date:** 2026-02-27 | **Plan:** `plans/260227-2231-mekong-raas-agencyos-bridge/`

## Summary

Created 7-phase parallel implementation plan for the open-core bridge connecting mekong-cli (MIT, Python) to AgencyOS (closed, Next.js) for non-tech RaaS delivery.

## Key Architecture Decision

All new code lives in `src/raas/` — a self-contained Python package within the existing mekong-cli project. Only 1 line touches existing code (mounting the router in `gateway.py`). This preserves backward compatibility and keeps the open-core boundary clean.

```
src/raas/
├── __init__.py        # Phase 01
├── auth.py            # Phase 01 — API key auth + FastAPI dependency
├── tenant.py          # Phase 01 — SQLite-backed tenant store
├── credits.py         # Phase 02 — atomic credit operations
├── billing.py         # Phase 02 — Polar.sh webhook handler
├── missions.py        # Phase 03 — 5 REST endpoints wrapping AGIBridge
├── mission_models.py  # Phase 03 — Pydantic models + enums
├── dashboard.py       # Phase 04 — summary + costs endpoints
├── sse.py             # Phase 04 — SSE streaming infrastructure
├── sdk.py             # Phase 05 — thin Python client for AgencyOS
├── registry.py        # Phase 06 — recipe marketplace
```

## Parallel Execution Strategy

```
TIME ──────────────────────────────────────────────────>

Group A (8h):  [Phase 01: Auth] + [Phase 02: Credits] + [Phase 03: Missions]
                     ↓                    ↓                     ↓
Group B (10h): [Phase 04: Dashboard SSE] + [Phase 05: SDK] + [Phase 06: Registry]
                            ↓                    ↓                  ↓
Group C (6h):  [Phase 07: Integration Tests + Docs]
```

Wall-clock with 3 parallel agents: ~14h (vs 24h sequential).

## File Ownership Matrix — Zero Overlap

Each phase owns exclusive files. No merge conflicts possible during parallel execution.

## Builds On Existing Infrastructure

| Existing Component | How Bridge Uses It |
|---|---|
| `gateway.py` (738 lines) | Mount 1 router via `include_router()` |
| `agi_bridge.py` | `dispatch()`, `status()`, `logs()` for mission lifecycle |
| `event_bus.py` | Subscribe to events for SSE streaming |
| `memory.py` | Read execution history for dashboard |
| SQLAlchemy (in deps) | Already available; using SQLite for tenant/credit storage |
| httpx (in dev deps) | Promote to main deps for SDK |

## Unresolved Questions

1. **Mission completion callback:** Current Tôm Hùm signals via `/tmp/tom_hum_mission_done` (single file, not tenant-scoped). Phase 03 will need polling or tenant-scoped signal files.
2. **httpx promotion:** Currently dev dep only. SDK needs it as main dep. Need to update pyproject.toml.
3. **SQLite path:** Using `~/.mekong/raas/tenants.db`. Need to ensure dir creation on first run.
4. **Cloudflare Worker update:** `apps/raas-gateway/index.js` may need new routes for `/raas/*` passthrough. Deferred — local gateway sufficient for v1.
5. **Credit cost calibration:** Actual LLM cost per mission type needs profiling from live runs before launch pricing.
