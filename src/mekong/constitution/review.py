# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Constitutional sandbox review engine.

The top-level entry point is ``review_constitution(path)`` which parses a
ZENOS.md document, runs every audit rule, and returns a ``ReviewResult``.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.mekong.constitution.parser import parse_constitution
from src.mekong.constitution.rules import RULES, Rule


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class RuleResult:
    """Outcome of a single rule evaluation."""

    rule_id: str
    severity: str  # "FAIL" | "WARNING" | "INFO"
    passed: bool
    message: str


@dataclass
class ReviewResult:
    """Aggregated outcome of a full constitutional review."""

    constitution_name: str
    article_count: int
    line_count: int
    verdict: str  # "PASS" | "WARNINGS" | "FAIL"
    fails: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    infos: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""

    # ------------------------------------------------------------------
    # Output formatting
    # ------------------------------------------------------------------

    def format(self) -> str:
        """Return a human-readable review report suitable for CLI output."""
        lines: list[str] = []
        sep = "=" * 58

        lines.append(sep)
        header = f"  CONSTITUTIONAL REVIEW: {self.constitution_name}"
        lines.append(header)
        lines.append(sep)
        lines.append(f"  Verdict:    {self._verdict_label()}")
        lines.append(f"  Articles:   {self.article_count}")
        lines.append(f"  Lines:      {self.line_count}")
        if self.timestamp:
            lines.append(f"  Timestamp:  {self.timestamp}")
        lines.append("")

        if self.fails:
            lines.append(f"  {'-' * 38}")
            lines.append(f"  FAIL ({len(self.fails)})")
            lines.append(f"  {'-' * 38}")
            for f_result in self.fails:
                lines.append(f"  [{f_result['id']}] {f_result['message']}")
            lines.append("")

        if self.warnings:
            lines.append(f"  {'-' * 38}")
            lines.append(f"  WARNINGS ({len(self.warnings)})")
            lines.append(f"  {'-' * 38}")
            for w_result in self.warnings:
                lines.append(f"  [{w_result['id']}] {w_result['message']}")
            lines.append("")

        if self.infos:
            lines.append(f"  {'-' * 38}")
            lines.append(f"  INFO ({len(self.infos)})")
            lines.append(f"  {'-' * 38}")
            for i_result in self.infos:
                lines.append(f"  [{i_result['id']}] {i_result['message']}")
            lines.append("")

        return "\n".join(lines)

    def _verdict_label(self) -> str:
        if self.verdict == "FAIL":
            return "\033[91mFAIL\033[0m"  # red
        if self.verdict == "WARNINGS":
            return "\033[93mWARNINGS\033[0m"  # yellow
        return "\033[92mPASS\033[0m"  # green


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def review_constitution(path: str | Path) -> ReviewResult:
    """Full constitutional audit.

    Parses the constitution at *path*, runs all registered rules, and returns
    a ``ReviewResult`` with the verdict and per-rule findings.

    Raises ``ValueError`` if the file cannot be parsed.
    """
    path = Path(path)
    constitution = parse_constitution(path)
    results = _run_rules(constitution, RULES)
    review = _aggregate(results)

    # Fill in the metadata that _aggregate left blank.
    review.constitution_name = constitution.name
    review.article_count = len(constitution.articles)
    review.line_count = constitution.lines

    return review


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run review from the command line.

    Usage::

        python -m src.mekong.constitution.review path/to/constitution.md
    """
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


if __name__ == "__main__":
    main()
