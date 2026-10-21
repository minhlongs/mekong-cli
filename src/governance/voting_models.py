# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models, exceptions, and quorum/majority helpers for reputation-weighted voting."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class VoteType(Enum):
    """Types of votes that can be cast."""

    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"
    RECUSE = "recuse"


class VotingMethod(Enum):
    """Voting method variants."""

    SIMPLE_MAJORITY = "simple_majority"
    SUPERMAJORITY = "supermajority"
    QUORUM_REQUIRED = "quorum_required"
    CONSENSUS = "consensus"


@dataclass
class Voter:
    """Represents a voting member with reputation weight."""

    member_id: str
    reputation_score: float
    delegated_to: Optional[str] = None
    voting_power: float = 1.0
    is_active: bool = True


@dataclass
class Vote:
    """A single vote cast in an election."""

    voter_id: str
    proposal_id: str
    vote_type: VoteType
    weight: float
    timestamp: datetime
    rationale: Optional[str] = None


@dataclass
class VotingConfig:
    """Configuration for a voting instance."""

    method: VotingMethod = VotingMethod.SIMPLE_MAJORITY
    quorum_percentage: float = 0.5
    threshold_percentage: float = 0.5
    allow_abstention: bool = True
    allow_delegation: bool = True
    max_delegation_chain: int = 3
    recusal_allowed: bool = True
    time_window_hours: int = 168


@dataclass
class VotingResults:
    """Results of a completed vote."""

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
    voter_summary: Dict[str, int] = field(default_factory=dict)


class VotingError(Exception):
    """Base exception for voting errors."""


class QuorumNotMetError(VotingError):
    """Raised when quorum requirements are not satisfied."""


class InvalidVoteError(VotingError):
    """Raised when a vote is invalid."""


class DelegationCycleError(VotingError):
    """Raised when delegation chain contains a cycle."""


def calculate_quorum(
    total_eligible_members: int,
    participation_rate: float,
    required_quorum: float,
) -> Tuple[bool, float]:
    """Calculate whether quorum is met."""
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
    """Compute whether weighted majority threshold is met."""
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
