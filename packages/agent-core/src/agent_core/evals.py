"""Offline Eval Harness — Giai đoạn 3.3.A (Pillar 3 Feedback Loop).

Runs a fixed dataset against LLMClient, scores each case, detects regression
vs baseline. Statsig-style pre-deploy regression guard.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class EvalCase:
    """Single evaluation case from a dataset file."""

    id: str
    prompt: str
    expect_substring: str
    weight: float = 1.0


@dataclass
class EvalResult:
    """Outcome of running one EvalCase."""

    case_id: str
    prompt: str
    response: str
    expect_substring: str
    score: float  # case.weight if passed, else 0.0
    passed: bool
    weight: float


@dataclass
class EvalRunSummary:
    """Aggregated results across all cases in a dataset run."""

    dataset_name: str
    total_score: float
    total_weight: float
    passed_count: int
    total_count: int
    details: list[EvalResult] = field(default_factory=list)

    @property
    def score_pct(self) -> float:
        """Weighted score as fraction (0.0–1.0). Returns 1.0 when no cases."""
        return self.total_score / self.total_weight if self.total_weight else 1.0

    def as_record(self) -> dict[str, Any]:
        """Serialisable dict for SeedMemory.record_eval_run *details* arg."""
        return {
            "cases": [
                {
                    "id": r.case_id,
                    "passed": r.passed,
                    "score": r.score,
                    "weight": r.weight,
                }
                for r in self.details
            ]
        }


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------


def load_dataset(path: Path) -> list[EvalCase]:
    """Load and parse a JSON dataset file into EvalCase list.

    Expected format::

        {
            "name": "smoke",
            "cases": [
                {"id": "greet", "prompt": "Say hello", "expect_substring": "[offline]"},
                ...
            ]
        }

    *weight* is optional per case (defaults to 1.0).
    """
    with open(path, encoding="utf-8") as fh:
        raw: dict = json.load(fh)

    cases: list[EvalCase] = []
    for item in raw.get("cases", []):
        cases.append(
            EvalCase(
                id=str(item["id"]),
                prompt=str(item["prompt"]),
                expect_substring=str(item["expect_substring"]),
                weight=float(item.get("weight", 1.0)),
            )
        )
    return cases


def dataset_hash(dataset_dict: dict) -> str:
    """Canonical SHA-256 of dataset JSON (sort_keys=True) as hex string."""
    canonical = json.dumps(dataset_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def run_dataset(cases: list[EvalCase], llm_client: Any) -> EvalRunSummary:
    """Run all cases against *llm_client* and return aggregated summary.

    Calls ``llm_client.chat([{"role": "user", "content": prompt}])`` for each case.
    Score per case = case.weight if expect_substring in response, else 0.0.
    """
    results: list[EvalResult] = []
    total_score = 0.0
    total_weight = 0.0
    passed_count = 0
    dataset_name = ""  # filled in by caller via summary

    for case in cases:
        total_weight += case.weight
        try:
            response = llm_client.chat([{"role": "user", "content": case.prompt}])
        except Exception as exc:  # noqa: BLE001
            log.warning("Eval case %r raised: %s — treating as failure", case.id, exc)
            response = ""

        passed = case.expect_substring in response
        score = case.weight if passed else 0.0
        total_score += score
        if passed:
            passed_count += 1

        results.append(
            EvalResult(
                case_id=case.id,
                prompt=case.prompt,
                response=response,
                expect_substring=case.expect_substring,
                score=score,
                passed=passed,
                weight=case.weight,
            )
        )
        log.debug("case=%s passed=%s score=%.2f", case.id, passed, score)

    return EvalRunSummary(
        dataset_name=dataset_name,
        total_score=total_score,
        total_weight=total_weight,
        passed_count=passed_count,
        total_count=len(cases),
        details=results,
    )


# ---------------------------------------------------------------------------
# Regression detection
# ---------------------------------------------------------------------------


def detect_regression(
    current: EvalRunSummary,
    baseline: dict | None,
    threshold_pct: float = 0.05,
) -> list[str]:
    """Compare *current* run against *baseline* record from SeedMemory.

    Returns a list of regression messages. Empty list = no regression.
    Returns empty list when *baseline* is None (first run — nothing to compare).

    *baseline* is a dict as returned by ``SeedMemory.recent_eval_runs()``.
    Regression fires when:  (baseline_score_pct - current_score_pct) > threshold_pct
    """
    if baseline is None:
        return []

    baseline_score: float = baseline.get("score", 0.0)
    baseline_total: float = baseline.get("total", 0) or 1  # avoid div-zero
    baseline_pct = baseline_score / baseline_total if baseline_total else 0.0

    current_pct = current.score_pct
    drop = baseline_pct - current_pct

    if drop > threshold_pct:
        msgs = [
            f"REGRESSION detected: score dropped {drop:.1%} "
            f"(baseline {baseline_pct:.1%} → current {current_pct:.1%}, "
            f"threshold {threshold_pct:.1%})"
        ]
        # Surface individual failures that might be new
        failed_ids = [r.case_id for r in current.details if not r.passed]
        if failed_ids:
            msgs.append(f"Failed cases: {', '.join(failed_ids)}")
        return msgs

    return []
