# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Self-Improvement & Recipe Evolution Engine."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore[import-untyped]
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from .evals_bridge import get_evals_db_path, query_evals
from .event_bus import EventType, get_event_bus
from .memory_canonical import MemoryStore
from .recipe_gen import RecipeGenerator

logger = logging.getLogger(__name__)


@dataclass
class JournalEntry:
    timestamp: float = field(default_factory=time.time)
    action: str = ""
    target: str = ""
    reason: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"timestamp": self.timestamp, "action": self.action, "target": self.target, "reason": self.reason, "data": self.data}


class SelfImprover:
    """Analyzes execution history and orchestrates autonomous workflow evolution."""

    MAX_JOURNAL: int = 500
    DEPRECATION_THRESHOLD: float = 0.20
    MIN_RUNS_FOR_DEPRECATION: int = 5

    def __init__(self, memory_store: Optional[MemoryStore] = None, recipe_generator: Optional[RecipeGenerator] = None, journal_path: Optional[str] = None, evals_db_path: Optional[Path] = None) -> None:
        self.memory = memory_store or MemoryStore()
        self.generator = recipe_generator or RecipeGenerator()
        self.journal_path = Path(journal_path or ".mekong/journal.yaml")
        self.evals_db_path = evals_db_path or get_evals_db_path()
        self._journal: list[JournalEntry] = []
        self._load_journal()

    def analyze_and_improve(self) -> list[JournalEntry]:
        new_entries: list[JournalEntry] = []
        for name in self.deprecate_bad_recipes():
            entry = JournalEntry(action="deprecated", target=name, reason="Success rate below 20% threshold across multiple runs", data={"recipe": name})
            self._record(entry)
            new_entries.append(entry)
        for goal in self.suggest_new_recipes():
            if matching := [e for e in self.memory.recent(100) if e.goal == goal and e.status == "success"]:
                recipe = self.generator.from_successful_run(matching[0])
                if recipe.valid:
                    entry = JournalEntry(action="generated", target=recipe.name, reason=f"Auto-generated from successful goal execution: {goal}", data={"path": self.generator.save_recipe(recipe), "source_goal": goal})
                    self._record(entry)
                    new_entries.append(entry)
        for entry in self.evolve_failing_recipes():
            self._record(entry)
            new_entries.append(entry)
        return new_entries

    def deprecate_bad_recipes(self) -> list[str]:
        deprecated: list[str] = []
        recipe_runs: dict[str, list[str]] = {}
        for e in self.memory.recent(500):
            if e.recipe_used:
                recipe_runs.setdefault(e.recipe_used, []).append(e.status)
        bus = get_event_bus()
        for recipe_name, statuses in recipe_runs.items():
            if len(statuses) >= self.MIN_RUNS_FOR_DEPRECATION:
                sr = sum(1 for s in statuses if s == "success") / len(statuses)
                if sr < self.DEPRECATION_THRESHOLD:
                    deprecated.append(recipe_name)
                    if bus:
                        try:
                            bus.emit(EventType.RECIPE_DEPRECATED, {"name": recipe_name, "success_rate": sr, "total_runs": len(statuses)})
                        except Exception:
                            pass
        return deprecated

    def suggest_new_recipes(self) -> list[str]:
        suggestions, seen = [], set()
        for e in self.memory.recent(100):
            if e.status == "success" and not e.recipe_used and e.goal not in seen:
                seen.add(e.goal)
                suggestions.append(e.goal)
        return suggestions[:5]

    def evolve_failing_recipes(self) -> list[JournalEntry]:
        evolved: list[JournalEntry] = []
        if not (clusters := query_evals(agent_id="all", window_days=14, db_path=self.evals_db_path).get("failure_clusters", [])):
            return evolved
        top = clusters[0]
        cat, reasons = top.get("category", ""), top.get("sample_reasons", [])
        for item in self.generator.list_auto_recipes()[:3]:
            r_path = Path(item.get("path", ""))
            if r_path.is_file() and "<!-- evolved:" not in (content := r_path.read_text(encoding="utf-8")):
                r_path.write_text(self._apply_cluster_improvements(content, cat, reasons), encoding="utf-8")
                evolved.append(JournalEntry(action="evolved", target=item.get("name", ""), reason=f"Added mitigations for '{cat}' failure cluster ({top.get('percentage')}% failures)", data={"path": str(r_path), "cluster": cat, "reasons": reasons[:2]}))
        return evolved

    def evolve_recipe(self, recipe_name: str, target_goal: str = "", force: bool = False) -> Optional[JournalEntry]:
        slug = self.generator._slugify(recipe_name)
        target_file = Path(self.generator.AUTO_DIR) / f"{slug}.md"
        if not target_file.exists():
            goal_text = target_goal or recipe_name
            recipe = self.generator.from_goal_pattern(goal_text, steps=["Validate environment and dependencies", f"Execute primary goal: {goal_text}", "Run verification tests and audit output"])
            entry = JournalEntry(action="generated", target=slug, reason=f"Synthesized initial recipe for evolution: {recipe_name}", data={"path": self.generator.save_recipe(recipe)})
            self._record(entry)
            return entry
        content = target_file.read_text(encoding="utf-8")
        if not force and "<!-- evolved: v2" in content:
            return None
        clusters = query_evals(agent_id="all", window_days=14, db_path=self.evals_db_path).get("failure_clusters", [])
        cat, reasons = (clusters[0]["category"], clusters[0].get("sample_reasons", [])) if clusters else ("General Hardening", [])
        target_file.write_text(self._apply_cluster_improvements(content, cat, reasons), encoding="utf-8")
        entry = JournalEntry(action="evolved", target=slug, reason=f"Hardened against '{cat}' patterns with pre-flight checks and automated verification", data={"path": str(target_file), "cluster": cat, "version": "v2"})
        self._record(entry)
        return entry

    def _apply_cluster_improvements(self, content: str, category: str, sample_reasons: list[str]) -> str:
        mitigations = {
            "Timeout": "### Step 0: Pre-flight Check & Task Partitioning\nPartition large operations into incremental sub-tasks to ensure execution within timeout bounds.\n",
            "Syntax / Type Error": "### Step 0: Static Analysis & Scaffolding Check\nRun linter and verify required imports/scaffolded files exist before modification.\n",
            "Missing Dependency / File": "### Step 0: Static Analysis & Scaffolding Check\nRun linter and verify required imports/scaffolded files exist before modification.\n",
            "Context Budget Exceeded": "### Step 0: Context Budget Optimization\nPrune non-essential context and restrict tool reads to targeted line ranges (≤ 40k budget).\n",
        }
        step0 = mitigations.get(category, "### Step 0: Pre-flight Verification\nVerify prerequisites, file presence, and environment readiness before initiating tasks.\n")
        evolved = "".join(line + (f"\n{step0}\n" if "## Steps" in line else "") for line in content.splitlines(keepends=True))
        if "### Step Final" not in evolved:
            evolved += "\n\n### Step Final: Post-execution Verification\nRun test suite and boundary audits to confirm zero regressions.\n"
        return evolved + f"\n<!-- evolved: v2 | date: {time.strftime('%Y-%m-%d %H:%M:%S')} | cluster: {category} -->\n"

    def get_journal(self, limit: int = 20) -> list[JournalEntry]:
        return self._journal[-limit:]

    def get_evolution_stats(self) -> dict[str, Any]:
        return {
            "total_generated": sum(1 for e in self._journal if e.action == "generated"), "total_deprecated": sum(1 for e in self._journal if e.action == "deprecated"),
            "total_evolved": sum(1 for e in self._journal if e.action == "evolved"), "journal_size": len(self._journal),
            "last_evolution": self._journal[-1].timestamp if self._journal else 0.0,
        }

    def _load_journal(self) -> None:
        if not self.journal_path.exists():
            self._journal = []
            return
        try:
            raw = self.journal_path.read_text(encoding="utf-8")
            data = (yaml.safe_load(raw) if _YAML_AVAILABLE else None) or json.loads(raw)
            self._journal = [JournalEntry(float(d.get("timestamp", 0.0)), str(d.get("action", "")), str(d.get("target", "")), str(d.get("reason", "")), dict(d.get("data", {}))) for d in data if isinstance(d, dict)] if isinstance(data, list) else []
        except Exception:
            self._journal = []

    def _save_journal(self) -> None:
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        data = [e.to_dict() for e in self._journal]
        try:
            self.journal_path.write_text(yaml.dump(data, default_flow_style=False) if _YAML_AVAILABLE else json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to save evolution journal to %s: %s", self.journal_path, exc)

    def _record(self, entry: JournalEntry) -> None:
        self._journal = (self._journal + [entry])[-self.MAX_JOURNAL:]
        self._save_journal()


__all__ = ["JournalEntry", "SelfImprover"]
