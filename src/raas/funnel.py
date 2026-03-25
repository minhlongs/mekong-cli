"""Mekong CLI - Acquisition Funnel Tracker.

Tracks user progression through the 8-stage acquisition funnel
from first visit to referral.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Optional


class FunnelStage(IntEnum):
    """Funnel stages in order of progression."""

    VISIT = 0
    INSTALL = 1
    FIRST_COOK = 2
    THIRD_COOK = 3
    LIMIT_HIT = 4
    UPGRADE = 5
    TEAM_INVITE = 6
    REFERRAL = 7


# Target conversion rates between stages
_TARGET_RATES: Dict[tuple[FunnelStage, FunnelStage], float] = {
    (FunnelStage.VISIT, FunnelStage.INSTALL): 0.15,
    (FunnelStage.INSTALL, FunnelStage.FIRST_COOK): 0.60,
    (FunnelStage.FIRST_COOK, FunnelStage.THIRD_COOK): 0.40,
    (FunnelStage.THIRD_COOK, FunnelStage.LIMIT_HIT): 0.50,
    (FunnelStage.LIMIT_HIT, FunnelStage.UPGRADE): 0.10,
    (FunnelStage.UPGRADE, FunnelStage.TEAM_INVITE): 0.20,
    (FunnelStage.TEAM_INVITE, FunnelStage.REFERRAL): 0.15,
}


@dataclass
class StageMetrics:
    """Metrics for a single funnel stage."""

    stage: FunnelStage
    count: int = 0
    target_rate: float = 0.0


@dataclass
class FunnelSnapshot:
    """Point-in-time snapshot of all funnel stages."""

    stages: Dict[FunnelStage, int] = field(default_factory=dict)

    def conversion_rate(
        self, from_stage: FunnelStage, to_stage: FunnelStage
    ) -> float:
        """Calculate conversion rate between two stages.

        Args:
            from_stage: Source stage.
            to_stage: Target stage.

        Returns:
            Conversion rate as a float (0.0 to 1.0).
        """
        from_count = self.stages.get(from_stage, 0)
        to_count = self.stages.get(to_stage, 0)
        if from_count == 0:
            return 0.0
        return round(to_count / from_count, 4)


class FunnelTracker:
    """Track user progression through the acquisition funnel.

    8 stages: visit → install → first_cook → third_cook →
    limit_hit → upgrade → team_invite → referral
    """

    def __init__(self) -> None:
        """Initialize with zero counts for all stages."""
        self._counts: Dict[FunnelStage, int] = {
            stage: 0 for stage in FunnelStage
        }

    def record(self, stage: FunnelStage, count: int = 1) -> None:
        """Record events at a funnel stage.

        Args:
            stage: The funnel stage to record.
            count: Number of events (default 1).
        """
        self._counts[stage] = self._counts.get(stage, 0) + count

    def snapshot(self) -> FunnelSnapshot:
        """Get current funnel snapshot.

        Returns:
            FunnelSnapshot with current counts.
        """
        return FunnelSnapshot(stages=dict(self._counts))

    def conversion_rate(
        self, from_stage: FunnelStage, to_stage: FunnelStage
    ) -> float:
        """Calculate conversion rate between two stages.

        Args:
            from_stage: Source stage.
            to_stage: Target stage.

        Returns:
            Conversion rate as a float (0.0 to 1.0).
        """
        return self.snapshot().conversion_rate(from_stage, to_stage)

    def target_rate(
        self, from_stage: FunnelStage, to_stage: FunnelStage
    ) -> Optional[float]:
        """Get target conversion rate for a stage transition.

        Args:
            from_stage: Source stage.
            to_stage: Target stage.

        Returns:
            Target rate if defined, None otherwise.
        """
        return _TARGET_RATES.get((from_stage, to_stage))

    def stage_metrics(self) -> list[StageMetrics]:
        """Get metrics for all stages.

        Returns:
            List of StageMetrics for each stage.
        """
        metrics: list[StageMetrics] = []
        stages = list(FunnelStage)
        for i, stage in enumerate(stages):
            target = 0.0
            if i > 0:
                prev = stages[i - 1]
                target = _TARGET_RATES.get((prev, stage), 0.0)
            metrics.append(
                StageMetrics(
                    stage=stage,
                    count=self._counts.get(stage, 0),
                    target_rate=target,
                )
            )
        return metrics

    def reset(self) -> None:
        """Reset all counts to zero."""
        self._counts = {stage: 0 for stage in FunnelStage}


__all__ = ["FunnelSnapshot", "FunnelStage", "FunnelTracker", "StageMetrics"]
