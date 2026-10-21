# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Query, analytics, and workflow runner helpers for AmendmentSystem."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .amendment_models import Amendment, AmendmentError, AmendmentStatus
from .voting import VotingSystem

logger = logging.getLogger(__name__)


class AmendmentAnalyticsMixin:
    """Mixin providing amendment queries, quorum checks, stage durations, and statistics."""

    voting_system: VotingSystem
    _amendments: Dict[str, Amendment]

    def get_amendment(self, amendment_id: str) -> Optional[Amendment]:
        return self._amendments.get(amendment_id)

    def list_amendments(
        self, status: Optional[AmendmentStatus] = None, proposer_id: Optional[str] = None
    ) -> List[Amendment]:
        amendments = list(self._amendments.values())
        if status:
            amendments = [a for a in amendments if a.status == status]
        if proposer_id:
            amendments = [a for a in amendments if a.proposer_id == proposer_id]
        return sorted(amendments, key=lambda a: (-a.priority, a.submitted_at or datetime.min))

    def get_active_amendments(self) -> List[Amendment]:
        terminal = {
            AmendmentStatus.IMPLEMENTED, AmendmentStatus.FAILED,
            AmendmentStatus.WITHDRAWN, AmendmentStatus.REJECTED_IN_REVIEW,
        }
        return [a for a in self._amendments.values() if a.status not in terminal]

    def check_quorum_during_monitoring(
        self, amendment_id: str, interested_members: int
    ) -> Tuple[bool, float]:
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")
        amendment = self._amendments[amendment_id]
        if amendment.status != AmendmentStatus.MONITORING:
            raise AmendmentError(f"Amendment {amendment_id} not in monitoring")
        if not amendment.voting_config:
            return False, 0.0

        estimated_rate = interested_members / max(1, self.voting_system.config.quorum_percentage * 100)
        return estimated_rate >= amendment.voting_config.quorum_percentage, estimated_rate

    def get_stage_duration(self, amendment_id: str) -> Dict[str, Optional[float]]:
        if amendment_id not in self._amendments:
            return {}
        amendment = self._amendments[amendment_id]
        now = datetime.utcnow()
        durations: Dict[str, Optional[float]] = {
            "draft": None, "submitted": None, "review": None,
            "deliberation": None, "monitoring": None, "voting": None,
        }
        if amendment.submitted_at:
            durations["submitted"] = (now - amendment.submitted_at).total_seconds() / 3600
        if amendment.review_started_at:
            review_end = amendment.review_completed_at or now
            durations["review"] = (review_end - amendment.review_started_at).total_seconds() / 3600
        if amendment.deliberation_started_at:
            delib_end = amendment.deliberation_completed_at or amendment.monitoring_started_at or now
            durations["deliberation"] = (delib_end - amendment.deliberation_started_at).total_seconds() / 3600
        if amendment.monitoring_started_at:
            monitor_end = amendment.voting_started_at or now
            durations["monitoring"] = (monitor_end - amendment.monitoring_started_at).total_seconds() / 3600
        if amendment.voting_started_at:
            voting_end = amendment.voting_ended_at or now
            durations["voting"] = (voting_end - amendment.voting_started_at).total_seconds() / 3600
        return durations

    def get_amendment_statistics(self) -> Dict[str, Any]:
        amendments = list(self._amendments.values())
        by_status: Dict[str, int] = {}
        for amd in amendments:
            by_status[amd.status.value] = by_status.get(amd.status.value, 0) + 1

        delib_durations = [
            (a.voting_started_at - a.deliberation_started_at).total_seconds() / 3600
            for a in amendments if a.deliberation_started_at and a.voting_started_at
        ]
        avg_deliberation = sum(delib_durations) / len(delib_durations) if delib_durations else 0.0
        return {
            "total": len(amendments), "by_status": by_status,
            "active": len(self.get_active_amendments()),
            "average_deliberation_hours": avg_deliberation,
            "pass_rate": by_status.get("ratified", 0)
            / max(1, by_status.get("passed", 0) + by_status.get("failed", 0)),
        }


def run_amendment_workflow(
    system: Any, amendment_id: str, auto_advance: bool = True
) -> Amendment:
    """Execute the complete amendment workflow automatically for testing/demo."""
    amendment = system.get_amendment(amendment_id)
    if not amendment:
        raise AmendmentError(f"Amendment {amendment_id} not found")

    if amendment.status == AmendmentStatus.DRAFT:
        system.submit_amendment(amendment_id)
    if amendment.status == AmendmentStatus.SUBMITTED:
        system.start_review(amendment_id, reviewer_id="reviewer")
        system.complete_review(amendment_id, approved=True, reviewer_id="reviewer")
    if amendment.status == AmendmentStatus.DELIBERATION and auto_advance:
        amendment.deliberation_completed_at = datetime.utcnow()
        system.start_monitoring(amendment_id)
    if amendment.status == AmendmentStatus.MONITORING and auto_advance:
        amendment.monitoring_started_at = datetime.utcnow() - timedelta(hours=50)
        system.start_voting(amendment_id)
    if amendment.status == AmendmentStatus.VOTING and auto_advance:
        amendment.voting_ended_at = datetime.utcnow()
        system.end_voting(amendment_id)
    if amendment.status == AmendmentStatus.PASSED:
        system.ratify_amendment(amendment_id, ratified_by="authority")
    return amendment
