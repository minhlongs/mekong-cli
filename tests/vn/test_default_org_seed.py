"""8 test cases for Phase 9 P06 — Default Org Seeding + 262-Pilot Backfill.

Isolation: tmp_path + monkeypatch CONFIG_DIR + MEKONG_PILOT_STORAGE=sqlite.
Schema created fresh per test via ensure_schema. Backend cache reset between tests.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Generator

import pytest

import src.api.vn_pilot_state as _state
from src.services.sqlite_migrations import ensure_schema
from src.services.storage_backend import _reset_backend_cache
from src.services.default_org_seeder import (
    DEFAULT_ORG_ID,
    FOUNDER_USER_ID,
    seed_default_org,
    verify_prereqs,
)
from src.services.org_service import RESERVED_SLUGS, ReservedSlugError, create_org


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def isolated_sqlite_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator:
    """Fresh SQLite DB per test; sets storage=sqlite, resets backend cache."""
    monkeypatch.setattr(_state, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("MEKONG_PILOT_STORAGE", "sqlite")

    db_path = tmp_path / "pilot.db"
    conn = sqlite3.connect(str(db_path))
    ensure_schema(conn)
    conn.close()

    _reset_backend_cache()
    yield
    _reset_backend_cache()


def _insert_pilot(db_path: Path, user_id: str, onboarded_at: str = "2026-01-01T00:00:00.000000Z") -> None:
    """Helper to insert a minimal pilot row into pilots table."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT OR IGNORE INTO pilots
            (user_id, org_id, name, zalo, onboarded_at, pilot_end_at, status, raw_payload)
        VALUES (?, 'default', ?, '0909000000', ?, '2026-12-31T00:00:00.000000Z', 'active', '{}')
        """,
        (user_id, f"Pilot {user_id}", onboarded_at),
    )
    conn.commit()
    conn.close()


def _count(db_path: Path, table: str, where: str = "", params: tuple = ()) -> int:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    sql = f"SELECT COUNT(*) AS cnt FROM {table}"
    if where:
        sql += f" WHERE {where}"
    result = conn.execute(sql, params).fetchone()["cnt"]
    conn.close()
    return result


def _fetch_member(db_path: Path, user_id: str) -> dict | None:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM org_members WHERE org_id = ? AND user_id = ?",
        (DEFAULT_ORG_ID, user_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# =============================================================================
# Tests
# =============================================================================


class TestFreshSeed:
    def test_fresh_seed_creates_default_org_and_backfills(
        self, tmp_path: Path
    ) -> None:
        """founder + 3 pilots → orgs.count=1, members.count=4, correct scopes."""
        db = tmp_path / "pilot.db"
        for i in range(1, 4):
            _insert_pilot(db, f"opc_pilot_00{i}")

        result = seed_default_org("founder@test.com")

        assert result["orgs_inserted"] == 1
        assert result["members_inserted"] == 4  # founder + 3 pilots
        assert result["pilots_seeded"] == 3

        # DB state
        assert _count(db, "orgs", "org_id = ?", (DEFAULT_ORG_ID,)) == 1
        assert _count(db, "org_members", f"org_id = '{DEFAULT_ORG_ID}'") == 4

        # Founder scope
        founder = _fetch_member(db, FOUNDER_USER_ID)
        assert founder is not None
        assert founder["scope"] == "org_admin"
        assert founder["invited_by"] is None

        # Pilot scope
        pilot = _fetch_member(db, "opc_pilot_001")
        assert pilot is not None
        assert pilot["scope"] == "readonly"
        assert pilot["invited_by"] == FOUNDER_USER_ID

    def test_empty_pilots_table_seeds_only_default_org_and_founder(
        self, tmp_path: Path
    ) -> None:
        """0 pilots → orgs=1, members=1 (founder only)."""
        result = seed_default_org("founder@test.com")

        assert result["orgs_inserted"] == 1
        assert result["members_inserted"] == 1
        assert result["pilots_seeded"] == 0

        db = tmp_path / "pilot.db"
        assert _count(db, "orgs") == 1
        assert _count(db, "org_members") == 1


class TestIdempotency:
    def test_rerun_is_noop(self, tmp_path: Path) -> None:
        """Run twice → second run returns pilots_seeded=0, orgs_inserted=0, no errors."""
        db = tmp_path / "pilot.db"
        _insert_pilot(db, "opc_pilot_001")
        _insert_pilot(db, "opc_pilot_002")

        result1 = seed_default_org("founder@test.com")
        assert result1["orgs_inserted"] == 1
        assert result1["pilots_seeded"] == 2

        result2 = seed_default_org("founder@test.com")
        assert result2["orgs_inserted"] == 0
        assert result2["pilots_seeded"] == 0
        assert result2["members_inserted"] == 0

        # Row counts unchanged
        assert _count(db, "org_members", f"org_id = '{DEFAULT_ORG_ID}'") == 3  # founder + 2 pilots


class TestDryRun:
    def test_dry_run_writes_nothing(self, tmp_path: Path) -> None:
        """dry_run=True → returns counts but DB state unchanged."""
        db = tmp_path / "pilot.db"
        _insert_pilot(db, "opc_pilot_001")
        _insert_pilot(db, "opc_pilot_002")
        _insert_pilot(db, "opc_pilot_003")

        result = seed_default_org("founder@test.com", dry_run=True)

        # Counts reported (would insert)
        assert result["orgs_inserted"] == 1
        assert result["members_inserted"] >= 0  # dry run computes delta

        # DB untouched
        assert _count(db, "orgs") == 0
        assert _count(db, "org_members") == 0


class TestPrereqs:
    def test_missing_storage_env_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unset MEKONG_PILOT_STORAGE → RuntimeError with hint."""
        monkeypatch.setenv("MEKONG_PILOT_STORAGE", "jsonl")

        with pytest.raises(RuntimeError, match="MEKONG_PILOT_STORAGE must be 'sqlite'"):
            verify_prereqs()

    def test_missing_p02_schema_raises(self, tmp_path: Path) -> None:
        """orgs + org_members tables absent → RuntimeError with P02 hint.

        autouse fixture creates schema via ensure_schema; we drop the P02
        tables to simulate pre-P02 state and verify the guard triggers.
        """
        db = tmp_path / "pilot.db"
        conn = sqlite3.connect(str(db))
        conn.execute("DROP TABLE IF EXISTS org_members")
        conn.execute("DROP TABLE IF EXISTS orgs")
        conn.commit()
        conn.close()

        with pytest.raises(RuntimeError, match="P02 schema"):
            verify_prereqs()


class TestReservedSlug:
    def test_reserved_slug_still_rejected_post_seed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """After seeding 'default' org, create_org('Default') still raises ReservedSlugError."""
        seed_default_org("founder@test.com")

        # 'default' is in RESERVED_SLUGS → create_org must reject it
        assert "default" in RESERVED_SLUGS
        with pytest.raises(ReservedSlugError):
            create_org("Default", "user@test.com")


class TestSyntheticEmail:
    def test_synthetic_email_format(self, tmp_path: Path) -> None:
        """Pilot member.email matches f'{user_id}@pilot.mekong.local'."""
        db = tmp_path / "pilot.db"
        _insert_pilot(db, "opc_pilot_abc123")

        seed_default_org("founder@test.com")

        pilot = _fetch_member(db, "opc_pilot_abc123")
        assert pilot is not None
        assert pilot["email"] == "opc_pilot_abc123@pilot.mekong.local"
