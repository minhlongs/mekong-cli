"""
Binh Phap Reactions — Event-driven command dispatch.

Inspired by Composio's reaction system. When events happen,
OpenClaw automatically dispatches the right Binh Phap chapter.

Events come from: GitHub webhooks, Polar webhooks, health checks,
MRR tracking, customer actions, CI/CD pipelines.
"""

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
    """An event that triggers a reaction."""
    type: str
    source: EventSource
    data: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class Reaction:
    """A reaction to an event — maps event → chapter → commands."""
    event_type: str
    chapter: int
    commands: list[str]
    escalation: EscalationLevel
    description: str
    condition: Optional[str] = None  # Python expression evaluated against event.data


# Event → Reaction mapping (the nervous system)
REACTIONS: list[Reaction] = [
    # ── GitHub Events ──
    Reaction(
        event_type="ci.failed",
        chapter=8,
        commands=["debug", "fix"],
        escalation=EscalationLevel.NOTIFY,
        description="CI failed → Chapter 8 (adapt) → auto-fix",
    ),
    Reaction(
        event_type="pr.changes_requested",
        chapter=8,
        commands=["fix", "review"],
        escalation=EscalationLevel.NOTIFY,
        description="Review changes requested → address feedback",
    ),
    Reaction(
        event_type="pr.approved",
        chapter=7,
        commands=["deploy"],
        escalation=EscalationLevel.APPROVE,
        description="PR approved → Chapter 7 (maneuver) → deploy",
    ),
    Reaction(
        event_type="issue.opened",
        chapter=3,
        commands=["plan", "cook"],
        escalation=EscalationLevel.NOTIFY,
        description="New issue → Chapter 3 (strategy) → plan and build",
    ),
    Reaction(
        event_type="security.alert",
        chapter=13,
        commands=["security", "audit", "fix"],
        escalation=EscalationLevel.APPROVE,
        description="Security alert → Chapter 13 (intel) → audit and fix",
    ),

    # ── Polar/Revenue Events ──
    Reaction(
        event_type="subscription.created",
        chapter=9,
        commands=["standup"],
        escalation=EscalationLevel.AUTONOMOUS,
        description="New customer → Chapter 9 (march) → log progress",
    ),
    Reaction(
        event_type="subscription.canceled",
        chapter=8,
        commands=["debug"],
        escalation=EscalationLevel.NOTIFY,
        description="Customer churned → Chapter 8 (adapt) → investigate why",
    ),
    Reaction(
        event_type="credits.exhausted",
        chapter=5,
        commands=["outreach"],
        escalation=EscalationLevel.AUTONOMOUS,
        description="Credits exhausted → Chapter 5 (momentum) → upsell",
    ),
    Reaction(
        event_type="credits.low",
        chapter=5,
        commands=["content"],
        escalation=EscalationLevel.AUTONOMOUS,
        description="Credits low → Chapter 5 → send usage report",
    ),

    # ── Metrics Events ──
    Reaction(
        event_type="mrr.dropped",
        chapter=1,
        commands=["swot", "competitive"],
        escalation=EscalationLevel.APPROVE,
        description="MRR dropped → Chapter 1 (calculate) → reassess strategy",
        condition="data.get('drop_percent', 0) > 10",
    ),
    Reaction(
        event_type="mrr.milestone",
        chapter=12,
        commands=["marketing", "content"],
        escalation=EscalationLevel.NOTIFY,
        description="MRR milestone hit → Chapter 12 (fire) → amplify success",
    ),
    Reaction(
        event_type="churn.spike",
        chapter=6,
        commands=["research", "competitive", "fix"],
        escalation=EscalationLevel.APPROVE,
        description="Churn spike → Chapter 6 (void) → find product gaps",
    ),

    # ── Health Events ──
    Reaction(
        event_type="health.degraded",
        chapter=8,
        commands=["debug", "ops:health-sweep"],
        escalation=EscalationLevel.NOTIFY,
        description="Health degraded → Chapter 8 → diagnose",
    ),
    Reaction(
        event_type="health.down",
        chapter=7,
        commands=["sre:incident", "release:hotfix"],
        escalation=EscalationLevel.APPROVE,
        description="Service down → Chapter 7 (maneuver) → incident response",
    ),

    # ── Cron Events (scheduled) ──
    Reaction(
        event_type="cron.daily",
        chapter=9,
        commands=["standup", "health"],
        escalation=EscalationLevel.AUTONOMOUS,
        description="Daily → Chapter 9 (march) → standup + health check",
    ),
    Reaction(
        event_type="cron.weekly",
        chapter=13,
        commands=["audit", "security"],
        escalation=EscalationLevel.AUTONOMOUS,
        description="Weekly → Chapter 13 (intel) → audit + security scan",
    ),
    Reaction(
        event_type="cron.monthly",
        chapter=2,
        commands=["finance:monthly-close"],
        escalation=EscalationLevel.NOTIFY,
        description="Monthly → Chapter 2 (resources) → financial close",
    ),
    Reaction(
        event_type="cron.quarterly",
        chapter=1,
        commands=["swot", "okr"],
        escalation=EscalationLevel.APPROVE,
        description="Quarterly → Chapter 1 (calculate) → SWOT + OKR review",
    ),
]

# Index for fast lookup
_REACTION_INDEX: dict[str, list[Reaction]] = {}
for r in REACTIONS:
    _REACTION_INDEX.setdefault(r.event_type, []).append(r)


class ReactionEngine:
    """Event-driven command dispatcher — the nervous system of OpenClaw."""

    def __init__(self, topology: Optional[TopologyEngine] = None):
        self.topology = topology or TopologyEngine()
        self.event_log_path = Path(".mekong/events.jsonl")
        self.event_log_path.parent.mkdir(parents=True, exist_ok=True)

    def react(self, event: Event) -> list[dict]:
        """Process an event and return dispatch actions.

        Returns list of actions to execute (may be multiple reactions).
        """
        self._log_event(event)
        reactions = _REACTION_INDEX.get(event.type, [])
        actions = []

        for reaction in reactions:
            # Check condition if present
            if reaction.condition:
                try:
                    data = event.data
                    if not eval(reaction.condition, {"data": data}):
                        continue
                except Exception:
                    continue

            # Check escalation — does this need human approval?
            needs_approval = reaction.escalation.value >= EscalationLevel.APPROVE.value
            llm = self.topology.get_llm_provider(reaction.commands[0])

            actions.append({
                "event": event.type,
                "chapter": reaction.chapter,
                "commands": reaction.commands,
                "escalation": reaction.escalation.name,
                "needs_approval": needs_approval,
                "llm": llm,
                "description": reaction.description,
            })

        if not actions:
            actions.append({
                "event": event.type,
                "chapter": 0,
                "commands": [],
                "escalation": "NONE",
                "needs_approval": False,
                "description": f"No reaction defined for event: {event.type}",
            })

        return actions

    def _log_event(self, event: Event) -> None:
        """Append event to JSONL log for audit trail."""
        entry = {
            "type": event.type,
            "source": event.source.value,
            "data": event.data,
            "timestamp": event.timestamp,
        }
        with open(self.event_log_path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_pending_reactions(self, events: list[Event]) -> list[dict]:
        """Process multiple events and return all pending actions."""
        all_actions = []
        for event in events:
            all_actions.extend(self.react(event))
        return all_actions

    def list_reactions(self) -> list[dict]:
        """List all registered reactions for inspection."""
        return [
            {
                "event": r.event_type,
                "chapter": r.chapter,
                "commands": r.commands,
                "escalation": r.escalation.name,
                "description": r.description,
            }
            for r in REACTIONS
        ]
