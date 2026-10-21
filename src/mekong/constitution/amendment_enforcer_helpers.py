# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helper functions for extended constitutional audit and contradiction detection."""

from __future__ import annotations

import re

from src.mekong.constitution.parser import Constitution
from src.mekong.constitution.review import RuleResult


def _detect_contradictions(cons: Constitution) -> list[dict]:
    """Return a list of dicts describing cross-article contradictions."""
    out: list[dict] = []
    seen: set[tuple[int, int]] = set()
    for i, a in enumerate(cons.articles):
        for j, b in enumerate(cons.articles):
            if i >= j:
                continue
            pair = (a.number, b.number)
            if pair in seen:
                continue
            seen.add(pair)
            sim = _keyword_overlap(a.content, b.content)
            if sim > 0.7:
                out.append(
                    {
                        "articles": [a.number, b.number],
                        "titles": [a.title, b.title],
                        "similarity": round(sim, 3),
                        "note": "High text overlap — manual review recommended",
                    }
                )
    return out


def _keyword_overlap(a: str, b: str) -> float:
    sa = set(_tokens(a))
    sb = set(_tokens(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(len(sa | sb), 1)


def _tokens(text: str) -> list[str]:
    text = (text or "").lower()
    words = re_pat(r"[a-z]{3,}").findall(text)
    return [
        w for w in words
        if w not in {"the", "and", "for", "that", "with", "this", "from", "have", "been"}
    ]


def _rule_fail(rule_id: str, message: str, con: Constitution) -> RuleResult:
    return RuleResult(rule_id=rule_id, severity="FAIL", message=message, article_ref=con.name)


def _rule_warn(rule_id: str, message: str, con: Constitution) -> RuleResult:
    return RuleResult(rule_id=rule_id, severity="WARN", message=message, article_ref=con.name)


def re_pat(pat: str, flags: int = 0):
    return re.compile(pat, flags)


def re_flags() -> int:
    return re.IGNORECASE | re.MULTILINE
