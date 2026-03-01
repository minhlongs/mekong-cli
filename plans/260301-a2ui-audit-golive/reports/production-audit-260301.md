# Production Code Audit — 260301

## Results

| Check | Result | Details |
|-------|--------|---------|
| Ruff Lint | ✅ | 13 auto-fixed (initial), +2 F401 fixed after planner.py edit — 0 remaining |
| Security Scan | ✅ | No hardcoded secrets or credential URLs in src/ — llm_client.py references are comment docs only |
| Tech Debt — print() | ✅ | 3 `print()` calls fixed → replaced with `logging.warning/error` in `src/core/planner.py` |
| Tech Debt — TODO/FIXME | ✅ | 0 real TODOs (3 grep hits are inside verifier.py checking for TODOs in external output) |
| Tech Debt — `: Any` types | ⚠️ | 17 instances in src/ (swarm.py, protocol_handler.py, agent_execution_sandbox.py, etc.) — see below |
| npm/pnpm audit | ⚠️ | 22 vulnerabilities (2 low, 5 moderate, 15 high) in sub-apps — all transitive, none in mekong-cli core src/ |
| @ts-ignore in src/ | ✅ | 1 legitimate use in `packages/core/vibe/src/hardened/diagnostics.ts` (import.meta cross-env cast) |

---

## Issues Fixed

- **13 ruff auto-fixes** (initial run with `--fix --unsafe-fixes`): unused imports, formatting, style
- **2 additional ruff F401 fixes**: `_Group` import in `src/a2ui/components.py`, `COMPONENT_REGISTRY` import in `src/a2ui/renderer.py`
- **E402 import order fix**: `src/core/planner.py` — moved `logger = logging.getLogger(__name__)` to after all imports
- **3 `print()` → `logging`** in `src/core/planner.py`:
  - `print("[PLANNER] LLM unavailable...")` → `logger.warning(...)`
  - `print("[PLANNER] LLM returned non-JSON...")` → `logger.warning(...)`
  - `print("[PLANNER] LLM decomposition failed: {e}")` → `logger.error(...)`
- **pnpm audit --fix**: Added package overrides for next, fastify, hono, ajv, minimatch, rollup, serialize-javascript, bn.js — lockfile updated

---

## Remaining Issues

### ⚠️ Type Safety — 17 `: Any` annotations in src/

Files with `Any` usage (not violations in themselves, but tech debt to track):

| File | Count | Notes |
|------|-------|-------|
| `src/core/swarm.py` | 6 | `_route_step`, `_dispatch_local`, `_dispatch_remote`, `dispatch` — step type unions |
| `src/core/protocol_handler.py` | 2 | `orchestrator: Any`, `recipe_registry: Any` — lazy circular import workaround |
| `src/core/agent_execution_sandbox.py` | 3 | `Callable[..., Any]`, signal handler frame |
| `src/core/agent_preferences_registry.py` | 1 | `**kwargs: Any` |
| `src/core/durable_step_store.py` | 1 | `result: Any` — heterogeneous step results |
| `src/core/verifier.py` | 2 | String literals in docstring/comment (not actual type annotations) |
| `src/binh_phap/standards.py` | 2 | String literals in docstring/grep scan (not actual type annotations) |

**Recommendation**: Address `swarm.py` and `protocol_handler.py` with proper Protocol/Union types in next sprint. The `verifier.py` and `standards.py` hits are false positives (grep strings, not annotations).

### ⚠️ npm/pnpm Vulnerabilities — 22 in sub-apps (NOT mekong-cli core)

All vulnerabilities are **transitive** in sub-application packages, not in the core Python src/:

| Severity | Count | Packages |
|----------|-------|---------|
| High | 15 | xlsx (com-anh-duong-10x), next (developers), fastify (engine), hono (apex-os), ajv, bn.js, minimatch, rollup, serialize-javascript |
| Moderate | 5 | Various transitive deps |
| Low | 2 | hono timing comparison |

**pnpm audit --fix** was applied — overrides added to `pnpm-lock.yaml`. Remaining vulnerabilities require manual version bumps in individual `apps/*/package.json`:
- `apps/com-anh-duong-10x`: `xlsx@0.18.5` → no public patch exists (no fix available per advisory)
- `apps/engine`: `fastify@4.29.1` → upgrade to `>=5.7.2`
- `apps/developers`: `next@16.0.10` → upgrade to `>=16.0.11`

### ⚠️ `@ts-ignore` — 1 legitimate instance

- `packages/core/vibe/src/hardened/diagnostics.ts:36` — suppresses `import.meta.env` access in cross-environment (Node/Vite) context. Acceptable as-is; tracked for future refactor using `globalThis` or conditional import.

---

## Unresolved Questions

1. Should `apps/com-anh-duong-10x` xlsx be replaced with a maintained fork (exceljs, sheetjs-pro)?
2. `swarm.py` Any types — should step types be unified under a `StepProtocol` TypedDict?
3. `apps/engine` fastify — is v5.x API-compatible with current engine code before upgrading?
