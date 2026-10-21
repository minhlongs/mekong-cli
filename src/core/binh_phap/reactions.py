# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Binh Phap Reactions — Event-driven command dispatch."""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from .topology import TopologyEngine, EscalationLevel


class EventSource(Enum):
    GITHUB = "github"
    POLAR = "polar"
    HEALTH = "health"
    METRICS = "metrics"
    CUSTOMER = "customer"
    MANUAL = "manual"
    CRON = "cron"


@dataclass
class Event:
    type: str
    source: EventSource
    data: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class Reaction:
    event_type: str
    chapter: int
    commands: list[str]
    escalation: EscalationLevel
    description: str
    condition: Optional[str] = None


def _evaluate_condition(condition: str, data: dict) -> bool:
    if "drop_percent" in condition:
        return data.get("drop_percent", 0) > 10
    return True


REACTIONS: list[Reaction] = [
    Reaction("ci.failed", 8, ["debug", "fix"], EscalationLevel.NOTIFY, "CI failed → Chapter 8 (adapt) → auto-fix"),
    Reaction("pr.changes_requested", 8, ["fix", "review"], EscalationLevel.NOTIFY, "Review changes requested → address feedback"),
    Reaction("pr.approved", 7, ["deploy"], EscalationLevel.APPROVE, "PR approved → Chapter 7 (maneuver) → deploy"),
    Reaction("issue.opened", 3, ["plan", "cook"], EscalationLevel.NOTIFY, "New issue → Chapter 3 (strategy) → plan and build"),
    Reaction("security.alert", 13, ["security", "audit", "fix"], EscalationLevel.APPROVE, "Security alert → Chapter 13 (intel) → audit and fix"),
    Reaction("subscription.created", 9, ["standup"], EscalationLevel.AUTONOMOUS, "New customer → Chapter 9 (march) → log progress"),
    Reaction("subscription.canceled", 8, ["debug"], EscalationLevel.NOTIFY, "Customer churned → Chapter 8 (adapt) → investigate why"),
    Reaction("credits.exhausted", 5, ["outreach"], EscalationLevel.AUTONOMOUS, "Credits exhausted → Chapter 5 (momentum) → upsell"),
    Reaction("credits.low", 5, ["content"], EscalationLevel.AUTONOMOUS, "Credits low → Chapter 5 → send usage report"),
    Reaction("mrr.dropped", 1, ["swot", "competitive"], EscalationLevel.APPROVE, "MRR dropped → Chapter 1 (calculate) → reassess strategy", "data.get('drop_percent', 0) > 10"),
    Reaction("mrr.milestone", 12, ["marketing", "content"], EscalationLevel.NOTIFY, "MRR milestone hit → Chapter 12 (fire) → amplify success"),
    Reaction("churn.spike", 6, ["research", "competitive", "fix"], EscalationLevel.APPROVE, "Churn spike → Chapter 6 (void) → find product gaps"),
    Reaction("health.degraded", 8, ["debug", "ops:health-sweep"], EscalationLevel.NOTIFY, "Health degraded → Chapter 8 → diagnose"),
    Reaction("health.down", 7, ["sre:incident", "release:hotfix"], EscalationLevel.APPROVE, "Service down → Chapter 7 (maneuver) → incident response"),
    Reaction("cron.daily", 9, ["standup", "health"], EscalationLevel.AUTONOMOUS, "Daily → Chapter 9 (march) → standup + health check"),
    Reaction("cron.weekly", 13, ["audit", "security"], EscalationLevel.AUTONOMOUS, "Weekly → Chapter 13 (intel) → audit + security scan"),
    Reaction("cron.monthly", 2, ["finance:monthly-close"], EscalationLevel.NOTIFY, "Monthly → Chapter 2 (resources) → financial close"),
    Reaction("cron.quarterly", 1, ["swot", "okr"], EscalationLevel.APPROVE, "Quarterly → Chapter 1 (calculate) → SWOT + OKR review"),
]

_REACTION_INDEX: dict[str, list[Reaction]] = {}
for _r in REACTIONS:
    _REACTION_INDEX.setdefault(_r.event_type, []).append(_r)


class ReactionEngine:
    """Event-driven command dispatcher — the nervous system of OpenClaw."""

    def __init__(self, topology: Optional[TopologyEngine] = None):
        self.topology = topology or TopologyEngine()
        self.event_log_path = Path(".mekong/events.jsonl")
        self.event_log_path.parent.mkdir(parents=True, exist_ok=True)

    def react(self, event: Event) -> list[dict]:
        self._log_event(event)
        actions = []
        for reaction in _REACTION_INDEX.get(event.type, []):
            if reaction.condition:
                try:
                    if not _evaluate_condition(reaction.condition, event.data):
                        continue
                except Exception:
                    continue
            actions.append({
                "event": event.type, "chapter": reaction.chapter, "commands": reaction.commands,
                "escalation": reaction.escalation.name,
                "needs_approval": reaction.escalation.value >= EscalationLevel.APPROVE.value,
                "llm": self.topology.get_llm_provider(reaction.commands[0]),
                "description": reaction.description,
            })
        if not actions:
            actions.append({
                "event": event.type, "chapter": 0, "commands": [],
                "escalation": "NONE", "needs_approval": False,
                "description": f"No reaction defined for event: {event.type}",
            })
        return actions

    def _log_event(self, event: Event) -> None:
        entry = {"type": event.type, "source": event.source.value, "data": event.data, "timestamp": event.timestamp}
        from src.core.file_lock import locked_append
        with locked_append(self.event_log_path) as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_pending_reactions(self, events: list[Event]) -> list[dict]:
        return [act for event in events for act in self.react(event)]

    def list_reactions(self) -> list[dict]:
        return [{"event": r.event_type, "chapter": r.chapter, "commands": r.commands, "escalation": r.escalation.name, "description": r.description} for r in REACTIONS]
