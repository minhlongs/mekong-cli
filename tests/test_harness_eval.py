"""Tests for deterministic CEO Solo harness evals."""

from __future__ import annotations

from src.harness.evals.solo_ceo import run_solo_ceo_harness_evals


def test_solo_ceo_harness_evals_pass() -> None:
    payload = run_solo_ceo_harness_evals()

    assert payload["suite"] == "solo-ceo-harness"
    assert payload["passed"] is True
    assert payload["total"] == 6
    assert payload["passed_count"] == 6


def test_harness_eval_ids_match_documented_evals() -> None:
    payload = run_solo_ceo_harness_evals()
    ids = {result["id"] for result in payload["results"]}

    assert ids == {"EVAL-07", "EVAL-08", "EVAL-09", "EVAL-10", "EVAL-11", "EVAL-12"}
