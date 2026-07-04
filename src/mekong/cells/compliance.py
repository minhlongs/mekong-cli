"""AI Cell compliance review engine.

Provides ``run_compliance_review()`` for performing detailed article-by-article
constitutional compliance checks on cell recommendations.

Each article check uses keyword-based heuristics against the recommendation
text to detect potential violations of the particle's constitution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.mekong.cells.types import CellRecommendation, ComplianceResult
from src.mekong.constitution.parser import Article, Constitution, parse_constitution
from src.mekong.graph.store import get_behaviors, open_db

# ---------------------------------------------------------------------------
# Article-specific violation keywords
# ---------------------------------------------------------------------------

# Article 1 (Mission) — keywords that suggest overriding or abandoning mission
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

# Article 3 (AI Boundaries / Privileges) — keywords that suggest exceeding limits
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

# Article 6 (Behavioral Integrity / Anti-Concentration)
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

# Article 8 (Right to Exit)
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

# ---------------------------------------------------------------------------
# Article routing: (title_keywords, check_keywords) pairs
# ---------------------------------------------------------------------------

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
    """Check recommendation text against a single article.

    Returns ``(severity, message)`` when a violation is detected, or ``None``
    if the recommendation passes the article's check.

    *severity* is ``"VIOLATION"`` for clear keyword matches or ``"WARNING"``
    for edge cases.
    """
    title_lower = article.title.lower()

    for keywords, violator_keywords, message_tpl in _ARTICLE_ROUTING:
        if not any(kw in title_lower for kw in keywords):
            continue

        # Check each violation keyword against the recommendation
        for kw in violator_keywords:
            if kw in rec_lower:
                msg = message_tpl.format(number=article.number)
                return ("VIOLATION", f"Article {article.number}: {msg} — contains '{kw}'")

    # Special: if article mentions "exit" and rec mentions "exit" negatively
    if any(kw in title_lower for kw in ["exit", "withdraw", "leave"]):
        if "exit" in rec_lower or "withdraw" in rec_lower:
            # Check for positive/neutral exit language — not a violation
            positive_exit = [
                "right to exit", "right to withdraw", "allow exit",
                "permit exit", "exit rights", "facilitate exit",
                "support exit", "enable exit",
            ]
            if not any(p in rec_lower for p in positive_exit):
                return ("WARNING",
                        f"Article {article.number}: Recommendation discusses exit "
                        f"without affirming exit rights — review '{article.title}'")

    return None


def _check_similar_recommendations(
    particle_id: str,
    recommendation: CellRecommendation,
    violations: list[str],
    warnings: list[str],
    graph_db: str | None = None,
) -> None:
    """Check behavior graph for similar past recommendations.

    Queries recent ``cell_recommendation`` behaviors for the same target
    particle and warns if a pattern of similar recommendations is detected.
    """
    if not recommendation.recommendation:
        return

    conn = open_db(graph_db)
    try:
        past = get_behaviors(
            conn,
            action="cell_recommendation",
            target_id=f"particle:{particle_id}",
            limit=20,
        )
    finally:
        conn.close()

    if not past:
        return

    # Check for similar recommendation text among recent records
    rec_lower = recommendation.recommendation.lower()
    similar_count = 0
    common_words: set[str] = set()

    for behavior in past:
        payload = behavior.payload or {}
        past_rec = str(payload.get("recommendation", "")).lower()
        if not past_rec:
            continue

        # Simple overlap heuristic: count shared significant words
        rec_words = set(rec_lower.split())
        past_words = set(past_rec.split())
        shared = rec_words & past_words
        if len(shared) >= len(rec_words) * 0.5 and len(rec_words) > 3:
            similar_count += 1
            common_words |= shared

    if similar_count >= 3:
        warnings.append(
            f"[REPEATED_PATTERN] Recommendation shares significant overlap with "
            f"{similar_count} past recommendation(s) — potential echo chamber "
            f"pattern detected"
        )


def run_compliance_review(
    particle_id: str,
    recommendation: CellRecommendation,
    constitution_path: str | Path,
    graph_db: str | None = None,
) -> ComplianceResult:
    """Run a detailed article-by-article compliance review on a recommendation.

    Steps
    -----
    1. Load and parse the particle's ``ZENOS.md`` constitution.
    2. Check the recommendation text against each article, routing by article
       title keywords:
       - Article 1 (Mission): does the recommendation serve the mission?
       - Article 3 (AI Boundaries): within privilege limits?
       - Article 6 (Behavioral Integrity): anti-concentration check?
       - Article 8 (Right to Exit): does it restrict exit?
    3. Query the behavior graph for similar past recommendations and flag
       echo-chamber patterns.
    4. Return a ``ComplianceResult`` with ``verdict`` of ``"PASS"``,
       ``"WARNING"``, or ``"VIOLATION"``.

    Parameters
    ----------
    particle_id:
        Identifier for the particle being reviewed.
    recommendation:
        The cell recommendation to review for compliance.
    constitution_path:
        Path to the ``ZENOS.md`` constitution file.
    graph_db:
        Optional path to the behavior graph SQLite database. Uses the
        environment default when ``None``.

    Returns
    -------
    ComplianceResult
        The review verdict with violations and warnings.

    Raises
    ------
    FileNotFoundError
        If the constitution file does not exist.
    ValueError
        If the constitution file cannot be parsed.

    Examples
    --------
    >>> from src.mekong.cells.types import CellRecommendation
    >>> rec = CellRecommendation(recommendation="Increase marketing budget")
    >>> result = run_compliance_review(
    ...     "my-particle", rec, "path/to/ZENOS.md"
    ... )
    >>> result.verdict
    'PASS'
    """
    constitution_path = Path(constitution_path)
    if not constitution_path.exists():
        raise FileNotFoundError(f"Constitution not found: {constitution_path}")

    constitution = parse_constitution(str(constitution_path))

    violations: list[str] = []
    warnings: list[str] = []
    checked_articles: list[int] = []

    rec_lower = recommendation.recommendation.lower()

    # 2. Check each article against the recommendation
    for article in constitution.articles:
        checked_articles.append(article.number)
        result = _check_article(article, rec_lower)
        if result is not None:
            severity, message = result
            if severity == "VIOLATION":
                violations.append(message)
            elif severity == "WARNING":
                warnings.append(message)

    # 3. Check behavior graph for similar past recommendations
    _check_similar_recommendations(
        particle_id, recommendation, violations, warnings, graph_db
    )

    # 4. Determine verdict
    if violations:
        verdict = "VIOLATION"
    elif warnings:
        verdict = "WARNING"
    else:
        verdict = "PASS"

    return ComplianceResult(
        verdict=verdict,
        checked_articles=checked_articles,
        violations=violations,
        warnings=warnings,
    )
