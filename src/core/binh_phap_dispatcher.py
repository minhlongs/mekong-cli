"""Binh Phap Dispatcher — Bridges 3D Topology Engine to PEV Orchestrator.

Translates topology dispatch decisions into orchestrator-compatible actions.
This is the integration layer: topology.py decides WHAT to run,
this module translates HOW to run it through the PEV pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from src.binh_phap.topology import (
    TopologyEngine,
    CommandResult,
    CycleLesson,
)
from src.binh_phap.reactions import (
    Event,
    EventSource,
    ReactionEngine,
)

logger = logging.getLogger(__name__)


# Command → recipe file mapping (commands that have JSON contracts)
def _find_recipe_path(command: str) -> Optional[Path]:
    """Find recipe/contract file for a command."""
    # Check factory contracts first
    contract = Path(f"factory/contracts/commands/{command}.json")
    if contract.exists():
        return contract
    # Check recipe files
    recipe = Path(f"recipes/{command}.md")
    if recipe.exists():
        return recipe
    return None


def _find_skill_path(command: str) -> Optional[Path]:
    """Find skill definition for a command."""
    # Namespaced commands: growth:experiment → growth/experiment
    parts = command.split(":")
    if len(parts) == 2:
        skill = Path(f".claude/skills/{parts[0]}-{parts[1]}/SKILL.md")
        if skill.exists():
            return skill
    skill = Path(f".claude/skills/{command}/SKILL.md")
    if skill.exists():
        return skill
    return None


class BinhPhapDispatcher:
    """Translates Binh Phap topology decisions into PEV orchestrator actions.

    Usage:
        dispatcher = BinhPhapDispatcher()
        action = dispatcher.next_action()
        # action contains: command, recipe_path, llm_provider, chapter, etc.

        # After execution:
        dispatcher.report_result(action["command"], success=True, output={})
    """

    def __init__(self, company_json: str = ".mekong/company.json") -> None:
        self.topology = TopologyEngine(company_json)
        self.reactions = ReactionEngine(self.topology)

    def next_action(self) -> dict[str, Any]:
        """Get next dispatch action translated for PEV orchestrator.

        Returns dict with keys:
            action: execute|execute_parallel|execute_loop|pause|stop
            command(s): str or list[str]
            recipe_path: Optional[Path] — recipe file if found
            skill_path: Optional[Path] — skill definition if found
            llm: str — provider to use (local_mlx, cloud_sonnet, cloud_opus)
            needs_approval: bool
            chapter: int — Binh Phap chapter number
            dimension: str — vertical|horizontal|diagonal
        """
        raw = self.topology.dispatch_next()
        action = raw.get("action", "unknown")

        if action == "execute":
            cmd = raw["command"]
            return {
                "action": "execute",
                "command": cmd,
                "recipe_path": _find_recipe_path(cmd),
                "skill_path": _find_skill_path(cmd),
                "llm": raw.get("llm", "local_mlx"),
                "needs_approval": raw.get("needs_approval", False),
                "chapter": raw.get("chapter", 0),
                "dimension": raw.get("dimension", "vertical"),
            }

        if action == "execute_parallel":
            cmds = raw.get("commands", [])
            return {
                "action": "execute_parallel",
                "commands": cmds,
                "recipes": {c: _find_recipe_path(c) for c in cmds},
                "skills": {c: _find_skill_path(c) for c in cmds},
                "group": raw.get("group", ""),
                "llm": raw.get("llm", []),
                "needs_approval": raw.get("needs_approval", False),
                "dimension": "horizontal",
            }

        if action == "execute_loop":
            cmds = raw.get("commands", [])
            return {
                "action": "execute_loop",
                "commands": cmds,
                "cycle": raw.get("cycle", 0),
                "previous_lessons": raw.get("previous_lessons", []),
                "dimension": "diagonal",
            }

        # pause or stop
        return raw

    def report_result(
        self,
        command: str,
        success: bool,
        output: dict | None = None,
        error: str = "",
        duration_ms: int = 0,
    ) -> None:
        """Report execution result back to topology engine."""
        result = CommandResult(
            command=command,
            chapter=self.topology._command_to_chapter(command),
            success=success,
            output_key=f"{command}_output",
            output_data=output or {},
            error=error,
            duration_ms=duration_ms,
        )

        dimension = self.topology.state.get("current_dimension", "vertical")

        if dimension == "vertical":
            self.topology.advance_vertical(result)
            if not success:
                self.topology.consecutive_failures += 1
            else:
                self.topology.consecutive_failures = 0

        elif dimension == "horizontal":
            # Find which group this command belongs to
            for name, group in self.topology.groups.items():
                if command in group.commands:
                    group.results.append(result)
                    # Check if all commands in group are done
                    if len(group.results) == len(group.commands):
                        self.topology.complete_group(name, group.results)
                    break

    def report_cycle_lesson(
        self,
        mrr: float,
        customers: int,
        lessons: list[str],
        adaptations: list[str] | None = None,
    ) -> None:
        """Record diagonal cycle lesson."""
        cycle = self.topology.state.get("cycle_number", 1)
        self.topology.record_cycle_lesson(CycleLesson(
            cycle=cycle,
            mrr=mrr,
            customers=customers,
            lessons=lessons,
            adaptations=adaptations or [],
        ))

    def handle_event(self, event_type: str, source: str = "manual", data: dict | None = None) -> list[dict]:
        """Process an external event through the reaction engine.

        Returns list of actions to execute.
        """
        try:
            src = EventSource(source)
        except ValueError:
            src = EventSource.MANUAL

        event = Event(type=event_type, source=src, data=data or {})
        return self.reactions.react(event)

    def get_status(self) -> dict[str, Any]:
        """Get current topology status for dashboard/CLI."""
        state = self.topology.state
        return {
            "dimension": state.get("current_dimension", "vertical"),
            "cycle": state.get("cycle_number", 0),
            "next_command": state.get("next_command", "swot"),
            "auto_dispatch": state.get("auto_dispatch", False),
            "target_mrr": state.get("target_mrr", 1000),
            "consecutive_failures": self.topology.consecutive_failures,
            "groups": {
                name: g.status.value
                for name, g in self.topology.groups.items()
            },
            "cycles_completed": len(state.get("cycle_history", [])),
        }
