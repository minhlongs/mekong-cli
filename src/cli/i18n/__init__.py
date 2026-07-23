"""Shared i18n helper for Mekong CLI."""
from __future__ import annotations

from typing import Optional

from src.cli.commands.company_init.i18n import (
    PROMPT_EN,
    PROMPT_VI,
    _get_locale,
    get_messages,
)


def t(key: str, locale: Optional[str] = None, default: str = "") -> str:
    """Return translated string for *key* in target locale."""
    locale = _get_locale(locale)
    return get_messages(locale).get(key) or get_messages(locale).get(key, default) or default


__all__ = ["t", "get_messages", "PROMPT_EN", "PROMPT_VI"]
