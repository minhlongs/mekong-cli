# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""P1 and P2 constitutional audit check functions."""

from __future__ import annotations

import re

from src.mekong.constitution.parser import Constitution

_ANTI_CONCENTRATION_KEYWORDS: list[str] = [
    "multi-sig",
    "multisig",
    "checks and balances",
    "separation of powers",
    "term limit",
    "rotation",
    "quorum",
    "super-majority",
    "supermajority",
    "veto",
    "oversight",
    "audit committee",
    "board",
    "council",
]

_AI_BOUNDARY_KEYWORDS: list[str] = [
    "ai cell",
    "ai limit",
    "ai agent",
    "automation boundary",
    "ai cannot",
    "ai shall not",
    "artificial intelligence",
    "autonomous agent",
    "machine decision",
    "algorithmic",
    "boundary",
    "automation limit",
    "decision autonomy",
]

_OSTROM_PRINCIPLES: list[tuple[str, list[str]]] = [
    ("Clearly defined boundaries", ["boundar", "membership", "inclusion", "define", "who may"]),
    ("Proportional equivalence", ["proportional", "equivalence", "cost", "benefit", "fair share"]),
    ("Collective-choice arrangements", ["collective", "vote", "democratic", "consensus", "decision"]),
    ("Monitoring", ["monitor", "audit", "transparency", "oversight", "review"]),
    ("Graduated sanctions", ["sanction", "penalt", "consequence", "graduated", "escalat"]),
    ("Conflict-resolution mechanisms", ["conflict", "dispute", "resolution", "arbitration", "mediation"]),
    ("Minimal recognition of rights", ["right to organize", "autonom", "self-govern", "right to"]),
    ("Nested enterprises", ["nested", "layer", "enterprise", "subsidiar", "multi-level"]),
]

_NAMING_EXPECTATIONS: list[tuple[str, re.Pattern]] = [
    ("Mission", re.compile(r"mission", re.IGNORECASE)),
    ("Exit", re.compile(r"exit|withdraw", re.IGNORECASE)),
    ("Governance", re.compile(r"govern", re.IGNORECASE)),
]


def _has_anti_concentration(c: Constitution) -> tuple[bool, str]:
    """The constitution should define anti-concentration mechanisms."""
    combined = "\n".join(a.content for a in c.articles).lower()
    found = [kw for kw in _ANTI_CONCENTRATION_KEYWORDS if kw in combined]
    if not found:
        return False, "No anti-concentration mechanisms found"
    return True, ""


def _has_ai_boundaries(c: Constitution) -> tuple[bool, str]:
    """The constitution should define AI Cell limits."""
    combined = "\n".join(a.content for a in c.articles).lower()
    found = [kw for kw in _AI_BOUNDARY_KEYWORDS if kw in combined]
    if not found:
        return False, "No AI Cell boundaries or automation limits defined"
    return True, ""


def _count_ostrom_principles(c: Constitution) -> tuple[bool, str]:
    """Report how many of 8 Ostrom design principles are addressed."""
    combined = "\n".join(a.content for a in c.articles).lower()
    addressed = 0
    for _name, keywords in _OSTROM_PRINCIPLES:
        if any(kw in combined for kw in keywords):
            addressed += 1
    total = len(_OSTROM_PRINCIPLES)
    return True, f"Addresses {addressed}/{total} Ostrom principles"


def _ostrom_principles_detail(c: Constitution) -> tuple[bool, str]:
    """List which Ostrom principles are present / missing."""
    combined = "\n".join(a.content for a in c.articles).lower()
    present: list[str] = []
    missing: list[str] = []
    for name, keywords in _OSTROM_PRINCIPLES:
        if any(kw in combined for kw in keywords):
            present.append(name)
        else:
            missing.append(name)
    detail = ""
    if present:
        detail += f"Present: {', '.join(present)}\n"
    if missing:
        detail += f"Missing: {', '.join(missing)}"
    return True, detail.strip()


def _check_article_naming(c: Constitution) -> tuple[bool, str]:
    """Check that key articles have descriptive titles."""
    titles_lower = [t.lower() for t in c.article_titles]
    missing_names = [
        name for name, pat in _NAMING_EXPECTATIONS
        if not any(pat.search(t) for t in titles_lower)
    ]
    if missing_names:
        return False, f"Articles missing expected names: {', '.join(missing_names)}"
    return True, "All key articles have descriptive titles"
