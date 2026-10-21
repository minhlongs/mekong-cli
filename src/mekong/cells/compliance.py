# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""AI Cell compliance review engine."""

from __future__ import annotations

from pathlib import Path

from src.mekong.cells.compliance_rules import (
    _ANTI_CONCENTRATION_VIOLATORS,
    _ARTICLE_ROUTING,
    _BOUNDARY_VIOLATORS,
    _EXIT_VIOLATORS,
    _MISSION_VIOLATORS,
    _check_article,
)
from src.mekong.cells.types import CellRecommendation, ComplianceResult
from src.mekong.constitution.parser import Article, parse_constitution
from src.mekong.graph.store import get_behaviors, open_db


def _check_similar_recommendations(
    particle_id: str,
    recommendation: CellRecommendation,
    violations: list[str],
    warnings: list[str],
    graph_db: str | None = None,
) -> None:
    """Check behavior graph for similar past recommendations."""
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

    rec_lower = recommendation.recommendation.lower()
    similar_count = 0
    common_words: set[str] = set()

    for behavior in past:
        payload = behavior.payload or {}
        past_rec = str(payload.get("recommendation", "")).lower()
        if not past_rec:
            continue

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
    """Run a detailed article-by-article compliance review on a recommendation."""
    constitution_path = Path(constitution_path)
    if not constitution_path.exists():
        raise FileNotFoundError(f"Constitution not found: {constitution_path}")

    constitution = parse_constitution(str(constitution_path))

    violations: list[str] = []
    warnings: list[str] = []
    checked_articles: list[int] = []

    rec_lower = recommendation.recommendation.lower()

    for article in constitution.articles:
        checked_articles.append(article.number)
        result = _check_article(article, rec_lower)
        if result is not None:
            severity, message = result
            if severity == "VIOLATION":
                violations.append(message)
            elif severity == "WARNING":
                warnings.append(message)

    _check_similar_recommendations(
        particle_id, recommendation, violations, warnings, graph_db
    )

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


__all__ = [
    "Article",
    "_ANTI_CONCENTRATION_VIOLATORS",
    "_ARTICLE_ROUTING",
    "_BOUNDARY_VIOLATORS",
    "_EXIT_VIOLATORS",
    "_MISSION_VIOLATORS",
    "_check_article",
    "_check_similar_recommendations",
    "run_compliance_review",
]
