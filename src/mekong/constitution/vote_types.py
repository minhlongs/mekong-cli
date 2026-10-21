# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Domain types and orchestration helpers for VoteEngine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from src.mekong.constitution.amendment import (
    AmendmentProposal,
    AmendmentTier,
    GovernanceError,
    ProposalState,
    VoteRecord,
)

if TYPE_CHECKING:
    from src.mekong.constitution.vote_engine import VoteEngine


@dataclass(frozen=True)
class MemberVoteWeight:
    member_id: str
    voting_power: float


class VoteEngineError(GovernanceError):
    pass


class MemberNotFoundError(VoteEngineError):
    pass


class FounderOverrideRequired(VoteEngineError):
    """Raised when an action needs founder override because member_count < 3."""


@dataclass
class ProposalBundle:
    proposal: AmendmentProposal
    votes: list[VoteRecord] = field(default_factory=list)
    result: Optional[AmendmentProposal] = None


def run_proposal_through_voting(
    engine: VoteEngine,
    *,
    title: str,
    body: str,
    tier: AmendmentTier | str,
    author_member_id: str,
    votes: list[tuple[str, str, float]],
    target_article: Optional[str] = None,
    new_text: str = "",
    eligible_power: float = 0.0,
    emergency: bool = False,
    founder_override_fn: Optional[callable] = None,
) -> ProposalBundle:
    """Convenience helper that runs the full propose -> vote -> tally cycle."""
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
    if result.state is ProposalState.PASSED:
        result = engine.enforce(result)
    return ProposalBundle(proposal=proposal, votes=recorded, result=result)
