"""
Binh Phap 3D Topology Engine — Vertical + Horizontal + Diagonal dispatch.

The nuclear fusion reactor: each cycle costs ~$0 (local LLM),
produces compound growth via self-improving feedback loops.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Dimension(Enum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    DIAGONAL = "diagonal"


class EscalationLevel(Enum):
    AUTONOMOUS = 0  # Local LLM, no human needed
    NOTIFY = 1  # Local LLM, notify human
    APPROVE = 2  # Cloud Sonnet, human approves
    STRATEGIC = 3  # Cloud Opus, human initiates


class GroupStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CommandResult:
    """Result of a single command execution."""
    command: str
    chapter: int
    success: bool
    output_key: str
    output_data: dict = field(default_factory=dict)
    error: str = ""
    duration_ms: int = 0


@dataclass
class CycleLesson:
    """What we learned from one diagonal cycle."""
    cycle: int
    mrr: float
    customers: int
    channels_tested: int = 0
    lessons: list[str] = field(default_factory=list)
    adaptations: list[str] = field(default_factory=list)


# Chapter → Command mapping (from BINH_PHAP_MASTER.md)
CHAPTER_COMMANDS: dict[int, list[str]] = {
    1: ["swot", "annual", "founder:validate", "okr", "venture:five-factors"],
    2: ["finance", "budget", "pricing", "finance:monthly-close"],
    3: ["plan", "brainstorm", "scope", "product:discovery", "ask"],
    4: ["cook", "code", "test", "review", "fix"],
    5: ["marketing", "sales", "growth:experiment", "content", "launch"],
    6: ["research", "competitive", "venture:void-substance", "scout"],
    7: ["deploy", "fix", "release:hotfix", "release:ship"],
    8: ["debug", "sre:incident", "devops:rollback", "ops:health-sweep"],
    9: ["sprint", "standup", "milestone", "backlog"],
    10: ["market", "venture:terrain", "positioning", "tam"],
    11: ["fundraise", "founder:negotiate", "founder:validate", "pivot"],
    12: ["campaign", "outreach", "launch", "growth:channel-optimize"],
    13: ["audit", "scout", "health", "status", "security"],
}

# Escalation routing
ESCALATION_MAP: dict[str, EscalationLevel] = {
    "standup": EscalationLevel.AUTONOMOUS,
    "health": EscalationLevel.AUTONOMOUS,
    "status": EscalationLevel.AUTONOMOUS,
    "audit": EscalationLevel.AUTONOMOUS,
    "scout": EscalationLevel.AUTONOMOUS,
    "cook": EscalationLevel.NOTIFY,
    "deploy": EscalationLevel.NOTIFY,
    "fix": EscalationLevel.NOTIFY,
    "marketing": EscalationLevel.NOTIFY,
    "sales": EscalationLevel.NOTIFY,
    "test": EscalationLevel.NOTIFY,
    "launch": EscalationLevel.APPROVE,
    "pricing": EscalationLevel.APPROVE,
    "fundraise": EscalationLevel.APPROVE,
    "pivot": EscalationLevel.STRATEGIC,
    "founder:raise": EscalationLevel.STRATEGIC,
}

# LLM routing by escalation level
LLM_ROUTING: dict[EscalationLevel, str] = {
    EscalationLevel.AUTONOMOUS: "local_mlx",
    EscalationLevel.NOTIFY: "local_mlx",
    EscalationLevel.APPROVE: "cloud_sonnet",
    EscalationLevel.STRATEGIC: "cloud_opus",
}


@dataclass
class BattleGroup:
    """A group of commands that execute in parallel."""
    name: str
    commands: list[str]
    depends_on: list[str] = field(default_factory=list)
    status: GroupStatus = GroupStatus.PENDING
    results: list[CommandResult] = field(default_factory=list)
    merge_output_key: str = ""

    def all_deps_completed(self, groups: dict[str, "BattleGroup"]) -> bool:
        return all(
            groups[dep].status == GroupStatus.COMPLETED
            for dep in self.depends_on
            if dep in groups
        )


# Default battle groups (horizontal dimension)
DEFAULT_BATTLE_GROUPS: dict[str, dict] = {
    "alpha": {
        "commands": ["swot", "audit", "venture:terrain"],
        "depends_on": [],
        "merge_output_key": "intelligence_brief",
    },
    "beta": {
        "commands": ["plan", "competitive"],
        "depends_on": ["alpha"],
        "merge_output_key": "strategy_brief",
    },
    "gamma": {
        "commands": ["cook", "marketing", "sprint"],
        "depends_on": ["beta"],
        "merge_output_key": "delivery_package",
    },
    "delta": {
        "commands": ["launch", "deploy", "audit"],
        "depends_on": ["gamma"],
        "merge_output_key": "campaign_result",
    },
}

# Diagonal loop sequence
DIAGONAL_LOOP: list[str] = ["audit", "swot", "plan", "cook", "growth:experiment", "launch"]


class TopologyEngine:
    """3D command dispatch engine — vertical, horizontal, diagonal."""

    def __init__(self, company_json_path: str = ".mekong/company.json"):
        self.company_path = Path(company_json_path)
        self.state = self._load_state()
        self.groups = self._init_groups()
        self.consecutive_failures = 0
        self.max_failures = 3

    def _load_state(self) -> dict:
        """Load binh_phap_state from company.json, or create default."""
        if self.company_path.exists():
            data = json.loads(self.company_path.read_text())
            return data.get("binh_phap_state", self._default_state())
        return self._default_state()

    def _default_state(self) -> dict:
        return {
            "topology": "3d",
            "current_dimension": "vertical",
            "cycle_number": 0,
            "cycle_history": [],
            "current_groups": {},
            "next_command": "swot",
            "auto_dispatch": False,
            "target_mrr": 1000,
        }

    def _init_groups(self) -> dict[str, BattleGroup]:
        """Initialize battle groups from defaults or saved state."""
        groups = {}
        saved = self.state.get("current_groups", {})
        for name, config in DEFAULT_BATTLE_GROUPS.items():
            status = GroupStatus(saved.get(name, "pending"))
            groups[name] = BattleGroup(
                name=name,
                commands=config["commands"],
                depends_on=config["depends_on"],
                status=status,
                merge_output_key=config["merge_output_key"],
            )
        return groups

    def save_state(self) -> None:
        """Persist binh_phap_state back to company.json."""
        if self.company_path.exists():
            data = json.loads(self.company_path.read_text())
        else:
            self.company_path.parent.mkdir(parents=True, exist_ok=True)
            data = {}

        self.state["current_groups"] = {
            name: g.status.value for name, g in self.groups.items()
        }
        data["binh_phap_state"] = self.state
        self.company_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # ── Escalation ──

    def get_escalation(self, command: str) -> EscalationLevel:
        """Determine escalation level for a command."""
        return ESCALATION_MAP.get(command, EscalationLevel.NOTIFY)

    def get_llm_provider(self, command: str) -> str:
        """Route to appropriate LLM based on escalation level."""
        level = self.get_escalation(command)
        return LLM_ROUTING[level]

    def needs_human_approval(self, command: str) -> bool:
        """Check if command requires human approval before execution."""
        level = self.get_escalation(command)
        return level.value >= EscalationLevel.APPROVE.value

    # ── Vertical Dispatch ──

    def get_vertical_chain(self) -> list[str]:
        """Get the sequential command chain for vertical execution."""
        return ["swot", "plan", "cook", "test", "deploy", "audit"]

    def next_vertical_command(self) -> Optional[str]:
        """Get next command in vertical chain."""
        chain = self.get_vertical_chain()
        current = self.state.get("next_command", chain[0])
        if current in chain:
            idx = chain.index(current)
            return chain[idx] if idx < len(chain) else None
        return chain[0]

    def advance_vertical(self, result: CommandResult) -> Optional[str]:
        """Move to next vertical command after completion."""
        chain = self.get_vertical_chain()
        if result.command in chain:
            idx = chain.index(result.command)
            if idx + 1 < len(chain):
                next_cmd = chain[idx + 1]
                self.state["next_command"] = next_cmd
                self.save_state()
                return next_cmd
        return None

    # ── Horizontal Dispatch ──

    def get_ready_groups(self) -> list[BattleGroup]:
        """Get battle groups ready for parallel execution."""
        ready = []
        for group in self.groups.values():
            if group.status == GroupStatus.PENDING and group.all_deps_completed(self.groups):
                ready.append(group)
        return ready

    def start_group(self, group_name: str) -> list[str]:
        """Start a battle group, return its commands for parallel execution."""
        group = self.groups.get(group_name)
        if not group:
            return []
        group.status = GroupStatus.IN_PROGRESS
        self.save_state()
        return group.commands

    def complete_group(self, group_name: str, results: list[CommandResult]) -> None:
        """Mark a battle group as completed with results."""
        group = self.groups.get(group_name)
        if not group:
            return
        group.results = results
        all_ok = all(r.success for r in results)
        group.status = GroupStatus.COMPLETED if all_ok else GroupStatus.FAILED
        if not all_ok:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
        self.save_state()

    # ── Diagonal Loop (Nuclear Fusion) ──

    def start_diagonal_cycle(self) -> list[str]:
        """Start a new diagonal improvement cycle."""
        self.state["current_dimension"] = "diagonal"
        self.state["cycle_number"] = self.state.get("cycle_number", 0) + 1
        self.state["next_command"] = DIAGONAL_LOOP[0]
        self.save_state()
        return DIAGONAL_LOOP

    def record_cycle_lesson(self, lesson: CycleLesson) -> None:
        """Record what we learned from this cycle."""
        history = self.state.get("cycle_history", [])
        history.append({
            "cycle": lesson.cycle,
            "result": {
                "mrr": lesson.mrr,
                "customers": lesson.customers,
                "channels_tested": lesson.channels_tested,
            },
            "lessons": lesson.lessons,
            "adaptations": lesson.adaptations,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        self.state["cycle_history"] = history
        self.save_state()

    def should_continue_diagonal(self) -> bool:
        """Check if diagonal loop should continue or stop."""
        if self.consecutive_failures >= self.max_failures:
            return False
        if not self.state.get("auto_dispatch", False):
            return False
        # Check if target MRR reached
        history = self.state.get("cycle_history", [])
        if history:
            last = history[-1]
            if last["result"]["mrr"] >= self.state.get("target_mrr", 1000):
                return False
        return True

    def get_previous_lessons(self) -> list[str]:
        """Get lessons from all previous cycles for adaptation."""
        lessons = []
        for cycle in self.state.get("cycle_history", []):
            lessons.extend(cycle.get("lessons", []))
        return lessons

    def get_previous_adaptations(self) -> list[str]:
        """Get adaptations applied in previous cycles."""
        adaptations = []
        for cycle in self.state.get("cycle_history", []):
            adaptations.extend(cycle.get("adaptations", []))
        return adaptations

    # ── Unified Dispatch ──

    def dispatch_next(self) -> dict:
        """Main dispatch logic — decides what to run next across all 3 dimensions."""

        # Safety: too many failures → stop
        if self.consecutive_failures >= self.max_failures:
            return {
                "action": "stop",
                "reason": f"{self.max_failures} consecutive failures",
                "recommendation": "Chapter 8: Nine Variations — adapt strategy",
            }

        dimension = self.state.get("current_dimension", "vertical")

        if dimension == "vertical":
            cmd = self.next_vertical_command()
            if cmd:
                return {
                    "action": "execute",
                    "dimension": "vertical",
                    "command": cmd,
                    "llm": self.get_llm_provider(cmd),
                    "needs_approval": self.needs_human_approval(cmd),
                    "chapter": self._command_to_chapter(cmd),
                }
            # Vertical chain complete → switch to horizontal
            self.state["current_dimension"] = "horizontal"
            self.save_state()
            return self.dispatch_next()

        if dimension == "horizontal":
            ready = self.get_ready_groups()
            if ready:
                group = ready[0]
                cmds = self.start_group(group.name)
                return {
                    "action": "execute_parallel",
                    "dimension": "horizontal",
                    "group": group.name,
                    "commands": cmds,
                    "llm": [self.get_llm_provider(c) for c in cmds],
                    "needs_approval": any(self.needs_human_approval(c) for c in cmds),
                }
            # All groups done → switch to diagonal
            self.state["current_dimension"] = "diagonal"
            self.save_state()
            return self.dispatch_next()

        if dimension == "diagonal":
            if not self.should_continue_diagonal():
                return {
                    "action": "pause",
                    "reason": "Diagonal loop paused",
                    "cycle": self.state.get("cycle_number", 0),
                    "lessons": self.get_previous_lessons()[-5:],
                }
            loop = self.start_diagonal_cycle()
            return {
                "action": "execute_loop",
                "dimension": "diagonal",
                "cycle": self.state.get("cycle_number", 0),
                "commands": loop,
                "previous_lessons": self.get_previous_lessons()[-3:],
                "previous_adaptations": self.get_previous_adaptations()[-3:],
            }

        return {"action": "unknown", "dimension": dimension}

    def _command_to_chapter(self, command: str) -> int:
        """Find which chapter a command belongs to."""
        for chapter, cmds in CHAPTER_COMMANDS.items():
            if command in cmds:
                return chapter
        return 0
