# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Amendment module — Complete amendment lifecycle: Proposal → Deliberation → Monitoring → Voting.

Implements Ostrom principle #3: Collective decision-making for changing rules.

Full amendment flow:
1. PROPOSAL: Draft amendment with clear text and justification
2. REVIEW: Initial review for completeness and conflicts
3. DELIBERATION: Discussion period with feedback collection
4. MONITORING: Track support/opposition, ensure quorum building
5. VOTING: Reputation-weighted vote with quorum requirements
6. RATIFICATION/REJECTION: Final outcome and implementation

Each stage has configurable time windows and requirements.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from .voting import VotingSystem, VotingConfig, VotingResults, VotingMethod
from .sanctions import SanctionSystem
from .dispute import DisputeSystem

logger = logging.getLogger(__name__)


class AmendmentStatus(Enum):
    """Status of an amendment through its lifecycle"""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEW = "review"
    REJECTED_IN_REVIEW = "rejected_in_review"
    DELIBERATION = "deliberation"
    MONITORING = "monitoring"
    VOTING = "voting"
    PASSED = "passed"
    FAILED = "failed"
    WITHDRAWN = "withdrawn"
    RATIFIED = "ratified"  # After voting + any appeal period
    IMPLEMENTED = "implemented"


@dataclass
class Amendment:
    """A proposed amendment to governance rules"""

    id: str
    title: str
    description: str
    proposed_text: str  # The actual amendment text
    current_text: str  # Text being amended (for context)
    proposer_id: str
    co_sponsors: List[str] = field(default_factory=list)
    submitted_at: Optional[datetime] = None
    status: AmendmentStatus = AmendmentStatus.DRAFT

    # Stage timestamps
    review_started_at: Optional[datetime] = None
    review_completed_at: Optional[datetime] = None
    deliberation_started_at: Optional[datetime] = None
    deliberation_completed_at: Optional[datetime] = None
    monitoring_started_at: Optional[datetime] = None
    voting_started_at: Optional[datetime] = None
    voting_ended_at: Optional[datetime] = None
    ratified_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None

    # Review/deliberation
    review_notes: List[str] = field(default_factory=list)
    feedback: Dict[str, List[str]] = field(default_factory=dict)  # member_id -> [comments]
    concerns: List[Dict[str, str]] = field(default_factory=list)

    # Voting
    voting_config: Optional[VotingConfig] = None
    voting_results: Optional[VotingResults] = None

    # Metadata
    tags: List[str] = field(default_factory=list)
    priority: int = 1  # 1=normal, 2=high, 3=urgent
    estimated_impact: str = ""  # "low", "medium", "high"
    requires_quorum: bool = True
    minimum_support_period_hours: int = 48  # Minimum monitoring period


@dataclass
class AmendmentConfig:
    """Configuration for amendment process"""

    # Time windows (hours)
    review_hours: int = 24
    deliberation_hours: int = 72
    minimum_monitoring_hours: int = 48
    voting_hours: int = 168  # 7 days

    # Requirements
    minimum_co_sponsors: int = 1
    maximum_active_amendments: int = 10
    require_review_approval: bool = True
    allow_withdrawal_after_voting: bool = False

    # Review criteria
    auto_reject_duplicate: bool = True
    duplicate_similarity_threshold: float = 0.8

    # Voting defaults
    default_voting_threshold: float = 0.6  # 60% for amendments
    default_quorum: float = 0.4  # 40% participation minimum


class AmendmentError(Exception):
    """Base exception for amendment errors"""
    pass


class StageTransitionError(AmendmentError):
    """Raised when stage transition is invalid"""
    pass


class QuorumError(AmendmentError):
    """Raised when quorum requirements fail"""
    pass


class AmendmentSystem:
    """
    Complete amendment lifecycle management system.

    Implements the full Ostrom amendment cycle:
    1. PROPOSAL → 2. REVIEW → 3. DELIBERATION → 4. MONITORING → 5. VOTING → 6. RATIFICATION

    Features:
    - Stage-based workflow with valid transitions
    - Automatic time window enforcement
    - Quorum tracking during monitoring
    - Integration with voting system
    - Conflict detection (duplicate amendments)
    - Co-sponsor requirements
    - Withdrawal mechanisms
    - Audit trail of entire lifecycle
    """

    # Valid stage transitions
    _VALID_TRANSITIONS = {
        AmendmentStatus.DRAFT: [AmendmentStatus.SUBMITTED, AmendmentStatus.WITHDRAWN],
        AmendmentStatus.SUBMITTED: [AmendmentStatus.REVIEW, AmendmentStatus.REJECTED_IN_REVIEW],
        AmendmentStatus.REVIEW: [AmendmentStatus.DELIBERATION, AmendmentStatus.REJECTED_IN_REVIEW],
        AmendmentStatus.DELIBERATION: [AmendmentStatus.MONITORING],
        AmendmentStatus.MONITORING: [AmendmentStatus.VOTING],
        AmendmentStatus.VOTING: [AmendmentStatus.PASSED, AmendmentStatus.FAILED],
        AmendmentStatus.PASSED: [AmendmentStatus.RATIFIED, AmendmentStatus.FAILED],
        AmendmentStatus.RATIFIED: [AmendmentStatus.IMPLEMENTED],
        AmendmentStatus.FAILED: [],  # Terminal
        AmendmentStatus.WITHDRAWN: [],  # Terminal
        AmendmentStatus.REJECTED_IN_REVIEW: [],  # Terminal
        AmendmentStatus.IMPLEMENTED: [],  # Terminal
    }

    def __init__(
        self,
        config: AmendmentConfig,
        voting_system: VotingSystem,
        sanction_system: Optional[SanctionSystem] = None,
        dispute_system: Optional[DisputeSystem] = None,
    ) -> None:
        """
        Initialize amendment system.

        Args:
            config: Amendment configuration
            voting_system: Voting system for final vote
            sanction_system: Optional sanction system for violations
            dispute_system: Optional dispute system for challenges
        """
        self.config = config
        self.voting_system = voting_system
        self.sanction_system = sanction_system
        self.dispute_system = dispute_system

        self._amendments: Dict[str, Amendment] = {}
        self._active_proposals: Set[str] = set()
        self._proposal_counter = 0

        logger.info(
            "AmendmentSystem initialized: max_active=%d, review=%dh, deliberation=%dh, voting=%dh",
            config.maximum_active_amendments,
            config.review_hours,
            config.deliberation_hours,
            config.voting_hours,
        )

    def _generate_id(self) -> str:
        """Generate unique amendment ID."""
        self._proposal_counter += 1
        return f"AMD-{self._proposal_counter:08d}"

    def _can_transition(self, current: AmendmentStatus, target: AmendmentStatus) -> bool:
        """Check if stage transition is valid."""
        return target in self._VALID_TRANSITIONS.get(current, [])

    def _check_active_limit(self) -> bool:
        """Check if we're under active proposal limit."""
        return len(self._active_proposals) < self.config.maximum_active_amendments

    def _check_co_sponsor_requirement(self, amendment: Amendment) -> bool:
        """Check if co-sponsor requirement is met."""
        return len(amendment.co_sponsors) >= self.config.minimum_co_sponsors

    def _is_duplicate(self, new_amendment: Amendment) -> Optional[str]:
        """
        Check if amendment is duplicate of existing one.

        Returns:
            ID of duplicate amendment, or None if not duplicate
        """
        if not self.config.auto_reject_duplicate:
            return None

        from difflib import SequenceMatcher

        for existing in self._amendments.values():
            # Skip self and terminal status amendments
            if existing.id == new_amendment.id:
                continue
            if existing.status in (AmendmentStatus.IMPLEMENTED, AmendmentStatus.FAILED, AmendmentStatus.WITHDRAWN):
                continue

            similarity = SequenceMatcher(
                None,
                new_amendment.proposed_text.lower(),
                existing.proposed_text.lower(),
            ).ratio()

            if similarity >= self.config.duplicate_similarity_threshold:
                return existing.id

        return None

    def create_amendment(
        self,
        title: str,
        description: str,
        proposed_text: str,
        current_text: str,
        proposer_id: str,
        co_sponsors: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        priority: int = 1,
        estimated_impact: str = "",
    ) -> Amendment:
        """
        Create a new amendment draft.

        Args:
            title: Amendment title
            description: Detailed description and justification
            proposed_text: New text to implement
            current_text: Current text being amended
            proposer_id: Member proposing
            co_sponsors: Supporting members
            tags: Category tags
            priority: Priority level (1-3)
            estimated_impact: Expected impact level

        Returns:
            Created Amendment in DRAFT status

        Raises:
            AmendmentError: If creation invalid
        """
        if not self._check_active_limit():
            raise AmendmentError(
                f"Maximum active amendments ({self.config.maximum_active_amendments}) reached"
            )

        amendment_id = self._generate_id()

        amendment = Amendment(
            id=amendment_id,
            title=title,
            description=description,
            proposed_text=proposed_text,
            current_text=current_text,
            proposer_id=proposer_id,
            co_sponsors=co_sponsors or [],
            status=AmendmentStatus.DRAFT,
            tags=tags or [],
            priority=priority,
            estimated_impact=estimated_impact,
        )

        self._amendments[amendment_id] = amendment
        logger.info("Amendment created: %s by %s", amendment_id, proposer_id)
        return amendment

    def submit_amendment(self, amendment_id: str) -> Amendment:
        """
        Submit amendment for review.

        Args:
            amendment_id: Amendment to submit

        Returns:
            Updated Amendment

        Raises:
            AmendmentError: If submission invalid
        """
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]

        if amendment.status != AmendmentStatus.DRAFT:
            raise AmendmentError(f"Cannot submit from status {amendment.status}")

        # Check requirements
        if not self._check_co_sponsor_requirement(amendment):
            raise AmendmentError(
                f"Minimum {self.config.minimum_co_sponsors} co-sponsors required"
            )

        duplicate = self._is_duplicate(amendment)
        if duplicate:
            raise AmendmentError(f"Duplicate amendment detected: {duplicate}")

        amendment.status = AmendmentStatus.SUBMITTED
        amendment.submitted_at = datetime.utcnow()

        logger.info("Amendment submitted: %s", amendment_id)
        return amendment

    def start_review(self, amendment_id: str, reviewer_id: str, notes: str = "") -> Amendment:
        """
        Start review process.

        Args:
            amendment_id: Amendment to review
            reviewer_id: Authority starting review
            notes: Initial review notes

        Returns:
            Updated Amendment
        """
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]

        if not self._can_transition(amendment.status, AmendmentStatus.REVIEW):
            raise StageTransitionError(f"Cannot transition from {amendment.status} to REVIEW")

        amendment.status = AmendmentStatus.REVIEW
        amendment.review_started_at = datetime.utcnow()
        if notes:
            amendment.review_notes.append(f"[{reviewer_id}] {notes}")

        logger.info("Review started: %s", amendment_id)
        return amendment

    def complete_review(
        self,
        amendment_id: str,
        approved: bool,
        reviewer_id: str,
        notes: Optional[str] = None,
    ) -> Amendment:
        """
        Complete review with decision.

        Args:
            amendment_id: Amendment to complete
            approved: Whether review approved
            reviewer_id: Who completed review
            notes: Review completion notes

        Returns:
            Updated Amendment
        """
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
            logger.info("Review approved, deliberation started: %s", amendment_id)
        else:
            amendment.status = AmendmentStatus.REJECTED_IN_REVIEW
            logger.warning("Review rejected: %s", amendment_id)

        if notes:
            amendment.review_notes.append(f"[{reviewer_id}] {notes}")

        return amendment

    def add_feedback(self, amendment_id: str, member_id: str, comment: str) -> None:
        """
        Add feedback during deliberation.

        Args:
            amendment_id: Amendment receiving feedback
            member_id: Member providing feedback
            comment: Feedback text
        """
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]

        if amendment.status != AmendmentStatus.DELIBERATION:
            raise AmendmentError(f"Cannot add feedback in status {amendment.status}")

        if member_id not in amendment.feedback:
            amendment.feedback[member_id] = []

        amendment.feedback[member_id].append(comment)
        logger.debug("Feedback added to %s by %s", amendment_id, member_id)

    def record_concern(
        self,
        amendment_id: str,
        concern_type: str,
        description: str,
        raised_by: str,
    ) -> None:
        """
        Record a concern about the amendment.

        Args:
            amendment_id: Amendment
            concern_type: Category of concern
            description: Concern description
            raised_by: Who raised it
        """
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]

        concern = {
            "type": concern_type,
            "description": description,
            "raised_by": raised_by,
            "raised_at": datetime.utcnow().isoformat(),
            "status": "open",
        }
        amendment.concerns.append(concern)
        logger.info("Concern raised on %s: %s by %s", amendment_id, concern_type, raised_by)

    def start_monitoring(self, amendment_id: str) -> Amendment:
        """
        Start monitoring period (pre-voting support assessment).

        Args:
            amendment_id: Amendment to monitor

        Returns:
            Updated Amendment
        """
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]

        if amendment.status != AmendmentStatus.DELIBERATION:
            raise StageTransitionError(
                f"Cannot start monitoring from {amendment.status}"
            )

        if not amendment.deliberation_started_at:
            raise AmendmentError("Deliberation never started")

        amendment.status = AmendmentStatus.MONITORING
        amendment.monitoring_started_at = datetime.utcnow()

        logger.info("Monitoring started: %s", amendment_id)
        return amendment

    def start_voting(
        self,
        amendment_id: str,
        voting_config: Optional[VotingConfig] = None,
    ) -> Tuple[Amendment, VotingSystem]:
        """
        Start voting period.

        Args:
            amendment_id: Amendment to vote on
            voting_config: Custom voting config

        Returns:
            Tuple of (updated Amendment, configured VotingSystem)

        Raises:
            AmendmentError: If voting cannot start
        """
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]

        if amendment.status != AmendmentStatus.MONITORING:
            raise StageTransitionError(f"Cannot start voting from {amendment.status}")

        if not amendment.monitoring_started_at:
            raise AmendmentError("Monitoring never started")

        # Check minimum monitoring period
        monitoring_duration = datetime.utcnow() - amendment.monitoring_started_at
        if monitoring_duration < timedelta(hours=amendment.minimum_support_period_hours):
            raise QuorumError(
                f"Minimum monitoring period not met: "
                f"{monitoring_duration} < {amendment.minimum_support_period_hours}h"
            )

        # Configure voting
        config = voting_config or VotingConfig(
            method=VotingMethod.SUPERMAJORITY,
            quorum_percentage=self.config.default_quorum,
            threshold_percentage=self.config.default_voting_threshold,
            time_window_hours=self.config.voting_hours,
        )
        amendment.voting_config = config

        amendment.status = AmendmentStatus.VOTING
        amendment.voting_started_at = datetime.utcnow()

        logger.info("Voting started: %s (threshold: %.1f%%)", amendment_id, config.threshold_percentage * 100)
        return amendment, self.voting_system

    def end_voting(self, amendment_id: str) -> Amendment:
        """
        End voting and tally results.

        Args:
            amendment_id: Amendment to finalize

        Returns:
            Updated Amendment with results

        Raises:
            AmendmentError: If voting cannot end
        """
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]

        if amendment.status != AmendmentStatus.VOTING:
            raise StageTransitionError(f"Cannot end voting in status {amendment.status}")

        if not amendment.voting_config:
            raise AmendmentError("No voting configuration")

        # Tally votes
        try:
            results = self.voting_system.tally_votes(amendment_id)
            amendment.voting_results = results
            amendment.voting_ended_at = datetime.utcnow()

            if results.passed:
                amendment.status = AmendmentStatus.PASSED
                logger.info("Voting PASSED: %s (%.1f%% yes)", amendment_id, (results.yes_weight / results.total_weight_cast) * 100)
            else:
                amendment.status = AmendmentStatus.FAILED
                logger.info("Voting FAILED: %s (quorum: %s, threshold: %s)",
                           amendment_id, results.quorum_met, results.threshold_met)

        except ValueError as e:
            logger.error("Voting tally failed for %s: %s", amendment_id, e)
            raise AmendmentError(f"Voting tally failed: {e}") from e

        return amendment

    def ratify_amendment(self, amendment_id: str, ratified_by: str) -> Amendment:
        """
        Ratify a passed amendment.

        Args:
            amendment_id: Amendment to ratify
            ratified_by: Authority ratifying

        Returns:
            Updated Amendment
        """
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]

        if amendment.status != AmendmentStatus.PASSED:
            raise StageTransitionError(f"Cannot ratify from status {amendment.status}")

        if not amendment.voting_results or not amendment.voting_results.passed:
            raise AmendmentError("Amendment did not pass voting")

        amendment.status = AmendmentStatus.RATIFIED
        amendment.ratified_at = datetime.utcnow()

        logger.info("Amendment ratified: %s by %s", amendment_id, ratified_by)
        return amendment

    def implement_amendment(self, amendment_id: str, implemented_by: str) -> Amendment:
        """
        Mark amendment as implemented.

        Args:
            amendment_id: Amendment to implement
            implemented_by: Who implemented

        Returns:
            Updated Amendment
        """
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]

        if amendment.status != AmendmentStatus.RATIFIED:
            raise StageTransitionError(f"Cannot implement from status {amendment.status}")

        amendment.status = AmendmentStatus.IMPLEMENTED
        amendment.implemented_at = datetime.utcnow()

        # Remove from active proposals
        self._active_proposals.discard(amendment_id)

        logger.info("Amendment implemented: %s by %s", amendment_id, implemented_by)
        return amendment

    def withdraw_amendment(self, amendment_id: str, withdrawn_by: str, reason: str) -> Amendment:
        """
        Withdraw an amendment before voting completes.

        Args:
            amendment_id: Amendment to withdraw
            withdrawn_by: Who withdraws (must be proposer or co-sponsor)
            reason: Reason for withdrawal

        Returns:
            Updated Amendment
        """
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]

        if amendment.status in (AmendmentStatus.IMPLEMENTED, AmendmentStatus.FAILED, AmendmentStatus.RATIFIED):
            raise AmendmentError(f"Cannot withdraw completed amendment: {amendment.status}")

        if withdrawn_by not in (amendment.proposer_id, *amendment.co_sponsors):
            raise AmendmentError("Only proposer or co-sponsors can withdraw")

        if amendment.status == AmendmentStatus.VOTING and not self.config.allow_withdrawal_after_voting:
            raise AmendmentError("Withdrawal not allowed after voting started")

        amendment.status = AmendmentStatus.WITHDRAWN

        # Remove from active proposals
        self._active_proposals.discard(amendment_id)

        logger.info("Amendment withdrawn: %s by %s - %s", amendment_id, withdrawn_by, reason)
        return amendment

    def get_amendment(self, amendment_id: str) -> Optional[Amendment]:
        """Get amendment by ID."""
        return self._amendments.get(amendment_id)

    def list_amendments(
        self,
        status: Optional[AmendmentStatus] = None,
        proposer_id: Optional[str] = None,
    ) -> List[Amendment]:
        """
        List amendments with optional filters.

        Args:
            status: Filter by status
            proposer_id: Filter by proposer

        Returns:
            List of matching amendments
        """
        amendments = list(self._amendments.values())

        if status:
            amendments = [a for a in amendments if a.status == status]
        if proposer_id:
            amendments = [a for a in amendments if a.proposer_id == proposer_id]

        # Sort by priority descending, then submitted_at
        return sorted(
            amendments,
            key=lambda a: (-a.priority, a.submitted_at or datetime.min),
        )

    def get_active_amendments(self) -> List[Amendment]:
        """Get all currently active (non-terminal) amendments."""
        terminal_statuses = {
            AmendmentStatus.IMPLEMENTED,
            AmendmentStatus.FAILED,
            AmendmentStatus.WITHDRAWN,
            AmendmentStatus.REJECTED_IN_REVIEW,
        }
        return [a for a in self._amendments.values() if a.status not in terminal_statuses]

    def check_quorum_during_monitoring(
        self,
        amendment_id: str,
        interested_members: int,
    ) -> Tuple[bool, float]:
        """
        Check if quorum is likely to be met during monitoring.

        Args:
            amendment_id: Amendment being monitored
            interested_members: Number of members showing interest

        Returns:
            Tuple of (quorum_likely, estimated_participation_rate)
        """
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]

        if amendment.status != AmendmentStatus.MONITORING:
            raise AmendmentError(f"Amendment {amendment_id} not in monitoring")

        if not amendment.voting_config:
            return False, 0.0

        estimated_rate = interested_members / max(1, self.voting_system.config.quorum_percentage * 100)
        quorum_likely = estimated_rate >= amendment.voting_config.quorum_percentage

        logger.debug(
            "Quorum check for %s: %d interested → %.1f%% est. participation",
            amendment_id,
            interested_members,
            estimated_rate * 100,
        )
        return quorum_likely, estimated_rate

    def get_stage_duration(self, amendment_id: str) -> Dict[str, Optional[float]]:
        """
        Get duration spent in each stage (hours).

        Args:
            amendment_id: Amendment to check

        Returns:
            Dictionary of stage -> duration in hours
        """
        if amendment_id not in self._amendments:
            return {}

        amendment = self._amendments[amendment_id]
        now = datetime.utcnow()
        durations: Dict[str, Optional[float]] = {
            "draft": None,
            "submitted": None,
            "review": None,
            "deliberation": None,
            "monitoring": None,
            "voting": None,
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

    def get_amendment_statistics(self) -> Dict[str, any]:
        """
        Get statistics about amendments.

        Returns:
            Statistics dictionary
        """
        amendments = list(self._amendments.values())

        by_status: Dict[str, int] = {}
        for amd in amendments:
            by_status[amd.status.value] = by_status.get(amd.status.value, 0) + 1

        avg_deliberation = 0.0
        delib_durations = [
            d for a in amendments
            if a.deliberation_started_at and a.voting_started_at
            for d in [(a.voting_started_at - a.deliberation_started_at).total_seconds() / 3600]
        ]
        if delib_durations:
            avg_deliberation = sum(delib_durations) / len(delib_durations)

        return {
            "total": len(amendments),
            "by_status": by_status,
            "active": len(self.get_active_amendments()),
            "average_deliberation_hours": avg_deliberation,
            "pass_rate": by_status.get("ratified", 0) / max(1, by_status.get("passed", 0) + by_status.get("failed", 0)),
        }


# Convenience function for creating complete amendment flow
def run_amendment_workflow(
    system: AmendmentSystem,
    amendment_id: str,
    auto_advance: bool = True,
) -> Amendment:
    """
    Execute the complete amendment workflow automatically for testing/demo.

    Args:
        system: Amendment system
        amendment_id: Amendment to process
        auto_advance: Auto-advance through stages

    Returns:
        Final Amendment state

    Note:
        This is for demonstration. Production workflows require manual
        stage advancement with human review at key points.
    """
    amendment = system.get_amendment(amendment_id)
    if not amendment:
        raise AmendmentError(f"Amendment {amendment_id} not found")

    logger.info("Starting workflow for %s", amendment_id)

    try:
        # Submit
        if amendment.status == AmendmentStatus.DRAFT:
            system.submit_amendment(amendment_id)

        # Review
        if amendment.status == AmendmentStatus.SUBMITTED:
            system.start_review(amendment_id, reviewer_id="reviewer")
            system.complete_review(amendment_id, approved=True, reviewer_id="reviewer")

        # Deliberation
        if amendment.status == AmendmentStatus.DELIBERATION:
            if auto_advance:
                # Simulate deliberation period
                amendment.deliberation_completed_at = datetime.utcnow()
                system.start_monitoring(amendment_id)

        # Monitoring
        if amendment.status == AmendmentStatus.MONITORING:
            if auto_advance:
                amendment.monitoring_started_at = datetime.utcnow() - timedelta(hours=50)  # Past minimum
                system.start_voting(amendment_id)

        # Voting (would require actual votes in production)
        if amendment.status == AmendmentStatus.VOTING:
            if auto_advance:
                amendment.voting_ended_at = datetime.utcnow()
                system.end_voting(amendment_id)

        # Ratify if passed
        if amendment.status == AmendmentStatus.PASSED:
            system.ratify_amendment(amendment_id, ratified_by="authority")

        logger.info("Workflow complete for %s: %s", amendment_id, amendment.status.value)
        return amendment

    except Exception as e:
        logger.error("Workflow failed for %s: %s", amendment_id, e)
        raise
