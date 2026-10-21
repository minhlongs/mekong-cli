# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and exceptions for graduated governance sanctions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class SanctionLevel(Enum):
    """Sanction severity levels."""

    WARNING = 1
    RESTITUTION = 2
    SUSPENSION = 3
    EXPULSION = 4


class ViolationType(Enum):
    """Types of governance violations."""

    FAILED_DUTY = "failed_duty"
    DISRUPTION = "disruption"
    COERCION = "coercion"
    MISREPRESENTATION = "misrepresentation"
    CONFLICT_OF_INTEREST = "conflict_of_interest"
    RESOURCE_ABUSE = "resource_abuse"
    EVASION = "evasion"


@dataclass
class Sanction:
    """A sanction imposed on a member."""

    id: str
    member_id: str
    level: SanctionLevel
    violation_type: ViolationType
    description: str
    imposed_by: str
    imposed_at: datetime
    evidence: List[str] = field(default_factory=list)
    effective_until: Optional[datetime] = None
    conditions: List[str] = field(default_factory=list)
    appealable: bool = True
    appeal_deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WarningSanction(Sanction):
    """Level 1: Verbal or written warning."""

    warning_level: int = 1
    required_training: List[str] = field(default_factory=list)


@dataclass
class RestitutionSanction(Sanction):
    """Level 2: Material compensation for harm caused."""

    restitution_amount: float = 0.0
    restitution_type: str = ""
    deadline: Optional[datetime] = None


@dataclass
class SuspensionSanction(Sanction):
    """Level 3: Temporary loss of privileges."""

    suspended_privileges: List[str] = field(default_factory=list)
    suspension_duration_days: int = 0
    reinstatement_conditions: List[str] = field(default_factory=list)
    monitoring_period_days: int = 0


@dataclass
class ExpulsionSanction(Sanction):
    """Level 4: Permanent removal."""

    asset_distribution: Dict[str, Any] = field(default_factory=dict)
    future_reinstatement_possible: bool = False
    cooling_period_days: int = 0


@dataclass
class SanctionHistory:
    """History of sanctions for a member."""

    member_id: str
    active_sanctions: List[Sanction] = field(default_factory=list)
    historical_sanctions: List[Sanction] = field(default_factory=list)
    total_warnings: int = 0
    total_suspensions: int = 0
    last_violation_at: Optional[datetime] = None

    def get_severity_score(self) -> float:
        """Calculate overall severity score based on sanction history (0.0 to 1.0)."""
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
    """Base exception for sanctions errors."""


class EscalationError(SanctionsError):
    """Raised when escalation rules are violated."""


class AppealError(SanctionsError):
    """Raised when appeal rules are violated."""
