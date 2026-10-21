# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

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
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from .voting_models import (
    DelegationCycleError,
    InvalidVoteError,
    QuorumNotMetError,
    Vote,
    Voter,
    VoteType,
    VotingConfig,
    VotingError,
    VotingMethod,
    VotingResults,
    calculate_quorum,
    compute_weighted_majority,
)
from .voting_tally import VotingTallyMixin

logger = logging.getLogger(__name__)


class VotingSystem(VotingTallyMixin):
    """Core voting system implementing Ostrom's collective decision-making principle."""

    def __init__(self, config: VotingConfig) -> None:
        """Initialize the voting system with configuration."""
        self.config = config
        self._active_votes: Dict[str, List[Vote]] = {}
        self._voters: Dict[str, Voter] = {}
        self._delegation_graph: Dict[str, List[str]] = {}
        logger.info("VotingSystem initialized with config: %s", config)

    def register_voter(self, voter: Voter) -> None:
        """Register a voter in the system."""
        if voter.member_id in self._voters:
            raise ValueError(f"Voter {voter.member_id} already registered")

        if not (0 <= voter.reputation_score <= 1):
            raise ValueError("Reputation score must be between 0 and 1")

        self._voters[voter.member_id] = voter
        logger.debug("Registered voter: %s (reputation: %.2f)", voter.member_id, voter.reputation_score)

    def update_voter_reputation(self, member_id: str, new_score: float) -> None:
        """Update a voter's reputation score."""
        if member_id not in self._voters:
            raise ValueError(f"Voter {member_id} not found")
        if not (0 <= new_score <= 1):
            raise ValueError("Reputation score must be between 0 and 1")

        old_score = self._voters[member_id].reputation_score
        self._voters[member_id].reputation_score = new_score
        logger.info("Updated %s reputation: %.2f → %.2f", member_id, old_score, new_score)

    def _resolve_delegation(
        self, voter_id: str, visited: Optional[Set[str]] = None
    ) -> Tuple[str, float]:
        """Resolve delegation chain to find ultimate vote recipient."""
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
            raise ValueError(
                f"Delegation chain exceeds max length of {self.config.max_delegation_chain}"
            )

        return self._resolve_delegation(voter.delegated_to, visited)

    def validate_and_compute_weight(self, voter_id: str) -> float:
        """Validate voter eligibility and compute their effective voting weight."""
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
        """Cast a vote in a proposal."""
        if not self.config.allow_abstention and vote_type == VoteType.ABSTAIN:
            raise InvalidVoteError("Abstention not allowed in this vote")

        if not self.config.recusal_allowed and vote_type == VoteType.RECUSE:
            raise InvalidVoteError("Recusal not allowed in this vote")

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


__all__ = [
    "VoteType",
    "VotingMethod",
    "Voter",
    "Vote",
    "VotingConfig",
    "VotingResults",
    "VotingError",
    "QuorumNotMetError",
    "InvalidVoteError",
    "DelegationCycleError",
    "VotingSystem",
    "calculate_quorum",
    "compute_weighted_majority",
]
