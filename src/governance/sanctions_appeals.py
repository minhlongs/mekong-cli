# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Appeals, escalation checks, expiration, and member history queries for SanctionSystem."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .sanctions_models import (
    AppealError,
    Sanction,
    SanctionHistory,
    SanctionLevel,
    ViolationType,
)

logger = logging.getLogger(__name__)


class SanctionsAppealsMixin:
    """Mixin providing sanction validation, appeal filing/resolution, expiry, and queries."""

    _ESCALATION_MATRIX: Dict[Tuple[int, int], int]
    _sanctions: Dict[str, Sanction]
    _member_history: Dict[str, SanctionHistory]

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
        """Check if a member is in good standing (no active sanctions)."""
        return len(self.get_active_sanctions(member_id)) == 0

    def get_member_history(self, member_id: str) -> Optional[SanctionHistory]:
        """Get full sanction history for a member."""
        return self._member_history.get(member_id)

    def can_impose_sanction(
        self, member_id: str, proposed_level: SanctionLevel
    ) -> Tuple[bool, str]:
        """Check if a proposed sanction is valid according to escalation rules."""
        current_max = self._get_current_max_level(member_id)  # type: ignore[attr-defined]
        violation_severity = self._get_violation_severity(ViolationType.FAILED_DUTY)  # type: ignore[attr-defined]

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
    ) -> Dict[str, Any]:
        """File an appeal against a sanction."""
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
        sanction.metadata.setdefault("appeals", []).append(appeal)
        logger.info("Appeal filed: %s against %s", appellant_id, sanction_id)
        return appeal

    def resolve_appeal(
        self, sanction_id: str, resolution: str, resolved_by: str, notes: str = ""
    ) -> None:
        """Resolve an appeal ('upheld', 'modified', or 'overturned')."""
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

        if resolution == "overturned":
            self.lift_sanction(sanction_id, resolved_by, f"Appeal upheld: {notes}")  # type: ignore[attr-defined]
        elif resolution == "modified":
            logger.info("Sanction modified by appeal: %s", sanction_id)

        logger.info("Appeal resolved: %s → %s by %s", sanction_id, resolution, resolved_by)

    def check_and_expire_sanctions(self) -> List[str]:
        """Check for expired sanctions and clean them from active list."""
        now = datetime.utcnow()
        expired = []

        for _member_id, history in self._member_history.items():
            to_remove = [
                s for s in history.active_sanctions
                if s.effective_until and s.effective_until <= now
            ]
            for sanction in to_remove:
                history.active_sanctions.remove(sanction)
                expired.append(sanction.id)
                logger.info("Sanction expired: %s", sanction.id)

        return expired
