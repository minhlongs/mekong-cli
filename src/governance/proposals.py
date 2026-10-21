# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Governance proposal facade for the ZenOS Commons kickoff."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from .amendment import (
    Amendment,
    AmendmentSystem,
    AmendmentConfig,
    AmendmentStatus,
)
from .voting import (
    VotingMethod,
    VotingSystem,
    VotingConfig,
    VotingResults,
)
from .proposal_models import (
    Proposal,
    _tier_from_priority,
    _VOTING_METHOD_BY_TIER,
    _THRESHOLD_BY_TIER,
    _QUORUM_DEFAULT,
    _build_voting_config,
    _ammendment_to_proposal,
)
from src.graph import get_graph_repository

logger = logging.getLogger(__name__)


class GovernanceProposalSystem:
    """Facade over the amendment / voting engines for the governance CLI."""

    def __init__(self, *, voting_window_hours: int = 168) -> None:
        amendment_cfg = AmendmentConfig(
            review_hours=24, deliberation_hours=72,
            minimum_monitoring_hours=48, voting_hours=voting_window_hours,
            minimum_co_sponsors=0,
        )
        voting_cfg = VotingConfig(
            method=VotingMethod.SIMPLE_MAJORITY, quorum_percentage=_QUORUM_DEFAULT,
            threshold_percentage=0.5, time_window_hours=voting_window_hours,
        )
        self._amendments = AmendmentSystem(config=amendment_cfg, voting_system=VotingSystem(voting_cfg))
        self._voting_window = voting_window_hours
        self._participants: dict[str, str] = {}

    def propose(
        self,
        title: str,
        description: str,
        text: str,
        proposer: str,
        tier: str,
        co_sponsors: Optional[list[str]] = None,
    ) -> Proposal:
        """Draft a new governance proposal."""
        if tier not in _VOTING_METHOD_BY_TIER:
            raise ValueError(f"tier must be one of {sorted(_VOTING_METHOD_BY_TIER)}; got {tier!r}")
        priority = {"soft": 1, "operational": 2, "foundational": 3}[tier]
        amendment = self._amendments.create_amendment(
            title=title, description=description, proposed_text=text,
            current_text="", proposer_id=proposer,
            co_sponsors=list(co_sponsors or []), priority=priority, estimated_impact=tier,
        )
        return _ammendment_to_proposal(amendment, tier)

    def submit(self, proposal_id: str) -> Proposal:
        """Move proposal from DRAFT -> SUBMITTED."""
        amendment = self._amendments.submit_amendment(proposal_id)
        return _ammendment_to_proposal(amendment, _tier_from_priority(amendment.priority))

    def start_vote(self, proposal_id: str) -> tuple[Proposal, VotingSystem]:
        """Advance to VOTING; returns (Proposal, VotingSystem for cast_vote)."""
        tier = _tier_from_priority(
            self._amendments.get_amendment(proposal_id).priority  # type: ignore[union-attr]
        )
        voting_cfg = _build_voting_config(tier, self._voting_window)
        amendment, _voting = self._amendments.start_voting(proposal_id, voting_config=voting_cfg)
        ends_at = amendment.voting_started_at and (
            amendment.voting_started_at + timedelta(hours=self._voting_window)
        )
        return _ammendment_to_proposal(amendment, tier, voting_ends_at=ends_at), self._amendments.voting_system

    def tally(self, proposal_id: str) -> tuple[Proposal, VotingResults]:
        """End voting and tally."""
        amendment = self._amendments.end_voting(proposal_id)
        tier = _tier_from_priority(amendment.priority)
        proposal = _ammendment_to_proposal(amendment, tier)
        results = amendment.voting_results or VotingResults(
            proposal_id=proposal_id, total_weight_cast=0, total_participants=0,
            yes_weight=0, no_weight=0, abstain_weight=0, recuse_weight=0,
            passed=False, quorum_met=False, threshold_met=False,
            timestamp=datetime.utcnow(), voter_summary={},
        )
        return proposal, results

    def get(self, proposal_id: str) -> Optional[Proposal]:
        amendment = self._amendments.get_amendment(proposal_id)
        if amendment is None:
            return None
        _graph_repo = get_graph_repository()
        _graph_repo.create_edge(proposal_id, amendment.proposer_id, "PROPOSED_BY")
        return _ammendment_to_proposal(amendment, _tier_from_priority(amendment.priority))

    def list_proposals(self, *, status: Optional[str] = None) -> list[Proposal]:
        amendments = self._amendments.list_amendments(
            status=AmendmentStatus(status) if status else None
        )
        _graph_repo = get_graph_repository()
        return [_ammendment_to_proposal(a, _tier_from_priority(a.priority)) for a in amendments]

    def record_voter(self, voter_id: str, key_id: str) -> None:
        """Register a member as eligible voter (kickoff primitive)."""
        _graph_repo = get_graph_repository()
        _graph_repo.create_entity("member", {"id": voter_id, "key_id": key_id, "role": "voter"})
        _graph_repo.create_edge(voter_id, key_id, "OWNS_KEY")
        self._participants[voter_id] = key_id


__all__ = [
    "Proposal", "GovernanceProposalSystem", "Amendment", "AmendmentSystem",
    "AmendmentConfig", "AmendmentStatus", "VotingMethod", "VotingSystem",
    "VotingConfig", "VotingResults", "_tier_from_priority",
    "_VOTING_METHOD_BY_TIER", "_THRESHOLD_BY_TIER", "_QUORUM_DEFAULT",
    "_build_voting_config", "_ammendment_to_proposal", "get_graph_repository",
]
