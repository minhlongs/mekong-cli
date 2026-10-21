# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""vote_engine.py — Contribution-weighted vote engine for ZenOS Commons."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from src.mekong.constitution.amendment import (
    AmendmentEngine,
    AmendmentProposal,
    AmendmentTier,
    GovernanceError,
    ProposalState,
    VoteRecord,
)
from src.mekong.constitution.vote_types import (
    FounderOverrideRequired,
    MemberNotFoundError,
    MemberVoteWeight,
    ProposalBundle,
    VoteEngineError,
    run_proposal_through_voting,
)


@dataclass
class VoteEngine:
    """Wrapper around ``AmendmentEngine`` that applies contribution weighting."""

    amendment_engine: AmendmentEngine = field(default_factory=AmendmentEngine)
    commons_member_count: int = 0
    require_founder_override_below: int = 3
    current_founder_id: Optional[str] = None

    def needs_override(self) -> bool:
        return self.commons_member_count < self.require_founder_override_below

    def assert_can_vote(self, proposal: AmendmentProposal) -> None:
        if self.needs_override() and proposal.founder_review_required:
            if self.current_founder_id is None:
                raise FounderOverrideRequired(
                    "Founder override required (commons_member_count < 3) "
                    "but no founder_id configured"
                )

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
        return self.amendment_engine.cast_vote(
            proposal=proposal,
            member_id=member_id,
            choice=choice,
            voting_power=voting_power,
            at=at,
        )

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

    def cooling_remaining(self, proposal: AmendmentProposal) -> timedelta:
        return proposal.cooling_remaining()

    def voting_remaining(self, proposal: AmendmentProposal) -> timedelta:
        return proposal.voting_remaining()

    def turnout(self, proposal: AmendmentProposal) -> float:
        return proposal.turnout_fraction()

    def contribution_power(self, commit_count: int) -> float:
        """ZENOS-COMMONS v1 formula: Power = 1.0 + min(commit_count ** 0.5, 10.0), capped at 5x."""
        base = 1.0
        bonus = min(math.sqrt(max(commit_count, 0)), 10.0)
        return min(base + bonus, 5.0)


__all__ = [
    "AmendmentEngine",
    "AmendmentProposal",
    "AmendmentTier",
    "FounderOverrideRequired",
    "GovernanceError",
    "MemberNotFoundError",
    "MemberVoteWeight",
    "ProposalBundle",
    "ProposalState",
    "VoteEngine",
    "VoteEngineError",
    "VoteRecord",
    "run_proposal_through_voting",
]
