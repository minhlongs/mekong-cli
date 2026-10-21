# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Amendment types, value objects, and validators for ZenOS Commons Charter."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class ProposalState(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PASSED = "PASSED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    ENACTED = "ENACTED"
    ARCHIVED = "ARCHIVED"
    FOUNDER_REVIEW = "FOUNDER_REVIEW"


class AmendmentTier(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class GovernanceError(Exception):
    """Base governance failure."""


class CoolingError(GovernanceError):
    """Vote cast during the cooling window."""


class QuorumError(GovernanceError):
    """Quorum not reached."""


class ThresholdError(GovernanceError):
    """Proposal did not meet its tier threshold."""


class ConcentrationError(GovernanceError):
    """Anti-concentration cap breached."""


class FounderVetoError(GovernanceError):
    """Founder veto was exercised."""


@dataclass(frozen=True)
class AmendmentTierSpec:
    threshold: float
    cooling_days: int
    voting_days: int
    quorum_fraction: float
    requires_founder_approval: bool = False


DEFAULT_TIERS: dict[AmendmentTier, AmendmentTierSpec] = {
    AmendmentTier.L1: AmendmentTierSpec(2 / 3, 90, 14, 2 / 3, True),
    AmendmentTier.L2: AmendmentTierSpec(3 / 4, 30, 14, 1 / 2),
    AmendmentTier.L3: AmendmentTierSpec(0.5, 7, 7, 1 / 3),
}


@dataclass
class VoteRecord:
    member_id: str
    proposal_id: str
    choice: str
    cast_at: datetime
    chain_hash: Optional[str] = None


@dataclass
class AmendmentProposal:
    proposal_id: str
    title: str
    body: str
    tier: AmendmentTier
    author_member_id: str
    state: ProposalState
    created_at: datetime
    cooling_ends_at: datetime
    voting_opens_at: datetime
    voting_closes_at: datetime
    target_article: Optional[str] = None
    new_text: str = ""
    votes_for: float = 0.0
    votes_against: float = 0.0
    votes_abstain: float = 0.0
    eligible_power: float = 0.0
    enacted_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    founder_review_required: bool = False
    founder_approved: Optional[bool] = None
    emergency: bool = False
    emergency_expires_at: Optional[datetime] = None
    vetoed: bool = False
    veto_reason: str = ""
    chain_seed: str = field(default_factory=lambda: secrets.token_hex(16))

    def cooling_remaining(self, when: Optional[datetime] = None) -> timedelta:
        w = when or datetime.now(timezone.utc)
        return max(timedelta(0), self.cooling_ends_at - w)

    def voting_remaining(self, when: Optional[datetime] = None) -> timedelta:
        w = when or datetime.now(timezone.utc)
        if w < self.voting_opens_at:
            return self.voting_closes_at - self.voting_opens_at
        return max(timedelta(0), self.voting_closes_at - w)

    def is_cooling(self, when: Optional[datetime] = None) -> bool:
        return self.cooling_remaining(when).total_seconds() > 0

    def is_voting(self, when: Optional[datetime] = None) -> bool:
        w = when or datetime.now(timezone.utc)
        return self.voting_opens_at <= w <= self.voting_closes_at

    def is_expired(self, when: Optional[datetime] = None) -> bool:
        w = when or datetime.now(timezone.utc)
        return w > self.voting_closes_at and self.state is ProposalState.ACTIVE

    def current_power_for(self) -> float:
        return self.votes_for

    def current_power_against(self) -> float:
        return self.votes_against

    def turnout_fraction(self) -> float:
        if self.eligible_power <= 0:
            return 0.0
        return (self.votes_for + self.votes_against + self.votes_abstain) / self.eligible_power

    def next_vote_chain(self) -> str:
        prior = self.chain_seed
        payload = f"{self.proposal_id}:{self.votes_for + self.votes_against + self.votes_abstain:.6f}"
        return hashlib.sha256((prior + ":" + payload).encode()).hexdigest()


def _new_id(prefix: str = "prop") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{ts}_{secrets.token_hex(3)}"


def validate_quorum(eligible_power: float, turnout_power: float, quorum_fraction: float) -> None:
    if eligible_power <= 0:
        raise QuorumError("No eligible voting power registered — quorum cannot be met")
    if turnout_power / eligible_power < quorum_fraction:
        raise QuorumError(
            f"Quorum not met: {turnout_power:.2f} / {eligible_power:.2f} "
            f"= {turnout_power / eligible_power:.1%} < {quorum_fraction:.0%}"
        )


def validate_threshold(votes_for: float, votes_against: float, threshold: float) -> None:
    total = votes_for + votes_against
    if total <= 0:
        raise ThresholdError("No votes cast — threshold cannot be met")
    if votes_for / total < threshold:
        raise ThresholdError(
            f"Threshold not met: {votes_for:.2f} / {total:.2f} "
            f"= {votes_for / total:.1%} < {threshold:.0%}"
        )
