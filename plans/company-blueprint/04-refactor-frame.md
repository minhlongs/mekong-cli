# 04 - Refactor to 2026 Frame

> **Goal:** Transform the monolith (Python FastAPI + Node.js CLI) into a Cloudflare-first, edge-deployed API surface. The CLI becomes the sole interface; Python is fully removed.

## Current Architecture Issues

1. **Dual-stack complexity** -- Python backend (`src/`) and Node.js CLI coexist with no clear boundary. Both implement overlapping concerns (API key management, LLM routing, billing). This increases maintenance surface and forces developers to context-switch between two ecosystems.

2. **100+ scripts with mixed naming conventions** -- Scripts accumulated organically across `scripts/`, `bin/`, and `src/`. Some are Python, some are shell, some are inline Node.js. No naming standard, no ownership tags, no deprecation markers.

3. **338 commands in `.claude/commands/`** -- The command catalog grew without audit. Many are one-liner wrappers, duplicates, or references to deleted features. Each command adds cognitive load and maintenance cost.

4. **No unified API gateway** -- Currently relies on Claude Code's direct-to-script execution model. There is no API gateway layer for rate limiting, authentication, billing checks, or observability. Every "API endpoint" is just a file the LLM can invoke.

## Target Architecture

```
mekong/
  cli/              # CLI entrypoints (Node.js, run directly by user)
    mekong           # Main CLI binary
    mekong-dev       # Dev-mode CLI with hot reload
  core/             # Shared modules (NOT scripts)
    router/          # Command routing and dispatch
    billing/         # Unified billing checks and quota
    config/          # Project and user config management
    deploy/          # Deployment orchestration
    verify/          # Verification gates (build, test, audit)
  api/              # Cloudflare Workers edge API
    gateway.ts       # Unified API gateway (rate limit, auth, billing)
    routes/          # Per-domain route handlers
    middleware/      # Auth, logging, error handling
    wrangler.toml    # Workers config
```

## Refactor Priorities

### P1: CLI Is the ONLY Interface

- Remove Python FastAPI backend (`src/`) entirely.
- Port any surviving Python logic to TypeScript modules under `core/`.
- All CLI commands resolve through a single `mekong` entrypoint, not scattered scripts.
- Scripts that remain (shell wrappers, one-off tools) must live in `scripts/` and be tagged with a `@mekong-script` header for discoverability and audit.

**Acceptance:**
- `src/` directory deleted from repo root.
- `npm run mekong` is the one command to run the CLI.
- No `.py` file is executed during any refactor target workflow.

### P2: Consolidate Scripts into `core/` Modules

- Audit every file in `scripts/`, `bin/`, and top-level `.sh` files.
- Classify each into: (a) move to `core/` as a typed module, (b) move to `scripts/` with header, (c) delete (dead).
- `core/` modules export typed functions with Zod input validation, not stringly-typed shell wrappers.

**Acceptance:**
- `core/` contains no executable scripts -- only importable modules with unit tests.
- Every `core/` module has at least one test file in `tests/unit/core/`.
- Audit spreadsheet (or inline `scripts/AUDIT.md`) shows disposition of every original script.

### P3: Audit + Deduplicate Commands

- Scan all 338 entries in `.claude/commands/`. Tag each as: `keep`, `merge-into`, `deprecate`, `delete`.
- Merge duplicate commands into a single canonical implementation in `core/router/`.
- Deprecated commands get a one-line stub that prints `[DEPRECATED] Use 'mekong <subcommand>' instead.` and exits.
- Delete stubs after one major version cycle (tagged with `@deprecated-since`).

**Acceptance:**
- `.claude/commands/` reduced to under 100 entries.
- No duplicate commands exist (same operation, different name).
- Every kept command has a help text and argument validation.

### P4: Add Unified Billing API Endpoint

- Deploy a Cloudflare Worker at `api/` that provides a single `POST /billing/check` endpoint.
- Accepts: `{ userId, feature, quantity }`.
- Returns: `{ allowed: boolean, reason?: string, remainingCredits?: number }`.
- Used by both the CLI (before running billable commands) and any future API consumers.
- Backed by D1 for credit balances, with KV caching for fast reads.

**Acceptance:**
- `POST /billing/check` returns correct allow/deny for every tier (BASIC, PREMIUM, ENTERPRISE, MASTER).
- Worker deploys via `npm run deploy:api` from the project root.
- CLI calls `/billing/check` before executing any billable command and prints `[BILLING] Denied: ...` on rejection.

## Migration Plan

### Phase 1: Audit and Inventory (Week 1)

1. Run full script inventory and produce `scripts/AUDIT.md`.
2. Run full command catalog audit and tag every entry in `.claude/commands/`.
3. Identify Python modules with no Node.js equivalent -- these are the only porting candidates.
4. Freeze all new command additions until audit completes.

### Phase 2: Core Module Build (Week 2)

1. Scaffold `core/` directory structure with `router/`, `billing/`, `config/`, `deploy/`, `verify/`.
2. Port the top 5 most-used Python utilities to TypeScript in `core/`.
3. Wire up `mekong` CLI entrypoint to dispatch through `core/router/`.
4. Add unit tests for each ported module.

### Phase 3: API Gateway (Week 3)

1. Scaffold `api/` with Cloudflare Workers configuration (`wrangler.toml`, `gateway.ts`).
2. Implement `POST /billing/check` with D1 + KV.
3. Implement `GET /health` and `GET /version` endpoints.
4. Wire CLI to call `POST /billing/check` before billable operations.
5. Deploy to production and verify end-to-end.

### Phase 4: Cleanup (Week 4)

1. Delete `src/` Python backend.
2. Delete deprecated `.claude/commands/` entries.
3. Move remaining scripts to `scripts/` with headers.
4. Run full verification: `npm run build`, `npm test`, `mekong <every kept command>`.
5. Update `README.md` and `docs/` with new architecture.

## Risks and Rollback

| Risk | Mitigation |
|------|-----------|
| Python module has no Node.js equivalent library | Wrap in a thin shell subprocess call as last resort; mark for re-write |
| Breaking existing Claude Code commands | Keep old command names as aliases that dispatch through `core/router/` |
| Billing endpoint outage blocks CLI | CLI caches last-known billing decision for 60 seconds; falls back to allow on unreachable |
| Script audit misses a critical workflow | Keep all scripts in place during audit phase; delete only after Phase 4 verification |

## Verification

1. `npm run build` -- zero TypeScript errors.
2. `npm test` -- all tests pass.
3. `mekong --help` -- prints usage with all subcommands listed.
4. `mekong billing check --user=<id>` -- returns structured JSON.
5. `curl https://api.mekong.dev/billing/check` -- returns 200 with valid response.
6. `ls src/` -- returns `No such file or directory`.
7. `ls .claude/commands/ | wc -l` -- returns under 100.
