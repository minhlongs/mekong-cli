# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sanitize errors to prevent credential and internals leakage.

Redacts API keys, tokens, passwords, bearer tokens, authorization headers,
and PEM private keys from error messages before they leave the system.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_REDACTED = "[REDACTED]"

# Compiled patterns — order matters (more specific first)
_PATTERNS: list[re.Pattern[str]] = [
    # PEM private/public keys (multi-line)
    re.compile(
        r"-----BEGIN\s+[\w\s]+?KEY-----[\s\S]*?-----END\s+[\w\s]+?KEY-----",
        re.IGNORECASE,
    ),
    # api_key / api-key assignments
    re.compile(r"api[_-]?key\s*[=:]\s*\S+", re.IGNORECASE),
    # token assignments
    re.compile(r"token\s*[=:]\s*\S+", re.IGNORECASE),
    # password assignments
    re.compile(r"password\s*[=:]\s*\S+", re.IGNORECASE),
    # Bearer tokens
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),
    # Authorization header values
    re.compile(r"Authorization:\s*\S+", re.IGNORECASE),
]


def sanitize(error: Exception | str) -> str:
    """Return a sanitized string with credentials redacted.

    Accepts either an Exception (uses its string representation) or a
    plain string.  Original structure is preserved where possible — only
    matched patterns are replaced with ``[REDACTED]``.
    """
    text = str(error)
    for pattern in _PATTERNS:
        text = pattern.sub(_REDACTED, text)
    return text
