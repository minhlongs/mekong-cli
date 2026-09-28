# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - Self-Improvement & Recipe Evolution Engine.

Analyzes execution patterns from canonical memory and offline evals telemetry,
deprecates underperforming recipes, synthesizes new recipes from successful runs,
and evolves existing workflows based on diagnosed failure clusters.
Maintains an evolution journal in .mekong/journal.yaml (or JSON fallback).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore[import-untyped]
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from .event_bus import EventType, get_event_bus
from .evals_bridge import cluster_failures, get_evals_db_path, query_evals
from .memory_canonical import MemoryEntry, MemoryStore
from .recipe_gen import GeneratedRecipe, RecipeGenerator

logger = logging.getLogger(__name__)


@dataclass
class JournalEntry:
    """A single evolution journal record."""

    timestamp: float = field(default_factory=time.time)
    action: str = ""  # "generated" | "deprecated" | "suggestion" | "evolved"
    target: str = ""  # recipe name or goal
    reason: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "target": self.target,
            "reason": self.reason,
            "data": self.data,
        }


class SelfImprover:
    """Analyzes execution history and orchestrates autonomous workflow evolution."""

    MAX_JOURNAL: int = 500
    DEPRECATION_THRESHOLD: float = 0.20  # < 20% success rate
    MIN_RUNS_FOR_DEPRECATION: int = 5

    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        recipe_generator: Optional[RecipeGenerator] = None,
        journal_path: Optional[str] = None,
        evals_db_path: Optional[Path] = None,
    ) -> None:
        """
        Initialize the self-improvement engine.

        Args:
            memory_store: Long-term execution memory store.
            recipe_generator: Recipe generator and validator.
            journal_path: Path to YAML/JSON journal.
            evals_db_path: Optional path override for evals SQLite.
        """
        self.memory = memory_store or MemoryStore()
        self.generator = recipe_generator or RecipeGenerator()
        self.journal_path = Path(journal_path or ".mekong/journal.yaml")
        self.evals_db_path = evals_db_path or get_evals_db_path()
        self._journal: list[JournalEntry] = []
        self._load_journal()

    def analyze_and_improve(self) -> list[JournalEntry]:
        """
        Run the complete self-improvement & evolution cycle.

        1. Deprecate consistently failing recipes (< 20% success rate).
        2. Synthesize new recipes from high-performing manual goals.
        3. Evolve existing recipes that exhibit failure clusters.
        """
        new_entries: list[JournalEntry] = []

        # 1. Deprecate bad recipes
        deprecated = self.deprecate_bad_recipes()
        for name in deprecated:
            entry = JournalEntry(
                action="deprecated",
                target=name,
                reason="Success rate below 20% threshold across multiple runs",
                data={"recipe": name},
            )
            self._record(entry)
            new_entries.append(entry)

        # 2. Suggest & generate new recipes from successful executions
        suggestions = self.suggest_new_recipes()
        for goal in suggestions:
            # Look up successful memory entry
            matching = [
                e for e in self.memory.recent(100)
                if e.goal == goal and e.status == "success"
            ]
            if matching:
                entry_mem = matching[0]
                recipe = self.generator.from_successful_run(entry_mem)
                if recipe.valid:
                    path = self.generator.save_recipe(recipe)
                    entry = JournalEntry(
                        action="generated",
                        target=recipe.name,
                        reason=f"Auto-generated from successful goal execution: {goal}",
                        data={"path": path, "source_goal": goal},
                    )
                    self._record(entry)
                    new_entries.append(entry)

        # 3. Evolve recipes based on offline failure telemetry
        evolved_entries = self.evolve_failing_recipes()
        for entry in evolved_entries:
            self._record(entry)
            new_entries.append(entry)

        return new_entries

    def deprecate_bad_recipes(self) -> list[str]:
        """Identify recipes with success rates below threshold."""
        deprecated: list[str] = []
        entries = self.memory.recent(500)

        recipe_runs: dict[str, list[str]] = {}
        for e in entries:
            if e.recipe_used:
                recipe_runs.setdefault(e.recipe_used, []).append(e.status)

        bus = get_event_bus()
        for recipe_name, statuses in recipe_runs.items():
            if len(statuses) < self.MIN_RUNS_FOR_DEPRECATION:
                continue
            success_count = sum(1 for s in statuses if s == "success")
            success_rate = success_count / len(statuses)

            if success_rate < self.DEPRECATION_THRESHOLD:
                deprecated.append(recipe_name)
                if bus:
                    try:
                        bus.emit(
                            EventType.RECIPE_DEPRECATED,
                            {
                                "name": recipe_name,
                                "success_rate": success_rate,
                                "total_runs": len(statuses),
                            },
                        )
                    except Exception:
                        pass

        return deprecated

    def suggest_new_recipes(self) -> list[str]:
        """Find successful goals that executed without a predefined recipe."""
        entries = self.memory.recent(100)
        suggestions: list[str] = []
        seen_goals: set[str] = set()

        for e in entries:
            if e.status == "success" and not e.recipe_used and e.goal not in seen_goals:
                seen_goals.add(e.goal)
                suggestions.append(e.goal)

        return suggestions[:5]

    def evolve_failing_recipes(self) -> list[JournalEntry]:
        """
        Analyze offline evals clusters and evolve recipes to fix recurring failure modes.
        """
        evolved: list[JournalEntry] = []
        eval_data = query_evals(agent_id="all", window_days=14, db_path=self.evals_db_path)
        clusters = eval_data.get("failure_clusters", [])

        if not clusters:
            return evolved

        top_cluster = clusters[0]
        category = top_cluster.get("category", "")
        sample_reasons = top_cluster.get("sample_reasons", [])

        # Look for recipes in auto directory or common templates that need evolution
        auto_recipes = self.generator.list_auto_recipes()
        for item in auto_recipes[:3]:
            r_name = item.get("name", "")
            r_path = Path(item.get("path", ""))
            if not r_path.is_file():
                continue

            content = r_path.read_text(encoding="utf-8")
            if "<!-- evolved:" in content:
                continue  # Already evolved for this cycle

            evolved_content = self._apply_cluster_improvements(content, category, sample_reasons)
            r_path.write_text(evolved_content, encoding="utf-8")

            entry = JournalEntry(
                action="evolved",
                target=r_name,
                reason=f"Added mitigations for '{category}' failure cluster ({top_cluster.get('percentage')}% failures)",
                data={
                    "path": str(r_path),
                    "cluster": category,
                    "reasons": sample_reasons[:2],
                },
            )
            evolved.append(entry)

        return evolved

    def evolve_recipe(
        self,
        recipe_name: str,
        target_goal: str = "",
        force: bool = False,
    ) -> Optional[JournalEntry]:
        """
        Evolve a specific recipe by name with defensive error handling and verification steps.
        """
        slug = self.generator._slugify(recipe_name)
        auto_dir = Path(self.generator.AUTO_DIR)
        target_file = auto_dir / f"{slug}.md"

        if not target_file.exists():
            # If recipe does not exist, synthesize it first
            goal_text = target_goal or recipe_name
            recipe = self.generator.from_goal_pattern(
                goal_text,
                steps=[
                    "Validate environment and dependencies",
                    f"Execute primary goal: {goal_text}",
                    "Run verification tests and audit output",
                ],
            )
            saved_path = self.generator.save_recipe(recipe)
            entry = JournalEntry(
                action="generated",
                target=slug,
                reason=f"Synthesized initial recipe for evolution: {recipe_name}",
                data={"path": saved_path},
            )
            self._record(entry)
            return entry

        content = target_file.read_text(encoding="utf-8")
        if not force and "<!-- evolved: v2" in content:
            logger.info("Recipe %s already evolved to latest version", slug)
            return None

        eval_data = query_evals(agent_id="all", window_days=14, db_path=self.evals_db_path)
        clusters = eval_data.get("failure_clusters", [])
        category = clusters[0]["category"] if clusters else "General Hardening"
        reasons = clusters[0].get("sample_reasons", []) if clusters else []

        evolved_content = self._apply_cluster_improvements(content, category, reasons)
        target_file.write_text(evolved_content, encoding="utf-8")

        entry = JournalEntry(
            action="evolved",
            target=slug,
            reason=f"Hardened against '{category}' patterns with pre-flight checks and automated verification",
            data={
                "path": str(target_file),
                "cluster": category,
                "version": "v2",
            },
        )
        self._record(entry)
        return entry

    def _apply_cluster_improvements(
        self,
        content: str,
        category: str,
        sample_reasons: list[str],
    ) -> str:
        """Inject defensive checks and verification steps into recipe markdown."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        evolution_header = f"\n<!-- evolved: v2 | date: {timestamp} | cluster: {category} -->\n"

        mitigation_step = "### Step 0: Pre-flight Verification\nVerify prerequisites, file presence, and environment readiness before initiating tasks.\n"
        if category == "Timeout":
            mitigation_step = "### Step 0: Pre-flight Check & Task Partitioning\nPartition large operations into incremental sub-tasks to ensure execution within timeout bounds.\n"
        elif category in ("Syntax / Type Error", "Missing Dependency / File"):
            mitigation_step = "### Step 0: Static Analysis & Scaffolding Check\nRun linter and verify required imports/scaffolded files exist before modification.\n"
        elif category == "Context Budget Exceeded":
            mitigation_step = "### Step 0: Context Budget Optimization\nPrune non-essential context and restrict tool reads to targeted line ranges (≤ 40k budget).\n"

        verification_step = "\n### Step Final: Post-execution Verification\nRun test suite and boundary audits to confirm zero regressions.\n"

        lines = content.splitlines(keepends=True)
        new_lines: list[str] = []
        in_steps = False

        for line in lines:
            new_lines.append(line)
            if "## Steps" in line:
                in_steps = True
                new_lines.append(f"\n{mitigation_step}\n")

        evolved = "".join(new_lines)
        if "### Step Final" not in evolved:
            evolved += f"\n{verification_step}"

        evolved += f"{evolution_header}"
        return evolved

    def get_journal(self, limit: int = 20) -> list[JournalEntry]:
        """Return the most recent journal records."""
        return self._journal[-limit:]

    def get_evolution_stats(self) -> dict[str, Any]:
        """Compute summary statistics for the evolution journal."""
        generated = sum(1 for e in self._journal if e.action == "generated")
        deprecated = sum(1 for e in self._journal if e.action == "deprecated")
        evolved = sum(1 for e in self._journal if e.action == "evolved")
        return {
            "total_generated": generated,
            "total_deprecated": deprecated,
            "total_evolved": evolved,
            "journal_size": len(self._journal),
            "last_evolution": self._journal[-1].timestamp if self._journal else 0.0,
        }

    def _load_journal(self) -> None:
        """Load journal entries from YAML or JSON."""
        if not self.journal_path.exists():
            self._journal = []
            return

        try:
            raw = self.journal_path.read_text(encoding="utf-8")
            data = None
            if _YAML_AVAILABLE:
                data = yaml.safe_load(raw)
            if data is None:
                try:
                    data = json.loads(raw)
                except Exception:
                    data = []

            if isinstance(data, list):
                self._journal = [
                    JournalEntry(
                        timestamp=float(d.get("timestamp", 0.0)),
                        action=str(d.get("action", "")),
                        target=str(d.get("target", "")),
                        reason=str(d.get("reason", "")),
                        data=dict(d.get("data", {})),
                    )
                    for d in data if isinstance(d, dict)
                ]
        except Exception as exc:
            logger.debug("Failed to load self-improve journal from %s: %s", self.journal_path, exc)
            self._journal = []

    def _save_journal(self) -> None:
        """Persist journal entries to disk."""
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        data = [e.to_dict() for e in self._journal]
        try:
            if _YAML_AVAILABLE:
                self.journal_path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
            else:
                self.journal_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to save evolution journal to %s: %s", self.journal_path, exc)

    def _record(self, entry: JournalEntry) -> None:
        """Append an entry with FIFO eviction and persist."""
        self._journal.append(entry)
        if len(self._journal) > self.MAX_JOURNAL:
            self._journal = self._journal[-self.MAX_JOURNAL:]
        self._save_journal()


__all__ = [
    "JournalEntry",
    "SelfImprover",
]
