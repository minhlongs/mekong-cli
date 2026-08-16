# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Backward-compat shim — logic moved to src/raas/billing_proration.py"""
from src.raas.billing_proration import (  # noqa: F401
    ProrationResult,
    OverageCalculation,
    ProrationCalculator,
    OverageTracker,
    get_calculator,
    reset_calculator,
)

__all__ = [
    "ProrationResult",
    "OverageCalculation",
    "ProrationCalculator",
    "OverageTracker",
    "get_calculator",
    "reset_calculator",
]
