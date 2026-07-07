"""Governance proposal facade for the ZenOS Commons kickoff.

Delegates to existing engines:
- Amendment system (state machine: DRAFT -> SUBMITTED -> REVIEW -> DELIBERATION -> ...)
- Voting system (reputation-weighted tally with quorum)
- Sanctions / Dispute systems (available via import)

Provides a single entry + a small, YAGNI-scoped read API so the CLI layer
doesn't reach into the Amendment dataclasses directly.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

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
from src.graph import get_graph_repository

logger = logging.getLogger(__name__)

# ---- lightweight proposal summary (what CLI surface shows) ----


class Proposal:
    """Lightweight read model derived from `Amendment` for CLI display.

    Attributes mirror ZENOS Article 9 / zenos-commons.md tiers:
    Soft / Operational / Foundational
    """

    __slots__ = (
        "id",
        "title",
        "status",
        "tier",
        "proposer",
        "co_sponsors",
        "submitted_at",
        "voting_ends_at",
        "results",
    )

    def __init__(
        self,
        id: str,
        title: str,
        status: str,
        tier: str,
        proposer: str,
        co_sponsors: Optional[list[str]] = None,
        submitted_at: Optional[datetime] = None,
        voting_ends_at: Optional[datetime] = None,
        results: Optional[VotingResults] = None,
    ) -> None:
        self.id = id
        self.title = title
        self.status = status
        self.tier = tier
        self.proposer = proposer
        self.co_sponsors = list(co_sponsors or [])
        self.submitted_at = submitted_at
        self.voting_ends_at = voting_ends_at
        self.results = results

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "tier": self.tier,
            "proposer": self.proposer,
            "co_sponsors": self.co_sponsors,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "voting_ends_at": self.voting_ends_at.isoformat() if self.voting_ends_at else None,
            "results": {
                "passed": self.results.passed,
                "quorum_met": self.results.quorum_met,
                "threshold_met": self.results.threshold_met,
                "yes_weight": self.results.yes_weight,
                "no_weight": self.results.no_weight,
                "total_participants": self.results.total_participants,
            }
            if self.results
            else None,
        }


def _tier_from_priority(priority: int) -> str:
    if priority <= 1:
        return "soft"
    if priority == 2:
        return "operational"
    return "foundational"


_VOTING_METHOD_BY_TIER: dict[str, str] = {
    "soft": VotingMethod.SIMPLE_MAJORITY.value,
    "operational": VotingMethod.SUPERMAJORITY.value,
    "foundational": VotingMethod.SUPERMAJORITY.value,
}

_THRESHOLD_BY_TIER: dict[str, float] = {
    "soft": 0.5,
    "operational": 0.75,
    "foundational": 0.75,
}

_QUORUM_DEFAULT = 0.4


def _build_voting_config(tier: str, time_window_hours: int) -> VotingConfig:
    return VotingConfig(
        method=VotingMethod(_VOTING_METHOD_BY_TIER[tier]),
        quorum_percentage=_QUORUM_DEFAULT,
        threshold_percentage=_THRESHOLD_BY_TIER[tier],
        time_window_hours=time_window_hours,
        allow_abstention=True,
        allow_delegation=True,
        max_delegation_chain=3,
        recusal_allowed=True,
    )


# ---- facade ----


class GovernanceProposalSystem:
    """Facade over the amendment / voting engines for the governance CLI.

    Lifetime: one process. State lives in memory (no persistence) — this
    is the same assumption as the existing engines and matches the kickoff
    scope.
    """

    def __init__(
        self,
        *,
        voting_window_hours: int = 168,
    ) -> None:
        amendment_cfg = AmendmentConfig(
            review_hours=24,
            deliberation_hours=72,
            minimum_monitoring_hours=48,
            voting_hours=voting_window_hours,
            minimum_co_sponsors=0,  # YAGNI: founder-only during kickoff
        )
        voting_cfg = VotingConfig(
            method=VotingMethod.SIMPLE_MAJORITY,
            quorum_percentage=_QUORUM_DEFAULT,
            threshold_percentage=0.5,
            time_window_hours=voting_window_hours,
        )
        self._amendments = AmendmentSystem(
            config=amendment_cfg,
            voting_system=VotingSystem(voting_cfg),
        )
        self._voting_window = voting_window_hours
        self._participants: dict[str, str] = {}
        logger.info(
            "GovernanceProposalSystem ready (window=%dh)", voting_window_hours
        )

    # ---- lifecycle ----

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
            raise ValueError(
                f"tier must be one of {sorted(_VOTING_METHOD_BY_TIER)}; got {tier!r}"
            )
        priority = {"soft": 1, "operational": 2, "foundational": 3}[tier]
        amendment = self._amendments.create_amendment(
            title=title,
            description=description,
            proposed_text=text,
            current_text="",
            proposer_id=proposer,
            co_sponsors=list(co_sponsors or []),
            priority=priority,
            estimated_impact=tier,
        )
        return _ammendment_to_proposal(amendment, tier)

    def submit(self, proposal_id: str) -> Proposal:
        """Move proposal from DRAFT -> SUBMITTED."""
        amendment = self._amendments.submit_amendment(proposal_id)
        return _ammendment_to_proposal(
            amendment, _tier_from_priority(amendment.priority)
        )

    def start_vote(self, proposal_id: str) -> tuple[Proposal, VotingSystem]:
        """Advance to VOTING; returns (Proposal, VotingSystem for cast_vote)."""
        tier = _tier_from_priority(
            self._amendments.get_amendment(proposal_id).priority
        )
        voting_cfg = _build_voting_config(tier, self._voting_window)
        amendment, voting = self._amendments.start_voting(
            proposal_id, voting_config=voting_cfg
        )
        ends_at = amendment.voting_started_at and (
            amendment.voting_started_at
            + timedelta(hours=self._voting_window) 
        )
        proposal = _ammendment_to_proposal(
            amendment, tier, voting_ends_at=ends_at
        )
        # Return a VotingSystem pre-seeded with no voters so the CLI can
        # register participants before casting. In kickoff mode we add them
        # outside in tests; in production a member registry will drive this.
        return proposal, self._amendments.voting_system

    def tally(self, proposal_id: str) -> tuple[Proposal, VotingResults]:
        """End voting and tally."""
        amendment = self._amendments.end_voting(proposal_id)
        tier = _tier_from_priority(amendment.priority)
        proposal = _ammendment_to_proposal(amendment, tier)
        results = amendment.voting_results or VotingResults(
            proposal_id=proposal_id,
            total_weight_cast=0,
            total_participants=0,
            yes_weight=0,
            no_weight=0,
            abstain_weight=0,
            recuse_weight=0,
            passed=False,
            quorum_met=False,
            threshold_met=False,
            timestamp=datetime.utcnow(),
            voter_summary={},
        )
        return proposal, results

    def get(self, proposal_id: str) -> Optional[Proposal]:
        amendment = self._amendments.get_amendment(proposal_id)
        if amendment is None:
            return None
        graph_repo = get_graph_repository()
        graph_repo.create_edge(
            proposal_id, amendment.proposer_id, "PROPOSED_BY"
        )
        return _ammendment_to_proposal(
            amendment, _tier_from_priority(amendment.priority)
        )

    def list_proposals(self, *, status: Optional[str] = None) -> list[Proposal]:
        amendments = self._amendments.list_amendments(
            status=AmendmentStatus(status) if status else None
        )
        graph_repo = get_graph_repository()
        return [
            _ammendment_to_proposal(a, _tier_from_priority(a.priority))
            for a in amendments
        # filter removed: has_node is not part of GraphRepository API
        ]

    def record_voter(self, voter_id: str, key_id: str) -> None:
        """Register a member as eligible voter (kickoff primitive)."""
        graph_repo = get_graph_repository()
        graph_repo.create_entity("member", {"id": voter_id, "key_id": key_id, "role": "voter"})
        graph_repo.create_edge(voter_id, key_id, "OWNS_KEY")
        self._participants[voter_id] = key_id

    # ---- helpers ----


def _ammendment_to_proposal(
    amendment: Amendment,
    tier: str,
    voting_ends_at: Optional[datetime] = None,
) -> Proposal:
    return Proposal(
        id=amendment.id,
        title=amendment.title,
        status=amendment.status.value,
        tier=tier,
        proposer=amendment.proposer_id,
        co_sponsors=list(amendment.co_sponsors),
        submitted_at=amendment.submitted_at,
        voting_ends_at=voting_ends_at,
        results=amendment.voting_results,
    )
