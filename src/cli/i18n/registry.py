# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Central i18n registry for Mekong CLI."""

DEFAULT_LOCALE = "en"
VALID_LOCALES = ["en", "vi"]

VI = "vi"
_VI = "vi"

_MESSAGES: dict[str, dict[str, str]] = {}


def register(locale: str, messages: dict[str, str]) -> None:
    _MESSAGES[locale] = messages


def get_messages(locale: str) -> dict[str, str]:
    return _MESSAGES.get(locale, _MESSAGES.get(DEFAULT_LOCALE, {}))


def t(locale: str, key: str, default: str = "") -> str:
    return get_messages(locale).get(key) or get_messages(DEFAULT_LOCALE).get(key) or default
