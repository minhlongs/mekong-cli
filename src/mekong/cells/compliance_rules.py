# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Article-level violation keyword dictionaries and checker for compliance reviews."""

from __future__ import annotations

from src.mekong.constitution.parser import Article

_MISSION_VIOLATORS: list[str] = [
    "abandon the mission",
    "abandon mission",
    "ignore the mission",
    "ignore mission",
    "override the mission",
    "override mission",
    "replace the mission",
    "replace mission",
    "discard the mission",
    "discard mission",
    "dismantle the mission",
    "dismantle mission",
    "abandon the purpose",
    "abandon purpose",
    "change the objective",
    "change objective",
    "contradict the mission",
    "contradict mission",
    "violate the mission",
    "violate mission",
    "abandon the goal",
    "abandon goal",
    "ignore the goal",
    "ignore goal",
    "contradict the goal",
    "contradict goal",
    "against the mission",
    "against mission",
    "contrary to mission",
]

_BOUNDARY_VIOLATORS: list[str] = [
    "unlimited access",
    "unrestricted access",
    "bypass approval",
    "no human review",
    "fully autonomous",
    "without oversight",
    "no supervision",
    "act independently",
    "without approval",
    "access all data",
    "unchecked authority",
    "absolute control",
    "escalate privileges",
    "elevate access",
]

_ANTI_CONCENTRATION_VIOLATORS: list[str] = [
    "concentrate power",
    "accumulate power",
    "single point of control",
    "take control",
    "consolidate authority",
    "centralize decision",
    "centralize control",
    "eliminate checks",
    "remove oversight",
    "remove checks",
    "monopoly",
    "dominant position",
    "sole authority",
]

_EXIT_VIOLATORS: list[str] = [
    "cannot leave",
    "no exit",
    "cannot withdraw",
    "no withdrawal",
    "lock in",
    "forced retention",
    "prevent exit",
    "block exit",
    "restrict exit",
    "exit penalty",
    "penalty for leaving",
    "cannot opt out",
    "no opt out",
]

_ARTICLE_ROUTING: list[tuple[list[str], list[str], str]] = [
    (["mission"], _MISSION_VIOLATORS,
     "Recommendation may contradict the mission defined in Article {number}"),
    (["ai", "boundar", "automation", "privilege", "limit"], _BOUNDARY_VIOLATORS,
     "Recommendation may exceed AI Cell boundaries defined in Article {number}"),
    (["behavior", "integrity", "anti", "concentration", "capture", "check"], _ANTI_CONCENTRATION_VIOLATORS,
     "Recommendation may concentrate power in violation of Article {number}"),
    (["exit", "withdraw", "leave", "opt out"], _EXIT_VIOLATORS,
     "Recommendation may restrict exit rights in violation of Article {number}"),
]


def _check_article(article: Article, rec_lower: str) -> tuple[str, str] | None:
    """Check recommendation text against a single article."""
    title_lower = article.title.lower()

    for keywords, violator_keywords, message_tpl in _ARTICLE_ROUTING:
        if not any(kw in title_lower for kw in keywords):
            continue
        for kw in violator_keywords:
            if kw in rec_lower:
                msg = message_tpl.format(number=article.number)
                return ("VIOLATION", f"Article {article.number}: {msg} — contains '{kw}'")

    if any(kw in title_lower for kw in ["exit", "withdraw", "leave"]):
        if "exit" in rec_lower or "withdraw" in rec_lower:
            positive_exit = [
                "right to exit", "right to withdraw", "allow exit",
                "permit exit", "exit rights", "facilitate exit",
                "support exit", "enable exit",
            ]
            if not any(p in rec_lower for p in positive_exit):
                return (
                    "WARNING",
                    f"Article {article.number}: Recommendation discusses exit "
                    f"without affirming exit rights — review '{article.title}'",
                )

    return None
