"""Stats writer + aggregator tests."""

from __future__ import annotations

from pathlib import Path

import sqlite3

from mekongd.stats import (
    aggregate_signals,
    aggregate_signals_by_model,
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


def test_record_route_persists_cost_usd(tmp_path: Path):
    """Cloud routes must store cost_usd for daily spend aggregation."""
    from mekongd.stats import today_cloud_spent_usd

    db = tmp_path / "stats.sqlite"
    record_route(db, "POST /v1/messages", 1000, 2000, "cloud", 0.0, "claude-opus-4-7", 0.05)
    record_route(db, "POST /v1/messages", 500, 1000, "cloud", 0.0, "claude-opus-4-7", 0.02)
    record_route(db, "POST /v1/messages", 100, 200, "local", 0.003, "qwen3-8b", 0.0)

    spent = today_cloud_spent_usd(db)
    assert abs(spent - 0.07) < 1e-9  # 0.05 + 0.02
    # Local routes don't count
    s = aggregate_stats(db)
    assert s.cloud_requests == 2
    assert s.local_requests == 1


def test_today_cloud_spent_usd_empty(tmp_path: Path):
    from mekongd.stats import today_cloud_spent_usd

    assert today_cloud_spent_usd(tmp_path / "missing.sqlite") == 0.0


def test_today_cloud_spent_excludes_yesterday(tmp_path: Path):
    """Rows from previous UTC day must not leak into today's spend."""
    from datetime import datetime, timedelta, timezone

    from mekongd.stats import today_cloud_spent_usd

    db = tmp_path / "stats.sqlite"
    record_route(db, "POST /v1/messages", 100, 200, "cloud", 0.0, "claude", 0.04)

    # Backdate a row to yesterday
    conn = sqlite3.connect(str(db))
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    conn.execute(
        "INSERT INTO routes (ts, method, tokens_in, tokens_out, destination, "
        "cost_saved_usd, cost_usd, model) VALUES (?, ?, 0, 0, 'cloud', 0, 99.0, 'old')",
        (yesterday, "POST /v1/messages"),
    )
    conn.commit()
    conn.close()

    spent = today_cloud_spent_usd(db)
    assert abs(spent - 0.04) < 1e-9  # yesterday's 99.0 excluded


def test_cloud_cost_by_model_groups_totals(tmp_path: Path):
    from mekongd.stats import cloud_cost_by_model

    db = tmp_path / "stats.sqlite"
    record_route(db, "POST /v1/messages", 100, 200, "cloud", 0.0, "claude-opus-4-7", 0.05)
    record_route(db, "POST /v1/messages", 50, 100, "cloud", 0.0, "claude-opus-4-7", 0.02)
    record_route(db, "POST /v1/messages", 30, 60, "cloud", 0.0, "claude-sonnet-4-6", 0.01)
    # Local route must NOT count (cost_usd=0)
    record_route(db, "POST /v1/messages", 100, 200, "local", 0.003, "qwen3-8b", 0.0)

    by_model = cloud_cost_by_model(db)
    assert abs(by_model["claude-opus-4-7"] - 0.07) < 1e-9
    assert abs(by_model["claude-sonnet-4-6"] - 0.01) < 1e-9
    assert "qwen3-8b" not in by_model  # local, zero cost


def test_cloud_cost_by_model_empty(tmp_path: Path):
    from mekongd.stats import cloud_cost_by_model

    assert cloud_cost_by_model(tmp_path / "missing.sqlite") == {}


def test_cloud_cost_by_model_honors_since_hours(tmp_path: Path):
    from datetime import datetime, timedelta, timezone

    from mekongd.stats import cloud_cost_by_model

    db = tmp_path / "stats.sqlite"
    record_route(db, "POST /v1/messages", 50, 100, "cloud", 0.0, "claude", 0.03)

    # Backdate a row 2 days ago
    conn = sqlite3.connect(str(db))
    old_ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    conn.execute(
        "INSERT INTO routes (ts, method, tokens_in, tokens_out, destination, "
        "cost_saved_usd, cost_usd, model) VALUES (?, ?, 0, 0, 'cloud', 0, 99.0, 'stale-model')",
        (old_ts, "POST /v1/messages"),
    )
    conn.commit()
    conn.close()

    all_time = cloud_cost_by_model(db)
    assert "stale-model" in all_time
    # last 1h excludes the stale row
    recent = cloud_cost_by_model(db, since_hours=1)
    assert "stale-model" not in recent
    assert abs(recent["claude"] - 0.03) < 1e-9


def test_legacy_routes_table_migrates_cost_usd(tmp_path: Path):
    """Pre-existing routes table without cost_usd column gets migrated on init_db."""
    from mekongd.stats import today_cloud_spent_usd

    db = tmp_path / "legacy.sqlite"
    conn = sqlite3.connect(str(db))
    conn.executescript(
        """
        CREATE TABLE routes (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            ts             TEXT    NOT NULL,
            method         TEXT    NOT NULL,
            tokens_in      INTEGER NOT NULL DEFAULT 0,
            tokens_out     INTEGER NOT NULL DEFAULT 0,
            destination    TEXT    NOT NULL,
            cost_saved_usd REAL    NOT NULL DEFAULT 0.0,
            model          TEXT    NOT NULL DEFAULT ''
        );
        """
    )
    conn.commit()
    conn.close()

    # Trigger migration
    assert record_route(db, "POST /v1/messages", 100, 200, "cloud", 0.0, "claude", 0.05)
    assert abs(today_cloud_spent_usd(db) - 0.05) < 1e-9


def test_record_signal_with_model_and_breakdown(tmp_path: Path):
    db = tmp_path / "stats.sqlite"
    assert record_signal(db, "good", "fast", "qwen3-8b")
    assert record_signal(db, "bad", "wrong", "qwen3-8b")
    assert record_signal(db, "good", "", "claude-sonnet-4-6")
    assert record_signal(db, "bad", "")  # legacy — empty model

    by = aggregate_signals_by_model(db)
    assert by["qwen3-8b"] == {"good": 1, "bad": 1}
    assert by["claude-sonnet-4-6"] == {"good": 1, "bad": 0}
    assert by[""] == {"good": 0, "bad": 1}


def test_aggregate_signals_by_model_empty(tmp_path: Path):
    assert aggregate_signals_by_model(tmp_path / "missing.sqlite") == {}


def test_list_recent_signals_returns_newest_first(tmp_path: Path):
    from mekongd.stats import list_recent_signals

    db = tmp_path / "stats.sqlite"
    assert record_signal(db, "good", "first", "qwen3-8b")
    assert record_signal(db, "bad", "second", "claude-sonnet-4-6")
    assert record_signal(db, "good", "third")  # no model

    rows = list_recent_signals(db, limit=10)
    assert [r["note"] for r in rows] == ["third", "second", "first"]
    assert rows[0]["model"] == ""  # empty model stringified
    assert rows[1]["model"] == "claude-sonnet-4-6"
    assert rows[2]["kind"] == "good"


def test_list_recent_signals_honors_limit(tmp_path: Path):
    from mekongd.stats import list_recent_signals

    db = tmp_path / "stats.sqlite"
    for i in range(5):
        record_signal(db, "good", f"note-{i}")
    assert len(list_recent_signals(db, limit=3)) == 3
    # limit capped at 500 internally — a huge limit still works
    assert len(list_recent_signals(db, limit=999999)) == 5
    # non-positive limit → empty
    assert list_recent_signals(db, limit=0) == []


def test_list_recent_signals_empty_when_db_missing(tmp_path: Path):
    from mekongd.stats import list_recent_signals

    assert list_recent_signals(tmp_path / "missing.sqlite", limit=10) == []


def test_aggregate_signals_by_model_honors_since_hours(tmp_path: Path):
    """Rows older than since_hours are excluded."""
    from datetime import datetime, timedelta, timezone

    db = tmp_path / "stats.sqlite"
    # Record a recent signal via public API
    assert record_signal(db, "good", "recent", "qwen3-8b")

    # Backdate a row to 2 days ago via direct SQL
    conn = sqlite3.connect(str(db))
    old_ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    conn.execute(
        "INSERT INTO signals (ts, kind, note, model) VALUES (?, ?, ?, ?)",
        (old_ts, "bad", "stale", "qwen3-8b"),
    )
    conn.commit()
    conn.close()

    # all-time: both counted
    all_time = aggregate_signals_by_model(db)
    assert all_time["qwen3-8b"] == {"good": 1, "bad": 1}

    # last 1h: only the recent good signal
    recent = aggregate_signals_by_model(db, since_hours=1)
    assert recent["qwen3-8b"] == {"good": 1, "bad": 0}


def test_legacy_signals_table_migrates_model_column(tmp_path: Path):
    """Pre-existing signals table without `model` column gets migrated on init_db."""
    db = tmp_path / "legacy.sqlite"
    conn = sqlite3.connect(str(db))
    conn.executescript(
        """
        CREATE TABLE signals (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            ts   TEXT    NOT NULL,
            kind TEXT    NOT NULL,
            note TEXT    NOT NULL DEFAULT ''
        );
        INSERT INTO signals (ts, kind, note) VALUES ('2026-04-17T00:00:00Z', 'bad', 'old');
        """
    )
    conn.commit()
    conn.close()

    # Trigger migration via any record_signal (calls init_db)
    assert record_signal(db, "good", "new", "qwen3-8b")

    by = aggregate_signals_by_model(db)
    assert by[""] == {"good": 0, "bad": 1}  # legacy row bucket
    assert by["qwen3-8b"] == {"good": 1, "bad": 0}
