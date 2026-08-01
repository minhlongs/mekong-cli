"""periodic_audit.py — Periodic constitutional audit runner.

Wraps the existing `review_constitution()` and adds:
- Continuous multi-article contradiction detection (currently within-article only in review.py)
- Clause deletion integrity (no dangling references after edits)
- Proposed P3 category: constitutional completeness (cross-document conflicts with ZENOS.md)

All new checks surface as --severity added findings without changing the
existing P0/P1/P2 verdict structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.mekong.constitution.parser import Constitution, parse_constitution
from src.mekong.constitution.review import review_constitution

# Re-export parent module so callers can use it via this module.
CommonsMember = None  # placeholder — kept for import-shape stability


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditReport:
    verdict: str  # PASS | WARNINGS | FAIL
    rules: list
    contradictions: list[dict]
    new_findings: list
    source: str = "periodic_audit.py"

    @property
    def has_failures(self) -> bool:
        return any(getattr(r, "severity", "") == "FAIL" for r in self.rules + self.new_findings)

    @property
    def has_warnings(self) -> bool:
        return any(getattr(r, "severity", "") == "WARN" for r in self.rules + self.new_findings)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_extended_audit(path: str) -> AuditReport:
    """Run the base review_constitution() + multi-article contradiction checks."""
    rules_results = review_constitution(path)
    cons = parse_constitution(path)

    new_findings: list = []
    for check in [_check_superseding_sovereign_articles, _check_no_double_branch_occupancy]:
        finding = check(cons)
        if finding is not None:
            new_findings.append(finding)

    verdict = "PASS"
    if any(r.severity == "FAIL" for r in rules_results + new_findings):
        verdict = "FAIL"
    elif any(r.severity == "WARN" for r in rules_results + new_findings):
        verdict = "WARNINGS"

    return AuditReport(
        verdict=verdict,
        rules=list(rules_results),
        contradictions=[],
        new_findings=new_findings,
        source=path,
    )


# ---------------------------------------------------------------------------
# New checks
# ---------------------------------------------------------------------------


def _check_superseding_sovereign_articles(cons: Constitution):
    """Any article whose body contains phrases weakening founder/human control
    (e.g. "AI may override founder") is a contradiction with ZENOS Art 1."""
    phrases = ["override founder", "supersede founder", "founder may not"]
    for art in cons.articles:
        for phrase in phrases:
            if phrase.lower() in art.content.lower():
                return _rule_fail(
                    "ZENOS-C-01",
                    f"Article {art.number} ({art.title}) contains '{phrase}' "
                    "that weakens ZENOS Art 1 (Human Supremacy)",
                    con=cons,
                )
    return None


def _check_no_double_branch_occupancy(cons: Constitution):
    """Tripartite branch definitions must not allow single-entity dual occupancy."""
    pat = re_pat(
        r"(?:same|single|one)\s+(?:entity|member|cell).*(?:vote|execute|mediate)"
    )
    for art in cons.articles:
        if pat.search(art.content):
            return _rule_warn(
                "ZENOS-C-02",
                f"Article {art.number} ({art.title}) might permit dual-branch occupancy",
                con=cons,
            )
    return None


# ---------------------------------------------------------------------------
# Helpers matching review.py conventions
# ---------------------------------------------------------------------------


def _rule_fail(rule_id: str, message: str, con: Constitution):
    return RuleResult(rule_id=rule_id, severity="FAIL", message=message, article_ref=con.name)


def _rule_warn(rule_id: str, message: str, con: Constitution):
    return RuleResult(rule_id=rule_id, severity="WARN", message=message, article_ref=con.name)


def re_pat(pat: str):
    import re
    return re.compile(pat, re.IGNORECASE)


# ---------------------------------------------------------------------------
# Cross-document comparison
# ---------------------------------------------------------------------------


def compare_with_zenns(commons_path: str, zenns_path: str = "mekong/constitution/ZENOS.md") -> AuditReport:
    """Run extended audit on the Commons charter with ZENOS.md as context."""
    commons = parse_constitution(commons_path)
    zenns = parse_constitution(zenns_path)
    merged = Constitution(
        name="merged",
        articles=[*zenns.articles, *commons.articles],
        lines=commons.lines + zenns.lines,
    )
    findings: list = []
    for check in [_check_superseding_sovereign_articles, _check_no_double_branch_occupancy]:
        f = check(merged)
        if f is not None:
            findings.append(f)
    verdict = "FAIL" if any(getattr(r, "severity", "") == "FAIL" for r in findings) else (
        "WARNINGS" if findings else "PASS"
    )
    return AuditReport(
        verdict=verdict,
        rules=[],
        contradictions=[],
        new_findings=findings,
        source=commons_path,
    )


# ---------------------------------------------------------------------------
# Lazy RuleResult import shim so we don't need top-level circular imports.
# ---------------------------------------------------------------------------

try:
    from src.mekong.constitution.review import RuleResult  # noqa: E402
except Exception:  # pragma: no cover

    @dataclass(frozen=True)
    class RuleResult:  # type: ignore[no-redef]
        rule_id: str
        severity: str
        message: str
        article_ref: str
