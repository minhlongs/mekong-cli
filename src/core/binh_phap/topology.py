# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Binh Phap 3D Topology Engine — Vertical + Horizontal + Diagonal dispatch."""

from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import time
from typing import Optional


class Dimension(Enum):
    VERTICAL, HORIZONTAL, DIAGONAL = "vertical", "horizontal", "diagonal"


class EscalationLevel(Enum):
    AUTONOMOUS, NOTIFY, APPROVE, STRATEGIC = 0, 1, 2, 3


class GroupStatus(Enum):
    PENDING, IN_PROGRESS, COMPLETED, FAILED = "pending", "in_progress", "completed", "failed"


@dataclass
class CommandResult:
    command: str
    chapter: int
    success: bool
    output_key: str
    output_data: dict = field(default_factory=dict)
    error: str = ""
    duration_ms: int = 0


@dataclass
class CycleLesson:
    cycle: int
    mrr: float
    customers: int
    channels_tested: int = 0
    lessons: list[str] = field(default_factory=list)
    adaptations: list[str] = field(default_factory=list)


@dataclass
class BattleGroup:
    name: str
    commands: list[str]
    depends_on: list[str] = field(default_factory=list)
    status: GroupStatus = GroupStatus.PENDING
    results: list[CommandResult] = field(default_factory=list)
    merge_output_key: str = ""

    def all_deps_completed(self, groups: dict[str, "BattleGroup"]) -> bool:
        return all(groups[dep].status == GroupStatus.COMPLETED for dep in self.depends_on if dep in groups)


CHAPTER_COMMANDS: dict[int, list[str]] = {
    1: ["swot", "annual", "founder:validate", "okr", "venture:five-factors"], 2: ["finance", "budget", "pricing", "finance:monthly-close"], 3: ["plan", "brainstorm", "scope", "product:discovery", "ask"], 4: ["cook", "code", "test", "review", "fix"],
    5: ["marketing", "sales", "growth:experiment", "content", "launch"], 6: ["research", "competitive", "venture:void-substance", "scout"], 7: ["deploy", "fix", "release:hotfix", "release:ship"], 8: ["debug", "sre:incident", "devops:rollback", "ops:health-sweep"],
    9: ["sprint", "standup", "milestone", "backlog"], 10: ["market", "venture:terrain", "positioning", "tam"], 11: ["fundraise", "founder:negotiate", "founder:validate", "pivot"], 12: ["campaign", "outreach", "launch", "growth:channel-optimize"], 13: ["audit", "scout", "health", "status", "security"],
}
ESCALATION_MAP: dict[str, EscalationLevel] = {**{k: EscalationLevel.AUTONOMOUS for k in ("standup", "health", "status", "audit", "scout")}, **{k: EscalationLevel.NOTIFY for k in ("cook", "deploy", "fix", "marketing", "sales", "test")}, **{k: EscalationLevel.APPROVE for k in ("launch", "pricing", "fundraise")}, **{k: EscalationLevel.STRATEGIC for k in ("pivot", "founder:raise")}}
COMMERCIAL_CHAPTERS: frozenset[int] = frozenset({1, 2, 5, 11, 12})
LLM_ROUTING: dict[EscalationLevel, str] = {EscalationLevel.AUTONOMOUS: "local_mlx", EscalationLevel.NOTIFY: "local_mlx", EscalationLevel.APPROVE: "cloud_sonnet", EscalationLevel.STRATEGIC: "cloud_opus"}
DEFAULT_BATTLE_GROUPS: dict[str, dict] = {"alpha": {"commands": ["swot", "audit", "venture:terrain"], "depends_on": [], "merge_output_key": "intelligence_brief"}, "beta": {"commands": ["plan", "competitive"], "depends_on": ["alpha"], "merge_output_key": "strategy_brief"}, "gamma": {"commands": ["cook", "marketing", "sprint"], "depends_on": ["beta"], "merge_output_key": "delivery_package"}, "delta": {"commands": ["launch", "deploy", "audit"], "depends_on": ["gamma"], "merge_output_key": "campaign_result"}}
DIAGONAL_LOOP: list[str] = ["audit", "swot", "plan", "cook", "growth:experiment", "launch"]


class TopologyEngine:
    """3D command dispatch engine — vertical, horizontal, diagonal."""
    def __init__(self, company_json_path: str = ".mekong/company.json"):
        self.company_path = Path(company_json_path)
        default_state = {"topology": "3d", "current_dimension": "vertical", "cycle_number": 0, "cycle_history": [], "current_groups": {}, "next_command": "swot", "auto_dispatch": False, "target_mrr": 1000, "commerce_mode": True, "revenue_events": [], "last_mrr_update": None}
        self.state = json.loads(self.company_path.read_text()).get("binh_phap_state", default_state) if self.company_path.exists() else default_state
        saved = self.state.get("current_groups", {})
        self.groups = {name: BattleGroup(name=name, commands=cfg["commands"], depends_on=cfg["depends_on"], status=GroupStatus(saved.get(name, "pending")), merge_output_key=cfg["merge_output_key"]) for name, cfg in DEFAULT_BATTLE_GROUPS.items()}
        self.consecutive_failures, self.max_failures = 0, 3

    def save_state(self) -> None:
        data = json.loads(self.company_path.read_text()) if self.company_path.exists() else {}
        self.company_path.parent.mkdir(parents=True, exist_ok=True)
        self.state["current_groups"] = {name: g.status.value for name, g in self.groups.items()}
        data["binh_phap_state"] = self.state
        self.company_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    def get_escalation(self, command: str) -> EscalationLevel:
        return ESCALATION_MAP.get(command, EscalationLevel.NOTIFY)
    def get_llm_provider(self, command: str) -> str:
        return LLM_ROUTING[self.get_escalation(command)]
    def needs_human_approval(self, command: str) -> bool:
        return self.get_escalation(command).value >= EscalationLevel.APPROVE.value
    def get_vertical_chain(self) -> list[str]:
        return ["swot", "plan", "cook", "test", "deploy", "audit"]
    def next_vertical_command(self) -> Optional[str]:
        chain = self.get_vertical_chain()
        return chain[chain.index(cur)] if (cur := self.state.get("next_command", chain[0])) in chain else chain[0]
    def advance_vertical(self, result: CommandResult) -> Optional[str]:
        chain = self.get_vertical_chain()
        if result.command in chain and chain.index(result.command) + 1 < len(chain):
            self.state["next_command"] = chain[chain.index(result.command) + 1]
            self.save_state()
            return self.state["next_command"]
        return None
    def get_ready_groups(self) -> list[BattleGroup]:
        return [g for g in self.groups.values() if g.status == GroupStatus.PENDING and g.all_deps_completed(self.groups)]
    def start_group(self, group_name: str) -> list[str]:
        if not (group := self.groups.get(group_name)):
            return []
        group.status = GroupStatus.IN_PROGRESS
        self.save_state()
        return group.commands
    def complete_group(self, group_name: str, results: list[CommandResult]) -> None:
        if group := self.groups.get(group_name):
            group.results, all_ok = results, all(r.success for r in results)
            group.status = GroupStatus.COMPLETED if all_ok else GroupStatus.FAILED
            self.consecutive_failures = 0 if all_ok else self.consecutive_failures + 1
            self.save_state()
    def start_diagonal_cycle(self) -> list[str]:
        self.state.update({"current_dimension": "diagonal", "cycle_number": self.state.get("cycle_number", 0) + 1, "next_command": DIAGONAL_LOOP[0]})
        self.save_state()
        return DIAGONAL_LOOP
    def record_mrr_event(self, **kwargs) -> None:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.state.setdefault("revenue_events", []).append({"tx_id": kwargs.get("tx_id"), "amount": kwargs.get("amount"), "customer_id": kwargs.get("customer_id"), "product_id": kwargs.get("product_id"), "timestamp": now})
        self.state["last_mrr_update"] = now
        self.save_state()
    def record_cycle_lesson(self, lesson: CycleLesson) -> None:
        self.state.setdefault("cycle_history", []).append({"cycle": lesson.cycle, "result": {"mrr": lesson.mrr, "customers": lesson.customers, "channels_tested": lesson.channels_tested}, "lessons": lesson.lessons, "adaptations": lesson.adaptations, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        self.save_state()
    def should_continue_diagonal(self) -> bool:
        history = self.state.get("cycle_history", [])
        return self.consecutive_failures < self.max_failures and bool(self.state.get("auto_dispatch", False)) and not (history and history[-1]["result"]["mrr"] >= self.state.get("target_mrr", 1000))
    def get_previous_lessons(self) -> list[str]:
        return [item for c in self.state.get("cycle_history", []) for item in c.get("lessons", [])]
    def get_previous_adaptations(self) -> list[str]:
        return [item for c in self.state.get("cycle_history", []) for item in c.get("adaptations", [])]
    def _command_to_chapter(self, command: str) -> int:
        return next((ch for ch, cmds in CHAPTER_COMMANDS.items() if command in cmds), 0)

    def dispatch_next(self) -> dict:
        if self.consecutive_failures >= self.max_failures:
            return {"action": "stop", "reason": f"{self.max_failures} consecutive failures", "recommendation": "Chapter 8: Nine Variations — adapt strategy"}
        dim = self.state.get("current_dimension", "vertical")
        if dim == "vertical":
            if cmd := self.next_vertical_command():
                ch = self._command_to_chapter(cmd)
                res = {"action": "execute", "dimension": "vertical", "command": cmd, "llm": self.get_llm_provider(cmd), "needs_approval": self.needs_human_approval(cmd), "chapter": ch}
                return {**res, "llm": LLM_ROUTING[EscalationLevel.STRATEGIC], "needs_approval": True} if ch in COMMERCIAL_CHAPTERS else res
            self.state["current_dimension"] = "horizontal"
            self.save_state()
            return self.dispatch_next()
        if dim == "horizontal":
            if ready := self.get_ready_groups():
                cmds = self.start_group(ready[0].name)
                res = {"action": "execute_parallel", "dimension": "horizontal", "group": ready[0].name, "commands": cmds, "llm": [self.get_llm_provider(c) for c in cmds], "needs_approval": any(self.needs_human_approval(c) for c in cmds)}
                return {**res, "llm": [LLM_ROUTING[EscalationLevel.STRATEGIC]] * len(cmds), "needs_approval": True} if any(self._command_to_chapter(c) in COMMERCIAL_CHAPTERS for c in cmds) else res
            self.state["current_dimension"] = "diagonal"
            self.save_state()
            return self.dispatch_next()
        if dim == "diagonal":
            if not self.should_continue_diagonal():
                return {"action": "pause", "reason": "Diagonal loop paused", "cycle": self.state.get("cycle_number", 0), "lessons": self.get_previous_lessons()[-5:]}
            loop = self.start_diagonal_cycle()
            res = {"action": "execute_loop", "dimension": "diagonal", "cycle": self.state.get("cycle_number", 0), "commands": loop, "previous_lessons": self.get_previous_lessons()[-3:], "previous_adaptations": self.get_previous_adaptations()[-3:]}
            return {**res, "llm": LLM_ROUTING[EscalationLevel.STRATEGIC], "needs_approval": True, "commercial_loop": True} if any(self._command_to_chapter(c) in COMMERCIAL_CHAPTERS for c in loop) else res
        return {"action": "unknown", "dimension": dim}
