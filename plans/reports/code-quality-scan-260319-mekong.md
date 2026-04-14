# Code Quality Scan Report — Mekong CLI

**Date:** 2026-03-19
**Scope:** Python (`mekong/`, `scripts/`, `src/`), TypeScript (`packages/`)
**Report Path:** `/plans/reports/code-quality-scan-260319-mekong.md`

---

## Executive Summary

| Category | Count | Severity |
|----------|-------|----------|
| Critical Security Issues | 4 | CRITICAL |
| Type Safety Violations | 146 (`: any` usages) | HIGH |
| Files > 200 Lines | 20+ | MEDIUM |
| Broad Exception Handlers | 100+ | MEDIUM |
| TODO/FIXME Comments | 59 | LOW |
| Console.log Statements | 48 files | LOW |

**Overall Assessment:** Codebase is functional but has significant technical debt in security practices, type safety, and code organization.

---

## CRITICAL Issues (Security)

### 1. Shell Injection Risk via `shell=True`

**Pattern:** `subprocess.run(cmd, shell=True, ...)` with string formatting

| File | Line | Code |
|------|------|------|
| `src/core/world_model.py` | 396 | `subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)` |
| `src/core/tool_registry.py` | 290 | `subprocess.run(f"{command} --help", shell=True, ...)` |
| `src/core/tool_registry.py` | 239-240 | Uses `shlex.split` but still vulnerable via `command_template.format()` |
| `src/commands/lint.py` | Multiple | 30+ subprocess calls without `shell=True` but using string commands |

**Risk:** Command injection if user input reaches these commands.

**Recommended Fix:**
```python
# Before (VULNERABLE)
subprocess.run(f"git {subcommand}", shell=True)

# After (SAFE)
import shlex
subprocess.run(["git"] + shlex.split(subcommand), capture_output=True)
```

### 2. WorldModel Environment Variable Exposure

**File:** `src/core/world_model.py`
**Line:** 144-154

```python
# Current code masks but still stores sensitive values
if any(s in k.upper() for s in _SENSITIVE):
    state.env_vars[k] = v[:4] + "****" if len(v) > 4 else "****"
```

**Issue:** Masking happens AFTER values are already captured. The masking is cosmetic only.

**Recommended Fix:** Exclude sensitive vars entirely from snapshot.

### 3. Code Evolution Engine — Self-Modification Without Validation

**File:** `src/core/code_evolution.py`
**Lines:** 275-282, 443-459

```python
# LLM generates code directly without validation
modified = self._llm_generate_improvement(file_path, original, description)
full_path.write_text(change.modified_content)  # Direct write!
```

**Risk:** LLM could generate malicious code that gets written and executed.

**Recommended Fix:**
- Add syntax validation before write
- Add import/symbol verification
- Require human approval for self-modifications

### 4. Hardcoded Secret Patterns in Codebase

**Files with SECRET/TOKEN patterns (non-exhaustive):**

| File | Pattern | Risk |
|------|---------|------|
| `src/auth/config.py` | `JWT_SECRET=REDACTED_KEY`, `STRIPE_SECRET_KEY` | Env vars (acceptable) |
| `src/auth/session_manager.py:22` | `JWT_SECRET=REDACTED = os.getenv("JWT_SECRET=REDACTED", secrets.token_urlsafe(32))` | Fallback secret in code |
| `src/raas/webhook_bridge.py` | `STRIPE_SECRET_KEY`, `POLAR_API_KEY` | Env vars (acceptable) |
| `jobs/nightly_reconciliation.py` | `STRIPE_SECRET_KEY`, `TELEGRAM_BOT_TOKEN` | Env vars (acceptable) |

**Recommendation:** Remove fallback secrets, require env vars in all environments.

---

## HIGH Priority Issues

### 1. Type Safety — `any` Type Usage (146 occurrences across 48 files)

**Top Offenders:**

| File | Count |
|------|-------|
| `packages/mekong-engine/src/types/error.ts` | 6 |
| `packages/mekong-engine/src/lib/ledger-utils.ts` | 2 |
| `packages/mekong-engine/src/lib/webhook-utils.ts` | 3 |
| `packages/mekong-engine/src/routes/*` | 40+ |

**Example:**
```typescript
// packages/mekong-engine/src/types/error.ts:118
export function handleAsync<T>(
  fn: (c: any) => Promise<T>  // ❌ Should be typed Hono Context
): (c: any) => Promise<T | Response>  // ❌ Both params untyped
```

**Recommended Fix:**
```typescript
import type { Context } from 'hono'
import type { Bindings } from './index'

export function handleAsync<T>(
  fn: (c: Context<{ Bindings: Bindings }>) => Promise<T>
): (c: Context<{ Bindings: Bindings }>) => Promise<T | Response>
```

### 2. Missing Error Handling — Broad `except Exception:` (100+ occurrences)

**Pattern:** Silent exception swallowing without logging

| File | Lines | Issue |
|------|-------|-------|
| `src/core/autonomous.py` | 118, 135, 143, 165, 174, 222, 264, 278, 287, 342 | 10 bare excepts |
| `src/core/orchestrator.py` | 151, 415, 549, 560, 572, 594, 606, 656 | 8 bare excepts |
| `src/lib/raas_gate.py` | 70, 186, 209, 588, 628, 652, 669, 694 | 8 bare excepts |
| `src/core/agi_score.py` | 164-266 | 9 bare excepts in scoring logic |

**Example:**
```python
# src/core/autonomous.py:118
try:
    # Critical operation
except Exception:
    pass  # ❌ Silent failure
```

**Recommended Fix:**
```python
import logging
logger = logging.getLogger(__name__)

try:
    # Critical operation
except Exception as e:
    logger.error("Operation failed: %s", e, exc_info=True)
    raise  # Or handle appropriately
```

### 3. TypeScript Files Over 200 Lines

| File | Lines | Recommendation |
|------|-------|----------------|
| `packages/mekong-engine/src/types/error.ts` | 323 | Split error types, helpers, handlers |
| `packages/mekong-engine/src/index.ts` | 259 | Extract route registration |
| `packages/mekong-engine/src/lib/ledger-utils.ts` | 258 | Split by domain function |
| `packages/mekong-engine/src/routes/governance.ts` | 400 | Split into sub-routes |
| `packages/mekong-engine/src/routes/funding.ts` | 298 | Split into sub-routes |
| `packages/mekong-engine/src/routes/chat.ts` | 285 | Extract message handling |
| `packages/mekong-engine/src/routes/matching.ts` | 274 | Extract matching logic |
| `packages/mekong-engine/src/routes/equity.ts` | 333 | Split equity operations |

### 4. Python Files Over 200 Lines (Outside skills/)

| File | Lines | Issue |
|------|-------|-------|
| `src/commands/lint.py` | 430+ | Single responsibility violation |
| `src/commands/deploy.py` | 320+ | Multiple deployment platforms |
| `src/commands/docs.py` | 420+ | Multiple doc platforms |
| `src/commands/security.py` | 430+ | Multiple security tools |
| `src/commands/monitor.py` | 330+ | Multiple monitoring types |
| `src/core/executor.py` | 480+ | Multiple execution modes |
| `src/core/verifier.py` | 450+ | Multiple verification types |
| `src/core/browser_agent.py` | 350+ | Multiple browser operations |
| `src/core/machine_fingerprint.py` | 460+ | Multiple fingerprint methods |
| `src/core/auto_recovery.py` | 650+ | CRITICAL — needs refactoring |
| `src/raas/final_phase_validator.py` | 290+ | Multiple validation phases |

---

## MEDIUM Priority Issues

### 1. Missing Type Hints on Functions

**Pattern:** Functions without return type annotations

```python
# src/core/world_model.py:392
def _run_cmd(self, cmd: str) -> str:  # ✅ Has type hints
    ...

# src/core/autonomous.py (many functions)
def some_function(param):  # ❌ Missing type hints
    ...
```

### 2. Missing Docstrings on Public Methods

**Files with incomplete docstrings:**

| File | Missing Docstrings |
|------|-------------------|
| `src/core/autonomous.py` | 15+ public methods |
| `src/core/orchestrator.py` | 10+ public methods |
| `src/lib/raas_gate.py` | 20+ middleware functions |

### 3. Inconsistent Logging

**Pattern:** Mix of `print()`, `logger.debug()`, and Rich console

```python
# src/core/executor.py
print("Running command...")  # ❌ Should use logger

# src/commands/deploy.py
console.print("[green]Deployed![/green]")  # ✅ Rich console OK for CLI
```

### 4. Console.log in TypeScript Production Code

**48 files with `console.log/error/warn` statements:**

| File | Count | Type |
|------|-------|------|
| `packages/mekong-cli-core/src/cli/commands/billing.ts` | 20+ | Debug logging |
| `packages/mekong-cli-core/src/cli/commands/crm.ts` | 5+ | Debug logging |
| `packages/mekong-cli-core/src/cli/commands/license-admin.ts` | 25+ | Debug logging |
| `packages/observability/src/logger.ts` | 3 | Intentional (logger) |

**Recommendation:** Replace with proper logger in production code, keep only in CLI commands.

---

## LOW Priority Issues

### 1. TODO/FIXME Comments (59 occurrences)

**Notable items:**

| File | Comment | Line |
|------|---------|------|
| `src/core/verifier.py` | `# TODO: Add retry logic` | Multiple |
| `src/core/code_evolution.py` | `# FIXME: Handle edge cases` | Multiple |
| `packages/mekong-engine/src/lib/route-utils.ts` | `// TODO: Add caching` | 2 |
| `components/robot-interface/v2.1.79/hooks/useRobotStatus.ts` | `// TODO: Add reconnection` | 2 |

### 2. Test Coverage Gaps

**Pytest collected 3649 items but 24 errors during collection.**

```bash
collecting ... collected 3649 items / 24 errors
```

**Recommendation:** Fix collection errors to ensure full test coverage.

---

## Scout Findings — Edge Cases Not in Diff

### 1. Async Race Conditions

**File:** `src/core/cc_spawner.py:162-165`
```python
process = await asyncio.create_subprocess_exec(
    cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
)
# No timeout handling, no process cleanup on cancellation
```

**Risk:** Process leak if task cancelled mid-execution.

### 2. State Mutation in WorldModel

**File:** `src/core/world_model.py:157-159`
```python
self._snapshots.append(state)
if len(self._snapshots) > 20:
    self._snapshots = self._snapshots[-20:]  # Creates new list, but state objects are mutable
```

**Risk:** Old snapshot states could be modified externally, affecting diff calculations.

### 3. Database Transaction Boundaries

**File:** `packages/mekong-engine/src/routes/ledger.ts` (258 lines)
- Multiple DB operations without explicit transaction wrapping
- Risk of partial writes on failure

### 4. Rate Limiter Edge Cases

**File:** `src/lib/tier_rate_limit_middleware.py:111`
```python
except Exception:
    # Silent failure — rate limiter fails open
```

**Risk:** DDoS vulnerability if rate limiter fails.

---

## Recommended Actions (Prioritized)

### Phase 1: Critical Security (Week 1)

1. **Replace all `shell=True` with `shlex.split()` + list commands**
   - Target files: `world_model.py`, `tool_registry.py`
   - Add security test suite

2. **Remove fallback secrets from code**
   - `session_manager.py:22` — require env var
   - Add startup validation for required secrets

3. **Add code validation to Evolution Engine**
   - Syntax check via `ast.parse()`
   - Import verification
   - Signature validation

4. **Fix WorldModel env var masking**
   - Exclude sensitive vars entirely, don't just mask

### Phase 2: Type Safety (Week 2-3)

1. **Replace all `any` types in TypeScript**
   - Start with `packages/mekong-engine/src/types/error.ts`
   - Add Hono Context types

2. **Add strict mode to `tsconfig.json`**
   - Enable `strictNullChecks`, `noImplicitAny`

3. **Fix broad exception handlers**
   - Start with `autonomous.py`, `orchestrator.py`, `raas_gate.py`
   - Add logging before re-raise

### Phase 3: Code Organization (Week 4)

1. **Split files > 200 lines**
   - Priority: `auto_recovery.py` (650 lines), `executor.py`, `verifier.py`
   - Extract by responsibility

2. **Add missing docstrings**
   - Focus on public APIs first

3. **Standardize logging**
   - Replace `print()` with `logger`
   - Configure structured logging

---

## Metrics Summary

| Metric | Current | Target |
|--------|---------|--------|
| Type Coverage (TS) | ~70% | 100% |
| Test Coverage | Unknown (24 collection errors) | >80% |
| Files >200 lines | 20+ | 0 |
| `any` type usages | 146 | 0 |
| Broad `except Exception:` | 100+ | 0 |
| `shell=True` usage | 4 critical | 0 |
| TODO/FIXME comments | 59 | 0 |
| Console.log in prod | 48 files | 0 |

---

## Unresolved Questions

1. **Backward compatibility:** Are there external consumers of these packages that would break with strict type changes?

2. **Test strategy:** What's the plan for fixing 24 pytest collection errors before running full coverage?

3. **Secret rotation:** Is there a secret rotation policy for the hardcoded fallback secrets?

4. **Evolution Engine:** Should self-modifying code be disabled in production until validation is added?

5. **Rate limiter:** Should rate limiter fail closed (block all) or open (allow all) when it errors?

---

**Next Steps:** Delegate to `code-reviewer` agent to create implementation plan for Phase 1 security fixes.
