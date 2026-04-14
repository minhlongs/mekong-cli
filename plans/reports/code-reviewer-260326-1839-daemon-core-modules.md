# Code Review: Daemon Core Modules

**Date:** 2026-03-26 | **Score: 7/10** | **Verdict: COMMENT (approve with notes)**

## Scope

- Files: 5 (`llm_config.py`, `agent_loop.py`, `mission_dispatch.py`, `pipeline_executor.py`, `__main__.py`)
- LOC: ~410
- Focus: Security, error handling, code quality, edge cases

## Overall Assessment

Code is well-structured with good sandbox protections and clean separation of concerns. Two security issues found (SSRF, file handle leak), plus config duplication and a tier mismatch bug. No critical blockers.

---

## Critical Issues

### 1. SSRF via `http_get` tool (agent_loop.py:117-123)

The `http_get` tool only checks `url.startswith("http")` -- this allows the LLM to request internal network resources (metadata endpoints, localhost services, internal IPs).

```python
# Current — allows http://169.254.169.254/metadata, http://localhost:5432, etc.
if not url.startswith("http"):
    return "Error: URL must start with http"
```

**Impact:** LLM-directed SSRF. The agent loop gives tool-calling LLMs an unrestricted HTTP client. A jailbroken or confused model could probe internal services.

**Fix:** Add allowlist or block private IP ranges:
```python
from urllib.parse import urlparse
import ipaddress

def _is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
        return False
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_global
    except ValueError:
        return True  # domain name, allow
```

### 2. Sentry DSN exposed in source code (__main__.py:7)

```python
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN", ""), ...)
```

Currently safe (empty default), but `__main__.py` lives in `src/daemon/` which is in the `.gitignore`-equivalent block per CLAUDE.md. Verify this file is NOT tracked in git.

---

## High Priority

### 3. Config duplication: LLM endpoints defined twice

`llm_config.py` and `agent_loop.py` both define the same model URLs, IDs, and timeouts independently:

- `llm_config.py:45-47` — `M1_MAX_HOST`, `DEEPSEEK_BASE_URL`, `NEMOTRON_BASE_URL`
- `agent_loop.py:37-50` — `TIER_CONFIG` with hardcoded `192.168.11.111`

**Impact:** Config drift. Changing the host in one file but not the other causes silent routing failures.

**Fix:** `agent_loop.py` should import from `llm_config.py`:
```python
from .llm_config import FAST_MODEL, DEEP_MODEL
TIER_CONFIG = {
    "fast": {"url": FAST_MODEL.base_url, "model": FAST_MODEL.model_id, ...},
    "deep": {"url": DEEP_MODEL.base_url, "model": DEEP_MODEL.model_id, ...},
}
```

### 4. Tier mismatch bug (mission_dispatch.py:123)

```python
tier = "coding" if task.capability in {"builder", "reviewer"} else "fast"
```

But `TIER_CONFIG` in `agent_loop.py` only has keys `"fast"` and `"deep"` -- there is no `"coding"` tier. This falls through to `TIER_CONFIG.get("coding", TIER_CONFIG["fast"])` silently using the fast model for builder/reviewer tasks that should use the deep model.

**Impact:** Builder and reviewer tasks silently run on the wrong (fast) model.

**Fix:** Change to `"deep"`:
```python
tier = "deep" if task.capability in {"builder", "reviewer"} else "fast"
```

### 5. File handle leak (pipeline_executor.py:94)

```python
log_path.open("a").write(entry)
```

File handle opened but never closed. Will leak under repeated pipeline runs.

**Fix:**
```python
with log_path.open("a") as f:
    f.write(entry)
```

---

## Medium Priority

### 6. `append_log` incomplete path traversal protection (agent_loop.py:134)

```python
fname = args["filename"].replace("/", "_").replace("..", "")
```

This strips `..` but not `.` or other bypass patterns. The `_safe_path` function used by other tools provides proper protection, but `append_log` uses a custom sanitizer.

**Fix:** Use `_safe_path` consistently:
```python
log_path = _safe_path(f"logs/{args['filename']}")
```

### 7. Journal race condition (mission_dispatch.py:72-85)

`_update_journal` reads, modifies, and writes JSON without any locking. If two dispatches run concurrently (possible from pipeline_executor), one write clobbers the other.

**Impact:** Lost journal entries under concurrent dispatch.

**Fix:** Use `fcntl.flock` or atomic write (write to temp, rename).

### 8. `asyncio.get_event_loop()` deprecated pattern (agent_loop.py:226)

```python
loop = asyncio.get_event_loop()
return await loop.run_in_executor(None, lambda: run_agent_sync(task, **kwargs))
```

`get_event_loop()` is deprecated since Python 3.10+. Use `asyncio.get_running_loop()` instead.

### 9. Broad exception catching (agent_loop.py:194)

```python
except (URLError, Exception) as e:
```

`Exception` is a superclass of `URLError`, making the tuple redundant. This catches everything silently. Should at least differentiate network errors from parse errors.

---

## Low Priority

### 10. `FALLBACK_MODEL` == `FAST_MODEL` may surprise (llm_config.py:72)

Fallback is the fast (lightweight) model. If deep model fails, fallback to a less capable model may produce low-quality results silently. Consider logging when fallback activates.

### 11. Unused imports: `Any` in mission_dispatch.py

`Any` from typing is used only for the `item` parameter type hint which could be the actual `QueueItem` type instead.

### 12. Magic number `4000` for truncation (agent_loop.py:109,123)

Both `read_file` and `http_get` truncate at 4000 chars. Extract to a named constant.

---

## Positive Observations

- Sandbox path traversal protection (`_safe_path`) is correctly implemented with `.resolve()` check
- Clean dataclass design for `ModelConfig` with computed properties
- Good separation: config / routing / execution / dispatch layers
- Cron parser handles step/range/list syntax well
- Lazy imports avoid circular dependencies
- Proper `__all__` exports in config module

---

## Recommended Actions (priority order)

1. **Fix tier mismatch** `"coding"` -> `"deep"` in mission_dispatch.py (bug)
2. **Add SSRF protection** to `http_get` tool (security)
3. **Fix file handle leak** in pipeline_executor.py (resource leak)
4. **Consolidate config** -- agent_loop.py should import from llm_config.py (DRY)
5. **Use `_safe_path`** for `append_log` tool (consistency)
6. **Add journal file locking** or atomic writes (concurrency)

---

## Metrics

| Metric | Value |
|--------|-------|
| Type Coverage | ~85% (good use of type hints, some `Any` remains) |
| Test Coverage | Unknown (no tests found for daemon modules) |
| Linting Issues | 2 (deprecated asyncio API, redundant except) |
| Security Issues | 2 (SSRF, inconsistent path sanitization) |
| Bugs | 1 (tier mismatch: "coding" key does not exist) |

## Unresolved Questions

1. Is `src/daemon/` excluded from git tracking? CLAUDE.md says it should be, but no `.gitignore` was checked.
2. Are there tests for the daemon modules? None found in scope.
3. Is concurrent dispatch possible? If yes, journal locking is required.
