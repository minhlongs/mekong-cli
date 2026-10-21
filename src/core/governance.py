# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Mekong CLI - Governance Layer."""

from __future__ import annotations

import logging
import os
import re
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from .event_bus import EventType, get_event_bus

logger = logging.getLogger(__name__)


class ActionClass(str, Enum):
    SAFE = "safe"
    REVIEW_REQUIRED = "review_required"
    FORBIDDEN = "forbidden"


@dataclass
class GovernanceDecision:
    action_class: ActionClass
    reason: str
    requires_approval: bool = False
    approved: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass
class AuditEntry:
    timestamp: float = field(default_factory=time.time)
    goal: str = ""
    action_class: str = ""
    approved: bool = False
    result: str = ""


class Governance:
    """Safety governance layer for autonomous operations."""

    FORBIDDEN_PATTERNS: list[str] = [
        r"\brm\s+-rf\b", r"\bdrop\s+(database|table)\b", r"\bdelete\s+all\b",
        r"\bdestroy\b", r"\bformat\b", r"\btruncate\b",
    ]
    REVIEW_PATTERNS: list[str] = [
        r"\bdeploy\b.*\bprod", r"\bpush\b.*\bmain\b", r"\bmodify\b.*\bconfig\b",
        r"\bupdate\b.*\bdns\b", r"\bmigrate\b",
    ]
    RISK_LEVEL_MAP: dict[str, ActionClass] = {
        "LOW": ActionClass.SAFE, "MEDIUM": ActionClass.SAFE,
        "HIGH": ActionClass.REVIEW_REQUIRED, "CRITICAL": ActionClass.FORBIDDEN,
    }
    MAX_AUDIT: int = 1000

    def __init__(self, audit_path: str | None = None) -> None:
        self.audit_path = audit_path or ".mekong/audit.yaml"
        self._halted = False
        self._audit: list[AuditEntry] = []
        self._load_audit()

    def classify(self, goal: str) -> GovernanceDecision:
        goal_lower = goal.lower()
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, goal_lower):
                decision = GovernanceDecision(ActionClass.FORBIDDEN, f"Matched forbidden pattern: {pattern}")
                self._record_audit_for_decision(goal, decision, "blocked")
                return decision
        for pattern in self.REVIEW_PATTERNS:
            if re.search(pattern, goal_lower):
                return GovernanceDecision(ActionClass.REVIEW_REQUIRED, f"Matched review pattern: {pattern}", requires_approval=True)
        decision = GovernanceDecision(ActionClass.SAFE, "No dangerous patterns detected")
        self._record_audit_for_decision(goal, decision, "executed")
        return decision

    def classify_risk(self, risk_level: str) -> GovernanceDecision:
        action_class = self.RISK_LEVEL_MAP.get(risk_level.upper(), ActionClass.SAFE)
        if action_class == ActionClass.FORBIDDEN:
            decision = GovernanceDecision(action_class, f"CRITICAL risk level: {risk_level}")
            self._record_audit_for_decision(f"capability:{risk_level}", decision, "blocked")
            return decision
        if action_class == ActionClass.REVIEW_REQUIRED:
            return GovernanceDecision(action_class, f"{risk_level} risk requires review", requires_approval=True)
        decision = GovernanceDecision(action_class, f"{risk_level} risk classified as safe")
        self._record_audit_for_decision(f"capability:{risk_level}", decision, "executed")
        return decision

    def _record_audit_for_decision(self, goal: str, decision: GovernanceDecision, result: str) -> None:
        self.record_audit(AuditEntry(goal=goal, action_class=decision.action_class.value, approved=decision.approved, result=result))

    def request_approval(self, goal: str, decision: GovernanceDecision) -> bool:
        if decision.action_class == ActionClass.FORBIDDEN:
            return False
        if decision.requires_approval:
            if os.getenv("GOVERNANCE_AUTO_APPROVE", "").lower() not in ("true", "1", "yes"):
                logger.warning("Governance: action '%s' requires human approval (set GOVERNANCE_AUTO_APPROVE=true to bypass)", goal)
                decision.approved = False
                self._record_audit_for_decision(goal, decision, "rejected")
                return False
            logger.warning("Governance: auto-approving '%s' via GOVERNANCE_AUTO_APPROVE", goal)
            decision.approved = True
            self._record_audit_for_decision(goal, decision, "approved")
            return True
        self._record_audit_for_decision(goal, decision, "executed")
        return True

    def record_audit(self, entry: AuditEntry) -> None:
        self._audit = (self._audit + [entry])[-self.MAX_AUDIT:]
        try:
            self._save_audit()
        except OSError as exc:
            logger.warning("Governance: failed to persist audit trail to %s (entry kept in memory): %s", self.audit_path, exc)

    def get_audit_trail(self, limit: int = 50) -> list[AuditEntry]:
        return self._audit[-limit:]

    def is_halted(self) -> bool:
        return self._halted

    def halt(self) -> None:
        self._halted = True
        get_event_bus().emit(EventType.HALT_TRIGGERED, {"timestamp": time.time()})

    def resume(self) -> None:
        self._halted = False

    def _load_audit(self) -> None:
        path = Path(self.audit_path)
        if not path.exists():
            self._audit = []
            return
        try:
            data = yaml.safe_load(path.read_text()) or []
            self._audit = [
                AuditEntry(d.get("timestamp", 0), d.get("goal", ""), d.get("action_class", ""), d.get("approved", False), d.get("result", ""))
                for d in data
            ]
        except Exception as e:
            logger.debug("Failed to load audit trail: %s", e)
            self._audit = []

    def _save_audit(self) -> None:
        path = Path(self.audit_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [{"timestamp": e.timestamp, "goal": e.goal, "action_class": e.action_class, "approved": e.approved, "result": e.result} for e in self._audit]
        _fd, _tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".yaml.tmp")
        try:
            with os.fdopen(_fd, "w") as _fh:
                _fh.write(yaml.dump(data, default_flow_style=False))
            os.replace(_tmp_path, str(path))
        except Exception:
            try:
                os.unlink(_tmp_path)
            except OSError:
                pass
            raise

    __all__ = ["ActionClass", "AuditEntry", "Governance", "GovernanceDecision"]
