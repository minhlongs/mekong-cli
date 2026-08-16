# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Structured error types for the PEV (Plan-Execute-Verify) loop.

Hierarchy
---------
PEVError
├── PlanningError
├── ExecutionError
└── VerificationError

Every exception carries a stable ``error_code`` so callers can branch
without relying on string matching, plus optional ``step_order`` for
per-step context and a ``cause`` reference to the underlying exception.
"""
from __future__ import annotations

__all__ = [
    "PEVError",
    "PlanningError",
    "ExecutionError",
    "VerificationError",
]


class PEVError(Exception):
    """Base for all PEV-engine errors.

    Args:
        message: Human-readable description.
        error_code: Stable, machine-friendly identifier (e.g. ``PLAN_DECOMP_FAIL``)
            used by orchestrators for branching and retry decisions.
        step_order: 1-based order of the step that failed (if known).
        cause: Underlying exception that triggered the error.
    """

    error_code: str = "PEV_ERROR"

    def __init__(
        self,
        message: str = "",
        *,
        error_code: str | None = None,
        step_order: int | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        if error_code is not None:
            self.error_code = error_code
        self.step_order = step_order
        self.cause = cause

    def __str__(self) -> str:
        parts = [super().__str__(), f"code={self.error_code}"]
        if self.step_order is not None:
            parts.append(f"step={self.step_order}")
        if self.cause is not None:
            parts.append(f"cause={type(self.cause).__name__}: {self.cause}")
        return " | ".join(parts)


class PlanningError(PEVError):
    """Raised when the PLAN phase cannot produce an executable recipe."""

    error_code: str = "PLAN_ERROR"


class ExecutionError(PEVError):
    """Raised when the EXECUTE phase fails for a recipe step."""

    error_code: str = "EXEC_ERROR"


class VerificationError(PEVError):
    """Raised when the VERIFY phase detects quality-gate failures."""

    error_code: str = "VERIFY_ERROR"
