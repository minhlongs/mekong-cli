"""CAI research-backed constitutional rules organised by severity.

Rule severities follow the P0/P1/P2 scheme from the Constitutional Sandbox plan:

- **P0 (FAIL)**:  Structural or contradiction errors that make a constitution
  unsafe. A single P0 failure produces a ``FAIL`` verdict.
- **P1 (WARNING)**:  Patterns that weaken alignment — anti-concentration gaps,
  missing AI boundaries, broad missions. Produces a ``WARNINGS`` verdict.
- **P2 (INFO)**:  Governance best practices and Ostrom principle coverage.
  Does not affect the verdict.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from src.mekong.constitution.parser import Constitution

# ---------------------------------------------------------------------------
# Rule data type
# ---------------------------------------------------------------------------

RuleCheck = Callable[[Constitution], tuple[bool, str]]
"""A rule check function.

Returns ``(passed, message)`` where *passed* is ``True`` when the
constitution satisfies the rule.
"""


@dataclass
class Rule:
    """A single constitutional audit rule."""

    id: str
    severity: str  # "FAIL" | "WARNING" | "INFO"
    check: RuleCheck
    message: str


# Convenience factory helpers
def fail_rule(rule_id: str, check: RuleCheck, message: str) -> Rule:
    return Rule(id=rule_id, severity="FAIL", check=check, message=message)


def warn_rule(rule_id: str, check: RuleCheck, message: str) -> Rule:
    return Rule(id=rule_id, severity="WARNING", check=check, message=message)


def info_rule(rule_id: str, check: RuleCheck, message: str) -> Rule:
    return Rule(id=rule_id, severity="INFO", check=check, message=message)


# ---------------------------------------------------------------------------
# P0 — Structural completeness: missing required articles
# ---------------------------------------------------------------------------


def _no_empty_articles(c: Constitution) -> tuple[bool, str]:
    """No articles may be entirely empty (including whitespace-only)."""
    empties = [a for a in c.articles if not a.content.strip()]
    if empties:
        titles = ", ".join(a.title for a in empties)
        return False, f"Empty articles found: {titles}"
    return True, ""


# ---------------------------------------------------------------------------
# P0 — Self-contradiction detection
# ---------------------------------------------------------------------------

# Pairs of keyword groups that indicate a governance contradiction when the
# same constitution mentions both (spread across different articles).
_CONTRADICTION_PAIRS: list[tuple[list[str], list[str], str]] = [
    (
        ["founder", "ceo", "single leader", "sole authority", "dictator"],
        ["community vote", "democratic", "consensus", "all members decide"],
        "Governance: single-rule model conflicts with democratic model",
    ),
    (
        ["mission over profit", "mission integrity", "purpose first"],
        ["shareholder value", "investor return", "profit maximization"],
        "Mission-first and profit-first provisions contradict each other",
    ),
    (
        ["no amendments", "cannot be changed", "immutable constitution", "permanently locked"],
        ["amendment process", "can be changed", "right to amend"],
        "Amendment prohibition conflicts with amendment process",
    ),
]


def _no_governance_contradiction(c: Constitution) -> tuple[bool, str]:
    """Detect contradictory governance provisions — within the SAME article only."""
    for group_a, group_b, msg in _CONTRADICTION_PAIRS:
        for article in c.articles:
            content = article.content.lower()
            has_a = any(kw in content for kw in group_a)
            has_b = any(kw in content for kw in group_b)
            if has_a and has_b:
                return False, f"Article {article.number}: {msg}"
    return True, ""


# ---------------------------------------------------------------------------
# P1 — Adversarial patterns (from ASIMOV / Reverse CAI research)
# ---------------------------------------------------------------------------

_ADVERSARIAL_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"(absolute|unlimited|unchecked|total|unrestricted)\s+"
            r"(authority|power|control|discretion)",
            re.IGNORECASE,
        ),
        "Grants absolute or unchecked authority without checks",
    ),
    (
        re.compile(
            r"(unilateral(ly)?|sole|alone)\s+(can|may)\s+(amend|change|modify|rewrite)",
            re.IGNORECASE,
        ),
        "Allows unilateral constitutional amendment",
    ),
    (
        re.compile(
            r"(cannot|never|shall not)\s+be\s+(changed|amended|modified|altered)",
            re.IGNORECASE,
        ),
        "Constitution is declared immutable — no amendment mechanism",
    ),
    (
        re.compile(
            r"(mission|purpose|objective)\s+is\s+to\s+(do\s+)?(anything|everything|any|all)",
            re.IGNORECASE,
        ),
        "Mission statement is overly broad or unfalsifiable",
    ),
]


def _no_adversarial_patterns(c: Constitution) -> tuple[bool, str]:
    """Warn on patterns that weaken constitutional alignment."""
    combined = "\n".join(
        f"[Article {a.number}: {a.title}] {a.content}" for a in c.articles
    )
    for pattern, msg in _ADVERSARIAL_PATTERNS:
        if pattern.search(combined):
            return False, msg
    return True, ""


# ---------------------------------------------------------------------------
# P1 — Anti-concentration checks
# ---------------------------------------------------------------------------

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


def _has_anti_concentration(c: Constitution) -> tuple[bool, str]:
    """The constitution should define anti-concentration mechanisms."""
    combined = "\n".join(a.content for a in c.articles).lower()
    found = [kw for kw in _ANTI_CONCENTRATION_KEYWORDS if kw in combined]
    if not found:
        return False, "No anti-concentration mechanisms found"
    return True, ""


# ---------------------------------------------------------------------------
# P1 — AI Cell boundaries
# ---------------------------------------------------------------------------

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


def _has_ai_boundaries(c: Constitution) -> tuple[bool, str]:
    """The constitution should define AI Cell limits."""
    combined = "\n".join(a.content for a in c.articles).lower()
    found = [kw for kw in _AI_BOUNDARY_KEYWORDS if kw in combined]
    if not found:
        return False, "No AI Cell boundaries or automation limits defined"
    return True, ""


# ---------------------------------------------------------------------------
# P2 — Ostrom principles coverage
# ---------------------------------------------------------------------------

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


def _count_ostrom_principles(c: Constitution) -> tuple[bool, str]:
    """Report how many of 8 Ostrom design principles are addressed."""
    combined = "\n".join(a.content for a in c.articles).lower()
    addressed = 0
    addressed_names: list[str] = []
    for name, keywords in _OSTROM_PRINCIPLES:
        if any(kw in combined for kw in keywords):
            addressed += 1
            addressed_names.append(name)
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


# ---------------------------------------------------------------------------
# P2 — Best practice: article naming
# ---------------------------------------------------------------------------

_NAMING_EXPECTATIONS: list[tuple[str, re.Pattern]] = [
    ("Mission", re.compile(r"mission", re.IGNORECASE)),
    ("Exit", re.compile(r"exit|withdraw", re.IGNORECASE)),
    ("Governance", re.compile(r"govern", re.IGNORECASE)),
]


def _check_article_naming(c: Constitution) -> tuple[bool, str]:
    """Check that key articles have descriptive titles."""
    titles_lower = [t.lower() for t in c.article_titles]
    missing_names = [name for name, pat in _NAMING_EXPECTATIONS
                     if not any(pat.search(t) for t in titles_lower)]
    if missing_names:
        return False, f"Articles missing expected names: {', '.join(missing_names)}"
    return True, "All key articles have descriptive titles"


# ---------------------------------------------------------------------------
# Full rule registry
# ---------------------------------------------------------------------------

RULES: list[Rule] = [
    # -- P0: Structural --
    fail_rule(
        "MISSION_REQUIRED",
        lambda c: (
            c.has_category("mission") or
            any("mission" in a.title.lower() for a in c.articles),
            "Constitution must include a Mission article",
        ),
        "Constitution must include a Mission article [REQUIRED]",
    ),
    fail_rule(
        "EXIT_REQUIRED",
        lambda c: (
            c.has_category("exit") or
            any("exit" in a.title.lower() or "withdraw" in a.title.lower()
                for a in c.articles),
            "Constitution must include a Right to Exit article",
        ),
        "Constitution must include a Right to Exit article [REQUIRED]",
    ),
    fail_rule(
        "ANTI_CAPTURE_REQUIRED",
        lambda c: (
            c.has_category("governance") or
            any("capture" in a.title.lower() or
                "anti-concentration" in a.title.lower()
                for a in c.articles),
            "Constitution must include an Anti-Capture or "
            "Anti-Concentration article",
        ),
        "Constitution must include an Anti-Capture article [REQUIRED]",
    ),
    # -- P0: Quality --
    fail_rule(
        "NONEMPTY_ARTICLES",
        _no_empty_articles,
        "All articles must have non-empty content",
    ),
    fail_rule(
        "NO_SELF_CONTRADICTION",
        _no_governance_contradiction,
        "Constitution contains contradictory governance provisions",
    ),
    # -- P1: Adversarial / Anti-concentration --
    warn_rule(
        "ADVERSARIAL_PATTERN",
        _no_adversarial_patterns,
        "Constitution contains adversarial alignment patterns",
    ),
    warn_rule(
        "ANTI_CONCENTRATION",
        _has_anti_concentration,
        "No anti-concentration mechanisms detected",
    ),
    warn_rule(
        "AI_BOUNDARIES",
        _has_ai_boundaries,
        "No AI Cell boundaries or automation limits defined",
    ),
    # -- P2: Advisory --
    info_rule(
        "OSTROM_PRINCIPLES",
        _count_ostrom_principles,
        "Ostrom principles coverage",
    ),
    info_rule(
        "ARTICLE_NAMING",
        _check_article_naming,
        "Article naming conventions",
    ),
]
