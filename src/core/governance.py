# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Governance Layer.

Safety governance for autonomous operations.
Classifies actions as safe/review_required/forbidden.
Maintains audit trail in .mekong/audit.yaml.
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Literal
import uuid

import yaml  # type: ignore[import-untyped]

from .event_bus import EventType, get_event_bus
from src.opc.approval import ApprovalSecurityError, PayloadBoundApprovalEngine, compute_action_digest
from src.opc.models import ActionPayload, ApprovalToken

logger = logging.getLogger(__name__)


class ActionClass(str, Enum):
    """Classification of an action's safety level."""

    SAFE = "safe"
    REVIEW_REQUIRED = "review_required"
    FORBIDDEN = "forbidden"


class ReRiskTier(str, Enum):
    """3-tier Reverse Engineering risk classification."""

    LOW_RISK = "LOW_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"


@dataclass(frozen=True)
class ReSandboxPolicy:
    """Execution sandbox policy derived from RE risk tier."""

    tier: ReRiskTier
    isolated_workspace: bool = False
    python_isolated_flag: bool = False
    network_disabled: bool = False
    requires_approval: bool = False
    docker_flags: tuple[str, ...] = ()



@dataclass
class GovernanceDecision:
    """Result of governance classification."""

    action_class: ActionClass
    reason: str
    requires_approval: bool = False
    approved: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class PolicyDecision:
    """Structured fail-closed policy evaluation decision for ticket/runtime actions."""

    decision: Literal["ALLOW", "APPROVAL_REQUIRED", "DENY"]
    actor: str
    capability: str
    resource_scope: str
    risk_level: str
    policy_version: str
    decision_reason: str
    audit_correlation_id: str
    payload_digest: str = ""


@dataclass
class AuditEntry:
    """Single audit trail entry."""

    timestamp: float = field(default_factory=time.time)
    goal: str = ""
    action_class: str = ""
    approved: bool = False
    result: str = ""  # "executed" | "blocked" | "rejected"


class Governance:
    """Safety governance layer for autonomous operations."""

    FORBIDDEN_PATTERNS: list[str] = [
        r"\brm\s+-rf\b",
        r"\bdrop\s+(database|table)\b",
        r"\bdelete\s+all\b",
        r"\bdestroy\b",
        r"\bformat\b",
        r"\btruncate\b",
    ]

    REVIEW_PATTERNS: list[str] = [
        r"\bdeploy\b.*\bprod",
        r"\bpush\b.*\bmain\b",
        r"\bmodify\b.*\bconfig\b",
        r"\bupdate\b.*\bdns\b",
        r"\bmigrate\b",
    ]

    # Risk-level mapping for capability-based governance (E3 + 3-tier RE)
    RISK_LEVEL_MAP: dict[str, ActionClass] = {
        "LOW": ActionClass.SAFE,
        "LOW_RISK": ActionClass.SAFE,
        "MEDIUM": ActionClass.SAFE,
        "MEDIUM_RISK": ActionClass.SAFE,
        "HIGH": ActionClass.REVIEW_REQUIRED,
        "HIGH_RISK": ActionClass.REVIEW_REQUIRED,
        "CRITICAL": ActionClass.FORBIDDEN,
    }

    RE_POLICY_MAP: dict[str, ReSandboxPolicy] = {
        "LOW": ReSandboxPolicy(
            tier=ReRiskTier.LOW_RISK,
            isolated_workspace=False,
            python_isolated_flag=False,
            network_disabled=False,
            requires_approval=False,
        ),
        "LOW_RISK": ReSandboxPolicy(
            tier=ReRiskTier.LOW_RISK,
            isolated_workspace=False,
            python_isolated_flag=False,
            network_disabled=False,
            requires_approval=False,
        ),
        "MEDIUM": ReSandboxPolicy(
            tier=ReRiskTier.MEDIUM_RISK,
            isolated_workspace=True,
            python_isolated_flag=True,
            network_disabled=False,
            requires_approval=False,
        ),
        "MEDIUM_RISK": ReSandboxPolicy(
            tier=ReRiskTier.MEDIUM_RISK,
            isolated_workspace=True,
            python_isolated_flag=True,
            network_disabled=False,
            requires_approval=False,
        ),
        "HIGH": ReSandboxPolicy(
            tier=ReRiskTier.HIGH_RISK,
            isolated_workspace=True,
            python_isolated_flag=True,
            network_disabled=True,
            requires_approval=True,
            docker_flags=("--network", "none"),
        ),
        "HIGH_RISK": ReSandboxPolicy(
            tier=ReRiskTier.HIGH_RISK,
            isolated_workspace=True,
            python_isolated_flag=True,
            network_disabled=True,
            requires_approval=True,
            docker_flags=("--network", "none"),
        ),
    }

    MAX_AUDIT: int = 1000

    def __init__(self, audit_path: str | None = None) -> None:
        """Initialize governance layer."""
        self.audit_path = audit_path or ".mekong/audit.yaml"
        self._halted = False
        self._audit: list[AuditEntry] = []
        self._load_audit()

    def classify(self, goal: str) -> GovernanceDecision:
        """Classify a goal as safe, review_required, or forbidden."""
        goal_lower = goal.lower()

        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, goal_lower):
                decision = GovernanceDecision(
                    action_class=ActionClass.FORBIDDEN,
                    reason=f"Matched forbidden pattern: {pattern}",
                )
                self._record_audit_for_decision(goal, decision, "blocked")
                return decision

        for pattern in self.REVIEW_PATTERNS:
            if re.search(pattern, goal_lower):
                decision = GovernanceDecision(
                    action_class=ActionClass.REVIEW_REQUIRED,
                    reason=f"Matched review pattern: {pattern}",
                    requires_approval=True,
                )
                # Don't record audit here — request_approval will handle it
                return decision

        decision = GovernanceDecision(
            action_class=ActionClass.SAFE,
            reason="No dangerous patterns detected",
        )
        self._record_audit_for_decision(goal, decision, "executed")
        return decision

    def classify_risk(self, risk_level: str) -> GovernanceDecision:
        """Classify a capability by its risk_level (fail-closed on unknown/empty risk).

        Map:
          LOW / LOW_RISK → SAFE
          MEDIUM / MEDIUM_RISK → SAFE (+mandatory audit)
          HIGH / HIGH_RISK → REVIEW_REQUIRED
          CRITICAL or unknown/malformed → FORBIDDEN
        """
        risk_clean = (risk_level or "").strip().upper()
        if not risk_clean or risk_clean not in self.RISK_LEVEL_MAP:
            decision = GovernanceDecision(
                action_class=ActionClass.FORBIDDEN,
                reason=f"Unknown or malformed risk level '{risk_level}' (fail-closed)",
            )
            self._record_audit_for_decision(f"capability:{risk_level}", decision, "blocked")
            return decision

        action_class = self.RISK_LEVEL_MAP[risk_clean]

        if action_class == ActionClass.FORBIDDEN:
            decision = GovernanceDecision(
                action_class=action_class,
                reason=f"CRITICAL risk level: {risk_level}",
            )
            self._record_audit_for_decision(f"capability:{risk_level}", decision, "blocked")
            return decision

        if action_class == ActionClass.REVIEW_REQUIRED:
            decision = GovernanceDecision(
                action_class=action_class,
                reason=f"{risk_level} risk requires review",
                requires_approval=True,
            )
            return decision

        # LOW or MEDIUM → SAFE
        decision = GovernanceDecision(
            action_class=action_class,
            reason=f"{risk_level} risk classified as safe",
        )
        self._record_audit_for_decision(f"capability:{risk_level}", decision, "executed")
        return decision

    def evaluate_ticket_action(
        self,
        *,
        actor: str,
        capability: str,
        resource_scope: str,
        risk_level: str,
        policy_version: str = "2026-11-01.v1",
        mandate_capabilities: tuple[str, ...] | list[str] | None = None,
        mandate_boundaries: tuple[str, ...] | list[str] | None = None,
        untrusted_context: bool = False,
        action_payload: ActionPayload | None = None,
        approval_token: ApprovalToken | None = None,
        approval_engine: PayloadBoundApprovalEngine | None = None,
    ) -> PolicyDecision:
        """Evaluate a runtime/ticket action under fail-closed governance and untrusted content separation."""
        correlation_id = f"pol_{uuid.uuid4().hex[:12]}"
        digest = compute_action_digest(action_payload) if action_payload is not None else ""

        if self._halted:
            return PolicyDecision(
                decision="DENY",
                actor=actor,
                capability=capability,
                resource_scope=resource_scope,
                risk_level=risk_level,
                policy_version=policy_version,
                decision_reason="Governance system is halted",
                audit_correlation_id=correlation_id,
                payload_digest=digest,
            )

        # 1. Fail-closed risk classification
        gov_decision = self.classify_risk(risk_level)
        if gov_decision.action_class == ActionClass.FORBIDDEN:
            return PolicyDecision(
                decision="DENY",
                actor=actor,
                capability=capability,
                resource_scope=resource_scope,
                risk_level=risk_level,
                policy_version=policy_version,
                decision_reason=gov_decision.reason,
                audit_correlation_id=correlation_id,
                payload_digest=digest,
            )

        # 2. Mandate capability & boundary enforcement
        if mandate_capabilities is not None and capability not in mandate_capabilities:
            self._record_audit_for_decision(
                f"ticket:{capability}",
                GovernanceDecision(action_class=ActionClass.FORBIDDEN, reason="Capability outside mandate"),
                "blocked",
            )
            return PolicyDecision(
                decision="DENY",
                actor=actor,
                capability=capability,
                resource_scope=resource_scope,
                risk_level=risk_level,
                policy_version=policy_version,
                decision_reason=f"Capability '{capability}' is not permitted by ImmutableMandate",
                audit_correlation_id=correlation_id,
                payload_digest=digest,
            )

        if mandate_boundaries is not None and len(mandate_boundaries) > 0:
            raw_parts = Path(resource_scope).parts if resource_scope else ()
            if ".." in raw_parts:
                return PolicyDecision(
                    decision="DENY",
                    actor=actor,
                    capability=capability,
                    resource_scope=resource_scope,
                    risk_level=risk_level,
                    policy_version=policy_version,
                    decision_reason=f"Resource scope '{resource_scope}' contains path traversal '..'",
                    audit_correlation_id=correlation_id,
                    payload_digest=digest,
                )
            norm_scope = "/" + "/".join(p for p in raw_parts if p not in ("/", ".", ""))
            allowed_scope = False
            for b in mandate_boundaries:
                b_parts = Path(b).parts if b else ()
                norm_b = "/" + "/".join(p for p in b_parts if p not in ("/", ".", ""))
                if norm_b == "/" or norm_scope == norm_b or norm_scope.startswith(norm_b + "/"):
                    allowed_scope = True
                    break
            if not allowed_scope:
                return PolicyDecision(
                    decision="DENY",
                    actor=actor,
                    capability=capability,
                    resource_scope=resource_scope,
                    risk_level=risk_level,
                    policy_version=policy_version,
                    decision_reason=f"Resource scope '{resource_scope}' violates mandate boundaries",
                    audit_correlation_id=correlation_id,
                    payload_digest=digest,
                )

        # 3. Untrusted content separation (issue comments, logs, web fetches, tool outputs)
        risk_clean = (risk_level or "").strip().upper()
        if untrusted_context:
            if risk_clean not in ("LOW", "LOW_RISK") or gov_decision.requires_approval:
                self._record_audit_for_decision(
                    f"untrusted:{capability}",
                    GovernanceDecision(
                        action_class=ActionClass.FORBIDDEN,
                        reason="Untrusted context attempted non-low-risk or privileged capability",
                    ),
                    "blocked",
                )
                return PolicyDecision(
                    decision="DENY",
                    actor=actor,
                    capability=capability,
                    resource_scope=resource_scope,
                    risk_level=risk_level,
                    policy_version=policy_version,
                    decision_reason="Untrusted content cannot escalate capabilities or trigger privileged actions",
                    audit_correlation_id=correlation_id,
                    payload_digest=digest,
                )

        # 4. Destructive / HIGH-risk actions require single-use payload-bound approval token
        if gov_decision.action_class == ActionClass.REVIEW_REQUIRED:
            if approval_token is None or action_payload is None:
                return PolicyDecision(
                    decision="APPROVAL_REQUIRED",
                    actor=actor,
                    capability=capability,
                    resource_scope=resource_scope,
                    risk_level=risk_level,
                    policy_version=policy_version,
                    decision_reason=gov_decision.reason,
                    audit_correlation_id=correlation_id,
                    payload_digest=digest,
                )
            engine = approval_engine or PayloadBoundApprovalEngine()
            try:
                engine.verify_and_consume(approval_token, action_payload)
            except ApprovalSecurityError as exc:
                self._record_audit_for_decision(
                    f"approval_violation:{capability}",
                    GovernanceDecision(action_class=ActionClass.FORBIDDEN, reason=str(exc)),
                    "blocked",
                )
                return PolicyDecision(
                    decision="DENY",
                    actor=actor,
                    capability=capability,
                    resource_scope=resource_scope,
                    risk_level=risk_level,
                    policy_version=policy_version,
                    decision_reason=str(exc),
                    audit_correlation_id=correlation_id,
                    payload_digest=digest,
                )

        return PolicyDecision(
            decision="ALLOW",
            actor=actor,
            capability=capability,
            resource_scope=resource_scope,
            risk_level=risk_level,
            policy_version=policy_version,
            decision_reason="Authorized by policy and mandate",
            audit_correlation_id=correlation_id,
            payload_digest=digest,
        )

    def get_re_policy(self, risk_level: str) -> ReSandboxPolicy:
        """Return the 3-tier RE sandbox policy for a given risk level."""
        risk_upper = (risk_level or "LOW").upper()
        return self.RE_POLICY_MAP.get(
            risk_upper,
            self.RE_POLICY_MAP["LOW_RISK"],
        )

    def _record_audit_for_decision(self, goal: str, decision: GovernanceDecision, result: str) -> None:
        """Record audit entry for a governance decision."""
        entry = AuditEntry(
            goal=goal,
            action_class=decision.action_class.value,
            approved=decision.approved,
            result=result,
        )
        self.record_audit(entry)

    def request_approval(
        self, goal: str, decision: GovernanceDecision
    ) -> bool:
        """Request human approval for review_required actions.

        Returns False by default — approval must come from a human
        or from GOVERNANCE_AUTO_APPROVE=true for non-forbidden actions.

        When auto-approving via env var, logs WARNING and records audit entry.
        """
        if decision.action_class == ActionClass.FORBIDDEN:
            return False

        if decision.requires_approval:
            # Auto-approve only when explicitly enabled via env var
            auto_approve = os.getenv("GOVERNANCE_AUTO_APPROVE", "").lower()
            if auto_approve not in ("true", "1", "yes"):
                logger.warning(
                    "Governance: action '%s' requires human approval "
                    "(set GOVERNANCE_AUTO_APPROVE=true to bypass)",
                    goal,
                )
                decision.approved = False
                self._record_audit_for_decision(goal, decision, "rejected")
                return False
            logger.warning(
                "Governance: auto-approving '%s' via GOVERNANCE_AUTO_APPROVE",
                goal,
            )
            decision.approved = True
            self._record_audit_for_decision(goal, decision, "approved")
            return True

        # Non-review actions need no approval gate — approve explicitly so the
        # function never falls through to an implicit None.
        self._record_audit_for_decision(goal, decision, "executed")
        return True

    def record_audit(self, entry: AuditEntry) -> None:
        """Record an audit entry with FIFO eviction.

        The entry is always kept in memory. Persistence is best-effort and
        loud: if the audit file cannot be written (unwritable path, full
        disk), a WARNING is logged but the decision path never crashes.
        """
        self._audit.append(entry)
        if len(self._audit) > self.MAX_AUDIT:
            self._audit = self._audit[-self.MAX_AUDIT:]
        try:
            self._save_audit()
        except OSError as exc:
            logger.warning(
                "Governance: failed to persist audit trail to %s "
                "(entry kept in memory): %s",
                self.audit_path,
                exc,
            )

    def get_audit_trail(self, limit: int = 50) -> list[AuditEntry]:
        """Get recent audit entries."""
        return self._audit[-limit:]

    def is_halted(self) -> bool:
        """Check if system is halted."""
        return self._halted

    def halt(self) -> None:
        """Halt all autonomous operations."""
        self._halted = True
        bus = get_event_bus()
        bus.emit(EventType.HALT_TRIGGERED, {"timestamp": time.time()})

    def resume(self) -> None:
        """Resume autonomous operations."""
        self._halted = False

    def _load_audit(self) -> None:
        """Load audit trail from YAML."""
        path = Path(self.audit_path)
        if not path.exists():
            self._audit = []
            return
        try:
            data = yaml.safe_load(path.read_text()) or []
            self._audit = [
                AuditEntry(
                    timestamp=d.get("timestamp", 0),
                    goal=d.get("goal", ""),
                    action_class=d.get("action_class", ""),
                    approved=d.get("approved", False),
                    result=d.get("result", ""),
                )
                for d in data
            ]
        except Exception as e:
            logger.debug("Failed to load audit trail: %s", e)
            self._audit = []

    def _save_audit(self) -> None:
        """Save audit trail to YAML."""
        path = Path(self.audit_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "timestamp": e.timestamp,
                "goal": e.goal,
                "action_class": e.action_class,
                "approved": e.approved,
                "result": e.result,
            }
            for e in self._audit
        ]
        # Atomic write — write to temp file then rename
        import tempfile as _tmp

        _fd, _tmp_path = _tmp.mkstemp(
            dir=path.parent, suffix=".yaml.tmp"
        )
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


__all__ = [
    "ActionClass",
    "AuditEntry",
    "Governance",
    "GovernanceDecision",
    "PolicyDecision",
    "ReRiskTier",
    "ReSandboxPolicy",
]