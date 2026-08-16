# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Shared i18n helper for Mekong CLI."""
from __future__ import annotations

from typing import Optional

from src.cli.i18n.registry import (
    VALID_LOCALES,
    DEFAULT_LOCALE,
    VI,
    _VI,
    get_messages,
    t,
)


def get_locale(locale: Optional[str]) -> str:
    return locale if locale in VALID_LOCALES else DEFAULT_LOCALE


__all__ = [
    "t",
    "get_messages",
    "get_locale",
    "VALID_LOCALES",
    "DEFAULT_LOCALE",
    "VI",
    "_VI",
]
