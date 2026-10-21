# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Monitoring, voting, ratification, implementation, and withdrawal for AmendmentSystem."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, Tuple

from .amendment_models import (
    Amendment,
    AmendmentConfig,
    AmendmentError,
    AmendmentStatus,
    QuorumError,
    StageTransitionError,
)
from .voting import VotingConfig, VotingMethod, VotingSystem

logger = logging.getLogger(__name__)


class AmendmentVotingMixin:
    """Mixin handling monitoring, voting, ratification, implementation, and withdrawal."""

    config: AmendmentConfig
    voting_system: VotingSystem
    _amendments: Dict[str, Amendment]
    _active_proposals: Set[str]

    def start_monitoring(self, amendment_id: str) -> Amendment:
        """Start monitoring period (pre-voting support assessment)."""
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]
        if amendment.status != AmendmentStatus.DELIBERATION:
            raise StageTransitionError(f"Cannot start monitoring from {amendment.status}")
        if not amendment.deliberation_started_at:
            raise AmendmentError("Deliberation never started")

        amendment.status = AmendmentStatus.MONITORING
        amendment.monitoring_started_at = datetime.utcnow()
        return amendment

    def start_voting(
        self,
        amendment_id: str,
        voting_config: Optional[VotingConfig] = None,
    ) -> Tuple[Amendment, VotingSystem]:
        """Start voting period."""
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]
        if amendment.status != AmendmentStatus.MONITORING:
            raise StageTransitionError(f"Cannot start voting from {amendment.status}")
        if not amendment.monitoring_started_at:
            raise AmendmentError("Monitoring never started")

        monitoring_duration = datetime.utcnow() - amendment.monitoring_started_at
        if monitoring_duration < timedelta(hours=amendment.minimum_support_period_hours):
            raise QuorumError(
                f"Minimum monitoring period not met: "
                f"{monitoring_duration} < {amendment.minimum_support_period_hours}h"
            )

        config = voting_config or VotingConfig(
            method=VotingMethod.SUPERMAJORITY,
            quorum_percentage=self.config.default_quorum,
            threshold_percentage=self.config.default_voting_threshold,
            time_window_hours=self.config.voting_hours,
        )
        amendment.voting_config = config
        amendment.status = AmendmentStatus.VOTING
        amendment.voting_started_at = datetime.utcnow()
        return amendment, self.voting_system

    def end_voting(self, amendment_id: str) -> Amendment:
        """End voting and tally results."""
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]
        if amendment.status != AmendmentStatus.VOTING:
            raise StageTransitionError(f"Cannot end voting in status {amendment.status}")
        if not amendment.voting_config:
            raise AmendmentError("No voting configuration")

        try:
            results = self.voting_system.tally_votes(amendment_id)
            amendment.voting_results = results
            amendment.voting_ended_at = datetime.utcnow()
            amendment.status = AmendmentStatus.PASSED if results.passed else AmendmentStatus.FAILED
        except ValueError as e:
            logger.error("Voting tally failed for %s: %s", amendment_id, e)
            raise AmendmentError(f"Voting tally failed: {e}") from e

        return amendment

    def ratify_amendment(self, amendment_id: str, ratified_by: str) -> Amendment:
        """Ratify a passed amendment."""
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]
        if amendment.status != AmendmentStatus.PASSED:
            raise StageTransitionError(f"Cannot ratify from status {amendment.status}")
        if not amendment.voting_results or not amendment.voting_results.passed:
            raise AmendmentError("Amendment did not pass voting")

        amendment.status = AmendmentStatus.RATIFIED
        amendment.ratified_at = datetime.utcnow()
        return amendment

    def implement_amendment(self, amendment_id: str, implemented_by: str) -> Amendment:
        """Mark amendment as implemented."""
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]
        if amendment.status != AmendmentStatus.RATIFIED:
            raise StageTransitionError(f"Cannot implement from status {amendment.status}")

        amendment.status = AmendmentStatus.IMPLEMENTED
        amendment.implemented_at = datetime.utcnow()
        self._active_proposals.discard(amendment_id)
        return amendment

    def withdraw_amendment(self, amendment_id: str, withdrawn_by: str, reason: str) -> Amendment:
        """Withdraw an amendment before voting completes."""
        if amendment_id not in self._amendments:
            raise AmendmentError(f"Amendment {amendment_id} not found")

        amendment = self._amendments[amendment_id]
        if amendment.status in (
            AmendmentStatus.IMPLEMENTED,
            AmendmentStatus.FAILED,
            AmendmentStatus.RATIFIED,
        ):
            raise AmendmentError(f"Cannot withdraw completed amendment: {amendment.status}")

        if withdrawn_by not in (amendment.proposer_id, *amendment.co_sponsors):
            raise AmendmentError("Only proposer or co-sponsors can withdraw")

        if (
            amendment.status == AmendmentStatus.VOTING
            and not self.config.allow_withdrawal_after_voting
        ):
            raise AmendmentError("Withdrawal not allowed after voting started")

        amendment.status = AmendmentStatus.WITHDRAWN
        self._active_proposals.discard(amendment_id)
        return amendment
