# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Phase Completion Detector — ROIaaS Final Phase

Detects when all six ROIaaS phases are fully operational and triggers
graceful shutdown sequence.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Awaitable, Callable, Dict, List, Optional

from rich.console import Console

from src.raas.phase_completion_checks_early import PhaseCompletionEarlyChecksMixin
from src.raas.phase_completion_checks_late import PhaseCompletionLateChecksMixin
from src.raas.phase_completion_models import (
    PhaseInfo,
    PhaseStatus,
    build_initial_phases,
)


class PhaseCompletionDetector(
    PhaseCompletionEarlyChecksMixin, PhaseCompletionLateChecksMixin
):
    """Detects when all ROIaaS phases are operational."""

    def __init__(self) -> None:
        self.console = Console()
        self._phases: Dict[str, PhaseInfo] = {}
        self._callbacks: List[Callable[[], Awaitable[None]]] = []
        self._all_operational = False
        self._last_check: Optional[datetime] = None
        self._check_interval = 30

        self._initialize_phases()

    def _initialize_phases(self) -> None:
        """Initialize all six ROIaaS phases."""
        self._phases = build_initial_phases()

    def register_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        """Register callback to be called when all phases become operational."""
        self._callbacks.append(callback)

    def get_phase_status(self, phase_id: str) -> Optional[PhaseInfo]:
        """Get status of a specific phase."""
        return self._phases.get(phase_id)

    def get_all_phases_status(self) -> Dict[str, PhaseInfo]:
        """Get status of all phases."""
        return self._phases.copy()

    def is_all_operational(self) -> bool:
        """Check if all phases are operational (sync method)."""
        return self._all_operational

    def get_last_check(self) -> Optional[datetime]:
        """Get timestamp of last phase check."""
        return self._last_check


# Global instance
_detector: Optional[PhaseCompletionDetector] = None


def get_detector() -> PhaseCompletionDetector:
    """Get global PhaseCompletionDetector instance."""
    global _detector
    if _detector is None:
        _detector = PhaseCompletionDetector()
    return _detector


def reset_detector() -> None:
    """Reset global detector instance (for testing)."""
    global _detector
    _detector = None


__all__ = [
    "PhaseStatus",
    "PhaseInfo",
    "PhaseCompletionDetector",
    "get_detector",
    "os",
    "reset_detector",
]
