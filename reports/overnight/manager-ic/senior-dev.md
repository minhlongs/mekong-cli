# Senior Developer Report — Mekong CLI
*Role: Senior Developer | Date: 2026-03-11*

---

## Codebase Assessment

Mekong CLI has a clean architectural foundation — the PEV engine is well-separated
into four modules (planner, executor, verifier, orchestrator) with clear responsibilities.
The agent registry pattern is extensible. The main technical risks are in
observability, test performance, and type coverage gaps.

---

## Code Review Standards

### What I look for in every PR

**1. Type safety first**
```python
# Bad — no type hints
def execute_step(step, context):
    return step.run(context)

# Good — full signatures
def execute_step(step: ExecutionStep, context: ExecutionContext) -> ExecutionResult:
    return step.run(context)
```

**2. Error handling completeness**
```python
# Bad — bare except
try:
    result = llm_client.complete(prompt)
except:
    return None

# Good — specific exceptions with context
try:
    result = llm_client.complete(prompt)
except LLMRateLimitError as e:
    logger.warning("LLM rate limit hit, retrying in %ds", e.retry_after)
    raise
except LLMTimeoutError as e:
    logger.error("LLM timeout after %ds for step %s", e.timeout, step.name)
    raise MekongError(f"LLM timeout: {step.name}") from e
```

**3. Rollback handlers present**
Every executor step that modifies state MUST have a rollback:
```python
ExecutionStep(
    name="create_database",
    params={"table": "users"},
    rollback={"action": "drop_table", "table": "users"}  # Required
)
```

**4. File size compliance**
Files > 200 lines flagged in review. Split proposal required with PR.

**5. No print() in production code**
```bash
# Pre-merge check
grep -r "^\s*print(" src/ --include="*.py" | grep -v "test_"
# Must return empty
```

---

## Architecture Patterns I Enforce

### 1. Single Responsibility in Agents
Each agent (`LeadHunter`, `ContentWriter`, etc.) must:
- Override ONLY `plan()`, `execute()`, `verify()` from `AgentBase`
- Not import from other agents (no cross-agent coupling)
- Not call `llm_client` directly — use `self.llm.complete()`

### 2. ExecutionResult as Contract
All executor paths must return `ExecutionResult`. No dict returns, no None returns.
```python
# Bad
def run_shell(cmd: str) -> dict:
    output = subprocess.run(cmd, ...)
    return {"stdout": output.stdout, "code": output.returncode}

# Good
def run_shell(cmd: str) -> ExecutionResult:
    output = subprocess.run(cmd, ...)
    return ExecutionResult(
        success=output.returncode == 0,
        output=output.stdout,
        exit_code=output.returncode,
        step_name=cmd
    )
```

### 3. LLM Calls via llm_client Only
No direct `httpx` or `requests` calls to LLM APIs anywhere in the codebase.
All LLM interaction routes through `src/core/llm_client.py` — this is the only
place where provider switching, retry logic, and cost tracking live.

---

## Mentoring Plan for Junior Developers

### Week 1-2: Orientation
- Read `src/core/` — understand PEV engine top to bottom
- Run `python3 -m pytest tests/ -v` — understand what each test validates
- Read `CLAUDE.md` — understand OpenClaw constitution and quality rules
- First task: add docstrings to any 3 functions missing them (low-risk, high-learning)

### Week 3-4: First Contribution
- Pick one failing or slow test from the test suite
- Fix it with guidance from senior dev
- Write the PR description explaining the root cause and fix

### Month 2: First Feature
- Add one new command to `.agencyos/commands/`
- Implement the corresponding handler in `src/core/executor.py` if needed
- Write unit tests achieving >80% coverage on new code
- Conduct self-review against the code review checklist before requesting review

### Month 3: Ownership
- Own one module end-to-end (suggested: a new agent in `src/agents/`)
- Lead the PR review process (request reviews, respond to feedback, merge)

---

## Best Practices Checklist

```
Pre-commit:
  [ ] python3 -m pytest tests/ — all pass
  [ ] mypy src/ — 0 errors
  [ ] grep -r "print(" src/ --include="*.py" | grep -v test_ — empty
  [ ] grep -r "TODO\|FIXME" src/ — empty (or tracked in GitHub Issues)
  [ ] All new files < 200 lines

PR description must include:
  [ ] What problem this solves
  [ ] How to test it locally (exact commands)
  [ ] Any breaking changes
  [ ] Rollback plan if needed
```

---

## Known Technical Debt I'd Address First

1. **`test_file_stats` performance** — scans entire repo. Add `tmp_path` fixture
   with synthetic files. Estimated fix: 30 minutes. Impact: test suite from 2.5min → 30s.

2. **`llm_client.py` missing retry** — Add `tenacity` library for exponential backoff:
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
   def complete(self, prompt: str) -> str: ...
   ```

3. **Untracked CF adapter files** — `src/jobs/cloudflare-*.ts` are untracked.
   Either integrate into the CF adapter layer or delete. Ambiguity is tech debt.

4. **No structured logging** — Replace `print()` and bare `logging` with `structlog`:
   ```python
   import structlog
   log = structlog.get_logger()
   log.info("step_started", step=step.name, attempt=attempt)
   ```

---

## Code Quality Metrics Target

| Metric | Current (est.) | Target |
|--------|---------------|--------|
| Test coverage | Unknown | >80% |
| mypy strict errors | Unknown | 0 |
| Avg function length | Unknown | <20 lines |
| Files > 200 lines | Unknown | 0 |
| Docstring coverage | Partial | 100% on public methods |

---

## Q2 Senior Dev Actions

- [ ] Fix `test_file_stats` performance (30-min task, high impact)
- [ ] Add `tenacity` retry to `llm_client.py`
- [ ] Run `mypy src/` and fix all errors
- [ ] Add `structlog` for structured JSON logging
- [ ] Write `CONTRIBUTING.md` with code review checklist
- [ ] Set up `pre-commit` hooks with mypy + pytest
