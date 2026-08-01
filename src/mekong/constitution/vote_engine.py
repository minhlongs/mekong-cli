"""vote_engine.py — Contribution-weighted vote engine for ZenOS Commons.

Implements the proposal lifecycle from `amendment.py` with:
- Contribution-weighted tallies (commit_count^0.5, 10x cap, 5x max)
- Quorum and threshold enforcement delegated to `amendment.validate_quorum`
  / `amendment.validate_threshold`
- Runtime gate: all significant proposals require founder override when
  `commons_member_count < 3` (see F2 plan RISK mitigations)
"""

from __future__ import annotations

import hashlib
import math
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.mekong.constitution.amendment import (
    AmendmentEngine,
    AmendmentProposal,
    AmendmentTier,
    AmendmentTierSpec,
    ConcentrationError,
    FounderVetoError,
    GovernanceError,
    ProposalState,
    VoteRecord,
    validate_quorum,
    validate_threshold,
)


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MemberVoteWeight:
    member_id: str
    voting_power: float  # pre-computed by registry.contribution_power()


class VoteEngineError(GovernanceError):
    pass


class MemberNotFoundError(VoteEngineError):
    pass


class FounderOverrideRequired(VoteEngineError):
    """Raised when an action needs founder override because member_count < 3."""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


@dataclass
class VoteEngine:
    """Wrapper around ``AmendmentEngine`` that applies contribution weighting
    and the < 3 member runtime gate."""

    amendment_engine: AmendmentEngine = field(default_factory=AmendmentEngine)
    commons_member_count: int = 0
    require_founder_override_below: int = 3
    current_founder_id: Optional[str] = None  # if set, override path is available

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def needs_override(self) -> bool:
        return self.commons_member_count < self.require_founder_override_below

    def assert_can_vote(self, proposal: AmendmentProposal) -> None:
        if self.needs_override() and proposal.founder_review_required:
            if self.current_founder_id is None:
                raise FounderOverrideRequired(
                    "Founder override required (commons_member_count < 3) "
                    "but no founder_id configured"
                )

    # ------------------------------------------------------------------
    # Proposal lifecycle
    # ------------------------------------------------------------------

    def propose(
        self,
        *,
        title: str,
        body: str,
        tier: AmendmentTier | str,
        author_member_id: str,
        target_article: Optional[str] = None,
        new_text: str = "",
        emergency: bool = False,
        eligible_power: float = 0.0,
        at: Optional[datetime] = None,
    ) -> AmendmentProposal:
        proposal = self.amendment_engine.create_proposal(
            title=title,
            body=body,
            tier=tier,
            author_member_id=author_member_id,
            target_article=target_article,
            new_text=new_text,
            emergency=emergency,
            at=at,
        )
        proposal.eligible_power = eligible_power
        self.amendment_engine.start_cooling(proposal)
        self.assert_can_vote(proposal)
        return proposal

    def vote(
        self,
        proposal: AmendmentProposal,
        member_id: str,
        choice: str,
        voting_power: float,
        at: Optional[datetime] = None,
    ) -> tuple[AmendmentProposal, VoteRecord]:
        if voting_power < 0:
            raise VoteEngineError("voting_power must be non-negative")
        if proposal.founder_review_required and self.needs_override():
            if self.current_founder_id is None:
                raise FounderOverrideRequired(
                    "Founder override required (commons_member_count < 3)"
                )
        proposal, rec = self.amendment_engine.cast_vote(
            proposal=proposal,
            member_id=member_id,
            choice=choice,
            voting_power=voting_power,
            at=at,
        )
        return proposal, rec

    def tally(self, proposal: AmendmentProposal) -> AmendmentProposal:
        self.assert_can_vote(proposal)
        return self.amendment_engine.tally(proposal)

    def founder_approve(self, proposal: AmendmentProposal) -> AmendmentProposal:
        return self.amendment_engine.founder_approve(proposal)

    def founder_reject(
        self, proposal: AmendmentProposal, reason: str = ""
    ) -> AmendmentProposal:
        return self.amendment_engine.founder_reject(proposal, reason=reason)

    def enforce(self, proposal: AmendmentProposal) -> AmendmentProposal:
        return self.amendment_engine.enforce(proposal)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def cooling_remaining(self, proposal: AmendmentProposal) -> timedelta:
        return proposal.cooling_remaining()

    def voting_remaining(self, proposal: AmendmentProposal) -> timedelta:
        return proposal.voting_remaining()

    def turnout(self, proposal: AmendmentProposal) -> float:
        return proposal.turnout_fraction()

    def contribution_power(self, commit_count: int) -> float:
        """ZENOS-COMMONS v1 formula.

        Power = 1.0 + min(commit_count ** 0.5, 10.0), capped at 5×.
        """
        base = 1.0
        bonus = min(math.sqrt(max(commit_count, 0)), 10.0)
        return min(base + bonus, 5.0)


# ---------------------------------------------------------------------------
# Convenience orchestration used by CLI commands
# ---------------------------------------------------------------------------


@dataclass
class ProposalBundle:
    proposal: AmendmentProposal
    votes: list[VoteRecord] = field(default_factory=list)
    result: Optional[AmendmentProposal] = None  # post-tally snapshot


def run_proposal_through_voting(
    engine: VoteEngine,
    *,
    title: str,
    body: str,
    tier: AmendmentTier | str,
    author_member_id: str,
    votes: list[tuple[str, str, float]],  # (member_id, choice, power)
    target_article: Optional[str] = None,
    new_text: str = "",
    eligible_power: float = 0.0,
    emergency: bool = False,
    founder_override_fn: Optional[callable] = None,
) -> ProposalBundle:
    """Convenience helper that runs the full propose -> vote -> tally cycle.

    Parameters
    ----------
    votes:
        Pre-computed (member_id, choice, voting_power) tuples.  Order reflects
        cast sequence; chain hashes chain automatically.

    Returns
    -------
    ProposalBundle
        proposal + votes + final state.
    """
    proposal = engine.propose(
        title=title,
        body=body,
        tier=tier,
        author_member_id=author_member_id,
        target_article=target_article,
        new_text=new_text,
        emergency=emergency,
        eligible_power=eligible_power,
    )
    recorded: list[VoteRecord] = []
    for member_id, choice, power in votes:
        proposal, rec = engine.vote(
            proposal=proposal, member_id=member_id, choice=choice, voting_power=power
        )
        recorded.append(rec)
    result = engine.tally(proposal)
    # Auto-enforce if passed (mirrors production behavior).
    if result.state is ProposalState.PASSED:
        result = engine.enforce(result)
    return ProposalBundle(proposal=proposal, votes=recorded, result=result)
