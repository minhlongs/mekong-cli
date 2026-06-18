"""
Voting module — Reputation-weighted voting with quorum calculations.

Implements:
- Reputation-weighted vote tallying (votes multiplied by voter reputation)
- Quorum determination (both participation and weight thresholds)
- Vote validation and tabulation
- Delegation support (vote delegation to trusted members)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class VoteType(Enum):
    """Types of votes that can be cast"""

    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"
    RECUSE = "recuse"


class VotingMethod(Enum):
    """Voting method variants"""

    SIMPLE_MAJORITY = "simple_majority"  # >50% of weighted votes
    SUPERMAJORITY = "supermajority"  # Configurable threshold (e.g., 2/3)
    QUORUM_REQUIRED = "quorum_required"  # Requires minimum participation
    CONSENSUS = "consensus"  # Near-unanimous (configurable)


@dataclass
class Voter:
    """Represents a voting member with reputation weight"""

    member_id: str
    reputation_score: float  # 0.0 to 1.0 (normalized)
    delegated_to: Optional[str] = None  # If set, this voter delegates to another
    voting_power: float = 1.0  # Additional multipliers (roles, stakes)
    is_active: bool = True


@dataclass
class Vote:
    """A single vote cast in an election"""

    voter_id: str
    proposal_id: str
    vote_type: VoteType
    weight: float  # Computed: reputation * voting_power
    timestamp: datetime
    rationale: Optional[str] = None


@dataclass
class VotingConfig:
    """Configuration for a voting instance"""

    method: VotingMethod = VotingMethod.SIMPLE_MAJORITY
    quorum_percentage: float = 0.5  # Minimum participation (by member count)
    threshold_percentage: float = 0.5  # Passing threshold (by weighted votes)
    allow_abstention: bool = True
    allow_delegation: bool = True
    max_delegation_chain: int = 3  # Max delegation hops
    recusal_allowed: bool = True
    time_window_hours: int = 168  # 7 days default voting window


@dataclass
class VotingResults:
    """Results of a completed vote"""

    proposal_id: str
    total_weight_cast: float
    total_participants: int
    yes_weight: float
    no_weight: float
    abstain_weight: float
    recuse_weight: float
    passed: bool
    quorum_met: bool
    threshold_met: bool
    timestamp: datetime
    voter_summary: Dict[str, int] = field(default_factory=dict)  # vote_type -> count


class VotingError(Exception):
    """Base exception for voting errors"""
    pass


class QuorumNotMetError(VotingError):
    """Raised when quorum requirements are not satisfied"""
    pass


class InvalidVoteError(VotingError):
    """Raised when a vote is invalid"""
    pass


class DelegationCycleError(VotingError):
    """Raised when delegation chain contains a cycle"""
    pass


class VotingSystem:
    """
    Core voting system implementing Ostrom's collective decision-making principle.

    Features:
    - Reputation-weighted voting (proportional equivalence)
    - Quorum enforcement (ensures adequate participation)
    - Delegation support (allows expertise-based proxy voting)
    - Vote validation (prevents double-voting, validates voter eligibility)
    - Transparent tallying with audit trail
    """

    def __init__(self, config: VotingConfig) -> None:
        """Initialize the voting system with configuration."""
        self.config = config
        self._active_votes: Dict[str, List[Vote]] = {}  # proposal_id -> votes
        self._voters: Dict[str, Voter] = {}
        self._delegation_graph: Dict[str, List[str]] = {}
        logger.info("VotingSystem initialized with config: %s", config)

    def register_voter(self, voter: Voter) -> None:
        """
        Register a voter in the system.

        Args:
            voter: Voter to register

        Raises:
            ValueError: If voter already exists
        """
        if voter.member_id in self._voters:
            raise ValueError(f"Voter {voter.member_id} already registered")

        if not (0 <= voter.reputation_score <= 1):
            raise ValueError("Reputation score must be between 0 and 1")

        self._voters[voter.member_id] = voter
        logger.debug("Registered voter: %s (reputation: %.2f)", voter.member_id, voter.reputation_score)

    def update_voter_reputation(self, member_id: str, new_score: float) -> None:
        """
        Update a voter's reputation score.

        Args:
            member_id: Voter to update
            new_score: New reputation score (0.0 to 1.0)

        Raises:
            ValueError: If score out of range or voter not found
        """
        if member_id not in self._voters:
            raise ValueError(f"Voter {member_id} not found")
        if not (0 <= new_score <= 1):
            raise ValueError("Reputation score must be between 0 and 1")

        old_score = self._voters[member_id].reputation_score
        self._voters[member_id].reputation_score = new_score
        logger.info("Updated %s reputation: %.2f → %.2f", member_id, old_score, new_score)

    def _resolve_delegation(self, voter_id: str, visited: Optional[Set[str]] = None) -> Tuple[str, float]:
        """
        Resolve delegation chain to find ultimate vote recipient.

        Args:
            voter_id: Starting voter ID
            visited: Set of visited IDs to detect cycles

        Returns:
            Tuple of (final_voter_id, cumulative_weight_multiplier)

        Raises:
            DelegationCycleError: If a delegation cycle is detected
            ValueError: If delegation chain exceeds max length or voter not found
        """
        if visited is None:
            visited = set()

        if voter_id not in self._voters:
            raise ValueError(f"Voter {voter_id} not found")

        if voter_id in visited:
            raise DelegationCycleError(f"Delegation cycle detected involving {voter_id}")

        visited.add(voter_id)
        voter = self._voters[voter_id]

        if not self.config.allow_delegation or not voter.delegated_to:
            return voter_id, voter.voting_power

        if len(visited) > self.config.max_delegation_chain:
            raise ValueError(f"Delegation chain exceeds max length of {self.config.max_delegation_chain}")

        return self._resolve_delegation(voter.delegated_to, visited)

    def validate_and_compute_weight(self, voter_id: str) -> float:
        """
        Validate voter eligibility and compute their effective voting weight.

        Args:
            voter_id: ID of voter

        Returns:
            Computed weight (reputation * voting_power)

        Raises:
            InvalidVoteError: If voter is invalid
        """
        if voter_id not in self._voters:
            raise InvalidVoteError(f"Voter {voter_id} not registered")

        voter = self._voters[voter_id]

        if not voter.is_active:
            raise InvalidVoteError(f"Voter {voter_id} is not active")

        try:
            final_voter, multiplier = self._resolve_delegation(voter_id)
            final_voter_obj = self._voters[final_voter]
            weight = final_voter_obj.reputation_score * final_voter_obj.voting_power * multiplier
        except (DelegationCycleError, ValueError) as e:
            raise InvalidVoteError(str(e)) from e

        return weight

    def cast_vote(
        self,
        voter_id: str,
        proposal_id: str,
        vote_type: VoteType,
        rationale: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> Vote:
        """
        Cast a vote in a proposal.

        Args:
            voter_id: ID of voting member
            proposal_id: ID of proposal being voted on
            vote_type: Type of vote (YES, NO, ABSTAIN, RECUSE)
            rationale: Optional explanation for the vote
            timestamp: Optional timestamp (defaults to now)

        Returns:
            The recorded Vote object

        Raises:
            InvalidVoteError: If vote cannot be cast
        """
        if not self.config.allow_abstention and vote_type == VoteType.ABSTAIN:
            raise InvalidVoteError("Abstention not allowed in this vote")

        if not self.config.recusal_allowed and vote_type == VoteType.RECUSE:
            raise InvalidVoteError("Recusal not allowed in this vote")

        # Check for double-voting
        if proposal_id in self._active_votes:
            for vote in self._active_votes[proposal_id]:
                if vote.voter_id == voter_id:
                    raise InvalidVoteError(f"Voter {voter_id} has already voted on {proposal_id}")

        weight = self.validate_and_compute_weight(voter_id)

        vote = Vote(
            voter_id=voter_id,
            proposal_id=proposal_id,
            vote_type=vote_type,
            weight=weight,
            timestamp=timestamp or datetime.utcnow(),
            rationale=rationale,
        )

        if proposal_id not in self._active_votes:
            self._active_votes[proposal_id] = []
        self._active_votes[proposal_id].append(vote)

        logger.debug(
            "Vote cast: %s on %s: %s (weight: %.3f)",
            voter_id,
            proposal_id,
            vote_type.value,
            weight,
        )
        return vote

    def tally_votes(self, proposal_id: str) -> VotingResults:
        """
        Tally votes for a proposal and determine outcome.

        Args:
            proposal_id: ID of proposal to tally

        Returns:
            VotingResults object with complete tally and outcome

        Raises:
            ValueError: If proposal has no votes
        """
        if proposal_id not in self._active_votes or not self._active_votes[proposal_id]:
            raise ValueError(f"No votes found for proposal {proposal_id}")

        votes = self._active_votes[proposal_id]

        yes_weight = sum(v.weight for v in votes if v.vote_type == VoteType.YES)
        no_weight = sum(v.weight for v in votes if v.vote_type == VoteType.NO)
        abstain_weight = sum(v.weight for v in votes if v.vote_type == VoteType.ABSTAIN)
        recuse_weight = sum(v.weight for v in votes if v.vote_type == VoteType.RECUSE)
        total_weight = yes_weight + no_weight

        # Count unique voters (resolving delegations)
        unique_voters: Set[str] = set()
        for vote in votes:
            try:
                final_voter, _ = self._resolve_delegation(vote.voter_id)
                unique_voters.add(final_voter)
            except DelegationCycleError:
                unique_voters.add(vote.voter_id)  # Count broken delegation as separate

        total_participants = len(unique_voters)

        # Voter summary
        voter_summary: Dict[str, int] = {}
        for vt in VoteType:
            voter_summary[vt.value] = sum(1 for v in votes if v.vote_type == vt)

        # Check quorum (participation threshold based on eligible voters)
        eligible_voters = sum(1 for v in self._voters.values() if v.is_active)
        quorum_threshold = eligible_voters * self.config.quorum_percentage
        quorum_met = total_participants >= quorum_threshold

        # Check threshold (weighted vote threshold)
        if self.config.method == VotingMethod.SUPERMAJORITY:
            threshold_met = total_weight > 0 and (yes_weight / total_weight) >= self.config.threshold_percentage
        elif self.config.method == VotingMethod.CONSENSUS:
            threshold_met = (yes_weight / total_weight) >= self.config.threshold_percentage if total_weight > 0 else False
        else:  # SIMPLE_MAJORITY or default
            threshold_met = yes_weight > no_weight

        passed = quorum_met and threshold_met

        results = VotingResults(
            proposal_id=proposal_id,
            total_weight_cast=total_weight + abstain_weight + recuse_weight,
            total_participants=total_participants,
            yes_weight=yes_weight,
            no_weight=no_weight,
            abstain_weight=abstain_weight,
            recuse_weight=recuse_weight,
            passed=passed,
            quorum_met=quorum_met,
            threshold_met=threshold_met,
            timestamp=datetime.utcnow(),
            voter_summary=voter_summary,
        )

        logger.info(
            "Tally complete for %s: %s (quorum: %s, threshold: %s)",
            proposal_id,
            "PASSED" if passed else "FAILED",
            quorum_met,
            threshold_met,
        )
        return results

    def get_vote_details(self, proposal_id: str) -> List[Dict[str, Any]]:
        """
        Get detailed breakdown of votes for a proposal.

        Args:
            proposal_id: Proposal to get details for

        Returns:
            List of vote detail dictionaries
        """
        if proposal_id not in self._active_votes:
            return []

        details = []
        for vote in self._active_votes[proposal_id]:
            details.append({
                "voter_id": vote.voter_id,
                "vote_type": vote.vote_type.value,
                "weight": vote.weight,
                "timestamp": vote.timestamp.isoformat(),
                "rationale": vote.rationale,
            })
        return details

    def clear_votes(self, proposal_id: str) -> None:
        """Clear votes for a proposal (for cleanup after completion)."""
        if proposal_id in self._active_votes:
            del self._active_votes[proposal_id]
            logger.debug("Cleared votes for %s", proposal_id)

    def get_active_vote_count(self) -> int:
        """Get number of proposals with active votes."""
        return len(self._active_votes)


def calculate_quorum(
    total_eligible_members: int,
    participation_rate: float,
    required_quorum: float,
) -> Tuple[bool, float]:
    """
    Calculate whether quorum is met.

    Args:
        total_eligible_members: Total number of eligible voters
        participation_rate: Actual participation as fraction (0-1)
        required_quorum: Required quorum as fraction (0-1)

    Returns:
        Tuple of (quorum_met, actual_quorum)
    """
    actual_quorum = participation_rate
    quorum_met = participation_rate >= required_quorum

    logger.debug(
        "Quorum check: %.1f%% participation vs %.1f%% required",
        participation_rate * 100,
        required_quorum * 100,
    )
    return quorum_met, actual_quorum


def compute_weighted_majority(
    yes_votes: float,
    no_votes: float,
    threshold: float = 0.5,
) -> Tuple[bool, float]:
    """
    Compute whether weighted majority threshold is met.

    Args:
        yes_votes: Total weight of yes votes
        no_votes: Total weight of no votes
        threshold: Required threshold (default 0.5 for simple majority)

    Returns:
        Tuple of (majority_achieved, margin)
    """
    total = yes_votes + no_votes
    if total == 0:
        return False, 0.0

    margin = (yes_votes - no_votes) / total
    majority_achieved = (yes_votes / total) >= threshold

    logger.debug(
        "Majority: %.1f%% (%.1f%% margin, threshold %.1f%%)",
        (yes_votes / total) * 100,
        margin * 100,
        threshold * 100,
    )
    return majority_achieved, margin
