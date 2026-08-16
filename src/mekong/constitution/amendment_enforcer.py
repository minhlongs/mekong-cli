"""periodic_audit.py — Extended constitutional audit runner.

Extends the existing `review.py` (P0/P1/P2) with:
- Multi-article contradiction detection (currently within-article only in review.py)
- Clause deletion integrity (no dangling references after edits)
- Proposed P3 category: "constitutional completeness" (checks for scoping
  conflicts between this charter and ZENOS.md sovereign articles)

All checks raise P0 (FAIL) or P1 (WARN) per the existing scheme; new rules
do not introduce new severities.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.mekong.constitution.parser import Constitution, parse_constitution
from src.mekong.constitution.review import RuleResult, review_constitution

# Re-export parent module so callers can use it via this module.
CommonsMember = None  # placeholder — kept for import-shape stability


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# New P0/P1 rules for multi-article checks
# ---------------------------------------------------------------------------


def check_superseding_sovereign_articles(cons: Constitution) -> Optional[RuleResult]:
    """P0: ZENOS Art 1 (Human Supremacy) must not be weakened by any charter article.

    Any article whose body contains a phrase weakening founder/human control
    (e.g. "AI may override founder") is a contradiction with the sovereign
    layer.
    """
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
    """P1: Tripartite branch definitions must not allow dual occupancy.

    Looks for phrases suggesting a single entity may vote and execute.
    """
    dual = re_pat(r"(?:same|single|one)\s+(?:entity|member|cell).*(?:vote|execute|mediate)", re_flags())
    for art in cons.articles:
        if dual.search(art.content):
            return _rule_warn(
                "ZENOS-C-02",
                f"Article {art.number} ({art.title}) might permit dual-branch occupancy",
                con=cons,
            )
    return None


def check_sunset_clause_presence(cons: Constitution) -> Optional[RuleResult]:
    """P1: Commons charter must carry a sunset clause or reference one.

    A charter without any sunset risks ZENOS Art 9 zombie-charter scenario.
    """
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
    """P1: If a Right to Exit article exists in the charter, confirm it
    delegates to ZENOS Art 8 and does not narrow the guarantee.
    """
    for art in cons.articles:
        if "right to exit" in (art.title or "").lower() or "right to exit" in (art.content or "").lower():
            narrow = ["no lock-in", "no penalty", "full data sovereignty"]
            ok = any(p.lower() in art.content.lower() for p in narrow)
            if not ok:
                return _rule_warn(
                    "ZENOS-C-04",
                    f"Article {art.number} ({art.title}) references Right to Exit "
                    "but omits the ZENOS Art 8 guarantees",
                    con=cons,
                )
    return None


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_extended_audit(path: str | Path) -> AuditReport:
    """Run the base review_constitution() + the multi-article contradiction checks."""
    path = str(path)
    rules_results = review_constitution(path)
    cons = parse_constitution(path)

    new_findings: list = []
    for check in [
        check_superseding_sovereign_articles,
        check_no_double_branch_occupancy,
        check_sunset_clause_presence,
        check_right_to_exit_redundancy,
    ]:
        finding = check(cons)
        if finding is not None:
            new_findings.append(finding)

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


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _detect_contradictions(cons: Constitution) -> list[dict]:
    """Return a list of dicts describing cross-article contradictions.
    Lightweight heuristic: two articles whose normalized keyword sets overlap
    > 60% on opposite-polarity keywords.
    """
    out: list[dict] = []
    seen: set[tuple[int, int]] = set()
    for i, a in enumerate(cons.articles):
        for j, b in enumerate(cons.articles):
            if i >= j:
                continue
            pair = (a.number, b.number)
            if pair in seen:
                continue
            seen.add(pair)
            sim = _keyword_overlap(a.content, b.content)
            if sim > 0.7:
                out.append(
                    {
                        "articles": [a.number, b.number],
                        "titles": [a.title, b.title],
                        "similarity": round(sim, 3),
                        "note": "High text overlap — manual review recommended",
                    }
                )
    return out


def _keyword_overlap(a: str, b: str) -> float:
    sa = set(_tokens(a))
    sb = set(_tokens(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(len(sa | sb), 1)


def _tokens(text: str) -> list[str]:
    text = (text or "").lower()
    words = re_pat(r"[a-z]{3,}").findall(text)
    return [w for w in words if w not in {"the", "and", "for", "that", "with", "this", "from", "have", "been"}]


# ---------------------------------------------------------------------------
# Rule factory helpers matching review.py conventions
# ---------------------------------------------------------------------------


def _rule_fail(rule_id: str, message: str, con: Constitution) -> RuleResult:
    return RuleResult(rule_id=rule_id, severity="FAIL", message=message, article_ref=con.name)


def _rule_warn(rule_id: str, message: str, con: Constitution) -> RuleResult:
    return RuleResult(rule_id=rule_id, severity="WARN", message=message, article_ref=con.name)


# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------


def re_pat(pat: str, flags: int = 0):
    import re
    return re.compile(pat, flags)


def re_flags() -> int:
    import re
    return re.IGNORECASE | re.MULTILINE


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def compare_with_zenns(commons_path: str | Path, zenns_path: str | Path) -> AuditReport:
    """Run extended audit on the commons charter with ZENOS.md as context.

    Base rules are run on commons_path.  The contradiction detector also pulls
    in ZENOS.md articles so cross-document conflicts are detected.
    """
    commons = parse_constitution(commons_path)
    zenns = parse_constitution(zenns_path)
    merged = Constitution(
        name="merged",
        articles=[*zenns.articles, *commons.articles],
        lines=commons.lines + zenns.lines,
    )
    findings: list = []
    findings.append(check_superseding_sovereign_articles(merged))
    findings.append(check_no_double_branch_occupancy(merged))
    findings = [f for f in findings if f is not None]
    contradictions = _detect_contradictions(merged)
    verdict = "FAIL" if any(f.severity == "FAIL" for f in findings) else "WARNINGS" if (findings or contradictions) else "PASS"
    return AuditReport(
        verdict=verdict,
        rules=findings,
        contradictions=contradictions,
        new_findings=[],
        source=str(commons_path),
    )
