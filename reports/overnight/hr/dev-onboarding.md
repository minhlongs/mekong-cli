# Developer Onboarding — March 2026
**Generated:** 2026-03-12 | **Audience:** New engineers joining the team | **Target:** Productive in day 1

---

## Executive Summary

This guide is for engineers hired onto the Mekong CLI core team (not external contributors —
see `hr/onboard.md` for contributor guide). You will understand the 5-layer architecture,
key source files, coding standards, and testing protocol by end of day 1.

---

## Day 1 Checklist

- [ ] Dev environment running (all 62 tests pass)
- [ ] Read this entire document
- [ ] Read `docs/system-architecture.md`
- [ ] Read `docs/code-standards.md`
- [ ] Shadowed founder on one `mekong cook` session
- [ ] Submitted first PR (even documentation fix counts)
- [ ] Access to: GitHub repo, Discord (admin), Cloudflare dashboard, Polar.sh dashboard

---

## Architecture Overview: 5 Layers

Mekong CLI v5.0 operates across 5 strategic layers mapped to business functions:

```
Layer 1 — Founder     (Commands: annual, okr, swot, fundraise, pitch)
Layer 2 — Business    (Commands: sales, marketing, finance, hr, pricing)
Layer 3 — Product     (Commands: plan, sprint, roadmap, brainstorm, scope)
Layer 4 — Engineer    (Commands: cook, fix, code, test, deploy, review)
Layer 5 — Ops         (Commands: audit, health, security, status, clean)
```

Each layer maps commands to agent workflows. A command like `mekong cook "build login page"`
flows through the full stack:

```
CLI (src/main.py)
  → Orchestrator (src/core/orchestrator.py)
    → Planner (src/core/planner.py)       — LLM decomposes task
    → Executor (src/core/executor.py)      — Runs each step
    → Verifier (src/core/verifier.py)      — Quality gates
  → Agent (src/agents/*.py)               — Specialized execution
    → LLM Client (src/core/llm_client.py) — Universal router
```

---

## Key Source Files — Read These First

### Core Engine (`src/core/`)

| File              | Purpose                                      | Lines | Read Priority |
|-------------------|----------------------------------------------|-------|---------------|
| `orchestrator.py` | Main PEV loop — entry point for all tasks    | ~180  | 1st           |
| `planner.py`      | LLM-powered task decomposition               | ~150  | 2nd           |
| `executor.py`     | Step execution (shell/LLM/API)               | ~170  | 3rd           |
| `verifier.py`     | Quality gates, rollback logic                | ~120  | 4th           |
| `llm_client.py`   | Universal OpenAI-compatible LLM router       | ~130  | 5th           |
| `agent_base.py`   | Base class all agents inherit from           | ~80   | 6th           |
| `exceptions.py`   | MekongError hierarchy                        | ~60   | 7th           |

### Agents (`src/agents/`)

| File                | Agent        | Capability                         |
|---------------------|--------------|------------------------------------|
| `git_agent.py`      | GitAgent     | git operations, PR creation        |
| `file_agent.py`     | FileAgent    | read/write/transform files         |
| `shell_agent.py`    | ShellAgent   | arbitrary shell command execution  |
| `lead_hunter.py`    | LeadHunter   | sales prospecting via web          |
| `content_writer.py` | ContentWriter| blog posts, docs, copy             |
| `__init__.py`       | Registry     | `AGENT_REGISTRY` dict — lookup map |

### CLI Entry Point (`src/main.py`)

Typer application with commands: `init`, `list`, `search`, `run`, `cook`, `plan`, `ui`, `version`.
Each command ultimately calls `orchestrator.run_task()`.

### API Gateway (`src/api/`)

FastAPI app deployed as Cloudflare Worker:
- `POST /v1/missions` — main task endpoint
- `GET /v1/account/balance` — MCU credit check
- Webhook: `POST /v1/webhooks/polar` — Polar.sh payment events
- HTTP 402 middleware blocks zero-balance requests

---

## Infrastructure: Cloudflare-Only Stack

No traditional servers. Everything runs on Cloudflare:

| Component          | CF Service       | Config File                    |
|--------------------|------------------|--------------------------------|
| Frontend           | Pages            | `wrangler.toml` (pages)        |
| API (Edge)         | Workers          | `wrangler.toml` (worker)       |
| Database           | D1 (SQLite edge) | `src/db/migrations/`           |
| Cache              | KV               | Namespace: `MEKONG_CACHE`      |
| File storage       | R2               | Bucket: `mekong-reports`       |
| Async jobs         | Queues           | Queue: `mekong-tasks`          |

### Local Development

```bash
# Install Wrangler
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Start local dev (simulates D1 + KV + R2 locally)
wrangler dev src/api/index.ts

# Python CLI runs locally against local Workers
LLM_BASE_URL=http://localhost:8787 mekong cook "test task"

# Run D1 migrations locally
wrangler d1 execute mekong-db --local --file=src/db/migrations/001_init.sql
```

---

## LLM Configuration

The LLM router supports any OpenAI-compatible API via 3 environment variables:

```bash
# Primary config (required)
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4

# Fallback chain (auto-detected if LLM_* not set)
OPENROUTER_API_KEY → ANTHROPIC_API_KEY → OPENAI_API_KEY → OLLAMA_BASE_URL

# For local/offline testing
export OLLAMA_BASE_URL=http://localhost:11434
export LLM_MODEL=llama3.2
```

Provider presets in `mekong/adapters/llm-providers.yaml` — copy a preset to `.env`.

---

## Coding Standards (Non-Negotiable)

### Python Style

```python
# snake_case for everything Python
def parse_task_steps(raw_input: str, max_steps: int = 10) -> list[Step]:
    """Parse raw task description into executable steps.

    Args:
        raw_input: The user's natural language task description.
        max_steps: Maximum number of steps to generate. Defaults to 10.

    Returns:
        List of Step objects, ordered by execution dependency.

    Raises:
        MekongParseError: If input cannot be decomposed into valid steps.
    """
    ...
```

### File Size Rule (Hard Limit)

**200 lines maximum per file.** If a file approaches 200 lines:
1. Extract helper functions to `src/core/helpers/[function-name].py`
2. Extract data classes to `src/core/models/[model-name].py`
3. Split agent into base + specialized: `base_agent.py` + `specialized_agent.py`

This is enforced in CI: `wc -l src/**/*.py | awk '$1 > 200'` fails the build.

### File Naming

- Python files: `snake_case.py` (e.g., `llm_client.py`, `git_agent.py`)
- Test files: `test_<module>.py` (e.g., `test_orchestrator.py`)
- Config/data: `kebab-case.yaml` / `kebab-case.json`
- Shell scripts: `kebab-case.sh`
- Markdown: `kebab-case.md`

### Type Hints (Required)

```python
# REQUIRED: All function parameters and return types
def run_task(task: str, agent_type: str, dry_run: bool = False) -> ExecutionResult:
    ...

# REQUIRED: Class attributes
class Step:
    action: str
    params: dict[str, str]
    rollback: dict[str, str] | None = None
```

Run `python3 -m mypy src/ --ignore-missing-imports` — must return 0 errors.

### No Bare Excepts

```python
# BAD
try:
    result = llm_client.complete(prompt)
except:
    pass

# GOOD
try:
    result = llm_client.complete(prompt)
except httpx.TimeoutException as e:
    raise MekongLLMError(f"LLM request timed out: {e}") from e
except httpx.HTTPStatusError as e:
    raise MekongLLMError(f"LLM API error {e.response.status_code}") from e
```

---

## Testing Protocol

### Test Suite Structure

```
tests/
├── test_orchestrator.py   # Integration: full PEV loop
├── test_planner.py        # Unit: step decomposition
├── test_executor.py       # Unit: step execution types
├── test_verifier.py       # Unit: quality gates
├── test_llm_client.py     # Unit: LLM routing, retry
├── test_agents.py         # Unit: each agent type
├── test_main.py           # CLI: Typer command tests
└── conftest.py            # Shared fixtures
```

### Running Tests

```bash
# Full suite (62 tests, ~2.5 min)
python3 -m pytest tests/ -v

# Single module
python3 -m pytest tests/test_orchestrator.py -v

# With coverage
python3 -m pytest tests/ --cov=src --cov-report=term-missing

# Stop on first failure
python3 -m pytest tests/ -x

# Note: DO NOT use --timeout flag (pytest-timeout not installed)
```

### Test Writing Rules

1. One test file per source module
2. Test class per feature area: `class TestPlanner`, `class TestPlannerEdgeCases`
3. Mock LLM calls — never hit real LLM in unit tests
4. Use `pytest.fixture` for shared setup
5. Test names describe behavior: `test_planner_raises_on_empty_input`

```python
# Example test structure
import pytest
from unittest.mock import patch, MagicMock
from src.core.planner import Planner
from src.core.exceptions import MekongParseError

class TestPlanner:
    def test_decomposes_simple_task_into_steps(self):
        with patch("src.core.planner.llm_client.complete") as mock_llm:
            mock_llm.return_value = '[{"action": "shell", "params": {"cmd": "ls"}}]'
            planner = Planner()
            steps = planner.plan("list files")
            assert len(steps) == 1
            assert steps[0].action == "shell"

    def test_raises_on_empty_input(self):
        planner = Planner()
        with pytest.raises(MekongParseError, match="Task input cannot be empty"):
            planner.plan("")
```

---

## Git Workflow

```bash
# Always branch from main
git checkout main && git pull origin main
git checkout -b feat/my-feature-name

# Commit often, conventional format
git commit -m "feat: add retry logic to LLM client"
git commit -m "fix: handle empty task input in planner"
git commit -m "test: add coverage for executor rollback"
git commit -m "docs: update architecture diagram"
git commit -m "refactor: extract step validation to helper"

# Pre-push checklist (automated in CI, but run locally too)
python3 -m pytest tests/           # All tests pass
python3 -m mypy src/               # No type errors
python3 -m flake8 src/             # No lint errors
wc -l src/**/*.py | awk '$1>200'   # No file over 200 lines

# Open PR — squash merge preferred
git push origin feat/my-feature-name
```

### PR Requirements

- Title: Conventional commit format (`feat:`, `fix:`, etc.)
- Description: "Why" not "what" (code shows what, PR shows why)
- Tests: New code requires new tests
- No secrets, no debug prints, no commented-out code
- CI must be green before merge

---

## Secrets Management

**Never commit secrets.** Period.

```bash
# All secrets in .env (gitignored)
LLM_API_KEY=sk-...
CLOUDFLARE_API_TOKEN=...
POLAR_WEBHOOK_SECRET=...

# For CF Workers: use Wrangler secrets
wrangler secret put LLM_API_KEY
wrangler secret put POLAR_WEBHOOK_SECRET

# Pre-commit check (add to .git/hooks/pre-commit)
git diff --cached | grep -E "sk-|Bearer |api_key\s*=" && echo "SECRET DETECTED" && exit 1
```

---

## First Week Plan

| Day | Focus                                         | Deliverable              |
|-----|-----------------------------------------------|--------------------------|
| 1   | Setup, architecture read, shadow session      | Tests passing, first PR  |
| 2   | Deep-dive PEV engine, write 3 unit tests      | PR merged                |
| 3   | Pick one `medium` issue from first-issues.md  | PR open                  |
| 4   | CF Workers local dev setup, API exploration   | Local API running        |
| 5   | First feature PR (from backlog or own idea)   | PR open for review       |

---

## Resources

| Resource                  | Location                                          |
|---------------------------|---------------------------------------------------|
| Architecture docs         | `docs/system-architecture.md`                    |
| Code standards            | `docs/code-standards.md`                         |
| Codebase summary          | `docs/codebase-summary.md`                       |
| Good first issues         | `reports/overnight/hr/first-issues.md`           |
| Contributor guide         | `reports/overnight/hr/onboard.md`                |
| LLM provider presets      | `mekong/adapters/llm-providers.yaml`             |
| CF deploy templates       | `mekong/infra/`                                  |
| CLAUDE.md (AI rules)      | `CLAUDE.md`                                      |

---

*Questions? Slack the founder directly. No question is too small in week 1.*
