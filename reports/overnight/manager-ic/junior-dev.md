# Junior Developer Report — Mekong CLI
*Role: Junior Developer | Date: 2026-03-11*

---

## Welcome to Mekong CLI

Mekong CLI is an AI-operated business platform built in Python + TypeScript.
The core idea: you give it a goal, it Plans → Executes → Verifies automatically.

As a junior dev, your superpower here is that the codebase is small enough to
understand fully within 2 weeks, and the AI agents (including `mekong cook` itself)
will help you write your own code contributions.

---

## Onboarding Path

### Day 1: Get it running
```bash
# 1. Clone the repo
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli

# 2. Install dependencies
make setup

# 3. Run the test suite — should pass all 62 tests
python3 -m pytest tests/ -v

# 4. Set up your LLM (free option — Ollama)
# Install Ollama: https://ollama.ai
ollama pull qwen2.5-coder
export OLLAMA_BASE_URL=http://localhost:11434/v1

# 5. Your first cook
mekong cook "Create a Python function that reverses a string"
```

### Day 2-3: Read the core engine
Read these files in order — they are the heart of the project:
1. `src/core/exceptions.py` — error hierarchy (small, read first)
2. `src/core/llm_client.py` — how we talk to LLMs
3. `src/core/planner.py` — how goals become steps
4. `src/core/executor.py` — how steps get executed
5. `src/core/verifier.py` — how we check if it worked
6. `src/core/orchestrator.py` — how it all ties together

### Day 4-5: Read an agent
Pick one agent from `src/agents/` — start with `src/agents/shell_agent.py`
(simplest). Notice how it inherits `AgentBase` and implements `plan()`,
`execute()`, `verify()`.

### Week 2: First contribution
Look at GitHub Issues labeled `good first issue`. Typical first tasks:
- Add docstrings to functions that are missing them
- Fix a failing test
- Add a new command definition to `.agencyos/commands/`

---

## Key Concepts to Understand

### PEV Loop
```
Your goal: "Create a REST API with auth"
    │
    ▼  PLAN
Planner asks LLM: "Break this into steps"
LLM returns: [create_project, add_dependencies, write_routes, add_auth, run_tests]
    │
    ▼  EXECUTE
Executor runs each step (shell commands, file writes, LLM code generation)
    │
    ▼  VERIFY
Verifier checks: did tests pass? did files get created? exit code 0?
    │
    ├── PASS → Done! Return result to user
    └── FAIL → Orchestrator tries rollback, then self-healing
```

### MCU Credits
MCU = Mission Control Unit. One credit = one task execution.
- Starter: 200 credits/mo for $49
- Pro: 1,000 credits/mo for $149
- Enterprise: unlimited for $499
Free users (Ollama): unlimited, no credits needed.

### Agent Registry
```python
# src/agents/__init__.py
AGENT_REGISTRY = {
    "lead-hunter": LeadHunterAgent,
    "content-writer": ContentWriterAgent,
    "git-agent": GitAgent,
    # Add your new agent here!
}
```

---

## Learning Resources

### Python Concepts You'll Use Daily
- Dataclasses: `ExecutionResult` is a dataclass — learn `@dataclass` decorator
- Type hints: `def my_func(name: str) -> bool:` — used everywhere
- Async/await: some executor paths are async
- `subprocess`: `src/core/executor.py` uses it for shell commands
- pytest: `tests/test_*.py` — learn fixtures, parametrize, mock

### Cloudflare Workers (TypeScript layer)
- `apps/raas-gateway/index.js` — simple CF Worker with auth
- `src/jobs/cloudflare-*.ts` — newer CF adapter files
- Learn: `wrangler dev` for local testing, `wrangler deploy` to push

### Recommended Learning Path
1. **Python:** Complete Python type hints guide (mypy docs)
2. **Testing:** pytest documentation — fixtures + parametrize
3. **Git:** Conventional commits format (`feat:`, `fix:`, `refactor:`)
4. **Cloudflare:** "Workers Docs" → Hello World tutorial
5. **LLMs:** OpenAI API documentation (same interface Mekong uses)

---

## First Contribution Checklist

Before opening your first PR:
- [ ] `python3 -m pytest tests/` passes locally (all tests green)
- [ ] Your new file is < 200 lines (split if longer)
- [ ] Every function you wrote has a type hint on parameters and return value
- [ ] Every public function/class has a docstring
- [ ] No `print()` statements (use `logger.info()` instead)
- [ ] No `TODO` or `FIXME` comments left in (file a GitHub Issue instead)
- [ ] PR description explains: what problem, how to test, any risks

---

## Common Mistakes to Avoid

| Mistake | Why it's a problem | Fix |
|---------|-------------------|-----|
| Using `python` instead of `python3` | `python` not available on macOS | Always use `python3` |
| Bare `except:` | Catches SystemExit, KeyboardInterrupt | Use `except SpecificError:` |
| Missing type hints | mypy will catch it in CI | Add `-> ReturnType` to all functions |
| Files > 200 lines | Hard to review, hard to understand | Split into modules |
| Calling LLM API directly | Bypasses retry, cost tracking | Use `llm_client.py` |
| Committing `.env` file | Exposes API keys | Add to `.gitignore` immediately |

---

## How to Ask for Help

1. **Search first:** `grep -r "error message" src/` often finds similar patterns
2. **Use `mekong fix`:** Describe your bug, let the PEV engine try to fix it
3. **GitHub Discussions:** Ask questions publicly — helps future contributors
4. **Be specific:** Share exact error message + command that triggered it

---

## Your 30-Day Goal

By end of month 1, you should have:
- [ ] Merged 1 PR (any size — even a docstring fix counts)
- [ ] Run `mekong cook` on 5 different goals and noted what works/fails
- [ ] Read all files in `src/core/` at least once
- [ ] Added 1 new command definition to `.agencyos/commands/`
- [ ] Written 3 new test cases in `tests/`
