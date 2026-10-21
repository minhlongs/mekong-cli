# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""periodic_audit.py — Extended constitutional audit runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.mekong.constitution.amendment_enforcer_helpers import (
    _detect_contradictions,
    _keyword_overlap,
    _rule_fail,
    _rule_warn,
    _tokens,
    re_flags,
    re_pat,
)
from src.mekong.constitution.parser import Constitution, parse_constitution
from src.mekong.constitution.review import RuleResult, review_constitution

CommonsMember = None  # placeholder — kept for import-shape stability


@dataclass(frozen=True)
class AuditReport:
    verdict: str  # PASS | WARNINGS | FAIL
    rules: list[RuleResult]
    contradictions: list[dict]
    new_findings: list[RuleResult]
    source: str = "periodic_audit.py"

    @property
    def has_failures(self) -> bool:
        return any(r.severity == "FAIL" for r in self.rules + self.new_findings)

    @property
    def has_warnings(self) -> bool:
        return any(r.severity == "WARN" for r in self.rules + self.new_findings)


def check_superseding_sovereign_articles(cons: Constitution) -> Optional[RuleResult]:
    """P0: ZENOS Art 1 (Human Supremacy) must not be weakened by any charter article."""
    for art in cons.articles:
        for phrase in ["override founder", "supersede founder", "founder may not"]:
            if phrase.lower() in art.content.lower():
                return _rule_fail(
                    "ZENOS-C-01",
                    f"Article {art.number} ({art.title}) contains phrase '{phrase}' "
                    "that weakens ZENOS Art 1 (Human Supremacy)",
                    con=cons,
                )
    return None


def check_no_double_branch_occupancy(cons: Constitution) -> Optional[RuleResult]:
    """P1: Tripartite branch definitions must not allow dual occupancy."""
    dual = re_pat(
        r"(?:same|single|one)\s+(?:entity|member|cell).*(?:vote|execute|mediate)",
        re_flags(),
    )
    for art in cons.articles:
        if dual.search(art.content):
            return _rule_warn(
                "ZENOS-C-02",
                f"Article {art.number} ({art.title}) might permit dual-branch occupancy",
                con=cons,
            )
    return None


def check_sunset_clause_presence(cons: Constitution) -> Optional[RuleResult]:
    """P1: Commons charter must carry a sunset clause or reference one."""
    has_sunset = any(
        "sunset" in (art.content or "").lower() or "expire" in (art.content or "").lower()
        for art in cons.articles
    )
    if not has_sunset:
        return _rule_warn(
            "ZENOS-C-03",
            "Commons charter has no sunset clause — risk of zombie charter",
            con=cons,
        )
    return None


def check_right_to_exit_redundancy(cons: Constitution) -> Optional[RuleResult]:
    """P1: If a Right to Exit article exists in the charter, confirm it delegates to ZENOS Art 8."""
    for art in cons.articles:
        if "right to exit" in (art.title or "").lower() or "right to exit" in (art.content or "").lower():
            narrow = ["no lock-in", "no penalty", "full data sovereignty"]
            if not any(p.lower() in art.content.lower() for p in narrow):
                return _rule_warn(
                    "ZENOS-C-04",
                    f"Article {art.number} ({art.title}) references Right to Exit "
                    "but omits the ZENOS Art 8 guarantees",
                    con=cons,
                )
    return None


def run_extended_audit(path: str | Path) -> AuditReport:
    """Run the base review_constitution() + the multi-article contradiction checks."""
    path = str(path)
    rules_results = review_constitution(path)
    cons = parse_constitution(path)

    new_findings = [
        f
        for check in [
            check_superseding_sovereign_articles,
            check_no_double_branch_occupancy,
            check_sunset_clause_presence,
            check_right_to_exit_redundancy,
        ]
        if (f := check(cons)) is not None
    ]
    contradictions = _detect_contradictions(cons)

    verdict = "PASS"
    if any(r.severity == "FAIL" for r in rules_results + new_findings):
        verdict = "FAIL"
    elif any(r.severity == "WARN" for r in rules_results + new_findings) or contradictions:
        verdict = "WARNINGS"

    return AuditReport(
        verdict=verdict,
        rules=list(rules_results),
        contradictions=contradictions,
        new_findings=new_findings,
        source=path,
    )


def compare_with_zenns(commons_path: str | Path, zenns_path: str | Path) -> AuditReport:
    """Run extended audit on the commons charter with ZENOS.md as context."""
    commons = parse_constitution(commons_path)
    zenns = parse_constitution(zenns_path)
    merged = Constitution(
        name="merged",
        articles=[*zenns.articles, *commons.articles],
        lines=commons.lines + zenns.lines,
    )
    findings = [
        f
        for f in [
            check_superseding_sovereign_articles(merged),
            check_no_double_branch_occupancy(merged),
        ]
        if f is not None
    ]
    contradictions = _detect_contradictions(merged)
    verdict = (
        "FAIL"
        if any(f.severity == "FAIL" for f in findings)
        else "WARNINGS"
        if (findings or contradictions)
        else "PASS"
    )
    return AuditReport(
        verdict=verdict,
        rules=findings,
        contradictions=contradictions,
        new_findings=[],
        source=str(commons_path),
    )


__all__ = [
    "AuditReport", "CommonsMember", "_detect_contradictions", "_keyword_overlap",
    "_rule_fail", "_rule_warn", "_tokens", "check_no_double_branch_occupancy",
    "check_right_to_exit_redundancy", "check_sunset_clause_presence",
    "check_superseding_sovereign_articles", "compare_with_zenns",
    "re_flags", "re_pat", "run_extended_audit",
]
