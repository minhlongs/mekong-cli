# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""IP command VND amount formatting — Vietnamese dot thousands separators."""

from __future__ import annotations


def format_vnd(amount: float) -> str:
    """Render a VND amount with Vietnamese dot thousands separators."""
    return f"{round(amount):,} VND".replace(",", ".")
