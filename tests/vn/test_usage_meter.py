"""
Tests cho src/core/usage_meter.py — event logging + credit gating.

Isolates file I/O via monkeypatching CONFIG_DIR + EVENTS_FILE + CREDITS_FILE
to per-test tmp paths (Phase 6 pilot data lives in ~/.mekong/).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core import usage_meter as um


@pytest.fixture
def isolated_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect meter to a clean per-test directory."""
    monkeypatch.setattr(um, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(um, "EVENTS_FILE", tmp_path / "usage_events.jsonl")
    monkeypatch.setattr(um, "CREDITS_FILE", tmp_path / "pilot_credits.json")
    # Clear the cached cost table — pricing.json read still works
    um._load_costs.cache_clear()
    return tmp_path


@pytest.fixture
def seed_user(isolated_paths: Path, monkeypatch: pytest.MonkeyPatch):
    """Factory: create a user with N credits + set MEKONG_USER_ID."""
    def _make(user_id: str = "opc_test_001", credits: int = 50):
        monkeypatch.setenv("MEKONG_USER_ID", user_id)
        balances_path = isolated_paths / "pilot_credits.json"
        balances_path.write_text(json.dumps({user_id: credits}), encoding="utf-8")
        return user_id
    return _make


class TestCostLookup:
    """Phí phải khớp factory/contracts/pricing.json::vn_services."""

    def test_ke_toan_costs_1_credit(self, isolated_paths):
        assert um._command_cost("ke-toan") == 1

    def test_zalo_oa_costs_2_credits(self, isolated_paths):
        assert um._command_cost("zalo-oa") == 2

    def test_phap_ly_vn_costs_2_credits(self, isolated_paths):
        assert um._command_cost("phap-ly-vn") == 2

    def test_subcommand_falls_back_to_base(self, isolated_paths):
        """'ke-toan invoice' không có trong table → dùng cost của 'ke-toan'."""
        assert um._command_cost("ke-toan invoice") == 1

    def test_unknown_command_uses_default(self, isolated_paths):
        assert um._command_cost("nonexistent-cmd") == um.DEFAULT_COST


class TestEventLogging:
    """Mỗi track() = 1 dòng JSONL với schema cố định."""

    def test_anonymous_user_logs_no_credit_gate(self, isolated_paths, monkeypatch):
        monkeypatch.delenv("MEKONG_USER_ID", raising=False)
        result = um.track("ke-toan")
        assert result.user_id == um.ANONYMOUS_USER
        assert result.balance_after == 0
        events = (isolated_paths / "usage_events.jsonl").read_text().strip().splitlines()
        assert len(events) == 1
        rec = json.loads(events[0])
        assert rec["user_id"] == "anonymous"
        assert rec["command"] == "ke-toan"
        assert rec["cost"] == 1
        assert rec["success"] is True

    def test_authenticated_track_decrements(self, isolated_paths, seed_user):
        uid = seed_user(credits=10)
        result = um.track("ke-toan")
        assert result.user_id == uid
        assert result.cost == 1
        assert result.balance_after == 9
        # Persisted on disk
        balances = json.loads((isolated_paths / "pilot_credits.json").read_text())
        assert balances[uid] == 9

    def test_event_includes_duration_ms(self, isolated_paths, seed_user):
        seed_user(credits=10)
        um.track("ke-toan", duration_ms=425)
        rec = json.loads((isolated_paths / "usage_events.jsonl").read_text().strip().splitlines()[0])
        assert rec["duration_ms"] == 425

    def test_failed_command_still_logs_but_decrements(self, isolated_paths, seed_user):
        """Track failures the same as successes — usage = usage. Founder
        analyzes error_rate via pilot-metrics.py separately."""
        seed_user(credits=10)
        um.track("ke-toan", success=False)
        rec = json.loads((isolated_paths / "usage_events.jsonl").read_text().strip().splitlines()[0])
        assert rec["success"] is False
        balances = json.loads((isolated_paths / "pilot_credits.json").read_text())
        assert balances["opc_test_001"] == 9  # decremented


class TestCreditGating:
    """Insufficient credits → exception + zero balance change."""

    def test_zero_balance_raises(self, isolated_paths, seed_user):
        seed_user(credits=0)
        with pytest.raises(um.InsufficientCreditsError) as exc:
            um.track("ke-toan")
        assert exc.value.cost == 1
        assert exc.value.balance == 0

    def test_cost_exceeds_balance_raises(self, isolated_paths, seed_user):
        seed_user(credits=1)
        with pytest.raises(um.InsufficientCreditsError):
            um.track("zalo-oa")  # cost = 2, balance = 1

    def test_failed_credit_check_logs_error_event(self, isolated_paths, seed_user):
        seed_user(credits=0)
        with pytest.raises(um.InsufficientCreditsError):
            um.track("ke-toan")
        events = (isolated_paths / "usage_events.jsonl").read_text().strip().splitlines()
        assert len(events) == 1
        rec = json.loads(events[0])
        assert rec["success"] is False
        assert rec["error"] == "insufficient_credits"

    def test_failed_credit_check_does_not_decrement(self, isolated_paths, seed_user):
        seed_user(credits=1)
        with pytest.raises(um.InsufficientCreditsError):
            um.track("zalo-oa")  # cost = 2 > balance = 1
        balances = json.loads((isolated_paths / "pilot_credits.json").read_text())
        assert balances["opc_test_001"] == 1  # unchanged

    def test_error_message_includes_upgrade_link(self, isolated_paths, seed_user):
        seed_user(credits=0)
        with pytest.raises(um.InsufficientCreditsError) as exc:
            um.track("ke-toan")
        assert "mekongmind.com/vn/bang-gia" in str(exc.value)


class TestBalanceQuery:
    def test_balance_for_known_user(self, isolated_paths, seed_user):
        uid = seed_user(credits=42)
        assert um.balance(uid) == 42

    def test_balance_for_unknown_user_returns_zero(self, isolated_paths, monkeypatch):
        monkeypatch.setattr(um, "CREDITS_FILE", isolated_paths / "missing.json")
        assert um.balance("opc_ghost") == 0

    def test_balance_for_anonymous_is_zero(self, isolated_paths, monkeypatch):
        monkeypatch.delenv("MEKONG_USER_ID", raising=False)
        assert um.balance() == 0


class TestStopwatch:
    def test_stopwatch_tracks_on_exit(self, isolated_paths, seed_user):
        seed_user(credits=10)
        with um.Stopwatch("ke-toan"):
            pass
        events = (isolated_paths / "usage_events.jsonl").read_text().strip().splitlines()
        assert len(events) == 1
        rec = json.loads(events[0])
        assert rec["command"] == "ke-toan"
        assert rec["success"] is True
        assert rec["duration_ms"] >= 0

    def test_stopwatch_marks_failure_on_exception(self, isolated_paths, seed_user):
        seed_user(credits=10)
        with pytest.raises(ValueError):
            with um.Stopwatch("ke-toan"):
                raise ValueError("boom")
        rec = json.loads((isolated_paths / "usage_events.jsonl").read_text().strip().splitlines()[0])
        assert rec["success"] is False

    def test_stopwatch_does_not_shadow_existing_exception(self, isolated_paths, seed_user):
        """Nếu user code đã raise + insufficient credits trigger ngay sau → original raise wins."""
        seed_user(credits=0)
        with pytest.raises(ValueError, match="user_error"):
            with um.Stopwatch("zalo-oa"):
                raise ValueError("user_error")
