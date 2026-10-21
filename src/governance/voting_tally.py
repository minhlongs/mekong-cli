# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vote tallying and inspection methods for VotingSystem."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Set

from .voting_models import (
    DelegationCycleError,
    Vote,
    Voter,
    VoteType,
    VotingConfig,
    VotingMethod,
    VotingResults,
)

logger = logging.getLogger(__name__)


class VotingTallyMixin:
    """Mixin providing vote tallying, breakdown inspection, and cleanup."""

    config: VotingConfig
    _active_votes: Dict[str, List[Vote]]
    _voters: Dict[str, Voter]

    def tally_votes(self, proposal_id: str) -> VotingResults:
        """Tally votes for a proposal and determine outcome."""
        if proposal_id not in self._active_votes or not self._active_votes[proposal_id]:
            raise ValueError(f"No votes found for proposal {proposal_id}")

        votes = self._active_votes[proposal_id]

        yes_weight = sum(v.weight for v in votes if v.vote_type == VoteType.YES)
        no_weight = sum(v.weight for v in votes if v.vote_type == VoteType.NO)
        abstain_weight = sum(v.weight for v in votes if v.vote_type == VoteType.ABSTAIN)
        recuse_weight = sum(v.weight for v in votes if v.vote_type == VoteType.RECUSE)
        total_weight = yes_weight + no_weight

        unique_voters: Set[str] = set()
        for vote in votes:
            try:
                final_voter, _ = self._resolve_delegation(vote.voter_id)  # type: ignore[attr-defined]
                unique_voters.add(final_voter)
            except DelegationCycleError:
                unique_voters.add(vote.voter_id)

        total_participants = len(unique_voters)

        voter_summary: Dict[str, int] = {}
        for vt in VoteType:
            voter_summary[vt.value] = sum(1 for v in votes if v.vote_type == vt)

        eligible_voters = sum(1 for v in self._voters.values() if v.is_active)
        quorum_threshold = eligible_voters * self.config.quorum_percentage
        quorum_met = total_participants >= quorum_threshold

        if self.config.method == VotingMethod.SUPERMAJORITY:
            threshold_met = (
                total_weight > 0
                and (yes_weight / total_weight) >= self.config.threshold_percentage
            )
        elif self.config.method == VotingMethod.CONSENSUS:
            threshold_met = (
                (yes_weight / total_weight) >= self.config.threshold_percentage
                if total_weight > 0
                else False
            )
        else:
            threshold_met = yes_weight > no_weight

        passed = quorum_met and threshold_met

        results = VotingResults(
            proposal_id=proposal_id,
            total_weight_cast=total_weight + abstain_weight + recuse_weight,
            total_participants=total_participants,
            yes_weight=yes_weight,
            no_weight=no_weight,
            abstain_weight=abstain_weight,
            recuse_weight=recuse_weight,
            passed=passed,
            quorum_met=quorum_met,
            threshold_met=threshold_met,
            timestamp=datetime.utcnow(),
            voter_summary=voter_summary,
        )

        logger.info(
            "Tally complete for %s: %s (quorum: %s, threshold: %s)",
            proposal_id,
            "PASSED" if passed else "FAILED",
            quorum_met,
            threshold_met,
        )
        return results

    def get_vote_details(self, proposal_id: str) -> List[Dict[str, Any]]:
        """Get detailed breakdown of votes for a proposal."""
        if proposal_id not in self._active_votes:
            return []

        return [
            {
                "voter_id": vote.voter_id,
                "vote_type": vote.vote_type.value,
                "weight": vote.weight,
                "timestamp": vote.timestamp.isoformat(),
                "rationale": vote.rationale,
            }
            for vote in self._active_votes[proposal_id]
        ]

    def clear_votes(self, proposal_id: str) -> None:
        """Clear votes for a proposal (for cleanup after completion)."""
        if proposal_id in self._active_votes:
            del self._active_votes[proposal_id]
            logger.debug("Cleared votes for %s", proposal_id)

    def get_active_vote_count(self) -> int:
        """Get number of proposals with active votes."""
        return len(self._active_votes)
