# Good First Issues — March 2026
**Generated:** 2026-03-12 | **Total:** 15 issues | **Labels:** easy / medium / hard

---

## Overview

These 15 issues are curated starting points for new contributors. Each includes
a difficulty rating, estimated time, required skills, and exact files to touch.
All are real improvements — no manufactured busy-work.

Apply the label `good first issue` + difficulty label on GitHub before posting.

---

## EASY (1–3 hours, minimal Python required)

### Issue 1: Add missing docstrings to agent files
**Label:** `good first issue`, `easy`, `documentation`
**Estimated time:** 1–2 hours
**Files:** `src/agents/*.py`
**Description:**
Several agent classes are missing class-level and method-level docstrings.
Add Google-style docstrings to all public methods in `src/agents/git_agent.py`,
`src/agents/file_agent.py`, and `src/agents/shell_agent.py`.

**Acceptance criteria:**
- All public methods have docstrings with Args, Returns, Raises sections
- `python3 -m pydocstyle src/agents/` shows no errors
- Existing tests still pass

---

### Issue 2: Improve CLI help text for `mekong cook` command
**Label:** `good first issue`, `easy`, `ux`
**Estimated time:** 1 hour
**Files:** `src/main.py`
**Description:**
The `cook` command help text is minimal. Expand it with examples, option descriptions,
and a link to documentation. Use Typer's `help=` parameter and Rich markup.

**Acceptance criteria:**
- `mekong cook --help` shows 3 usage examples
- Each option has a descriptive help string
- No existing tests broken

---

### Issue 3: Add `.env.example` file
**Label:** `good first issue`, `easy`, `developer-experience`
**Estimated time:** 30 minutes
**Files:** `.env.example` (new file)
**Description:**
New contributors don't know which environment variables to set. Create `.env.example`
with all required and optional vars, with inline comments explaining each.

**Acceptance criteria:**
- `.env.example` covers all vars used in `src/core/llm_client.py`
- Comments explain what each var does and where to get the value
- `.env.example` is committed; `.env` remains in `.gitignore`

---

### Issue 4: Add Python version badge to README
**Label:** `good first issue`, `easy`, `documentation`
**Estimated time:** 30 minutes
**Files:** `README.md`
**Description:**
Add shields.io badges to README: Python version, MIT license, CI status, PyPI version.
Improves credibility and first impressions on GitHub.

**Acceptance criteria:**
- 4 badges visible at top of README
- All badges link to relevant pages
- Badges use flat-square style for consistency

---

### Issue 5: Fix inconsistent error messages in exceptions.py
**Label:** `good first issue`, `easy`, `polish`
**Estimated time:** 1 hour
**Files:** `src/core/exceptions.py`, `tests/test_exceptions.py`
**Description:**
Error messages in `MekongError` subclasses use inconsistent capitalization and
punctuation. Standardize: sentence case, period at end, include context variables.

**Acceptance criteria:**
- All error messages follow: `"[Component]: [Description]. [Hint]."` format
- Tests updated to match new messages
- No functional changes to exception behavior

---

## MEDIUM (3–8 hours, Python required)

### Issue 6: Add `--json` output flag to `mekong list` command
**Label:** `good first issue`, `medium`, `feature`
**Estimated time:** 3–4 hours
**Files:** `src/main.py`, `tests/test_main.py`
**Description:**
`mekong list` outputs Rich-formatted tables. Add `--json` flag for machine-readable
output. Useful for CI/CD integration and scripting.

**Acceptance criteria:**
- `mekong list --json` outputs valid JSON array
- `mekong list --json | jq '.[0]'` works correctly
- Default behavior (Rich table) unchanged
- Unit tests for both output modes

---

### Issue 7: Implement retry logic in LLM client
**Label:** `good first issue`, `medium`, `reliability`
**Estimated time:** 4–5 hours
**Files:** `src/core/llm_client.py`, `tests/test_llm_client.py`
**Description:**
`llm_client.py` has no retry logic. Add exponential backoff retry for transient
errors (HTTP 429, 503, network timeouts). Max 3 retries, 2s initial delay.

**Acceptance criteria:**
- Retries on HTTP 429, 503, `httpx.TimeoutException`
- No retry on HTTP 400, 401, 404 (client errors)
- Configurable via `LLM_MAX_RETRIES` env var
- Unit tests mock `httpx` and verify retry behavior
- Logs retry attempts with Rich warning output

---

### Issue 8: Add `mekong version --check` to compare with latest PyPI release
**Label:** `good first issue`, `medium`, `feature`
**Estimated time:** 3 hours
**Files:** `src/main.py`, `tests/test_version.py`
**Description:**
Add `--check` flag to `mekong version` that fetches latest version from PyPI and
notifies user if an update is available. Non-blocking — fails gracefully if offline.

**Acceptance criteria:**
- `mekong version --check` prints current vs latest version
- Fails gracefully (no crash) when PyPI unreachable
- Caches PyPI response for 24h (no repeated network calls)
- Unit tests mock `httpx.get` for PyPI endpoint

---

### Issue 9: Add shell completion support (bash, zsh, fish)
**Label:** `good first issue`, `medium`, `developer-experience`
**Estimated time:** 4 hours
**Files:** `src/main.py`, `docs/install.md`
**Description:**
Typer supports shell completion out of the box. Enable and document it.
Add `mekong --install-completion` and `mekong --show-completion` commands.

**Acceptance criteria:**
- `mekong --install-completion bash` works on macOS/Linux
- `mekong --install-completion zsh` works on macOS
- Tab completion works for all top-level commands
- Installation documented in README and docs/install.md

---

### Issue 10: Add structured logging to orchestrator
**Label:** `good first issue`, `medium`, `observability`
**Estimated time:** 5 hours
**Files:** `src/core/orchestrator.py`, `src/core/executor.py`
**Description:**
Add JSON-structured logging throughout the PEV engine. Each step should log:
timestamp, step_id, action type, duration_ms, success/failure. Log level controlled
by `MEKONG_LOG_LEVEL` env var.

**Acceptance criteria:**
- Structured JSON log output when `MEKONG_LOG_LEVEL=DEBUG`
- Default: Rich human-readable output unchanged
- Each log entry includes: timestamp, component, level, message, context dict
- Unit tests verify log structure

---

### Issue 11: Add `mekong search` fuzzy matching
**Label:** `good first issue`, `medium`, `ux`
**Estimated time:** 4 hours
**Files:** `src/main.py`, `tests/test_search.py`
**Description:**
`mekong search` currently requires exact substring match. Add fuzzy matching using
`difflib.get_close_matches` so typos return relevant results.

**Acceptance criteria:**
- `mekong search cooK` finds `cook` command (case-insensitive)
- `mekong search reveiw` finds `review` (typo correction)
- Fuzzy results shown with match score in parentheses
- Exact matches ranked above fuzzy matches

---

## HARD (8+ hours, deep codebase knowledge required)

### Issue 12: Implement agent result caching with TTL
**Label:** `good first issue`, `hard`, `performance`
**Estimated time:** 8–12 hours
**Files:** `src/core/orchestrator.py`, `src/core/cache.py` (new), `tests/test_cache.py`
**Description:**
Repeated identical tasks call LLM every time. Implement a result cache with
configurable TTL. Cache key: hash of task string + agent type + LLM model.
Storage: local file cache (`~/.mekong/cache/`) for CLI, CF KV for Workers.

**Acceptance criteria:**
- Cache hit serves result without LLM call
- `MEKONG_CACHE_TTL=3600` configures TTL in seconds
- `MEKONG_CACHE_DISABLE=1` bypasses cache
- Cache keys are deterministic and collision-resistant (SHA-256)
- Cache file format is JSON for human inspection
- Unit tests verify cache hit/miss/expiry behavior

---

### Issue 13: Add parallel step execution to orchestrator
**Label:** `good first issue`, `hard`, `performance`
**Estimated time:** 10–15 hours
**Files:** `src/core/orchestrator.py`, `src/core/executor.py`, `tests/test_parallel.py`
**Description:**
Orchestrator currently executes steps sequentially. Add dependency graph analysis
and parallel execution for independent steps using `asyncio.gather`.

**Acceptance criteria:**
- Planner annotates steps with `depends_on: [step_id]`
- Independent steps execute in parallel
- Dependent steps wait for their dependencies
- `--no-parallel` flag forces sequential (debugging)
- Wall clock time improvement measurable in integration test
- Rollback still works correctly for parallel failures

---

### Issue 14: Build web dashboard for task history (CF Pages)
**Label:** `good first issue`, `hard`, `feature`
**Estimated time:** 12–16 hours
**Files:** `apps/dashboard/` (new), `mekong/infra/`
**Description:**
Build a minimal Cloudflare Pages dashboard showing task execution history stored
in D1. Stack: vanilla HTML/CSS/JS (no framework), Cloudflare Pages Functions for
API. Display: list of recent tasks, status, duration, MCU credits consumed.

**Acceptance criteria:**
- Deployed to CF Pages via `wrangler pages deploy`
- Shows last 50 task executions from D1
- Filters by: status (success/fail), date range, agent type
- Mobile-responsive (works on iPhone)
- Auth: Bearer token in localStorage (simple, sufficient for MVP)

---

### Issue 15: Implement WebSocket streaming for long-running tasks
**Label:** `good first issue`, `hard`, `feature`
**Estimated time:** 15–20 hours
**Files:** `src/api/stream.py` (new), `src/core/executor.py`, `tests/test_stream.py`
**Description:**
Long-running tasks (cook, plan) block until complete. Add WebSocket endpoint
`/v1/missions/stream` that emits step-by-step progress as tasks execute.
Client receives events: `{type: "step_start" | "step_complete" | "task_done", data: {...}}`.

**Acceptance criteria:**
- `wss://api/v1/missions/stream` accepts WebSocket connections
- Events emitted in real-time as each step completes
- Connection authenticated via MCU bearer token
- Graceful reconnection handling (resume from last event_id)
- Integration test using `websockets` library
- CF Workers Durable Objects for connection state (if needed)

---

## Issue Management Guidelines

| Label          | Meaning                                   |
|----------------|-------------------------------------------|
| `good first issue` | Suitable for new contributors        |
| `easy`         | < 3 hours, no deep codebase knowledge     |
| `medium`       | 3–8 hours, moderate Python required       |
| `hard`         | 8+ hours, deep knowledge required         |
| `help wanted`  | Maintainer needs community input          |
| `documentation`| Docs-only, no code required               |
| `feature`      | New functionality                         |
| `polish`       | UX/DX improvement, no new features        |
| `reliability`  | Error handling, retry, robustness         |
| `performance`  | Speed, caching, parallelism               |

---

*Post these issues to GitHub with full descriptions before community launch.*
*Next refresh: Add 5 new issues after each feature release.*
