---
phase: 03
title: "Wire Plan-Execute-Verify Engine"
priority: P1
status: pending
effort: 6h
---

# Phase 03: Wire Plan-Execute-Verify Engine

## Context Links

- Core Engine: `src/core/{planner.py, executor.py, verifier.py, orchestrator.py}`
- Antigravity Proxy: `~/.mekong/proxy/`
- Binh Phap Quality Gates: `.claude/rules/binh-phap-quality.md`
- Dependencies: Phase 01 (core packages), Phase 02 (package structure)

## Overview

**Priority:** P1
**Status:** Pending
**Effort:** 6h

Implement missing LLM integration in planner, multi-mode execution in executor, and Binh Phap quality gates in verifier to complete the Plan-Execute-Verify engine.

## Key Insights

- **Planner** currently shell-only; needs LLM-powered task decomposition
- **Executor** lacks `execute_llm()` and `execute_api()` methods
- **Verifier** needs Binh Phap quality gate enforcement
- **Orchestrator** coordinates the full workflow
- Antigravity Proxy provides unified LLM access (Gemini/Claude fallback)

## Requirements

### Functional Requirements
- Implement `_llm_decompose()` in `planner.py` using Antigravity Proxy
- Add `execute_llm()` method in `executor.py` for LLM task execution
- Add `execute_api()` method in `executor.py` for API calls
- Implement Binh Phap quality gates in `verifier.py`
- Wire orchestrator to use all three engines seamlessly
- Add retry logic with exponential backoff
- Support rollback on verification failure

### Non-Functional Requirements
- LLM calls timeout after 60s
- Retry up to 3 times on transient failures
- Quality gates configurable (can skip in dev mode)
- Structured logging for all operations
- Type safety with Pydantic models

## Architecture

### Engine Flow

```
┌─────────────────────────────────────────────────────────┐
│ RecipeOrchestrator                                      │
│ - Coordinates Plan → Execute → Verify loop             │
│ - Handles rollback on failure                          │
│ - Manages retry logic                                  │
└────────────┬──────────────┬──────────────┬─────────────┘
             │              │              │
    ┌────────▼────┐  ┌─────▼─────┐  ┌────▼─────┐
    │  Planner    │  │ Executor  │  │ Verifier │
    │ LLM + Rules │  │ Multi-mode│  │ Quality  │
    └─────────────┘  └───────────┘  └──────────┘
```

### Planner Architecture

```python
class RecipePlanner:
    def plan(self, goal: str, context: dict) -> Recipe:
        # 1. Analyze goal
        # 2. Decompose via LLM (NEW)
        # 3. Add dependencies
        # 4. Generate verification criteria
        return Recipe(tasks, dependencies, verification)

    def _llm_decompose(self, goal: str) -> List[Task]:
        # NEW: Use Antigravity Proxy
        # Prompt: "Decompose {goal} into atomic tasks"
        # Parse LLM response into Task objects
```

### Executor Architecture

```python
class RecipeExecutor:
    def execute(self, recipe: Recipe) -> Result:
        for task in recipe.tasks:
            if task.mode == "shell":
                result = self._execute_shell(task)
            elif task.mode == "llm":
                result = self._execute_llm(task)  # NEW
            elif task.mode == "api":
                result = self._execute_api(task)  # NEW

            if not result.success:
                self._rollback(task)
                raise ExecutionError(result)
```

### Verifier Architecture

```python
class RecipeVerifier:
    def verify(self, result: Result, criteria: Criteria) -> Verification:
        # Exit code checks
        # File existence checks
        # Binh Phap quality gates (NEW)
        # LLM quality assessment (optional)

        return Verification(
            passed=bool,
            gates_passed=dict,
            recommendations=list
        )
```

## Related Code Files

### Files to Modify
- `src/core/planner.py` - Add `_llm_decompose()`
- `src/core/executor.py` - Add `_execute_llm()`, `_execute_api()`
- `src/core/verifier.py` - Add Binh Phap gates
- `src/core/orchestrator.py` - Wire all engines together

### Files to Create
- `src/core/llm_client.py` - Antigravity Proxy client
- `src/core/models.py` - Pydantic models for Recipe, Task, Result
- `src/core/quality_gates.py` - Binh Phap gate definitions
- `tests/core/test_planner_llm.py` - LLM planner tests
- `tests/core/test_executor_modes.py` - Multi-mode executor tests
- `tests/core/test_verifier_gates.py` - Quality gate tests

### Files to Reference
- `.claude/rules/binh-phap-quality.md` - Quality gate definitions
- `~/.mekong/proxy/config.yaml` - Proxy configuration

## Implementation Steps

### Step 1: Create Pydantic Models
```python
# src/core/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Literal

class Task(BaseModel):
    id: str
    description: str
    mode: Literal["shell", "llm", "api"]
    command: str | None = None
    prompt: str | None = None
    api_endpoint: str | None = None
    dependencies: List[str] = []
    verification_criteria: Dict[str, any] = {}

class Recipe(BaseModel):
    goal: str
    tasks: List[Task]
    verification: Dict[str, any]

class Result(BaseModel):
    task_id: str
    success: bool
    output: str
    exit_code: int | None = None
    error: str | None = None
```

### Step 2: Create Antigravity Proxy Client
```python
# src/core/llm_client.py
import httpx
from typing import Dict

class AntigravityClient:
    def __init__(self, proxy_url: str = "http://localhost:8080"):
        self.proxy_url = proxy_url
        self.client = httpx.Client(timeout=60.0)

    def complete(self, prompt: str, model: str = "auto") -> str:
        """Call LLM via Antigravity Proxy with fallback."""
        response = self.client.post(
            f"{self.proxy_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def decompose_goal(self, goal: str, context: Dict) -> List[Dict]:
        """Decompose goal into tasks via LLM."""
        prompt = f"""Decompose this goal into atomic, executable tasks:

Goal: {goal}

Context:
{context}

Return ONLY a JSON array of tasks with format:
[
  {{"id": "task-1", "description": "...", "mode": "shell|llm|api", "command": "..."}},
  ...
]
"""
        response = self.complete(prompt)
        # Parse JSON from response
        import json
        return json.loads(response)
```

### Step 3: Implement LLM Planner
```python
# src/core/planner.py (add method)
from .llm_client import AntigravityClient
from .models import Recipe, Task

class RecipePlanner:
    def __init__(self):
        self.llm = AntigravityClient()

    def _llm_decompose(self, goal: str, context: dict) -> List[Task]:
        """Decompose goal using LLM."""
        try:
            task_dicts = self.llm.decompose_goal(goal, context)
            tasks = [Task(**task) for task in task_dicts]
            return tasks
        except Exception as e:
            logger.error(f"LLM decomposition failed: {e}")
            # Fallback to rule-based decomposition
            return self._rule_based_decompose(goal)

    def plan(self, goal: str, context: dict = None) -> Recipe:
        """Create execution plan."""
        context = context or {}

        # Try LLM decomposition first
        tasks = self._llm_decompose(goal, context)

        # Add dependencies
        tasks = self._add_dependencies(tasks)

        # Generate verification criteria
        verification = self._generate_verification(tasks)

        return Recipe(goal=goal, tasks=tasks, verification=verification)
```

### Step 4: Implement Multi-Mode Executor
```python
# src/core/executor.py (add methods)
from .llm_client import AntigravityClient
from .models import Task, Result
import subprocess
import httpx

class RecipeExecutor:
    def __init__(self):
        self.llm = AntigravityClient()
        self.http = httpx.Client()

    def _execute_llm(self, task: Task) -> Result:
        """Execute LLM task."""
        try:
            output = self.llm.complete(task.prompt)
            return Result(
                task_id=task.id,
                success=True,
                output=output,
                exit_code=0
            )
        except Exception as e:
            return Result(
                task_id=task.id,
                success=False,
                output="",
                error=str(e),
                exit_code=1
            )

    def _execute_api(self, task: Task) -> Result:
        """Execute API task."""
        try:
            response = self.http.post(
                task.api_endpoint,
                json=task.payload or {}
            )
            response.raise_for_status()
            return Result(
                task_id=task.id,
                success=True,
                output=response.text,
                exit_code=0
            )
        except Exception as e:
            return Result(
                task_id=task.id,
                success=False,
                output="",
                error=str(e),
                exit_code=1
            )

    def execute(self, recipe: Recipe) -> List[Result]:
        """Execute recipe with retry logic."""
        results = []
        for task in recipe.tasks:
            result = self._execute_with_retry(task, max_retries=3)
            results.append(result)

            if not result.success:
                logger.error(f"Task {task.id} failed, rolling back")
                self._rollback(results)
                raise ExecutionError(f"Task {task.id} failed")

        return results

    def _execute_with_retry(self, task: Task, max_retries: int) -> Result:
        """Execute task with exponential backoff."""
        import time
        for attempt in range(max_retries):
            if task.mode == "shell":
                result = self._execute_shell(task)
            elif task.mode == "llm":
                result = self._execute_llm(task)
            elif task.mode == "api":
                result = self._execute_api(task)

            if result.success:
                return result

            wait = 2 ** attempt
            logger.warning(f"Retry {attempt+1}/{max_retries} after {wait}s")
            time.sleep(wait)

        return result
```

### Step 5: Implement Quality Gates
```python
# src/core/quality_gates.py
from typing import Dict, Callable
import subprocess

class BinhPhapGates:
    """Binh Phap quality gates from 孫子兵法."""

    GATES = {
        "tech_debt": {
            "name": "始計 Tech Debt Elimination",
            "check": lambda: BinhPhapGates._check_tech_debt(),
            "critical": True
        },
        "type_safety": {
            "name": "作戰 Type Safety 100%",
            "check": lambda: BinhPhapGates._check_type_safety(),
            "critical": True
        },
        "performance": {
            "name": "謀攻 Performance",
            "check": lambda: BinhPhapGates._check_performance(),
            "critical": False
        },
        "security": {
            "name": "軍形 Security",
            "check": lambda: BinhPhapGates._check_security(),
            "critical": True
        }
    }

    @staticmethod
    def _check_tech_debt() -> Dict:
        """Check for TODOs, FIXMEs, console logs."""
        result = subprocess.run(
            ["grep", "-r", "TODO\\|FIXME\\|console\\.", "src/"],
            capture_output=True,
            text=True
        )
        passed = result.returncode != 0  # No matches = pass
        return {"passed": passed, "output": result.stdout}

    @staticmethod
    def _check_type_safety() -> Dict:
        """Check for 'any' types."""
        result = subprocess.run(
            ["grep", "-r", ": any", "src/", "--include=*.ts"],
            capture_output=True,
            text=True
        )
        passed = result.returncode != 0
        return {"passed": passed, "output": result.stdout}

    @staticmethod
    def _check_performance() -> Dict:
        """Check build time."""
        import time
        start = time.time()
        result = subprocess.run(["npm", "run", "build"], capture_output=True)
        elapsed = time.time() - start
        passed = elapsed < 10.0
        return {"passed": passed, "build_time": elapsed}

    @staticmethod
    def _check_security() -> Dict:
        """Check npm audit."""
        result = subprocess.run(
            ["npm", "audit", "--audit-level=high"],
            capture_output=True,
            text=True
        )
        passed = result.returncode == 0
        return {"passed": passed, "output": result.stdout}

    @classmethod
    def run_all(cls, skip_non_critical: bool = False) -> Dict:
        """Run all quality gates."""
        results = {}
        for gate_id, gate in cls.GATES.items():
            if skip_non_critical and not gate["critical"]:
                continue
            results[gate_id] = gate["check"]()
        return results
```

### Step 6: Implement Verifier with Gates
```python
# src/core/verifier.py (add method)
from .quality_gates import BinhPhapGates
from .models import Result, Recipe

class RecipeVerifier:
    def verify(self, results: List[Result], recipe: Recipe,
               skip_gates: bool = False) -> Dict:
        """Verify execution results and quality gates."""
        verification = {
            "execution_passed": all(r.success for r in results),
            "gates_passed": {},
            "overall_passed": False,
            "recommendations": []
        }

        # Check Binh Phap quality gates
        if not skip_gates:
            gate_results = BinhPhapGates.run_all()
            verification["gates_passed"] = gate_results

            failed_gates = [
                gate_id for gate_id, result in gate_results.items()
                if not result["passed"]
            ]

            if failed_gates:
                verification["recommendations"].append(
                    f"Failed quality gates: {', '.join(failed_gates)}"
                )

        # Overall pass requires both execution and gates
        verification["overall_passed"] = (
            verification["execution_passed"] and
            all(g["passed"] for g in verification["gates_passed"].values())
        )

        return verification
```

### Step 7: Wire Orchestrator
```python
# src/core/orchestrator.py
from .planner import RecipePlanner
from .executor import RecipeExecutor
from .verifier import RecipeVerifier
from .models import Recipe

class RecipeOrchestrator:
    def __init__(self):
        self.planner = RecipePlanner()
        self.executor = RecipeExecutor()
        self.verifier = RecipeVerifier()

    def run(self, goal: str, context: dict = None,
            skip_gates: bool = False) -> Dict:
        """Run full Plan → Execute → Verify workflow."""

        # PLAN
        logger.info(f"Planning: {goal}")
        recipe = self.planner.plan(goal, context)

        # EXECUTE
        logger.info(f"Executing {len(recipe.tasks)} tasks")
        results = self.executor.execute(recipe)

        # VERIFY
        logger.info("Verifying results")
        verification = self.verifier.verify(results, recipe, skip_gates)

        if not verification["overall_passed"]:
            logger.error("Verification failed")
            # Could trigger rollback here

        return {
            "recipe": recipe,
            "results": results,
            "verification": verification
        }
```

### Step 8: Add CLI Command
```python
# src/cli/commands.py
import typer
from ..core.orchestrator import RecipeOrchestrator

app = typer.Typer()

@app.command()
def run(
    goal: str,
    skip_gates: bool = typer.Option(False, "--skip-gates"),
    context: str = typer.Option(None, "--context")
):
    """Execute a goal using Plan-Execute-Verify engine."""
    orchestrator = RecipeOrchestrator()

    context_dict = {}
    if context:
        import json
        context_dict = json.loads(context)

    result = orchestrator.run(goal, context_dict, skip_gates)

    if result["verification"]["overall_passed"]:
        typer.secho("✅ Success", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed", fg=typer.colors.RED)
        for rec in result["verification"]["recommendations"]:
            typer.echo(f"  - {rec}")
```

### Step 9: Write Tests
```python
# tests/core/test_planner_llm.py
def test_llm_decompose():
    planner = RecipePlanner()
    tasks = planner._llm_decompose("Deploy API", {})
    assert len(tasks) > 0
    assert all(isinstance(t, Task) for t in tasks)

# tests/core/test_executor_modes.py
def test_execute_llm():
    executor = RecipeExecutor()
    task = Task(id="t1", mode="llm", prompt="Say hello")
    result = executor._execute_llm(task)
    assert result.success
    assert "hello" in result.output.lower()

# tests/core/test_verifier_gates.py
def test_quality_gates():
    gates = BinhPhapGates.run_all()
    assert "tech_debt" in gates
    assert "type_safety" in gates
```

### Step 10: Integration Test
```bash
# Test full workflow
mekong run "Create README.md file"

# Expected:
# - Planner decomposes via LLM
# - Executor runs shell command
# - Verifier checks file exists
# - Quality gates run (skip in dev)
```

### Step 11: Commit Checkpoint
```bash
git add src/core/
git commit -m "feat: wire Plan-Execute-Verify engine with LLM and quality gates"
```

## Todo List

- [ ] Pydantic models created
- [ ] Antigravity Proxy client implemented
- [ ] LLM decompose in planner
- [ ] execute_llm in executor
- [ ] execute_api in executor
- [ ] Retry logic with backoff
- [ ] Quality gates module created
- [ ] Verifier uses Binh Phap gates
- [ ] Orchestrator wires all engines
- [ ] CLI command added
- [ ] Unit tests written
- [ ] Integration test passes
- [ ] Git checkpoint committed

## Success Criteria

### Definition of Done
- ✅ `mekong run "goal"` executes Plan→Execute→Verify
- ✅ LLM decomposition works via Antigravity Proxy
- ✅ Multi-mode execution (shell/llm/api) functional
- ✅ Binh Phap quality gates enforce standards
- ✅ Retry logic handles transient failures
- ✅ All tests pass
- ✅ Zero type errors in engine code

### Validation Methods
```bash
# Type checking
cd src/core && mypy .

# Unit tests
pytest tests/core/

# Integration test
mekong run "Create test file" --skip-gates

# Quality gate test
mekong run "npm run build"  # Should trigger performance gate

# LLM test
mekong run "Summarize README.md"  # Should use LLM mode
```

## Risk Assessment

### Potential Issues
1. **Antigravity Proxy unavailable** - LLM calls fail
   - Mitigation: Fallback to rule-based planning, log warning
2. **LLM hallucinations** - Generated tasks invalid
   - Mitigation: Validation layer in planner, reject malformed tasks
3. **Quality gates too strict** - Block legitimate work
   - Mitigation: `--skip-gates` flag for development
4. **Timeout issues** - LLM calls hang
   - Mitigation: 60s timeout, exponential backoff

### Mitigation Strategies
- Extensive error handling in LLM client
- Graceful degradation (LLM → rules → manual)
- Comprehensive logging for debugging
- Gate configurability per project

## Security Considerations

- Validate all LLM outputs before execution
- Sanitize prompts to prevent injection
- Never pass secrets in LLM prompts
- Audit all API calls for security

## Next Steps

**Dependencies:** Phase 01 (core packages), Phase 02 (package structure)

**Blocks:** Phase 04 (BMAD needs working engine)

**Follow-up:** After completion, proceed to Phase 04 (Integrate BMAD) to make 169 workflows available through the engine.
