# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Mekong CLI - Recipe Planner."""
import logging
import re as _re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from src.providers.llm.client import LLMClient

from .parser import Recipe, RecipeStep

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    SIMPLE, MODERATE, COMPLEX = "simple", "moderate", "complex"


@dataclass
class PlanningContext:
    goal: str
    constraints: Dict[str, Any] = field(default_factory=dict)
    project_info: Dict[str, Any] = field(default_factory=dict)
    available_agents: List[str] = field(default_factory=list)
    complexity: TaskComplexity = TaskComplexity.MODERATE


@dataclass
class VerificationCriteria:
    exit_code: Optional[int] = 0
    file_exists: List[str] = field(default_factory=list)
    file_not_exists: List[str] = field(default_factory=list)
    output_contains: List[str] = field(default_factory=list)
    output_not_contains: List[str] = field(default_factory=list)
    custom_checks: List[str] = field(default_factory=list)


class RecipePlanner:
    AGENT_KEYWORDS: Dict[str, List[str]] = {
        "git": ["git", "commit", "branch", "merge", "rebase", "diff", "log", "push", "pull", "clone", "stash"],
        "file": ["file", "read", "write", "copy", "move", "delete", "rename", "directory", "folder", "tree"],
        "shell": ["run", "execute", "script", "command", "install", "build", "compile"],
        "lead": ["lead", "prospect", "ceo", "email", "company", "hunt", "outreach"], "content": ["content", "article", "blog", "seo", "write", "copywriting"],
        "crawler": ["crawl", "scrape", "recipe", "discover"], "tool": ["tool", "registry", "suggest", "discover tool"],
        "browse": ["browse", "url", "http", "website", "page", "link", "web"], "evolve": ["refactor", "optimize", "improve", "clean", "evolve"],
    }
    _URL_PREFIXES = ("http://", "https://", "www.")
    _TOOL_KEYWORDS: Dict[str, str] = {"git status": "git:status", "git diff": "git:diff", "git log": "git:log", "npm install": "npm:install", "npm test": "npm:test", "pip install": "pip:install", "docker build": "docker:build"}
    _SHELL_PREFIXES = ("find ", "ls ", "git ", "cat ", "grep ", "mkdir ", "rm ", "cp ", "mv ", "echo ", "pip ", "npm ", "python", "node ", "cd ", "curl ", "wget ", "docker ", "make ", "brew ")
    def __init__(self, llm_client: Optional["LLMClient"] = None) -> None:
        self.llm_client = llm_client
    def suggest_agent(self, goal: str) -> Optional[str]:
        gl = goal.lower()
        pos = {n: s for n, kws in self.AGENT_KEYWORDS.items() if (s := sum(1 for kw in kws if kw in gl)) > 0}
        return max(pos, key=lambda k: pos[k]) if pos else None
    def _detect_step_type(self, goal: str) -> str:
        gl = goal.lower()
        if any(gl.startswith(p) or f" {p}" in gl for p in self._URL_PREFIXES):
            return "browse"
        if any(kw in gl for kw in self._TOOL_KEYWORDS):
            return "tool"
        if any(w in gl for w in ["refactor", "optimize", "improve code", "clean code"]):
            return "evolve"
        return "browse" if any(w in gl for w in ["browse", "check website", "analyze page", "crawl", "scrape"]) else ""
    def _get_tool_name(self, goal: str) -> str:
        gl = goal.lower()
        return next((tn for kw, tn in self._TOOL_KEYWORDS.items() if kw in gl), "")
    def _extract_url(self, goal: str) -> str:
        m = _re.search(r"https?://\S+|www\.\S+", goal)
        return m.group(0) if m else ""
    def decompose_goal(self, goal: str, context: PlanningContext) -> List[Dict[str, Any]]:
        return self._llm_decompose(goal, context) if self.llm_client else self._rule_based_decompose(goal, context)
    def _rule_based_decompose(self, goal: str, context: PlanningContext) -> List[Dict[str, Any]]:
        suggested_agent, gl, dt = self.suggest_agent(goal), goal.lower(), self._detect_step_type(goal)
        if dt == "browse":
            url = self._extract_url(goal)
            tasks: List[Dict[str, Any]] = [{"title": goal, "description": f"Browse and analyze: {url or goal}", "dependencies": [], "type": "browse", "url": url or "https://example.com", "action": "analyze" if "analyze" in gl else "check"}]
        elif dt == "tool":
            tn = self._get_tool_name(goal)
            tasks = [{"title": goal, "description": f"Execute tool: {tn}", "dependencies": [], "type": "tool", "tool_name": tn, "tool_args": {}}]
        elif dt == "evolve":
            tasks = [{"title": f"Analyze: {goal}", "description": "Scan source code for improvement opportunities", "dependencies": [], "type": "shell"}, {"title": f"Apply: {goal}", "description": goal, "dependencies": [0], "type": "llm"}]
        elif any(w in gl for w in ["implement", "create", "build"]):
            tasks = [{"title": "Setup environment", "description": "Prepare project structure and dependencies", "dependencies": []}, {"title": "Implement core logic", "description": f"Implement {goal}", "dependencies": [0]}, {"title": "Write tests", "description": "Create test cases", "dependencies": [1]}, {"title": "Verify implementation", "description": "Run tests and validate", "dependencies": [2]}]
        elif any(w in gl for w in ["fix", "debug", "resolve"]):
            tasks = [{"title": "Identify issue", "description": f"Analyze and locate problem: {goal}", "dependencies": []}, {"title": "Apply fix", "description": "Implement solution", "dependencies": [0]}, {"title": "Verify fix", "description": "Test that issue is resolved", "dependencies": [1]}]
        elif any(gl.startswith(cmd) for cmd in self._SHELL_PREFIXES):
            m = _re.match(r"git\s+log\s+(\d+)$", goal, _re.IGNORECASE)
            tasks = [{"title": goal, "description": f"git log --oneline -n {m.group(1)}" if m else goal, "dependencies": [], "type": "shell"}]
        elif any(w in gl for w in ["list", "show", "search", "find"]):
            cmd = "find src/ -name '*.py' -not -path '*/__pycache__/*' | sort" if ("python" in gl or ".py" in gl) else ("find . -maxdepth 3 -not -path '*/node_modules/*' -not -path '*/.git/*' | head -50" if "file" in gl else "find . -maxdepth 2 -not -path '*/.git/*' | sort | head -30")
            tasks = [{"title": goal, "description": cmd, "dependencies": [], "type": "shell"}]
        else:
            tasks = [{"title": goal, "description": goal, "dependencies": [], "type": "llm"}]
        for t in (tasks if suggested_agent else []):
            t.setdefault("agent", suggested_agent)
        return tasks
    def _llm_decompose(self, goal: str, context: PlanningContext) -> List[Dict[str, Any]]:
        from src.providers.llm.client import get_client
        client = get_client()
        if not client.is_available:
            return self._rule_based_decompose(goal, context)
        prompt = f"Decompose this goal into atomic, executable tasks.\nGoal: {goal}\nComplexity: {context.complexity.value}\nConstraints: {context.constraints}\nReturn ONLY a JSON array of objects with title, description, dependencies."
        try:
            res = client.generate_json(prompt)
            if isinstance(res, dict) and "raw_content" in res:
                return self._rule_based_decompose(goal, context)
            tasks = res if isinstance(res, list) else (res["tasks"] if isinstance(res, dict) and "tasks" in res else [res])
            val = [{"title": t.get("title", "Untitled"), "description": t.get("description", ""), "dependencies": t.get("dependencies", [])} for t in tasks if isinstance(t, dict) and "title" in t]
            return val or self._rule_based_decompose(goal, context)
        except Exception as e:
            logger.error("[PLANNER] LLM decomposition failed: %s", e)
            return self._rule_based_decompose(goal, context)
    def generate_verification_criteria(self, task: Dict[str, Any]) -> VerificationCriteria:
        c, desc = VerificationCriteria(), task.get("description", "")
        dl = desc.lower()
        if ("create" in dl or "generate" in dl) and "directory" not in dl and "folder" not in dl:
            c.file_exists.extend(w for w in (x.strip("',\"()[]{}") for x in desc.split()) if "." in w and "/" not in w)
        if "test" in dl:
            c.output_contains.append("pass")
            c.output_not_contains.extend(["error", "failed"])
        if "build" in dl or "compile" in dl:
            c.output_not_contains.extend(["error:", "failed"])
        return c
    def _make_step(self, order: int, task: Dict[str, Any], deps: List[int]) -> RecipeStep:
        step = RecipeStep(order=order, title=task["title"], description=task["description"], agent=task.get("agent"), params={"type": task.get("type", "shell"), "dependencies": deps, "verification": self.generate_verification_criteria(task).__dict__})
        step.dependencies = deps  # type: ignore[attr-defined]
        return step
    def plan(self, goal: str, context: Optional[PlanningContext] = None) -> Recipe:
        context = context or PlanningContext(goal=goal)
        steps = [self._make_step(idx + 1, t, [d + 1 for d in t.get("dependencies", []) if isinstance(d, int)]) for idx, t in enumerate(self.decompose_goal(goal, context))]
        has_deps = any(bool(getattr(s, "dependencies", [])) for s in steps)
        if has_deps:
            from .dag_scheduler import validate_dag
            if validate_dag(steps):
                for s in steps:
                    s.dependencies, s.params["dependencies"] = [], []  # type: ignore[attr-defined]
                has_deps = False
        return Recipe(name=f"Plan: {goal}", description=f"Automated plan for: {goal}", steps=steps, metadata={"planned_by": "RecipePlanner", "complexity": context.complexity.value, "goal": goal, "dag_enabled": has_deps})
    def replan_failed_branch(self, recipe: Recipe, failed_step_order: int, error_context: str = "") -> Recipe:
        down, changed = {failed_step_order}, True
        while changed:
            changed = any(s.order not in down and any(d in down for d in s.params.get("dependencies", [])) and not down.add(s.order) for s in recipe.steps)  # type: ignore[func-returns-value]
        failed_step = next((s for s in recipe.steps if s.order == failed_step_order), None)
        if not failed_step:
            return recipe
        goal = f"{failed_step.description} (previous attempt failed: {error_context}. Try a different approach.)" if error_context else failed_step.description
        kept = [s for s in recipe.steps if s.order not in down]
        raw_deps = getattr(failed_step, "dependencies", None) or (failed_step.params or {}).get("dependencies", [])
        orig_deps, next_order, valid_kept = [d for d in raw_deps if d not in down], max((s.order for s in kept), default=0) + 1, {s.order for s in kept}
        for idx, task in enumerate(self.decompose_goal(goal, PlanningContext(goal=goal, constraints={"retry": True, "previous_error": error_context}))):
            nd = [next_order + d for d in task.get("dependencies", []) if isinstance(d, int)]
            if idx == 0 or not nd:
                nd.extend(od for od in orig_deps if od in valid_kept and od not in nd)
            kept.append(self._make_step(next_order + idx, task, nd))
        recipe.steps, recipe.metadata["replanned"], recipe.metadata["replanned_step"] = sorted(kept, key=lambda s: s.order), True, failed_step_order
        return recipe
    def validate_plan(self, recipe: Recipe) -> List[str]:
        issues, valid_orders = [], {s.order for s in recipe.steps}
        for s in recipe.steps:
            deps = s.params.get("dependencies", [])
            if s.order in deps:
                issues.append(f"Step {s.order} has circular dependency on itself")
            issues.extend(f"Step {s.order} depends on non-existent step {d}" if d not in valid_orders else f"Step {s.order} depends on future step {d}" for d in deps if d not in valid_orders or d >= s.order)
            if len(deps) != len(set(deps)):
                issues.append(f"Step {s.order} has duplicate dependencies")
        return issues if recipe.steps else [*issues, "Recipe has no steps"]


__all__ = ["RecipePlanner", "PlanningContext", "VerificationCriteria", "TaskComplexity"]
