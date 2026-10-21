# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Constitutional sandbox review engine."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.mekong.constitution.parser import parse_constitution
from src.mekong.constitution.review_models import ReviewResult, RuleResult
from src.mekong.constitution.rules import RULES, Rule


def _run_rules(constitution, rules: list[Rule]) -> list[RuleResult]:
    """Evaluate every rule and return ordered results."""
    results: list[RuleResult] = []
    for rule in rules:
        try:
            passed, message = rule.check(constitution)
        except Exception as exc:
            passed = False
            message = f"Rule check raised an error: {exc}"
        results.append(
            RuleResult(
                rule_id=rule.id,
                severity=rule.severity,
                passed=passed,
                message=message if not passed else f"OK: {rule.message}",
            )
        )
    return results


def _aggregate(results: list[RuleResult]) -> ReviewResult:
    """Build a ``ReviewResult`` from individual rule outcomes."""
    verdict: str = "PASS"
    fails: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []

    for r in results:
        entry = {"id": r.rule_id, "severity": r.severity, "message": r.message}
        if r.severity == "FAIL" and not r.passed:
            verdict = "FAIL"
            fails.append(entry)
        elif r.severity == "WARNING" and not r.passed:
            if verdict != "FAIL":
                verdict = "WARNINGS"
            warnings.append(entry)
        elif r.severity == "INFO":
            infos.append(entry)

    return ReviewResult(
        constitution_name="",
        article_count=0,
        line_count=0,
        verdict=verdict,
        fails=fails,
        warnings=warnings,
        infos=infos,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def review_constitution(path: str | Path) -> ReviewResult:
    """Full constitutional audit."""
    path = Path(path)
    constitution = parse_constitution(path)
    results = _run_rules(constitution, RULES)
    review = _aggregate(results)

    review.constitution_name = constitution.name
    review.article_count = len(constitution.articles)
    review.line_count = constitution.lines

    return review


def main() -> None:
    """Run review from the command line."""
    if len(sys.argv) < 2:
        print("Usage: review_constitution <path>")
        sys.exit(1)

    path = sys.argv[1]
    try:
        result = review_constitution(path)
        print(result.format())
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)


__all__ = [
    "RULES",
    "ReviewResult",
    "Rule",
    "RuleResult",
    "_aggregate",
    "_run_rules",
    "main",
    "parse_constitution",
    "review_constitution",
]


if __name__ == "__main__":
    main()
