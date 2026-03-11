# Developer Onboarding Guide — Mekong CLI

**Date:** 2026-03-11
**Audience:** New engineers joining the project

---

## 1. What Is Mekong CLI

Mekong CLI is an AI-operated business platform — a Python CLI that takes natural language goals and executes them via a Plan-Execute-Verify (PEV) engine. It routes tasks through LLM providers, shell commands, web browsing, and specialized agents.

Core idea: `mekong cook "create a sales email sequence"` → LLM decomposes → executes → verifies.

**Version:** v0.2.0 | **Language:** Python 3.9+ | **License:** MIT

---

## 2. Prerequisites

```bash
# Required
python3 --version     # 3.9+ required, 3.12 used in CI
git --version
node --version        # 20+ for CF Worker development

# Optional but useful
wrangler --version    # For Cloudflare Worker dev
gh --version          # GitHub CLI for PR/Actions management
```

---

## 3. Local Setup

```bash
# 1. Clone
git clone https://github.com/org/mekong-cli.git
cd mekong-cli

# 2. Python environment (use venv, not global pip)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -e .             # installs mekong CLI in editable mode

# 4. Verify CLI entry point
mekong --help

# 5. Configure LLM (pick one)
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4

# 6. Run tests to confirm setup
python3 -m pytest tests/test_planner.py tests/test_executor.py tests/test_verifier.py -q
# Expected: 118 passed
```

---

## 4. Project Layout

```
mekong-cli/
├── src/
│   ├── core/           # PEV engine — START HERE
│   │   ├── planner.py      # Decomposes goals → Recipe (DAG of steps)
│   │   ├── executor.py     # Executes steps (shell/llm/api/tool/browse)
│   │   ├── verifier.py     # Validates execution results
│   │   ├── orchestrator.py # Coordinates Plan→Execute→Verify
│   │   ├── agent_base.py   # Abstract base for all agents
│   │   ├── llm_client.py   # Universal LLM router (9-tier fallback)
│   │   └── dag_scheduler.py# Parallel step execution via DAG
│   ├── agents/         # Specialized task agents
│   │   ├── git_agent.py
│   │   ├── shell_agent.py
│   │   ├── lead_hunter.py
│   │   └── ...
│   ├── commands/       # Typer CLI command groups
│   ├── cli/            # CLI entry points
│   ├── lib/            # RaaS billing, rate limiting, quotas
│   ├── security/       # CommandSanitizer, attestation
│   └── main.py         # CLI root
├── apps/
│   └── raas-gateway/   # Cloudflare Worker edge proxy
├── tests/              # 3638 tests
├── .github/workflows/  # CI/CD pipelines
├── requirements.txt
└── pyproject.toml
```

---

## 5. Core Concepts

### Plan-Execute-Verify (PEV)

Every task goes through three phases:

```
1. PLAN   — RecipePlanner.plan(goal) → Recipe (list of RecipeSteps)
2. EXECUTE — RecipeExecutor.execute_step(step) → ExecutionResult
3. VERIFY  — RecipeVerifier.verify(result, criteria) → VerificationReport
```

The `RecipeOrchestrator` coordinates all three. Start reading `src/core/orchestrator.py` → `run_from_goal()`.

### Recipe

A `Recipe` is a DAG of `RecipeStep` objects. Each step has:
- `order` — execution sequence number
- `title` / `description` — what to do
- `agent` — optional agent name to handle this step
- `params` — dict with `type` (shell/llm/api/tool/browse), `dependencies`, `verification`

### Step Types

| Type | Handler | Used For |
|------|---------|----------|
| `shell` | `subprocess.run()` | CLI commands, scripts |
| `llm` | LLMClient.chat() | Text generation, analysis |
| `api` | requests.request() | External API calls |
| `tool` | ToolRegistry.execute() | Named tool invocations |
| `browse` | BrowserAgent | Web page analysis |

### LLM Client

`src/core/llm_client.py` — set 3 env vars and it works with any provider:
```bash
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-v1-...
LLM_MODEL=anthropic/claude-sonnet-4
```

Falls back through 9 providers automatically. Offline mode works without any key.

---

## 6. Running Tests

```bash
# Core PEV tests (fast, 6s)
python3 -m pytest tests/test_planner.py tests/test_executor.py \
  tests/test_verifier.py tests/test_orchestrator_integration.py -q

# Full test suite (CI scope, ~30s)
python3 -m pytest tests/ \
  --ignore=tests/backend --ignore=tests/e2e \
  --ignore=tests/integration --ignore=tests/unit \
  --ignore=tests/benchmarks -q

# Single test file
python3 -m pytest tests/test_planner.py -v

# With coverage
python3 -m pytest tests/test_planner.py --cov=src/core/planner --cov-report=term-missing
```

---

## 7. Writing a New Agent

1. Create `src/agents/my_agent.py`
2. Inherit `AgentBase`, implement `plan()` and `execute()`:

```python
from src.core.agent_base import AgentBase, Task, Result

class MyAgent(AgentBase):
    def __init__(self):
        super().__init__(name="my_agent")

    def plan(self, input_data: str) -> list[Task]:
        return [Task(id="t1", description=input_data, input={"goal": input_data})]

    def execute(self, task: Task) -> Result:
        # do work
        return Result(task_id=task.id, success=True, output="done")
```

3. Register in `src/agents/__init__.py`:

```python
from .my_agent import MyAgent
AGENT_REGISTRY["my_agent"] = MyAgent
```

4. Add keyword mapping in `src/core/planner.py` `AGENT_KEYWORDS`:

```python
"my_agent": ["keyword1", "keyword2"],
```

5. Write tests in `tests/test_my_agent.py`

---

## 8. Linting & Formatting

```bash
# Check lint (must pass before commit)
ruff check src/ tests/

# Auto-fix safe issues
ruff check src/ tests/ --fix

# Format check
ruff format --check src/ tests/

# Auto-format
ruff format src/ tests/

# Compile check (catch import errors)
python3 -m py_compile src/core/planner.py
```

---

## 9. Common Gotchas

| Gotcha | Fix |
|--------|-----|
| `python` not found | Use `python3` on macOS |
| `mekong: command not found` | Run `pip install -e .` first |
| `LLM offline` warnings | Set `LLM_API_KEY` env var or use offline mode |
| Tests slow (~30s) | Add `--ignore=tests/benchmarks` to skip file_stats scan |
| `pytest-timeout` not found | Do not use `--timeout` flag — plugin not installed |
| Import errors in tests | Set `PYTHONPATH=/Users/macbookprom1/mekong-cli` |

---

## 10. First Tasks for New Engineers

**Junior level:**
1. Add a keyword to `AGENT_KEYWORDS` in planner.py and write a test
2. Add a new verification check method to `RecipeVerifier`
3. Write tests for an untested agent in `src/agents/`

**Mid level:**
1. Fix `StepExecutor.console` bug (see refactor-plan.md SEC-01)
2. Wire LLM client into `ocop_commands.py` TODO stubs
3. Add URL validation to `_execute_api_step` (see security-audit.md SEC-02)

**Senior level:**
1. Split `orchestrator.py` into focused modules (see refactor-plan.md)
2. Add OpenAPI spec for gateway `/v1/*` endpoints
3. Implement strategy pattern for `_rule_based_decompose`

---

## 11. Key Files to Read First

Order for understanding the codebase:

1. `src/core/agent_base.py` — 165 lines, understand PEV pattern
2. `src/core/verifier.py` — 483 lines, understand verification
3. `src/core/planner.py` — 659 lines, understand decomposition
4. `src/core/executor.py` — 489 lines, understand execution modes
5. `src/core/orchestrator.py` — 1048 lines, understand full workflow
6. `apps/raas-gateway/index.js` — edge proxy architecture
