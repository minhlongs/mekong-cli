# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""amendment.py — Amendment workflow for the ZenOS Commons Charter."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.mekong.constitution.amendment_models import (
    DEFAULT_TIERS, AmendmentProposal, AmendmentTier, AmendmentTierSpec,
    ConcentrationError, CoolingError, FounderVetoError, GovernanceError,
    ProposalState, QuorumError, ThresholdError, VoteRecord, _new_id,
    validate_quorum, validate_threshold,
)


@dataclass
class AmendmentEngine:
    """Stateless amendment workflow engine."""

    tiers: dict[AmendmentTier, AmendmentTierSpec] = field(default_factory=lambda: dict(DEFAULT_TIERS))
    member_count: int = 0
    founder_override: bool = True

    def create_proposal(
        self, *, title: str, body: str, tier: AmendmentTier | str,
        author_member_id: str, target_article: Optional[str] = None,
        new_text: str = "", emergency: bool = False, at: Optional[datetime] = None,
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
        voting_closes = cooling_until + timedelta(days=spec.voting_days)
        return AmendmentProposal(
            proposal_id=_new_id(), title=title, body=body, tier=tier,
            author_member_id=author_member_id, state=ProposalState.DRAFT,
            created_at=now, cooling_ends_at=cooling_until,
            voting_opens_at=cooling_until, voting_closes_at=voting_closes,
            target_article=target_article, new_text=new_text, emergency=emergency,
            emergency_expires_at=now + timedelta(days=90) if emergency else None,
            founder_review_required=(spec.requires_founder_approval or (self.member_count < 3 and self.founder_override)),
        )

    def start_cooling(self, proposal: AmendmentProposal) -> AmendmentProposal:
        if proposal.state is not ProposalState.DRAFT:
            raise GovernanceError(f"Cannot start cooling while in {proposal.state.value}")
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
            raise GovernanceError(f"Voting is not open (state={proposal.state.value})")
        if proposal.is_cooling(w):
            raise CoolingError(f"Cooling window active — opens for voting at {proposal.voting_opens_at.isoformat()}")
        if w < proposal.voting_opens_at or w > proposal.voting_closes_at:
            raise GovernanceError("Voting window is not open")
        if choice not in {"for", "against", "abstain"} or voting_power < 0:
            raise GovernanceError("Invalid vote parameters")

        chain = proposal.next_vote_chain()
        rec = VoteRecord(member_id=member_id, proposal_id=proposal.proposal_id, choice=choice, cast_at=w, chain_hash=chain)
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
            raise GovernanceError(f"Cannot tally a proposal in state {proposal.state.value}")
        if proposal.is_cooling():
            raise CoolingError("Cooling window has not yet completed")
        if proposal.is_voting():
            raise GovernanceError("Voting window is still open")

        spec = self.tiers[proposal.tier]
        total_cast = proposal.votes_for + proposal.votes_against + proposal.votes_abstain
        turnout = total_cast / proposal.eligible_power if proposal.eligible_power > 0 else 0.0
        quorum_met = turnout >= spec.quorum_fraction
        threshold_met = proposal.votes_for / max(total_cast, 1e-9) >= spec.threshold and proposal.votes_for > proposal.votes_against

        if proposal.founder_review_required:
            if proposal.founder_approved is None:
                proposal.state = ProposalState.FOUNDER_REVIEW
                return proposal
            if not proposal.founder_approved:
                proposal.state, proposal.vetoed = ProposalState.FAILED, True
                return proposal

        proposal.state = ProposalState.EXPIRED if not quorum_met else (ProposalState.PASSED if threshold_met else ProposalState.FAILED)
        return proposal

    def cancel(self, proposal: AmendmentProposal) -> AmendmentProposal:
        if proposal.state not in {ProposalState.DRAFT, ProposalState.ACTIVE, ProposalState.FOUNDER_REVIEW}:
            raise GovernanceError(f"Cannot cancel a proposal in state {proposal.state.value}")
        proposal.state = ProposalState.CANCELLED
        proposal.archived_at = datetime.now(timezone.utc)
        return proposal

    def founder_approve(self, proposal: AmendmentProposal) -> AmendmentProposal:
        if not proposal.founder_review_required:
            raise GovernanceError("Founder approval is not required for this proposal")
        proposal.founder_approved = True
        return self.tally(proposal)

    def founder_reject(self, proposal: AmendmentProposal, reason: str = "") -> AmendmentProposal:
        if not proposal.founder_review_required:
            raise GovernanceError("Founder approval is not required for this proposal")
        proposal.founder_approved, proposal.veto_reason, proposal.vetoed = False, reason, True
        return self.tally(proposal)

    def enforce(self, proposal: AmendmentProposal) -> AmendmentProposal:
        if proposal.state is not ProposalState.PASSED:
            raise GovernanceError(f"Cannot enforce a proposal in state {proposal.state.value}")
        now = datetime.now(timezone.utc)
        if proposal.emergency and proposal.emergency_expires_at and now > proposal.emergency_expires_at:
            raise GovernanceError("Emergency amendment has expired before enactment")
        proposal.state = ProposalState.ENACTED
        proposal.enacted_at = now
        return proposal

    def archive(self, proposal: AmendmentProposal) -> AmendmentProposal:
        if proposal.state not in {ProposalState.FAILED, ProposalState.EXPIRED, ProposalState.CANCELLED}:
            raise GovernanceError(f"Cannot archive a proposal in state {proposal.state.value}")
        proposal.state = ProposalState.ARCHIVED
        proposal.archived_at = datetime.now(timezone.utc)
        return proposal


__all__ = [
    "AmendmentEngine", "AmendmentProposal", "AmendmentTier", "AmendmentTierSpec",
    "ConcentrationError", "CoolingError", "DEFAULT_TIERS", "FounderVetoError",
    "GovernanceError", "ProposalState", "QuorumError", "ThresholdError",
    "VoteRecord", "_new_id", "validate_quorum", "validate_threshold",
]
