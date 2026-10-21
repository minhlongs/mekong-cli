# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Amendment module — Complete amendment lifecycle: Proposal → Deliberation → Monitoring → Voting."""

from __future__ import annotations

import logging
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Set

from .amendment_models import (
    Amendment, AmendmentConfig, AmendmentError, AmendmentStatus, QuorumError, StageTransitionError,
)
from .amendment_voting import AmendmentVotingMixin
from .amendment_analytics import AmendmentAnalyticsMixin, run_amendment_workflow
from .voting import VotingSystem, VotingConfig, VotingResults, VotingMethod
from .sanctions import SanctionSystem
from .dispute import DisputeSystem

logger = logging.getLogger(__name__)


class AmendmentSystem(AmendmentVotingMixin, AmendmentAnalyticsMixin):
    """Complete amendment lifecycle management system."""

    _VALID_TRANSITIONS = {
        AmendmentStatus.DRAFT: [AmendmentStatus.SUBMITTED, AmendmentStatus.WITHDRAWN],
        AmendmentStatus.SUBMITTED: [AmendmentStatus.REVIEW, AmendmentStatus.REJECTED_IN_REVIEW],
        AmendmentStatus.REVIEW: [AmendmentStatus.DELIBERATION, AmendmentStatus.REJECTED_IN_REVIEW],
        AmendmentStatus.DELIBERATION: [AmendmentStatus.MONITORING],
        AmendmentStatus.MONITORING: [AmendmentStatus.VOTING],
        AmendmentStatus.VOTING: [AmendmentStatus.PASSED, AmendmentStatus.FAILED],
        AmendmentStatus.PASSED: [AmendmentStatus.RATIFIED, AmendmentStatus.FAILED],
        AmendmentStatus.RATIFIED: [AmendmentStatus.IMPLEMENTED],
        AmendmentStatus.FAILED: [], AmendmentStatus.WITHDRAWN: [],
        AmendmentStatus.REJECTED_IN_REVIEW: [], AmendmentStatus.IMPLEMENTED: [],
    }

    def __init__(
        self, config: AmendmentConfig, voting_system: VotingSystem,
        sanction_system: Optional[SanctionSystem] = None, dispute_system: Optional[DisputeSystem] = None,
    ) -> None:
        self.config = config
        self.voting_system = voting_system
        self.sanction_system = sanction_system
        self.dispute_system = dispute_system
        self._amendments: Dict[str, Amendment] = {}
        self._active_proposals: Set[str] = set()
        self._proposal_counter = 0

    def _generate_id(self) -> str:
        self._proposal_counter += 1
        return f"AMD-{self._proposal_counter:08d}"

    def _can_transition(self, current: AmendmentStatus, target: AmendmentStatus) -> bool:
        return target in self._VALID_TRANSITIONS.get(current, [])

    def _check_active_limit(self) -> bool:
        return len(self._active_proposals) < self.config.maximum_active_amendments

    def _check_co_sponsor_requirement(self, amendment: Amendment) -> bool:
        return len(amendment.co_sponsors) >= self.config.minimum_co_sponsors

    def _is_duplicate(self, new_amendment: Amendment) -> Optional[str]:
        if not self.config.auto_reject_duplicate:
            return None
        for existing in self._amendments.values():
            if existing.id == new_amendment.id or existing.status in (
                AmendmentStatus.IMPLEMENTED, AmendmentStatus.FAILED, AmendmentStatus.WITHDRAWN
            ):
                continue
            similarity = SequenceMatcher(None, new_amendment.proposed_text.lower(), existing.proposed_text.lower()).ratio()
            if similarity >= self.config.duplicate_similarity_threshold:
                return existing.id
        return None

    def create_amendment(
        self, title: str, description: str, proposed_text: str, current_text: str,
        proposer_id: str, co_sponsors: Optional[List[str]] = None, tags: Optional[List[str]] = None,
        priority: int = 1, estimated_impact: str = "",
    ) -> Amendment:
        if not self._check_active_limit():
            raise AmendmentError(f"Maximum active amendments ({self.config.maximum_active_amendments}) reached")
        amendment_id = self._generate_id()
        amendment = Amendment(
            id=amendment_id, title=title, description=description,
            proposed_text=proposed_text, current_text=current_text,
            proposer_id=proposer_id, co_sponsors=co_sponsors or [],
            status=AmendmentStatus.DRAFT, tags=tags or [],
            priority=priority, estimated_impact=estimated_impact,
        )
        self._amendments[amendment_id] = amendment
        return amendment

    def submit_amendment(self, amendment_id: str) -> Amendment:
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")
        amendment = self._amendments[amendment_id]
        if amendment.status != AmendmentStatus.DRAFT:
            raise AmendmentError(f"Cannot submit from status {amendment.status}")
        if not self._check_co_sponsor_requirement(amendment):
            raise AmendmentError(f"Minimum {self.config.minimum_co_sponsors} co-sponsors required")
        duplicate = self._is_duplicate(amendment)
        if duplicate:
            raise AmendmentError(f"Duplicate amendment detected: {duplicate}")

        amendment.status = AmendmentStatus.SUBMITTED
        amendment.submitted_at = datetime.utcnow()
        return amendment

    def start_review(self, amendment_id: str, reviewer_id: str, notes: str = "") -> Amendment:
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")
        amendment = self._amendments[amendment_id]
        if not self._can_transition(amendment.status, AmendmentStatus.REVIEW):
            raise StageTransitionError(f"Cannot transition from {amendment.status} to REVIEW")
        amendment.status = AmendmentStatus.REVIEW
        amendment.review_started_at = datetime.utcnow()
        if notes:
            amendment.review_notes.append(f"[{reviewer_id}] {notes}")
        return amendment

    def complete_review(
        self, amendment_id: str, approved: bool, reviewer_id: str, notes: Optional[str] = None
    ) -> Amendment:
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")
        amendment = self._amendments[amendment_id]
        if amendment.status != AmendmentStatus.REVIEW:
            raise StageTransitionError(f"Amendment {amendment_id} not in REVIEW status")
        if not amendment.review_started_at:
            raise AmendmentError(f"Amendment {amendment_id} has no review start time")

        amendment.review_completed_at = datetime.utcnow()
        if approved:
            amendment.status = AmendmentStatus.DELIBERATION
            amendment.deliberation_started_at = datetime.utcnow()
        else:
            amendment.status = AmendmentStatus.REJECTED_IN_REVIEW
        if notes:
            amendment.review_notes.append(f"[{reviewer_id}] {notes}")
        return amendment

    def add_feedback(self, amendment_id: str, member_id: str, comment: str) -> None:
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")
        amendment = self._amendments[amendment_id]
        if amendment.status != AmendmentStatus.DELIBERATION:
            raise AmendmentError(f"Cannot add feedback in status {amendment.status}")
        amendment.feedback.setdefault(member_id, []).append(comment)

    def record_concern(
        self, amendment_id: str, concern_type: str, description: str, raised_by: str
    ) -> None:
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")
        self._amendments[amendment_id].concerns.append({
            "type": concern_type, "description": description,
            "raised_by": raised_by, "raised_at": datetime.utcnow().isoformat(), "status": "open",
        })


__all__ = [
    "AmendmentStatus", "Amendment", "AmendmentConfig", "AmendmentError",
    "StageTransitionError", "QuorumError", "AmendmentSystem",
    "run_amendment_workflow", "VotingSystem", "VotingConfig",
    "VotingResults", "VotingMethod", "SanctionSystem", "DisputeSystem",
]
