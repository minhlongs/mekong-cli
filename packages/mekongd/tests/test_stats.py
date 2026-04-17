"""Stats writer + aggregator tests."""

from __future__ import annotations

from pathlib import Path

from mekongd.stats import (
    aggregate_signals,
    aggregate_stats,
    estimate_savings,
    init_db,
    record_route,
    record_signal,
)


def test_init_db_creates_file(tmp_path: Path):
    db = tmp_path / "stats.sqlite"
    init_db(db)
    assert db.exists()


def test_record_and_aggregate(tmp_path: Path):
    db = tmp_path / "stats.sqlite"
    ok = record_route(db, "POST /v1/messages", 100, 200, "local", 0.003, "Qwen3.6")
    assert ok
    ok = record_route(db, "POST /v1/messages", 50, 100, "cloud", 0.0, "claude-opus-4-7")
    assert ok
    s = aggregate_stats(db)
    assert s.total_requests == 2
    assert s.local_requests == 1
    assert s.cloud_requests == 1
    assert s.total_tokens_in == 150
    assert s.total_tokens_out == 300
    assert abs(s.total_cost_saved_usd - 0.003) < 1e-9
    assert 49 < s.local_pct < 51


def test_aggregate_empty(tmp_path: Path):
    s = aggregate_stats(tmp_path / "nonexistent.sqlite")
    assert s.total_requests == 0
    assert s.local_pct == 0.0


def test_record_and_aggregate_signals(tmp_path: Path):
    db = tmp_path / "stats.sqlite"
    assert record_signal(db, "good", "Qwen nailed the refactor")
    assert record_signal(db, "good", "")
    assert record_signal(db, "bad", "wrong language")
    agg = aggregate_signals(db)
    assert agg == {"good": 2, "bad": 1}


def test_aggregate_signals_empty(tmp_path: Path):
    assert aggregate_signals(tmp_path / "missing.sqlite") == {}


def test_estimate_savings():
    # 1M input tokens @ $3 + 1M output @ $15 = $18
    assert abs(estimate_savings(1_000_000, 1_000_000, 3.0, 15.0) - 18.0) < 1e-9
    assert estimate_savings(0, 0, 3.0, 15.0) == 0.0
