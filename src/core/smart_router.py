# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Smart Router (AGI v2)."""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .memory_canonical import MemoryStore
from .nlu import Intent, IntentResult

logger = logging.getLogger(__name__)


@dataclass
class RouteResult:
    action: str  # "recipe" | "direct" | "plan" | "tool" | "browse" | "evolve"
    recipe_path: str = ""
    recipe_name: str = ""
    tool_name: str = ""
    url: str = ""
    reason: str = ""


_INTENT_TAGS: Dict[Intent, str] = {
    Intent.DEPLOY: "deploy", Intent.AUDIT: "audit", Intent.CREATE: "create",
    Intent.FIX: "fix", Intent.STATUS: "status", Intent.SCHEDULE: "schedule",
    Intent.REFACTOR: "refactor", Intent.OPTIMIZE: "optimize", Intent.MIGRATE: "migrate",
    Intent.REPORT: "report",
}

_INTENT_TOOLS: Dict[Intent, str] = {Intent.STATUS: "git:status", Intent.AUDIT: "git:diff"}
_EVOLVE_INTENTS = {Intent.REFACTOR, Intent.OPTIMIZE}


class SmartRouter:
    """Memory-aware intent-to-recipe router with AGI v2 tool/browse awareness."""

    MIN_SUCCESS_RATE: float = 30.0

    def __init__(self, memory_store: Optional[MemoryStore] = None) -> None:
        self.memory = memory_store
        self._recipe_cache: Optional[Dict[str, str]] = None
        self._tool_registry: Optional[Any] = None
        self._browser_agent: Optional[Any] = None
        try:
            from .tool_registry import ToolRegistry
            self._tool_registry = ToolRegistry()
        except Exception as _exc:
            logger.debug("ToolRegistry unavailable, tool routing disabled: %s", _exc)

    def route(self, intent_result: IntentResult) -> RouteResult:
        """Route an intent to the best recipe, tool, or action."""
        if intent_result.intent == Intent.UNKNOWN:
            return RouteResult(action="plan", reason="Unknown intent")

        if intent_result.suggested_recipe:
            path = self._find_recipe_by_name(intent_result.suggested_recipe)
            if path and self._check_memory(intent_result.suggested_recipe):
                return RouteResult(action="recipe", recipe_path=path, recipe_name=intent_result.suggested_recipe, reason="Suggested recipe match")

        tag = _INTENT_TAGS.get(intent_result.intent, "")
        if tag:
            for name, path in self._scan_recipes().items():
                if tag in name.lower() and self._check_memory(name):
                    return RouteResult(action="recipe", recipe_path=path, recipe_name=name, reason=f"Intent tag match: {tag}")

        tool_name = _INTENT_TOOLS.get(intent_result.intent, "")
        if tool_name and self._tool_registry:
            try:
                if any(t.name == tool_name for t in self._tool_registry.list_tools()):
                    return RouteResult(action="tool", tool_name=tool_name, reason=f"Intent tool match: {tool_name}")
            except Exception as _exc:
                logger.debug("Intent tool lookup failed for '%s': %s", tool_name, _exc)

        if intent_result.intent in _EVOLVE_INTENTS:
            return RouteResult(action="evolve", reason=f"Code evolution route for {intent_result.intent.value}")

        if self._tool_registry:
            try:
                suggested = self._tool_registry.suggest_tool(intent_result.raw_goal)
                if suggested:
                    return RouteResult(action="tool", tool_name=suggested.name, reason=f"Tool suggestion: {suggested.name}")
            except Exception as _exc:
                logger.debug("Tool suggestion failed: %s", _exc)

        return RouteResult(action="plan", reason="No viable recipe found")

    def _find_recipe_by_name(self, name: str) -> Optional[str]:
        recipes = self._scan_recipes()
        if name in recipes:
            return recipes[name]
        name_lower = name.lower()
        return next((rpath for rname, rpath in recipes.items() if name_lower in rname.lower()), None)

    def _check_memory(self, recipe_name: str) -> bool:
        if not self.memory:
            return True
        entries = [e for e in self.memory._entries if e.recipe_used == recipe_name]
        if len(entries) < 3:
            return True
        recent = entries[-10:]
        return ((sum(1 for e in recent if e.status == "success") / len(recent)) * 100) >= self.MIN_SUCCESS_RATE

    def _scan_recipes(self) -> Dict[str, str]:
        if self._recipe_cache is not None:
            return self._recipe_cache
        recipe_dir = Path("recipes")
        self._recipe_cache = {f.stem: str(f) for f in recipe_dir.glob("*.md")} if recipe_dir.is_dir() else {}
        return self._recipe_cache


__all__ = ["RouteResult", "SmartRouter"]

