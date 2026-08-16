# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Sanctions module — Graduated sanctions for governance violations.

Implements Ostrom principle #5: Graduated sanctions
- Level 1: Warning (verbal/written)
- Level 2: Restitution (material compensation)
- Level 3: Suspension (temporary loss of privileges)
- Level 4: Expulsion (permanent removal)

Each sanction includes:
- Clear violation identification
- Proportional response
- Path to reinstatement (except expulsion)
- Audit trail with appeal rights
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SanctionLevel(Enum):
    """Sanction severity levels"""

    WARNING = 1
    RESTITUTION = 2
    SUSPENSION = 3
    EXPULSION = 4


class ViolationType(Enum):
    """Types of governance violations"""

    FAILED_DUTY = "failed_duty"  # Failed to perform assigned responsibility
    DISRUPTION = "disruption"  # Disrupted governance process
    COERCION = "coercion"  # Attempted to coerce other members
    MISREPRESENTATION = "misrepresentation"  # Provided false information
    CONFLICT_OF_INTEREST = "conflict_of_interest"  # Failed to disclose conflict
    RESOURCE_ABUSE = "resource_abuse"  # Misused common resources
    EVASION = "evasion"  # Evaded sanctions or monitoring


@dataclass
class Sanction:
    """A sanction imposed on a member"""

    id: str
    member_id: str
    level: SanctionLevel
    violation_type: ViolationType
    description: str
    imposed_by: str
    imposed_at: datetime
    evidence: List[str] = field(default_factory=list)  # References to evidence
    effective_until: Optional[datetime] = None  # None for permanent (expulsion)
    conditions: List[str] = field(default_factory=list)  # Conditions for lifting
    appealable: bool = True
    appeal_deadline: Optional[datetime] = None
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class WarningSanction(Sanction):
    """Level 1: Verbal or written warning"""

    warning_level: int = 1  # 1 = verbal, 2 = written, 3 = formal
    required_training: List[str] = field(default_factory=list)


@dataclass
class RestitutionSanction(Sanction):
    """Level 2: Material compensation for harm caused"""

    restitution_amount: float = 0.0
    restitution_type: str = ""  # "service", "resources", "credit"
    deadline: Optional[datetime] = None


@dataclass
class SuspensionSanction(Sanction):
    """Level 3: Temporary loss of privileges"""

    suspended_privileges: List[str] = field(default_factory=list)
    suspension_duration_days: int = 0
    reinstatement_conditions: List[str] = field(default_factory=list)
    monitoring_period_days: int = 0  # Increased monitoring after return


@dataclass
class ExpulsionSanction(Sanction):
    """Level 4: Permanent removal"""

    asset_distribution: Dict[str, any] = field(default_factory=dict)  # How shared assets are handled
    future_reinstatement_possible: bool = False
    cooling_period_days: int = 0  # Min time before petition for re-entry


@dataclass
class SanctionHistory:
    """History of sanctions for a member"""

    member_id: str
    active_sanctions: List[Sanction] = field(default_factory=list)
    historical_sanctions: List[Sanction] = field(default_factory=list)
    total_warnings: int = 0
    total_suspensions: int = 0
    last_violation_at: Optional[datetime] = None

    def get_severity_score(self) -> float:
        """
        Calculate overall severity score based on sanction history.

        Returns:
            Score from 0.0 to 1.0 where higher indicates more problematic
        """
        if not self.historical_sanctions:
            return 0.0

        total_severity = sum(s.level.value for s in self.historical_sanctions)
        max_possible = len(self.historical_sanctions) * SanctionLevel.EXPULSION.value
        return total_severity / max_possible if max_possible > 0 else 0.0

    def get_recent_violations(self, days: int = 365) -> List[Sanction]:
        """Get violations within specified time window."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return [s for s in self.historical_sanctions if s.imposed_at >= cutoff]


class SanctionsError(Exception):
    """Base exception for sanctions errors"""
    pass


class EscalationError(SanctionsError):
    """Raised when escalation rules are violated"""
    pass


class AppealError(SanctionsError):
    """Raised when appeal rules are violated"""
    pass


class SanctionSystem:
    """
    Graduated sanctions system implementing proportional response.

    Principles:
    1. Progressive escalation (warning → restitution → suspension → expulsion)
    2. Proportionality (severity matches harm)
    3. Path to redemption (except expulsion)
    4. Transparency (clear records, public to members)
    5. Appeal rights (each sanction can be appealed)
    """

    # Escalation matrix: (current_max_level, violation_severity) -> new_level
    _ESCALATION_MATRIX = {
        (0, 1): 1,  # First minor violation -> Warning
        (0, 2): 2,  # First moderate violation -> Restitution
        (0, 3): 3,  # First severe violation -> Suspension
        (1, 1): 2,  # Second minor after warning -> Restitution
        (1, 2): 3,  # Moderate after warning -> Suspension
        (1, 3): 4,  # Severe after warning -> Expulsion
        (2, 1): 3,  # Restitution + new violation -> Suspension
        (2, 2): 4,  # Moderate after restitution -> Expulsion
        (2, 3): 4,  # Severe after restitution -> Expulsion
        (3, 1): 4,  # Suspension + new violation -> Expulsion
        (3, 2): 4,  # Moderate after suspension -> Expulsion
        (3, 3): 4,  # Severe after suspension -> Expulsion
    }

    # Default durations (days)
    _DEFAULT_DURATIONS = {
        SanctionLevel.WARNING: 0,  # Permanent record but no active duration
        SanctionLevel.RESTITUTION: 30,
        SanctionLevel.SUSPENSION: 90,
        SanctionLevel.EXPULSION: 0,  # Permanent
    }

    def __init__(
        self,
        min_escalation_interval_days: int = 30,
        max_active_sanctions: int = 3,
        enable_appeals: bool = True,
        appeal_period_days: int = 14,
    ) -> None:
        """
        Initialize the sanction system.

        Args:
            min_escalation_interval_days: Minimum days between escalations
            max_active_sanctions: Maximum concurrent active sanctions
            enable_appeals: Whether appeals are allowed
            appeal_period_days: Days allowed to file appeal after sanction
        """
        self.min_escalation_interval = timedelta(days=min_escalation_interval_days)
        self.max_active_sanctions = max_active_sanctions
        self.enable_appeals = enable_appeals
        self.appeal_period = timedelta(days=appeal_period_days)

        self._sanctions: Dict[str, Sanction] = {}  # id -> sanction
        self._member_history: Dict[str, SanctionHistory] = {}
        self._sanction_counter = 0

        logger.info(
            "SanctionSystem initialized: max_active=%d, appeal_period=%d days",
            max_active_sanctions,
            appeal_period_days,
        )

    def _generate_id(self) -> str:
        """Generate unique sanction ID."""
        self._sanction_counter += 1
        return f"SAN-{self._sanction_counter:08d}"

    def _get_violation_severity(self, violation_type: ViolationType) -> int:
        """Map violation type to severity level (1-3)."""
        severity_map = {
            ViolationType.FAILED_DUTY: 1,
            ViolationType.DISRUPTION: 2,
            ViolationType.MISREPRESENTATION: 2,
            ViolationType.CONFLICT_OF_INTEREST: 2,
            ViolationType.RESOURCE_ABUSE: 2,
            ViolationType.EVASION: 3,
            ViolationType.COERCION: 3,
        }
        return severity_map.get(violation_type, 1)

    def _get_current_max_level(self, member_id: str) -> int:
        """Get the highest active sanction level for a member."""
        if member_id not in self._member_history:
            return 0

        active = self._member_history[member_id].active_sanctions
        return max(s.level.value for s in active) if active else 0

    def _calculate_duration(self, level: SanctionLevel, custom_duration: Optional[int] = None) -> timedelta:
        """Calculate sanction duration."""
        if custom_duration is not None:
            days = custom_duration
        else:
            days = self._DEFAULT_DURATIONS.get(level, 0)

        if days == 0:
            return timedelta(0)  # Permanent or no duration
        return timedelta(days=days)

    def impose_sanction(
        self,
        member_id: str,
        violation_type: ViolationType,
        description: str,
        imposed_by: str,
        evidence: Optional[List[str]] = None,
        custom_duration: Optional[int] = None,
        conditions: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> Sanction:
        """
        Impose a graduated sanction on a member.

        Args:
            member_id: Member to sanction
            violation_type: Type of violation
            description: Description of violation and sanction
            imposed_by: Authority imposing sanction
            evidence: Supporting evidence references
            custom_duration: Override default duration (days)
            conditions: Conditions for lifting sanction
            metadata: Additional context

        Returns:
            The imposed Sanction object

        Raises:
            EscalationError: If escalation rules are violated
            SanctionsError: If maximum active sanctions exceeded
        """
        now = datetime.utcnow()

        # Get or create member history
        if member_id not in self._member_history:
            self._member_history[member_id] = SanctionHistory(member_id=member_id)

        history = self._member_history[member_id]

        # Check active sanctions limit
        if len(history.active_sanctions) >= self.max_active_sanctions:
            raise SanctionsError(
                f"Member {member_id} has maximum active sanctions ({self.max_active_sanctions})"
            )

        # Check escalation rules
        current_max = self._get_current_max_level(member_id)
        violation_severity = self._get_violation_severity(violation_type)
        escalation_key = (current_max, violation_severity)

        if escalation_key not in self._ESCALATION_MATRIX:
            raise EscalationError(
                f"No escalation path from level {current_max} for severity {violation_severity}"
            )

        new_level_value = self._ESCALATION_MATRIX[escalation_key]
        new_level = SanctionLevel(new_level_value)

        # Calculate duration and effective until
        duration = self._calculate_duration(new_level, custom_duration)
        effective_until = (now + duration) if duration > timedelta(0) else None

        # Generate sanction
        sanction_id = self._generate_id()

        # Build appropriate sanction subclass
        common_kwargs = {
            "id": sanction_id,
            "member_id": member_id,
            "level": new_level,
            "violation_type": violation_type,
            "description": description,
            "evidence": evidence or [],
            "imposed_by": imposed_by,
            "imposed_at": now,
            "effective_until": effective_until,
            "conditions": conditions or [],
            "appealable": self.enable_appeals,
            "appeal_deadline": now + self.appeal_period if self.enable_appeals else None,
            "metadata": metadata or {},
        }

        sanction: Sanction
        if new_level == SanctionLevel.WARNING:
            sanction = WarningSanction(warning_level=1, **common_kwargs)
        elif new_level == SanctionLevel.RESTITUTION:
            sanction = RestitutionSanction(restitution_amount=metadata.get("amount", 0.0) if metadata else 0.0, **common_kwargs)
        elif new_level == SanctionLevel.SUSPENSION:
            suspension_days = custom_duration or 90
            sanction = SuspensionSanction(
                suspension_duration_days=suspension_days,
                suspended_privileges=metadata.get("privileges", []) if metadata else [],
                **common_kwargs,
            )
        elif new_level == SanctionLevel.EXPULSION:
            sanction = ExpulsionSanction(
                future_reinstatement_possible=metadata.get("reinstatable", False) if metadata else False,
                **common_kwargs,
            )

        # Record sanction
        self._sanctions[sanction_id] = sanction
        history.active_sanctions.append(sanction)
        history.historical_sanctions.append(sanction)
        history.last_violation_at = now

        # Update counters
        if new_level == SanctionLevel.WARNING:
            history.total_warnings += 1
        elif new_level == SanctionLevel.SUSPENSION:
            history.total_suspensions += 1

        logger.warning(
            "Sanction imposed: %s on %s: %s (level %d, until %s)",
            sanction_id,
            member_id,
            violation_type.value,
            new_level.value,
            effective_until.isoformat() if effective_until else "permanent",
        )
        return sanction

    def lift_sanction(self, sanction_id: str, lifted_by: str, reason: str) -> None:
        """
        Lift an active sanction (for non-expulsion cases).

        Args:
            sanction_id: ID of sanction to lift
            lifted_by: Authority lifting sanction
            reason: Reason for lifting

        Raises:
            ValueError: If sanction not found or cannot be lifted
        """
        if sanction_id not in self._sanctions:
            raise ValueError(f"Sanction {sanction_id} not found")

        sanction = self._sanctions[sanction_id]

        if sanction.level == SanctionLevel.EXPULSION:
            raise ValueError("Expulsion sanctions cannot be lifted")

        if sanction.effective_until is None:
            raise ValueError("Permanent sanctions cannot be lifted")

        # Remove from active list
        member_id = sanction.member_id
        if member_id in self._member_history:
            history = self._member_history[member_id]
            if sanction in history.active_sanctions:
                history.active_sanctions.remove(sanction)

        # Record lift in metadata
        if "lifted_by" not in sanction.metadata:
            sanction.metadata["lifted_by"] = []
        sanction.metadata["lifted_by"].append({
            "by": lifted_by,
            "at": datetime.utcnow().isoformat(),
            "reason": reason,
        })

        logger.info("Sanction lifted: %s by %s", sanction_id, lifted_by)

    def get_active_sanctions(self, member_id: str) -> List[Sanction]:
        """Get all currently active sanctions for a member."""
        if member_id not in self._member_history:
            return []

        now = datetime.utcnow()
        return [
            s for s in self._member_history[member_id].active_sanctions
            if s.effective_until is None or s.effective_until > now
        ]

    def is_member_in_good_standing(self, member_id: str) -> bool:
        """
        Check if a member is in good standing (no active sanctions).

        Args:
            member_id: Member to check

        Returns:
            True if member has no active sanctions
        """
        active = self.get_active_sanctions(member_id)
        return len(active) == 0

    def get_member_history(self, member_id: str) -> Optional[SanctionHistory]:
        """Get full sanction history for a member."""
        return self._member_history.get(member_id)

    def can_impose_sanction(self, member_id: str, proposed_level: SanctionLevel) -> Tuple[bool, str]:
        """
        Check if a proposed sanction is valid according to escalation rules.

        Args:
            member_id: Target member
            proposed_level: Proposed sanction level

        Returns:
            Tuple of (can_impose, reason)
        """
        current_max = self._get_current_max_level(member_id)
        violation_severity = self._get_violation_severity(ViolationType.FAILED_DUTY)  # Default

        escalation_key = (current_max, violation_severity)
        if escalation_key not in self._ESCALATION_MATRIX:
            return False, f"No escalation path from level {current_max}"

        max_possible = self._ESCALATION_MATRIX[escalation_key]
        if proposed_level.value > max_possible:
            return (
                False,
                f"Proposed level {proposed_level.value} exceeds maximum allowed {max_possible} "
                f"from current level {current_max}",
            )

        return True, "Valid sanction"

    def appeal_sanction(
        self,
        sanction_id: str,
        appellant_id: str,
        grounds: str,
        supporting_evidence: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """
        File an appeal against a sanction.

        Args:
            sanction_id: Sanction to appeal
            appellant_id: Member filing appeal (must be sanctioned member)
            grounds: Grounds for appeal
            supporting_evidence: Evidence supporting appeal

        Returns:
            Appeal record dictionary

        Raises:
            AppealError: If appeal cannot be filed
        """
        if sanction_id not in self._sanctions:
            raise AppealError(f"Sanction {sanction_id} not found")

        sanction = self._sanctions[sanction_id]

        if sanction.member_id != appellant_id:
            raise AppealError("Only the sanctioned member can file an appeal")

        if not sanction.appealable:
            raise AppealError(f"Sanction {sanction_id} is not appealable")

        now = datetime.utcnow()
        if sanction.appeal_deadline and now > sanction.appeal_deadline:
            raise AppealError(f"Appeal deadline passed: {sanction.appeal_deadline}")

        appeal = {
            "sanction_id": sanction_id,
            "appellant_id": appellant_id,
            "filed_at": now.isoformat(),
            "grounds": grounds,
            "supporting_evidence": supporting_evidence or [],
            "status": "pending",
        }

        if "appeals" not in sanction.metadata:
            sanction.metadata["appeals"] = []
        sanction.metadata["appeals"].append(appeal)

        logger.info("Appeal filed: %s against %s", appellant_id, sanction_id)
        return appeal

    def resolve_appeal(self, sanction_id: str, resolution: str, resolved_by: str, notes: str = "") -> None:
        """
        Resolve an appeal.

        Args:
            sanction_id: Sanction being appealed
            resolution: "upheld", "modified", or "overturned"
            resolved_by: Authority resolving appeal
            notes: Resolution notes

        Raises:
            AppealError: If resolution fails
        """
        if sanction_id not in self._sanctions:
            raise AppealError(f"Sanction {sanction_id} not found")

        sanction = self._sanctions[sanction_id]

        if "appeals" not in sanction.metadata or not sanction.metadata["appeals"]:
            raise AppealError(f"No appeal found for {sanction_id}")

        appeal = sanction.metadata["appeals"][-1]
        if appeal["status"] != "pending":
            raise AppealError(f"Appeal already resolved: {appeal['status']}")

        appeal["status"] = resolution
        appeal["resolved_at"] = datetime.utcnow().isoformat()
        appeal["resolved_by"] = resolved_by
        appeal["notes"] = notes

        # Apply resolution
        if resolution == "overturned":
            self.lift_sanction(sanction_id, resolved_by, f"Appeal upheld: {notes}")
        elif resolution == "modified":
            # Modified sanctions require re-imposition
            logger.info("Sanction modified by appeal: %s", sanction_id)

        logger.info("Appeal resolved: %s → %s by %s", sanction_id, resolution, resolved_by)

    def check_and_expire_sanctions(self) -> List[str]:
        """
        Check for expired sanctions and clean them from active list.

        Returns:
            List of sanction IDs that were expired
        """
        now = datetime.utcnow()
        expired = []

        for member_id, history in self._member_history.items():
            to_remove = []
            for sanction in history.active_sanctions:
                if sanction.effective_until and sanction.effective_until <= now:
                    to_remove.append(sanction)
                    expired.append(sanction.id)

            for sanction in to_remove:
                history.active_sanctions.remove(sanction)
                logger.info("Sanction expired: %s", sanction.id)

        return expired


def create_sanction_from_config(
    config: Dict[str, any],
    member_id: str,
    imposed_by: str,
) -> Sanction:
    """
    Factory function to create sanction from configuration.

    Args:
        config: Sanction configuration dictionary
        member_id: Target member
        imposed_by: Authority imposing

    Returns:
        Created Sanction object
    """
    system = SanctionSystem()
    return system.impose_sanction(
        member_id=member_id,
        violation_type=ViolationType(config["violation_type"]),
        description=config["description"],
        imposed_by=imposed_by,
        evidence=config.get("evidence", []),
        custom_duration=config.get("duration_days"),
        conditions=config.get("conditions", []),
        metadata=config.get("metadata", {}),
    )
