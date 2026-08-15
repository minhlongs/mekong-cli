"""Prompt injection + dangerous-code pattern guard — PDF BƯỚC 4.4.1.

Regex-only detection wired into POST /task. No LLM round-trip, no network.
Intentionally heuristic: server is cheap first line, not last line, of defense.
"""

from __future__ import annotations

import re

INJECTION_PATTERNS: tuple[str, ...] = (
    r"ignore\s+(all\s+)?(previous|above)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(everything|all)",
    r"new\s+system\s+prompt",
    r"you\s+are\s+now",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"system\s*:\s*",
    r"\bsudo\s+",
    r"<script\b",
    r"javascript\s*:",
    r"vbscript\s*:",
    r"\bonerror\s*=",
    r"\bonload\s*=",
)

DANGEROUS_CODE_PATTERNS: tuple[str, ...] = (
    r"\brm\s+-rf\b",
    r"\bDROP\s+TABLE\b",
    r"\bDELETE\s+FROM\b",
    r"\bTRUNCATE\s+TABLE\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"__import__\s*\(",
    r"\bos\.system\b",
    r"\bsubprocess\.",
    r"\bshell_exec\b",
    r"\bpopen\b",
    r"\bpassthru\s*\(",
    r"\bfs\.unlink\b",
    r"\bfs\.rmdir\b",
)

_INJ = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
_DNG = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_CODE_PATTERNS]
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MAX_LEN = 10_000


def detect_prompt_injection(text: str) -> tuple[bool, list[str]]:
    """Return (has_match, [pattern, ...]) for injection-style phrases."""
    hits = [p for p, r in zip(INJECTION_PATTERNS, _INJ, strict=True) if r.search(text)]
    return bool(hits), hits


def detect_dangerous_code(text: str) -> tuple[bool, list[str]]:
    """Return (has_match, [pattern, ...]) for destructive command shapes."""
    hits = [p for p, r in zip(DANGEROUS_CODE_PATTERNS, _DNG, strict=True) if r.search(text)]
    return bool(hits), hits


def sanitize_input(text: str) -> str:
    """Strip NULs + control chars, cap at 10k chars with truncate marker."""
    cleaned = _CTRL.sub("", text)
    if len(cleaned) > _MAX_LEN:
        cleaned = cleaned[:_MAX_LEN] + "... [truncated]"
    return cleaned
