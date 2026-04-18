"""Tests for agent_core.evals — dataset loading, scoring, regression detection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_core.evals import (
    EvalCase,
    EvalRunSummary,
    dataset_hash,
    detect_regression,
    load_dataset,
    run_dataset,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _write_dataset(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "dataset.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


class _ScriptedLLM:
    """Returns pre-canned responses in order."""

    def __init__(self, responses: list[str]):
        self._q = list(responses)

    def chat(self, messages, system=None, max_tokens=1024):
        return self._q.pop(0) if self._q else ""


SMOKE_DATASET = {
    "name": "smoke",
    "cases": [
        {"id": "greet", "prompt": "Say hello", "expect_substring": "hello"},
        {"id": "bye", "prompt": "Say bye", "expect_substring": "bye"},
        {"id": "fail", "prompt": "Say nothing", "expect_substring": "NEVER_MATCH"},
    ],
}


# ---------------------------------------------------------------------------
# dataset_hash determinism
# ---------------------------------------------------------------------------


def test_dataset_hash_is_deterministic():
    h1 = dataset_hash(SMOKE_DATASET)
    h2 = dataset_hash(SMOKE_DATASET)
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex


def test_dataset_hash_changes_on_content_change():
    h1 = dataset_hash(SMOKE_DATASET)
    modified = {**SMOKE_DATASET, "name": "different"}
    h2 = dataset_hash(modified)
    assert h1 != h2


def test_dataset_hash_is_order_independent_on_keys():
    d1 = {"name": "x", "cases": []}
    d2 = {"cases": [], "name": "x"}
    assert dataset_hash(d1) == dataset_hash(d2)


# ---------------------------------------------------------------------------
# load_dataset
# ---------------------------------------------------------------------------


def test_load_dataset_parses_cases(tmp_path):
    path = _write_dataset(tmp_path, SMOKE_DATASET)
    cases = load_dataset(path)
    assert len(cases) == 3
    assert cases[0].id == "greet"
    assert cases[0].expect_substring == "hello"
    assert cases[0].weight == 1.0


def test_load_dataset_applies_custom_weight(tmp_path):
    data = {
        "name": "w",
        "cases": [{"id": "heavy", "prompt": "p", "expect_substring": "x", "weight": 2.5}],
    }
    path = _write_dataset(tmp_path, data)
    cases = load_dataset(path)
    assert cases[0].weight == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# run_dataset scoring
# ---------------------------------------------------------------------------


def test_run_dataset_scores_correctly():
    cases = [
        EvalCase(id="pass", prompt="p1", expect_substring="hello"),
        EvalCase(id="fail", prompt="p2", expect_substring="NEVER"),
    ]
    llm = _ScriptedLLM(["hello world", "something else"])
    summary = run_dataset(cases, llm)

    assert summary.passed_count == 1
    assert summary.total_count == 2
    assert summary.total_score == pytest.approx(1.0)
    assert summary.total_weight == pytest.approx(2.0)
    assert summary.score_pct == pytest.approx(0.5)


def test_run_dataset_all_pass():
    cases = [EvalCase(id=f"c{i}", prompt="p", expect_substring="ok") for i in range(3)]
    llm = _ScriptedLLM(["ok", "ok", "ok"])
    summary = run_dataset(cases, llm)
    assert summary.passed_count == 3
    assert summary.score_pct == pytest.approx(1.0)


def test_run_dataset_all_fail():
    cases = [EvalCase(id="x", prompt="p", expect_substring="NOPE")]
    llm = _ScriptedLLM(["nothing"])
    summary = run_dataset(cases, llm)
    assert summary.passed_count == 0
    assert summary.score_pct == pytest.approx(0.0)


def test_run_dataset_weighted_scoring():
    cases = [
        EvalCase(id="heavy", prompt="p", expect_substring="yes", weight=3.0),
        EvalCase(id="light", prompt="p", expect_substring="yes", weight=1.0),
    ]
    llm = _ScriptedLLM(["yes", "nope"])  # heavy passes, light fails
    summary = run_dataset(cases, llm)
    assert summary.total_score == pytest.approx(3.0)
    assert summary.total_weight == pytest.approx(4.0)
    assert summary.score_pct == pytest.approx(0.75)


def test_run_dataset_llm_exception_treated_as_failure():
    class _BrokenLLM:
        def chat(self, messages, system=None, max_tokens=1024):
            raise RuntimeError("network down")

    cases = [EvalCase(id="x", prompt="p", expect_substring="ok")]
    summary = run_dataset(cases, _BrokenLLM())
    assert summary.passed_count == 0


# ---------------------------------------------------------------------------
# detect_regression
# ---------------------------------------------------------------------------


def _make_summary(score_pct: float, n: int = 4) -> EvalRunSummary:
    passed = round(score_pct * n)
    return EvalRunSummary(
        dataset_name="test",
        total_score=float(passed),
        total_weight=float(n),
        passed_count=passed,
        total_count=n,
    )


def test_detect_regression_no_baseline_returns_empty():
    summary = _make_summary(0.5)
    assert detect_regression(summary, baseline=None) == []


def test_detect_regression_no_regression_when_equal():
    current = _make_summary(1.0, n=4)
    baseline = {"score": 4.0, "total": 4}
    assert detect_regression(current, baseline) == []


def test_detect_regression_triggers_on_drop():
    current = _make_summary(0.5, n=4)  # 50%
    baseline = {"score": 4.0, "total": 4}  # 100%
    msgs = detect_regression(current, baseline, threshold_pct=0.05)
    assert len(msgs) >= 1
    assert "REGRESSION" in msgs[0]


def test_detect_regression_below_threshold_no_fire():
    # 3% drop, threshold 5% — should not fire
    current = _make_summary(0.97, n=100)
    baseline = {"score": 100.0, "total": 100}
    assert detect_regression(current, baseline, threshold_pct=0.05) == []
