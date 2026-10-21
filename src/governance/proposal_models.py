# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Proposal read model and tier-to-voting configuration helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from .amendment import Amendment
from .voting import VotingConfig, VotingMethod, VotingResults


class Proposal:
    """Lightweight read model derived from `Amendment` for CLI display."""

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
