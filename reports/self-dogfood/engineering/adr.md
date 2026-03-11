# Architecture Decision Records — v5.0
Generated: 2026-03-11

> Consolidated ADRs for key v5.0 decisions. Detailed rationale in `arch-docs.md`.

---

## ADR-001: PEV Engine as Core Orchestration Pattern
**Status:** Accepted | **Date:** 2025-Q4

Plan → Execute → Verify loop with per-step rollback.
Each phase independently testable. Overhead (3+ LLM calls) accepted for reliability.

**Outcome:** Reliable autonomous execution with deterministic rollback. `orchestrator.py` currently 1,022 lines — scheduled for split (see `refactor-plan.md`).

---

## ADR-002: DAG Scheduler for Parallel Step Execution
**Status:** Accepted | **Date:** 2025-Q4

Steps declare `depends_on` list. Independent steps run via `asyncio.gather`.
DAG validated at plan time to catch cycles before execution.

**Outcome:** 2–4x speedup for parallelizable goals. `dag_scheduler.py` is separate, independently tested module.

---

## ADR-003: Universal 3-Variable LLM Router
**Status:** Accepted | **Date:** 2025-Q4

`LLM_BASE_URL` + `LLM_API_KEY` + `LLM_MODEL` works with any OpenAI-compatible endpoint.
Fallback chain: OpenRouter → AgentRouter → Qwen → DeepSeek → Anthropic → OpenAI → Gemini → Ollama → Offline.

**Outcome:** No vendor lock-in. Fully local operation possible. Import time 1.13s (acceptable).

---

## ADR-004: SQLite for Multi-Tenant Persistence (with PostgreSQL Migration Trigger)
**Status:** Accepted with Review Trigger | **Date:** 2026-Q1

SQLite at `/data/tenants.db` on Fly.io persistent volume.

**Review trigger:** Migrate to PostgreSQL when:
- Concurrent writes exceed SQLite WAL limits, OR
- Horizontal scaling beyond single Fly.io machine required, OR
- >1,000 active tenants

**Outcome:** Zero ops overhead for early-stage. Works identically local and on Fly.io.

---

## ADR-005: 5-Layer Command Pyramid (Org-Mirrored Namespace)
**Status:** Accepted | **Date:** 2025-Q3

289 commands organized into Founder / Business / Product / Engineer / Ops layers.
Each layer has distinct MCU cost profile and target user role.

**Outcome:** Commands discoverable by role. Prevents namespace collisions. Primary mental model in README and CLAUDE.md.

---

## ADR-006: Polar.sh as Sole Payment Provider
**Status:** Accepted — Non-negotiable | **Date:** 2026-Q1

Polar.sh Standard Webhooks only. PayPal fully removed. Stripe references are stale.

**Outcome:** Single billing surface. All `STRIPE_*`/`PAYPAL_*` env vars deprecated.
`deployment-guide.md` Stripe env var references need cleanup (tracked in `docs-status.md`).

---

## ADR-007: main.py as Thin Dispatcher (≤75 lines)
**Status:** Accepted | **Date:** 2026-Q1

`src/main.py` refactored from 1,898 → 75 lines. All business logic pushed to sub-modules.
main.py contains only: Typer app init, sub-command registration, `@app.callback`.

**Outcome:** Clean entry point. Easy to navigate. Standard for all future commands.

---

## ADR-008: Tenant Isolation via JWT Middleware (not DB-level RLS)
**Status:** Accepted | **Date:** 2026-Q1

All `/v1/*` endpoints require `Bearer` token. `require_tenant` middleware resolves
`TenantContext` from token before any handler logic runs. Tenant ID is passed
explicitly through every DB query — no row-level security at SQLite level.

**Rationale:** SQLite does not support RLS. Middleware enforcement is auditable and
testable without DB-level triggers.

**Review trigger:** If migrating to PostgreSQL, evaluate adding RLS as defence-in-depth.

---

## ADR-009: SSE for Task Progress Streaming (not WebSocket)
**Status:** Accepted | **Date:** 2026-Q1

Server-Sent Events (one-way push) chosen over WebSocket for task progress streaming.

**Rationale:**
- Tasks are unidirectional (server → client updates only)
- SSE works over standard HTTP/2 — no upgrade handshake
- Simpler client implementation (`EventSource` API)
- Compatible with Cloudflare Workers edge proxy

**Outcome:** `GET /v1/tasks/{id}/stream` returns `text/event-stream`.
Headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no`.

---

## ADR-010: Recipe YAML as Primary Task Format (v5.1 target)
**Status:** Proposed | **Date:** 2026-Q1

Goals submitted as free-text strings (current) will be supplemented by structured
YAML recipes for repeatable, parameterized workflows.

**Proposed schema:**
```yaml
name: create-api-endpoint
version: "1.0"
inputs:
  - name: endpoint_name
    type: string
steps:
  - title: Scaffold route
    run: "python3 scaffold.py {{endpoint_name}}"
    verify: "grep -r '{{endpoint_name}}' src/"
```

**Status:** Not yet implemented. Tracked in `kanban.md` as RR-01 through RR-06.
