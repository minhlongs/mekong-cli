# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CAI research-backed constitutional rules organised by severity."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from src.mekong.constitution.parser import Constitution
from src.mekong.constitution.rules_checks import (
    _AI_BOUNDARY_KEYWORDS,
    _ANTI_CONCENTRATION_KEYWORDS,
    _NAMING_EXPECTATIONS,
    _OSTROM_PRINCIPLES,
    _check_article_naming,
    _count_ostrom_principles,
    _has_ai_boundaries,
    _has_anti_concentration,
    _ostrom_principles_detail,
)

RuleCheck = Callable[[Constitution], tuple[bool, str]]


@dataclass
class Rule:
    """A single constitutional audit rule."""

    id: str
    severity: str  # "FAIL" | "WARNING" | "INFO"
    check: RuleCheck
    message: str


def fail_rule(rule_id: str, check: RuleCheck, message: str) -> Rule:
    return Rule(id=rule_id, severity="FAIL", check=check, message=message)


def warn_rule(rule_id: str, check: RuleCheck, message: str) -> Rule:
    return Rule(id=rule_id, severity="WARNING", check=check, message=message)


def info_rule(rule_id: str, check: RuleCheck, message: str) -> Rule:
    return Rule(id=rule_id, severity="INFO", check=check, message=message)


def _no_empty_articles(c: Constitution) -> tuple[bool, str]:
    """No articles may be entirely empty (including whitespace-only)."""
    empties = [a for a in c.articles if not a.content.strip()]
    if empties:
        return False, f"Empty articles found: {', '.join(a.title for a in empties)}"
    return True, ""


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
            if any(kw in content for kw in group_a) and any(kw in content for kw in group_b):
                return False, f"Article {article.number}: {msg}"
    return True, ""


_ADVERSARIAL_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"(absolute|unlimited|unchecked|total|unrestricted)\s+(authority|power|control|discretion)", re.IGNORECASE),
        "Grants absolute or unchecked authority without checks",
    ),
    (
        re.compile(r"(unilateral(ly)?|sole|alone)\s+(can|may)\s+(amend|change|modify|rewrite)", re.IGNORECASE),
        "Allows unilateral constitutional amendment",
    ),
    (
        re.compile(r"(cannot|never|shall not)\s+be\s+(changed|amended|modified|altered)", re.IGNORECASE),
        "Constitution is declared immutable — no amendment mechanism",
    ),
    (
        re.compile(r"(mission|purpose|objective)\s+is\s+to\s+(do\s+)?(anything|everything|any|all)", re.IGNORECASE),
        "Mission statement is overly broad or unfalsifiable",
    ),
]


def _no_adversarial_patterns(c: Constitution) -> tuple[bool, str]:
    """Warn on patterns that weaken constitutional alignment."""
    combined = "\n".join(f"[Article {a.number}: {a.title}] {a.content}" for a in c.articles)
    for pattern, msg in _ADVERSARIAL_PATTERNS:
        if pattern.search(combined):
            return False, msg
    return True, ""


RULES: list[Rule] = [
    fail_rule(
        "MISSION_REQUIRED",
        lambda c: (
            c.has_category("mission") or any("mission" in a.title.lower() for a in c.articles),
            "Constitution must include a Mission article",
        ),
        "Constitution must include a Mission article [REQUIRED]",
    ),
    fail_rule(
        "EXIT_REQUIRED",
        lambda c: (
            c.has_category("exit") or any("exit" in a.title.lower() or "withdraw" in a.title.lower() for a in c.articles),
            "Constitution must include a Right to Exit article",
        ),
        "Constitution must include a Right to Exit article [REQUIRED]",
    ),
    fail_rule(
        "ANTI_CAPTURE_REQUIRED",
        lambda c: (
            c.has_category("governance") or any("capture" in a.title.lower() or "anti-concentration" in a.title.lower() for a in c.articles),
            "Constitution must include an Anti-Capture or Anti-Concentration article",
        ),
        "Constitution must include an Anti-Capture article [REQUIRED]",
    ),
    fail_rule("NONEMPTY_ARTICLES", _no_empty_articles, "All articles must have non-empty content"),
    fail_rule("NO_SELF_CONTRADICTION", _no_governance_contradiction, "Constitution contains contradictory governance provisions"),
    warn_rule("ADVERSARIAL_PATTERN", _no_adversarial_patterns, "Constitution contains adversarial alignment patterns"),
    warn_rule("ANTI_CONCENTRATION", _has_anti_concentration, "No anti-concentration mechanisms detected"),
    warn_rule("AI_BOUNDARIES", _has_ai_boundaries, "No AI Cell boundaries or automation limits defined"),
    info_rule("OSTROM_PRINCIPLES", _count_ostrom_principles, "Ostrom principles coverage"),
    info_rule("ARTICLE_NAMING", _check_article_naming, "Article naming conventions"),
]

__all__ = [
    "RULES", "Rule", "RuleCheck", "_ADVERSARIAL_PATTERNS", "_AI_BOUNDARY_KEYWORDS",
    "_ANTI_CONCENTRATION_KEYWORDS", "_CONTRADICTION_PAIRS", "_NAMING_EXPECTATIONS",
    "_OSTROM_PRINCIPLES", "_check_article_naming", "_count_ostrom_principles",
    "_has_ai_boundaries", "_has_anti_concentration", "_no_adversarial_patterns",
    "_no_empty_articles", "_no_governance_contradiction", "_ostrom_principles_detail",
    "fail_rule", "info_rule", "warn_rule",
]
