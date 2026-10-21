# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sanctions module — Graduated sanctions for governance violations."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .sanctions_models import (
    AppealError, EscalationError, ExpulsionSanction, RestitutionSanction, Sanction,
    SanctionHistory, SanctionLevel, SanctionsError, SuspensionSanction, ViolationType, WarningSanction,
)
from .sanctions_appeals import SanctionsAppealsMixin

logger = logging.getLogger(__name__)


class SanctionSystem(SanctionsAppealsMixin):
    """Graduated sanctions system implementing proportional response."""

    _ESCALATION_MATRIX = {
        (0, 1): 1, (0, 2): 2, (0, 3): 3,
        (1, 1): 2, (1, 2): 3, (1, 3): 4,
        (2, 1): 3, (2, 2): 4, (2, 3): 4,
        (3, 1): 4, (3, 2): 4, (3, 3): 4,
    }

    _DEFAULT_DURATIONS = {
        SanctionLevel.WARNING: 0,
        SanctionLevel.RESTITUTION: 30,
        SanctionLevel.SUSPENSION: 90,
        SanctionLevel.EXPULSION: 0,
    }

    def __init__(
        self,
        min_escalation_interval_days: int = 30,
        max_active_sanctions: int = 3,
        enable_appeals: bool = True,
        appeal_period_days: int = 14,
    ) -> None:
        self.min_escalation_interval = timedelta(days=min_escalation_interval_days)
        self.max_active_sanctions = max_active_sanctions
        self.enable_appeals = enable_appeals
        self.appeal_period = timedelta(days=appeal_period_days)
        self._sanctions: Dict[str, Sanction] = {}
        self._member_history: Dict[str, SanctionHistory] = {}
        self._sanction_counter = 0

    def _generate_id(self) -> str:
        self._sanction_counter += 1
        return f"SAN-{self._sanction_counter:08d}"

    def _get_violation_severity(self, violation_type: ViolationType) -> int:
        return {
            ViolationType.FAILED_DUTY: 1, ViolationType.DISRUPTION: 2,
            ViolationType.MISREPRESENTATION: 2, ViolationType.CONFLICT_OF_INTEREST: 2,
            ViolationType.RESOURCE_ABUSE: 2, ViolationType.EVASION: 3, ViolationType.COERCION: 3,
        }.get(violation_type, 1)

    def _get_current_max_level(self, member_id: str) -> int:
        if member_id not in self._member_history:
            return 0
        active = self._member_history[member_id].active_sanctions
        return max(s.level.value for s in active) if active else 0

    def _calculate_duration(self, level: SanctionLevel, custom_duration: Optional[int] = None) -> timedelta:
        days = custom_duration if custom_duration is not None else self._DEFAULT_DURATIONS.get(level, 0)
        return timedelta(0) if days == 0 else timedelta(days=days)

    def impose_sanction(
        self, member_id: str, violation_type: ViolationType, description: str, imposed_by: str,
        evidence: Optional[List[str]] = None, custom_duration: Optional[int] = None,
        conditions: Optional[List[str]] = None, metadata: Optional[Dict] = None,
    ) -> Sanction:
        """Impose a graduated sanction on a member."""
        now = datetime.utcnow()
        history = self._member_history.setdefault(member_id, SanctionHistory(member_id=member_id))

        if len(history.active_sanctions) >= self.max_active_sanctions:
            raise SanctionsError(f"Member {member_id} has maximum active sanctions ({self.max_active_sanctions})")

        current_max = self._get_current_max_level(member_id)
        violation_severity = self._get_violation_severity(violation_type)
        escalation_key = (current_max, violation_severity)
        if escalation_key not in self._ESCALATION_MATRIX:
            raise EscalationError(f"No escalation path from level {current_max} for severity {violation_severity}")

        new_level = SanctionLevel(self._ESCALATION_MATRIX[escalation_key])
        duration = self._calculate_duration(new_level, custom_duration)
        effective_until = (now + duration) if duration > timedelta(0) else None
        sanction_id = self._generate_id()

        common_kwargs: Dict[str, Any] = {
            "id": sanction_id, "member_id": member_id, "level": new_level,
            "violation_type": violation_type, "description": description,
            "evidence": evidence or [], "imposed_by": imposed_by, "imposed_at": now,
            "effective_until": effective_until, "conditions": conditions or [],
            "appealable": self.enable_appeals,
            "appeal_deadline": now + self.appeal_period if self.enable_appeals else None,
            "metadata": metadata or {},
        }

        if new_level == SanctionLevel.WARNING:
            sanction: Sanction = WarningSanction(warning_level=1, **common_kwargs)
            history.total_warnings += 1
        elif new_level == SanctionLevel.RESTITUTION:
            sanction = RestitutionSanction(
                restitution_amount=metadata.get("amount", 0.0) if metadata else 0.0, **common_kwargs
            )
        elif new_level == SanctionLevel.SUSPENSION:
            sanction = SuspensionSanction(
                suspension_duration_days=custom_duration or 90,
                suspended_privileges=metadata.get("privileges", []) if metadata else [],
                **common_kwargs,
            )
            history.total_suspensions += 1
        else:
            sanction = ExpulsionSanction(
                future_reinstatement_possible=metadata.get("reinstatable", False) if metadata else False,
                **common_kwargs,
            )

        self._sanctions[sanction_id] = sanction
        history.active_sanctions.append(sanction)
        history.historical_sanctions.append(sanction)
        history.last_violation_at = now
        return sanction

    def lift_sanction(self, sanction_id: str, lifted_by: str, reason: str) -> None:
        """Lift an active sanction (for non-expulsion cases)."""
        if sanction_id not in self._sanctions:
            raise ValueError(f"Sanction {sanction_id} not found")
        sanction = self._sanctions[sanction_id]
        if sanction.level == SanctionLevel.EXPULSION:
            raise ValueError("Expulsion sanctions cannot be lifted")
        if sanction.effective_until is None:
            raise ValueError("Permanent sanctions cannot be lifted")

        if sanction.member_id in self._member_history:
            history = self._member_history[sanction.member_id]
            if sanction in history.active_sanctions:
                history.active_sanctions.remove(sanction)

        sanction.metadata.setdefault("lifted_by", []).append(
            {"by": lifted_by, "at": datetime.utcnow().isoformat(), "reason": reason}
        )


def create_sanction_from_config(config: Dict[str, Any], member_id: str, imposed_by: str) -> Sanction:
    """Factory function to create sanction from configuration."""
    return SanctionSystem().impose_sanction(
        member_id=member_id, violation_type=ViolationType(config["violation_type"]),
        description=config["description"], imposed_by=imposed_by,
        evidence=config.get("evidence", []), custom_duration=config.get("duration_days"),
        conditions=config.get("conditions", []), metadata=config.get("metadata", {}),
    )


__all__ = [
    "SanctionLevel", "ViolationType", "Sanction", "WarningSanction",
    "RestitutionSanction", "SuspensionSanction", "ExpulsionSanction",
    "SanctionHistory", "SanctionsError", "EscalationError", "AppealError",
    "SanctionSystem", "create_sanction_from_config",
]
