# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Hearings, rulings, resolutions, and query methods for DisputeSystem."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .dispute_models import (
    Dispute,
    DisputeError,
    DisputeStatus,
    DisputeType,
    Evidence,
    Ruling,
    RulingType,
)

logger = logging.getLogger(__name__)


class DisputeProceedingsMixin:
    """Mixin providing hearing scheduling, rulings, resolution, and inspection."""

    default_hearing_days: int
    enable_appeals: bool
    appeal_days: int
    _disputes: Dict[str, Dispute]

    def schedule_hearing(
        self, dispute_id: str, scheduled_by: str, hearing_date: Optional[datetime] = None
    ) -> datetime:
        """Schedule a hearing for a dispute."""
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")

        dispute = self._disputes[dispute_id]
        if dispute.status not in (DisputeStatus.EVIDENCE_COLLECTION, DisputeStatus.HEARING_SCHEDULED):
            raise DisputeError(f"Cannot schedule hearing in status {dispute.status}")

        hearing_date = hearing_date or (datetime.utcnow() + timedelta(days=self.default_hearing_days))
        if hearing_date < datetime.utcnow():
            raise ValueError("Hearing date cannot be in the past")

        dispute.hearing_date = hearing_date
        dispute.status = DisputeStatus.HEARING_SCHEDULED
        return hearing_date

    def hold_hearing(self, dispute_id: str, notes: str = "") -> None:
        """Mark hearing as held."""
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")

        dispute = self._disputes[dispute_id]
        if dispute.status != DisputeStatus.HEARING_SCHEDULED:
            raise DisputeError(f"Cannot hold hearing in status {dispute.status}")
        if not dispute.hearing_date:
            raise DisputeError("No hearing date scheduled")

        self.submit_evidence(  # type: ignore[attr-defined]
            dispute_id=dispute_id, submitter_id="arbitration_panel",
            evidence_type="hearing_transcript", description="Hearing transcript/notes",
            content_reference=notes, is_confidential=dispute.is_confidential,
        )
        dispute.status = DisputeStatus.HEARING_HELD

    def issue_ruling(
        self,
        dispute_id: str,
        ruling_type: RulingType,
        decision: str,
        findings: List[str],
        reasoning: str,
        remedies: Optional[List[Dict[str, Any]]] = None,
        dissent: Optional[Dict[str, str]] = None,
    ) -> Ruling:
        """Issue a ruling on a dispute."""
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")

        dispute = self._disputes[dispute_id]
        if dispute.status not in (DisputeStatus.HEARING_HELD, DisputeStatus.DELIBERATION):
            raise DisputeError(f"Cannot issue ruling in status {dispute.status}")

        now = datetime.utcnow()
        effective_date = now if dispute.urgency_level == 2 else now + timedelta(days=3)

        ruling = Ruling(
            id=f"RUL-{dispute_id}", dispute_id=dispute_id, ruling_type=ruling_type,
            decision=decision, findings=findings, reasoning=reasoning,
            remedies=remedies or [], dissent=dissent, issued_at=now,
            effective_date=effective_date,
            appealable=self.enable_appeals and ruling_type != RulingType.DISMISSED,
            appeal_deadline=now + timedelta(days=self.appeal_days) if self.enable_appeals else None,
        )
        dispute.ruling = ruling
        dispute.status = DisputeStatus.RULING_ISSUED
        for arb in dispute.arbitrators:
            arb.cases_heard += 1
        return ruling

    def resolve_dispute(self, dispute_id: str, resolved_by: str, resolution_notes: str = "") -> None:
        """Mark a dispute as fully resolved."""
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")
        dispute = self._disputes[dispute_id]
        if dispute.status != DisputeStatus.RULING_ISSUED:
            raise DisputeError(f"Cannot resolve without ruling: {dispute.status}")
        dispute.status = DisputeStatus.RESOLVED

    def withdraw_dispute(self, dispute_id: str, withdrawn_by: str, reason: str) -> None:
        """Withdraw a dispute before resolution."""
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")
        dispute = self._disputes[dispute_id]
        if dispute.status in (DisputeStatus.RESOLVED, DisputeStatus.CLOSED):
            raise DisputeError(f"Cannot withdraw resolved dispute: {dispute.status}")

        dispute.status = DisputeStatus.WITHDRAWN
        dispute.ruling = Ruling(
            id=f"RUL-WD-{dispute_id}", dispute_id=dispute_id, ruling_type=RulingType.DISMISSED,
            decision="Withdrawn", findings=[f"Dispute withdrawn by {withdrawn_by}: {reason}"],
            reasoning="Withdrawn before resolution", issued_at=datetime.utcnow(),
            effective_date=datetime.utcnow(), appealable=False,
        )

    def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        """Get dispute by ID."""
        return self._disputes.get(dispute_id)

    def list_disputes(
        self, status: Optional[DisputeStatus] = None, dispute_type: Optional[DisputeType] = None
    ) -> List[Dispute]:
        """List disputes with optional filters."""
        disputes = list(self._disputes.values())
        if status:
            disputes = [d for d in disputes if d.status == status]
        if dispute_type:
            disputes = [d for d in disputes if d.dispute_type == dispute_type]
        return sorted(disputes, key=lambda d: d.filed_at, reverse=True)

    def get_evidence(self, dispute_id: str, include_confidential: bool = False) -> List[Evidence]:
        """Get evidence for a dispute."""
        if dispute_id not in self._disputes:
            return []
        if include_confidential:
            return self._disputes[dispute_id].evidence
        return [e for e in self._disputes[dispute_id].evidence if not e.is_confidential]

    def can_appeal(self, dispute_id: str, appellant_id: str) -> Tuple[bool, Optional[str]]:
        """Check if a ruling can be appealed."""
        if dispute_id not in self._disputes:
            return False, "Dispute not found"
        dispute = self._disputes[dispute_id]
        if dispute.status != DisputeStatus.RULING_ISSUED:
            return False, f"Ruling not yet issued: {dispute.status}"
        if not dispute.ruling:
            return False, "No ruling exists"
        if not dispute.ruling.appealable:
            return False, "Ruling is not appealable"
        if dispute.ruling.appeal_deadline and datetime.utcnow() > dispute.ruling.appeal_deadline:
            return False, f"Appeal deadline passed: {dispute.ruling.appeal_deadline}"
        if appellant_id not in (dispute.filing_party, dispute.respondent):
            return False, "Only parties to the dispute may appeal"
        return True, None
