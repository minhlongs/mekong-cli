"""amendment.py — Amendment workflow for the ZenOS Commons Charter.

Implements the ZENOS Art 9 3-tier amendment procedure (L1/L2/L3) with cooling
periods, quorum checks, and threshold enforcement.  Amendments flow through
DRAFT -> ACTIVE -> PASSED / FAILED / EXPIRED / CANCELLED.

Depends on ``CommonsConfig`` from ``commons_parser.py`` for tier thresholds.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class ProposalState(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PASSED = "PASSED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    ENACTED = "ENACTED"
    ARCHIVED = "ARCHIVED"
    FOUNDER_REVIEW = "FOUNDER_REVIEW"  # only when member_count < 3


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
    threshold: float  # 0.5 = simple majority, 0.666 = 2/3, 0.75 = 3/4
    cooling_days: int
    voting_days: int
    quorum_fraction: float
    requires_founder_approval: bool = False


# ZENOS-COMMONS defaults (override with parsed config if available)
DEFAULT_TIERS: dict[AmendmentTier, AmendmentTierSpec] = {
    AmendmentTier.L1: AmendmentTierSpec(
        threshold=2 / 3,
        cooling_days=90,
        voting_days=14,
        quorum_fraction=2 / 3,
        requires_founder_approval=True,
    ),
    AmendmentTier.L2: AmendmentTierSpec(
        threshold=3 / 4,
        cooling_days=30,
        voting_days=14,
        quorum_fraction=1 / 2,
    ),
    AmendmentTier.L3: AmendmentTierSpec(
        threshold=0.5,
        cooling_days=7,
        voting_days=7,
        quorum_fraction=1 / 3,
    ),
}


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass
class VoteRecord:
    member_id: str
    proposal_id: str
    choice: str  # "for" | "against" | "abstain"
    cast_at: datetime
    chain_hash: Optional[str] = None  # SHA-256 chain from prior vote


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


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


@dataclass
class AmendmentEngine:
    """Stateless amendment workflow engine.

    Tier tables may be injected via ``tiers`` so tests or runtime config can
    override the ZENOS-COMMONS defaults.
    """

    tiers: dict[AmendmentTier, AmendmentTierSpec] = field(
        default_factory=lambda: dict(DEFAULT_TIERS)
    )
    member_count: int = 0  # updated by caller from registry
    founder_override: bool = True  # when member_count < 3

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def create_proposal(
        self,
        *,
        title: str,
        body: str,
        tier: AmendmentTier | str,
        author_member_id: str,
        target_article: Optional[str] = None,
        new_text: str = "",
        emergency: bool = False,
        at: Optional[datetime] = None,
    ) -> AmendmentProposal:
        if isinstance(tier, str):
            tier = AmendmentTier(tier.upper())
        if tier not in self.tiers:
            raise GovernanceError(f"Unknown proposal tier: {tier}")
        if emergency and tier is AmendmentTier.L1:
            raise GovernanceError("Emergency amendments cannot target L1 tier")
        now = at or datetime.now(timezone.utc)
        spec = self.tiers[tier]
        cooling_until = now + timedelta(days=spec.cooling_days)
        voting_opens = cooling_until
        voting_closes = voting_opens + timedelta(days=spec.voting_days)
        emergency_expires: Optional[datetime] = None
        if emergency:
            emergency_expires = now + timedelta(days=90)
        proposal = AmendmentProposal(
            proposal_id=_new_id(),
            title=title,
            body=body,
            tier=tier,
            author_member_id=author_member_id,
            state=ProposalState.DRAFT,
            created_at=now,
            cooling_ends_at=cooling_until,
            voting_opens_at=voting_opens,
            voting_closes_at=voting_closes,
            target_article=target_article,
            new_text=new_text,
            emergency=emergency,
            emergency_expires_at=emergency_expires,
            founder_review_required=(
                spec.requires_founder_approval or (self.member_count < 3 and self.founder_override)
            ),
        )
        return proposal

    def start_cooling(self, proposal: AmendmentProposal) -> AmendmentProposal:
        if proposal.state is not ProposalState.DRAFT:
            raise GovernanceError(
                f"Cannot start cooling while in {proposal.state.value}"
            )
        proposal.state = ProposalState.ACTIVE
        return proposal

    def cast_vote(
        self,
        proposal: AmendmentProposal,
        member_id: str,
        choice: str,
        voting_power: float,
        at: Optional[datetime] = None,
    ) -> tuple[AmendmentProposal, VoteRecord]:
        w = at or datetime.now(timezone.utc)
        if proposal.state is not ProposalState.ACTIVE:
            raise GovernanceError(
                f"Voting is not open (state={proposal.state.value})"
            )
        if proposal.is_cooling(w):
            raise CoolingError(
                f"Cooling window active — opens for voting at "
                f"{proposal.voting_opens_at.isoformat()}"
            )
        if w < proposal.voting_opens_at:
            raise GovernanceError("Voting has not started yet")
        if w > proposal.voting_closes_at:
            raise GovernanceError("Voting window has closed")
        if choice not in {"for", "against", "abstain"}:
            raise GovernanceError(f"Invalid choice: {choice!r}")
        if voting_power < 0:
            raise GovernanceError("voting_power must be non-negative")

        chain = proposal.next_vote_chain()
        rec = VoteRecord(
            member_id=member_id,
            proposal_id=proposal.proposal_id,
            choice=choice,
            cast_at=w,
            chain_hash=chain,
        )
        if choice == "for":
            proposal.votes_for += voting_power
        elif choice == "against":
            proposal.votes_against += voting_power
        else:
            proposal.votes_abstain += voting_power
        proposal.chain_seed = chain
        return proposal, rec

    def tally(self, proposal: AmendmentProposal) -> AmendmentProposal:
        if proposal.state not in {ProposalState.ACTIVE, ProposalState.FOUNDER_REVIEW}:
            raise GovernanceError(
                f"Cannot tally a proposal in state {proposal.state.value}"
            )
        if proposal.is_cooling():
            raise CoolingError("Cooling window has not yet completed")
        if proposal.is_voting():
            raise GovernanceError("Voting window is still open")

        spec = self.tiers[proposal.tier]
        total_cast = proposal.votes_for + proposal.votes_against + proposal.votes_abstain
        turnout = total_cast / proposal.eligible_power if proposal.eligible_power > 0 else 0.0

        quorum_met = turnout >= spec.quorum_fraction
        threshold_met = (
            proposal.votes_for / max(total_cast, 1e-9) >= spec.threshold
            and proposal.votes_for > proposal.votes_against
        )

        # Founder paths
        if proposal.founder_review_required:
            if proposal.founder_approved is None:
                proposal.state = ProposalState.FOUNDER_REVIEW
                return proposal
            if not proposal.founder_approved:
                proposal.state = ProposalState.FAILED
                proposal.vetoed = True
                return proposal
            # founder approved -> fall through to standard check

        if not quorum_met:
            proposal.state = ProposalState.EXPIRED
            return proposal
        if not threshold_met:
            proposal.state = ProposalState.FAILED
            return proposal
        proposal.state = ProposalState.PASSED
        return proposal

    def cancel(self, proposal: AmendmentProposal) -> AmendmentProposal:
        if proposal.state not in {
            ProposalState.DRAFT,
            ProposalState.ACTIVE,
            ProposalState.FOUNDER_REVIEW,
        }:
            raise GovernanceError(
                f"Cannot cancel a proposal in state {proposal.state.value}"
            )
        proposal.state = ProposalState.CANCELLED
        proposal.archived_at = datetime.now(timezone.utc)
        return proposal

    def founder_approve(self, proposal: AmendmentProposal) -> AmendmentProposal:
        if not proposal.founder_review_required:
            raise GovernanceError("Founder approval is not required for this proposal")
        proposal.founder_approved = True
        return self.tally(proposal)

    def founder_reject(
        self, proposal: AmendmentProposal, reason: str = ""
    ) -> AmendmentProposal:
        if not proposal.founder_review_required:
            raise GovernanceError("Founder approval is not required for this proposal")
        proposal.founder_approved = False
        proposal.veto_reason = reason
        proposal.vetoed = True
        return self.tally(proposal)

    def enforce(self, proposal: AmendmentProposal) -> AmendmentProposal:
        if proposal.state is not ProposalState.PASSED:
            raise GovernanceError(
                f"Cannot enforce a proposal in state {proposal.state.value}"
            )
        now = datetime.now(timezone.utc)
        if proposal.emergency and proposal.emergency_expires_at and now > proposal.emergency_expires_at:
            raise GovernanceError("Emergency amendment has expired before enactment")
        proposal.state = ProposalState.ENACTED
        proposal.enacted_at = now
        return proposal

    def archive(self, proposal: AmendmentProposal) -> AmendmentProposal:
        if proposal.state not in {
            ProposalState.FAILED,
            ProposalState.EXPIRED,
            ProposalState.CANCELLED,
        }:
            raise GovernanceError(
                f"Cannot archive a proposal in state {proposal.state.value}"
            )
        proposal.state = ProposalState.ARCHIVED
        proposal.archived_at = datetime.now(timezone.utc)
        return proposal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _new_id(prefix: str = "prop") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    rand = secrets.token_hex(3)
    return f"{prefix}_{ts}_{rand}"


# ---------------------------------------------------------------------------
# Convenience validators used by vote_engine and amendment_enforcer
# ---------------------------------------------------------------------------


def validate_quorum(
    eligible_power: float,
    turnout_power: float,
    quorum_fraction: float,
) -> None:
    if eligible_power <= 0:
        raise QuorumError("No eligible voting power registered — quorum cannot be met")
    if turnout_power / eligible_power < quorum_fraction:
        raise QuorumError(
            f"Quorum not met: {turnout_power:.2f} / {eligible_power:.2f} "
            f"= {turnout_power / eligible_power:.1%} < {quorum_fraction:.0%}"
        )


def validate_threshold(
    votes_for: float,
    votes_against: float,
    threshold: float,
) -> None:
    total = votes_for + votes_against
    if total <= 0:
        raise ThresholdError("No votes cast — threshold cannot be met")
    if votes_for / total < threshold:
        raise ThresholdError(
            f"Threshold not met: {votes_for:.2f} / {total:.2f} "
            f"= {votes_for / total:.1%} < {threshold:.0%}"
        )
