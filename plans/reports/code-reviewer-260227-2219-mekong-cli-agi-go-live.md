# Code Review: Mekong CLI AGI Go Live

**Reviewer:** code-reviewer | **Date:** 2026-02-27 22:19
**Scope:** AGI Go Live plan — pyproject, gateway, CLI commands, CI/CD, Docker, docs
**Rating: 8/10**

---

## Critical Issues

### 1. HARDCODED API KEY COMMITTED TO GIT (CRITICAL / SECURITY)
**File:** `/Users/macbookprom1/mekong-cli/scripts/qwen_bridge.py` line 30
```python
_HARDCODED_KEYS = [
    "sk-4d2965a589ca4d9da2ea05e4bd200d97",  # minhlong.rice@gmail.com
]
```
This Dashscope API key is committed in `6789e64e`. Even if described as "expired", it was previously valid and is now in git history. **Must rotate immediately.** Also, `.ag_proxies/` directory with account emails is committed and NOT in `.gitignore`.

**Fix:** Add `.ag_proxies/` to `.gitignore`. Remove hardcoded key fallback; fail explicitly if env vars missing. Consider `git filter-branch` or BFG to scrub history before open-sourcing.

### 2. AGI PROXY ENDPOINTS UNAUTHENTICATED (HIGH / SECURITY)
**File:** `/Users/macbookprom1/mekong-cli/src/core/gateway.py` lines 714-731
```python
@gateway.get("/api/agi/health")
@gateway.get("/api/agi/metrics")
```
These endpoints proxy to local daemon port 9090 with no auth check. The `/cmd` endpoint requires `MEKONG_API_TOKEN`, but `/api/agi/*` does not. If gateway is exposed to network, anyone can query AGI metrics (mission history, scores).

**Fix:** Add same token check as `/cmd` or rate-limit, or restrict to localhost via middleware.

---

## High Priority

### 3. gateway.py exceeds 200 LOC limit (772 lines)
Per development rules, files should be under 200 lines. This file is ~4x the limit and growing with each feature addition (AGI proxy was just appended). Extract route groups into separate modules (e.g., `routes/agi.py`, `routes/swarm.py`).

### 4. Broad `except Exception` in gateway AGI endpoints
```python
except Exception:
    return {"error": "AGI daemon not reachable", "status": "offline"}
```
Catches all exceptions silently (including JSON decode errors, unexpected httpx errors). Should catch `(httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError)` specifically and log unexpected errors.

### 5. `ruff check || true` in CI (test.yml line 22)
Lint step always passes (`|| true`). This means lint regressions will never block CI. Either remove the `|| true` or use `ruff check --select E,F` for critical-only enforcement.

---

## Medium Priority

### 6. `agi_bridge.py` uses synchronous `httpx.get()` in `is_running()`/`status()`/`metrics()`
While acceptable for CLI usage, the `AGIBridge` class uses sync httpx in methods that are called from Typer CLI. This is fine today but will cause issues if reused from async contexts (like gateway). Consider making a note or providing async variants.

### 7. `agi.py` stop() command only stops self-spawned process
`bridge.stop()` only terminates the `_process` attribute, which is only set if the Python CLI started the daemon. If daemon was started via `npm run start` or `node task-watcher.js` directly, `stop()` does nothing useful. Consider adding a `/shutdown` HTTP call or process lookup by name.

### 8. PyPI publish workflow lacks build verification
`publish-pypi.yml` runs `poetry build` then `poetry publish` but does not run tests first. If a broken release tag is created, it publishes to PyPI without validation.

---

## Positive Observations

- **Clean architecture**: `AGIBridge` class with clear separation of concerns (125 LOC, well-typed)
- **No secrets in new code**: New files (`agi_bridge.py`, `agi.py`, `commands/__init__.py`) are clean
- **Dockerfile is minimal**: Multi-stage build, only 15 lines, production-ready
- **PayPal references properly removed** from `deploy.yml` and `.env.example`
- **Smoke test added** to deploy.yml with proper retry loop
- **httpx version range** properly pinned (`>=0.26.0,<0.28.0`)
- **399 tests passing**, zero failures
- **Port 9191 documented consistently** across CLAUDE.md and `.env.example`

---

## Summary

| Area | Status |
|------|--------|
| Security | 1 CRITICAL (hardcoded key in git), 1 HIGH (unauth endpoints) |
| Correctness | All imports valid, syntax clean, tests pass |
| Completeness | AGI bridge, CLI, gateway routes, CI/CD, Docker all present |
| File size | `gateway.py` 772 LOC (violation), rest under 200 LOC |
| Type hints | Present throughout new Python code |
| Docstrings | Present on all public methods |
| Tests | 399 passed / 0 failed |

**Recommended immediate actions:**
1. Add `.ag_proxies/` to `.gitignore` and remove from tracking
2. Remove hardcoded API key from `scripts/qwen_bridge.py`
3. Add auth to `/api/agi/health` and `/api/agi/metrics`
4. Remove `|| true` from ruff lint step in CI

---

## Unresolved Questions

- Is `gateway.py` refactoring into route modules planned for a future phase?
- Should `.ag_proxies/` directory history be scrubbed before open-source release?
- Is the `stop()` command expected to work for externally-spawned daemons?
