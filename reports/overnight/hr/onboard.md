# Contributor Onboarding Guide — March 2026
**Generated:** 2026-03-12 | **Target:** External contributors | **Goal:** First PR in 30 minutes

---

## Executive Summary

Mekong CLI is MIT-licensed and welcomes external contributors. This guide enables
a developer with Python experience to fork the repo, set up their dev environment,
understand the PEV engine, and submit a first PR — all within 30 minutes.

---

## Prerequisites

| Requirement        | Version   | Check Command              |
|--------------------|-----------|----------------------------|
| Python             | 3.9+      | `python3 --version`        |
| Git                | 2.30+     | `git --version`            |
| GitHub account     | —         | github.com                 |
| Terminal (bash/zsh)| —         | macOS/Linux/WSL2           |

Optional but helpful:
- OpenRouter account (for LLM testing): openrouter.ai
- Cloudflare account (for infra testing): cloudflare.com

---

## Step 1: Fork and Clone (5 minutes)

```bash
# 1. Fork via GitHub UI: github.com/[org]/mekong-cli → "Fork"

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/mekong-cli.git
cd mekong-cli

# 3. Add upstream remote
git remote add upstream https://github.com/[org]/mekong-cli.git

# 4. Verify remotes
git remote -v
# origin    https://github.com/YOUR_USERNAME/mekong-cli.git (fetch)
# upstream  https://github.com/[org]/mekong-cli.git (fetch)
```

---

## Step 2: Dev Environment Setup (10 minutes)

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -e ".[dev]"
# Or if no pyproject.toml extras:
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Verify installation
python3 -c "import mekong; print('OK')"
mekong --version  # Should print v5.0.0

# 4. Configure LLM (optional, for integration tests)
cp .env.example .env
# Edit .env:
# LLM_BASE_URL=https://openrouter.ai/api/v1
# LLM_API_KEY=sk-or-v1-yourkey
# LLM_MODEL=anthropic/claude-sonnet-4

# 5. Run test suite to verify setup
python3 -m pytest tests/ -v --tb=short
# Expected: 62 tests, ~2.5 min runtime, all passing
```

---

## Step 3: Understand the Codebase (10 minutes)

### Project Map

```
mekong-cli/
├── src/
│   ├── core/               # PEV Engine (the heart)
│   │   ├── planner.py      # Decomposes tasks into steps
│   │   ├── executor.py     # Runs shell/LLM/API steps
│   │   ├── verifier.py     # Quality gates + rollback
│   │   ├── orchestrator.py # Plan→Execute→Verify loop
│   │   ├── llm_client.py   # Universal LLM router
│   │   ├── agent_base.py   # Base class for all agents
│   │   └── exceptions.py   # MekongError hierarchy
│   ├── agents/             # 14 specialized agents
│   │   ├── __init__.py     # AGENT_REGISTRY dict
│   │   ├── git_agent.py
│   │   ├── file_agent.py
│   │   ├── shell_agent.py
│   │   ├── lead_hunter.py
│   │   └── content_writer.py
│   ├── api/                # FastAPI gateway
│   └── main.py             # Typer CLI entrypoint
├── tests/                  # pytest test suite
├── .claude/
│   ├── skills/             # 241 skill definitions
│   └── commands/           # 261 command definitions
├── factory/
│   └── contracts/          # 388 proprietary recipes (not public)
└── mekong/
    ├── adapters/            # LLM provider configs
    ├── infra/               # Cloudflare deploy templates
    └── daemon/              # Tôm Hùm autonomous dispatch
```

### The PEV Pattern (Core Concept)

Every agent follows Plan → Execute → Verify:

```python
class MyAgent(AgentBase):
    def plan(self, task: str) -> list[Step]:
        # Ask LLM to decompose task into steps
        return steps

    def execute(self, steps: list[Step]) -> ExecutionResult:
        # Run each step (shell, LLM call, API call)
        return result

    def verify(self, result: ExecutionResult) -> bool:
        # Check quality gates, rollback if needed
        return passed
```

### Key Data Types

```python
# ExecutionResult — standard output from executor
@dataclass
class ExecutionResult:
    success: bool
    output: str
    steps_completed: int
    steps_failed: int
    rollback_performed: bool

# Step — single unit of work
@dataclass
class Step:
    action: str        # "shell" | "llm" | "api"
    params: dict       # action-specific parameters
    rollback: dict     # optional undo action
```

---

## Step 4: Make Your First Contribution (5 minutes)

### Good First Issues

Start with issues labeled `good first issue` on GitHub.
See `hr/first-issues.md` for a curated list of 15 starter tasks.

### Workflow

```bash
# 1. Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# 2. Create feature branch (kebab-case)
git checkout -b fix/improve-error-message-for-missing-api-key

# 3. Make changes
# Edit files, following code standards:
# - snake_case for Python variables/functions
# - kebab-case for file names
# - Max 200 lines per file
# - Type hints on all functions
# - Docstring on every class and public method

# 4. Run tests (must pass before PR)
python3 -m pytest tests/ -v
# Fix any failures before continuing

# 5. Lint check
python3 -m flake8 src/ --max-line-length=100
python3 -m mypy src/ --ignore-missing-imports

# 6. Commit (conventional commit format)
git add src/core/exceptions.py tests/test_exceptions.py
git commit -m "fix: improve error message for missing LLM API key"

# 7. Push and open PR
git push origin fix/improve-error-message-for-missing-api-key
# GitHub will show "Open pull request" button
```

### PR Checklist

Before submitting, confirm:
- [ ] All 62 existing tests pass
- [ ] New tests added for new code
- [ ] No `any` types (Python: no untyped params)
- [ ] No `print()` statements (use `rich.console`)
- [ ] Docstring on new functions/classes
- [ ] PR description explains the "why" not just the "what"
- [ ] DCO sign-off: `git commit -s` (adds `Signed-off-by:` line)

---

## Step 5: PR Review Process

| Stage               | Timeline   | Who                |
|---------------------|------------|--------------------|
| Initial triage      | 24 hours   | Maintainer         |
| Code review         | 48–72 hours| Maintainer         |
| Requested changes   | Author's pace | Contributor    |
| Merge               | After approval | Maintainer    |
| Release             | Next patch tag | Maintainer    |

**Review criteria:**
1. Tests pass in CI
2. Code follows standards (snake_case, 200-line limit, type hints)
3. Change is purposeful (YAGNI — no speculative features)
4. No secrets, no debug prints, no commented-out code

---

## Community Resources

| Resource           | Link                                    | Purpose              |
|--------------------|-----------------------------------------|----------------------|
| GitHub Issues      | github.com/[org]/mekong-cli/issues      | Bug reports, features|
| GitHub Discussions | github.com/[org]/mekong-cli/discussions | Questions, ideas     |
| Discord            | discord.gg/mekong-cli                   | Real-time chat       |
| Docs               | mekongcli.com/docs                      | Full documentation   |
| Changelog          | CHANGELOG.md                            | Version history      |

---

## Coding Standards Quick Reference

```python
# GOOD: Type hints, docstring, snake_case
def parse_task_input(raw_input: str, max_steps: int = 10) -> list[Step]:
    """Parse raw user input into executable steps.

    Args:
        raw_input: The user's task description.
        max_steps: Maximum steps to generate.

    Returns:
        List of Step objects ready for execution.
    """
    ...

# BAD: No types, no docstring, unclear name
def parse(x, n=10):
    ...
```

---

*Questions? Open a GitHub Discussion or join Discord. We respond within 24 hours.*
