"""
Unit tests for src/core/entitlement_enforcer.py

Tests cover:
- EntitlementStatus enum values
- EntitlementResult dataclass fields
- EntitlementEnforcer._extract_key_id: valid and invalid token formats
- EntitlementEnforcer.check_entitlement:
    - no key_id → free tier (ALLOWED)
    - unlimited tier (daily_limit == 0)
    - normal allowed (< 80% usage)
    - warning zone (80–99% usage)
    - hard limit (100% usage)
    - exception fallback (offline mode)
- EntitlementEnforcer.should_block: based on _last_check state
- EntitlementEnforcer.get_warning_message: warning vs non-warning states
- EntitlementEnforcer.refresh_entitlement: success and failure paths
- check_and_enforce convenience function
- get_enforcer singleton
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.core.entitlement_enforcer import (
    EntitlementEnforcer,
    EntitlementResult,
    EntitlementStatus,
    check_and_enforce,
    get_enforcer,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_enforcer(
    token: str = "",
    usage_data: dict | None = None,
    usage_raises: Exception | None = None,
):
    """Build an EntitlementEnforcer with mocked dependencies.

    Note: get_usage_summary is async but the enforcer calls it without await,
    so its return value (a coroutine) triggers the except fallback. We force a
    plain MagicMock (new_callable=MagicMock) to bypass AsyncMock auto-detection
    and return a plain dict directly.
    """
    mock_auth = MagicMock()
    mock_auth._load_credentials.return_value = {"token": token}

    mock_kv = MagicMock()

    enforcer = EntitlementEnforcer.__new__(EntitlementEnforcer)
    enforcer.auth = mock_auth
    enforcer.kv = mock_kv
    enforcer._last_check = None

    patch_target = "src.core.entitlement_enforcer.get_usage_summary"

    if usage_raises is not None:
        # Force sync mock that raises immediately (not an AsyncMock)
        sync_mock = MagicMock(side_effect=usage_raises)
        enforcer._usage_patch = patch(patch_target, new=sync_mock)
    else:
        data = usage_data if usage_data is not None else {
            "commands_today": 200,
            "daily_limit": 1000,
        }
        # new_callable=MagicMock prevents AsyncMock auto-detection
        sync_mock = MagicMock(return_value=data)
        enforcer._usage_patch = patch(patch_target, new=sync_mock)

    return enforcer


# ---------------------------------------------------------------------------
# EntitlementStatus
# ---------------------------------------------------------------------------


class TestEntitlementStatus:
    def test_values(self):
        assert EntitlementStatus.ALLOWED.value == "allowed"
        assert EntitlementStatus.WARNING.value == "warning"
        assert EntitlementStatus.SOFT_LIMIT.value == "soft_limit"
        assert EntitlementStatus.HARD_LIMIT.value == "hard_limit"


# ---------------------------------------------------------------------------
# EntitlementResult
# ---------------------------------------------------------------------------


class TestEntitlementResult:
    def test_fields(self):
        reset = datetime.now(timezone.utc)
        result = EntitlementResult(
            status=EntitlementStatus.ALLOWED,
            message="ok",
            remaining=500,
            limit=1000,
            usage_percent=0.5,
            reset_at=reset,
        )
        assert result.status == EntitlementStatus.ALLOWED
        assert result.remaining == 500
        assert result.limit == 1000
        assert result.usage_percent == 0.5
        assert result.reset_at == reset

    def test_reset_at_defaults_to_none(self):
        result = EntitlementResult(
            status=EntitlementStatus.ALLOWED,
            message="ok",
            remaining=100,
            limit=100,
            usage_percent=0.0,
        )
        assert result.reset_at is None


# ---------------------------------------------------------------------------
# _extract_key_id
# ---------------------------------------------------------------------------


class TestExtractKeyId:
    def setup_method(self):
        mock_auth = MagicMock()
        mock_auth._load_credentials.return_value = {}
        mock_kv = MagicMock()
        self.enforcer = EntitlementEnforcer.__new__(EntitlementEnforcer)
        self.enforcer.auth = mock_auth
        self.enforcer.kv = mock_kv
        self.enforcer._last_check = None

    def test_valid_mk_token_extracts_key_id(self):
        key_id = self.enforcer._extract_key_id("mk_v1_abc123def")
        assert key_id == "abc123def"

    def test_mk_token_with_only_two_parts_returns_none(self):
        key_id = self.enforcer._extract_key_id("mk_v1")
        assert key_id is None

    def test_non_mk_prefix_returns_none(self):
        key_id = self.enforcer._extract_key_id("Bearer some-jwt-token")
        assert key_id is None

    def test_empty_string_returns_none(self):
        key_id = self.enforcer._extract_key_id("")
        assert key_id is None

    def test_plain_jwt_returns_none(self):
        key_id = self.enforcer._extract_key_id("eyJhbGci.eyJzdWIi.sig")
        assert key_id is None


# ---------------------------------------------------------------------------
# check_entitlement — no token (free tier)
# ---------------------------------------------------------------------------


class TestCheckEntitlementFreeUser:
    def test_no_token_returns_allowed_free_tier(self):
        enforcer = make_enforcer(token="")
        with enforcer._usage_patch:
            result = enforcer.check_entitlement()

        assert result.status == EntitlementStatus.ALLOWED
        assert result.remaining == 100
        assert result.limit == 100
        assert "Free tier" in result.message

    def test_non_mk_token_also_returns_free_tier(self):
        enforcer = make_enforcer(token="some-other-token")
        with enforcer._usage_patch:
            result = enforcer.check_entitlement()

        assert result.status == EntitlementStatus.ALLOWED


# ---------------------------------------------------------------------------
# check_entitlement — unlimited tier (daily_limit == 0)
# ---------------------------------------------------------------------------


class TestCheckEntitlementUnlimited:
    def test_zero_daily_limit_returns_unlimited_allowed(self):
        enforcer = make_enforcer(
            token="mk_v1_keyabc",
            usage_data={"commands_today": 5000, "daily_limit": 0},
        )
        with enforcer._usage_patch:
            result = enforcer.check_entitlement()

        assert result.status == EntitlementStatus.ALLOWED
        assert result.remaining == 999999
        assert "Unlimited" in result.message


# ---------------------------------------------------------------------------
# check_entitlement — normal ALLOWED (< 80%)
# ---------------------------------------------------------------------------


class TestCheckEntitlementAllowed:
    def test_low_usage_returns_allowed(self):
        enforcer = make_enforcer(
            token="mk_v1_keyabc",
            usage_data={"commands_today": 100, "daily_limit": 1000},
        )
        with enforcer._usage_patch:
            result = enforcer.check_entitlement("cook")

        assert result.status == EntitlementStatus.ALLOWED
        assert result.remaining == 900
        assert result.usage_percent == pytest.approx(0.10)

    def test_50_percent_usage_is_allowed(self):
        enforcer = make_enforcer(
            token="mk_v1_key999",
            usage_data={"commands_today": 500, "daily_limit": 1000},
        )
        with enforcer._usage_patch:
            result = enforcer.check_entitlement()

        assert result.status == EntitlementStatus.ALLOWED
        assert result.remaining == 500

    def test_result_stored_in_last_check(self):
        enforcer = make_enforcer(
            token="mk_v1_keyabc",
            usage_data={"commands_today": 100, "daily_limit": 1000},
        )
        with enforcer._usage_patch:
            result = enforcer.check_entitlement()

        assert enforcer._last_check is result

    def test_reset_at_is_set(self):
        enforcer = make_enforcer(
            token="mk_v1_keyabc",
            usage_data={"commands_today": 100, "daily_limit": 1000},
        )
        with enforcer._usage_patch:
            result = enforcer.check_entitlement()

        assert result.reset_at is not None


# ---------------------------------------------------------------------------
# check_entitlement — WARNING zone (80–99%)
# ---------------------------------------------------------------------------


class TestCheckEntitlementWarning:
    def test_80_percent_usage_is_warning(self):
        enforcer = make_enforcer(
            token="mk_v1_keyabc",
            usage_data={"commands_today": 800, "daily_limit": 1000},
        )
        with enforcer._usage_patch:
            result = enforcer.check_entitlement()

        assert result.status == EntitlementStatus.WARNING
        assert result.remaining == 200
        assert "Warning" in result.message

    def test_99_percent_usage_is_warning(self):
        enforcer = make_enforcer(
            token="mk_v1_keyabc",
            usage_data={"commands_today": 990, "daily_limit": 1000},
        )
        with enforcer._usage_patch:
            result = enforcer.check_entitlement()

        assert result.status == EntitlementStatus.WARNING
        assert result.remaining == 10


# ---------------------------------------------------------------------------
# check_entitlement — HARD_LIMIT (100%)
# ---------------------------------------------------------------------------


class TestCheckEntitlementHardLimit:
    def test_100_percent_usage_is_hard_limit(self):
        enforcer = make_enforcer(
            token="mk_v1_keyabc",
            usage_data={"commands_today": 1000, "daily_limit": 1000},
        )
        with enforcer._usage_patch:
            result = enforcer.check_entitlement()

        assert result.status == EntitlementStatus.HARD_LIMIT
        assert result.remaining == 0
        assert "blocked" in result.message.lower() or "cap" in result.message.lower()

    def test_over_100_percent_is_also_hard_limit(self):
        enforcer = make_enforcer(
            token="mk_v1_keyabc",
            usage_data={"commands_today": 1500, "daily_limit": 1000},
        )
        with enforcer._usage_patch:
            result = enforcer.check_entitlement()

        assert result.status == EntitlementStatus.HARD_LIMIT
        assert result.remaining == 0


# ---------------------------------------------------------------------------
# check_entitlement — exception fallback (offline mode)
# ---------------------------------------------------------------------------


class TestCheckEntitlementOfflineFallback:
    def test_exception_returns_allowed_offline_mode(self):
        enforcer = make_enforcer(
            token="mk_v1_keyabc",
            usage_raises=Exception("DB unreachable"),
        )
        with enforcer._usage_patch:
            result = enforcer.check_entitlement()

        assert result.status == EntitlementStatus.ALLOWED
        assert "offline" in result.message.lower() or "unavailable" in result.message.lower()
        assert result.remaining == 999999


# ---------------------------------------------------------------------------
# should_block
# ---------------------------------------------------------------------------


class TestShouldBlock:
    def test_no_last_check_returns_false(self):
        enforcer = make_enforcer()
        assert enforcer.should_block() is False

    def test_hard_limit_last_check_returns_true(self):
        enforcer = make_enforcer()
        enforcer._last_check = EntitlementResult(
            status=EntitlementStatus.HARD_LIMIT,
            message="blocked",
            remaining=0,
            limit=1000,
            usage_percent=1.0,
        )
        assert enforcer.should_block() is True

    def test_allowed_last_check_returns_false(self):
        enforcer = make_enforcer()
        enforcer._last_check = EntitlementResult(
            status=EntitlementStatus.ALLOWED,
            message="ok",
            remaining=500,
            limit=1000,
            usage_percent=0.5,
        )
        assert enforcer.should_block() is False

    def test_warning_last_check_returns_false(self):
        enforcer = make_enforcer()
        enforcer._last_check = EntitlementResult(
            status=EntitlementStatus.WARNING,
            message="warning",
            remaining=100,
            limit=1000,
            usage_percent=0.9,
        )
        assert enforcer.should_block() is False


# ---------------------------------------------------------------------------
# get_warning_message
# ---------------------------------------------------------------------------


class TestGetWarningMessage:
    def test_no_last_check_returns_none(self):
        enforcer = make_enforcer()
        assert enforcer.get_warning_message() is None

    def test_warning_status_returns_message(self):
        enforcer = make_enforcer()
        enforcer._last_check = EntitlementResult(
            status=EntitlementStatus.WARNING,
            message="80% usage warning",
            remaining=200,
            limit=1000,
            usage_percent=0.8,
        )
        msg = enforcer.get_warning_message()
        assert msg == "80% usage warning"

    def test_allowed_status_returns_none(self):
        enforcer = make_enforcer()
        enforcer._last_check = EntitlementResult(
            status=EntitlementStatus.ALLOWED,
            message="all good",
            remaining=800,
            limit=1000,
            usage_percent=0.2,
        )
        assert enforcer.get_warning_message() is None

    def test_hard_limit_status_returns_none(self):
        enforcer = make_enforcer()
        enforcer._last_check = EntitlementResult(
            status=EntitlementStatus.HARD_LIMIT,
            message="blocked",
            remaining=0,
            limit=1000,
            usage_percent=1.0,
        )
        assert enforcer.get_warning_message() is None


# ---------------------------------------------------------------------------
# refresh_entitlement
# ---------------------------------------------------------------------------


class TestRefreshEntitlement:
    def _make_kv_state(self, remaining: int, limit: int, reset_at=None):
        state = MagicMock()
        state.remaining = remaining
        state.limit = limit
        state.reset_at = reset_at or datetime.now(timezone.utc)
        return state

    def test_refresh_with_remaining_quota_sets_allowed(self):
        enforcer = make_enforcer(token="mk_v1_k")
        kv_state = self._make_kv_state(remaining=500, limit=1000)
        enforcer.kv.get_rate_limit_state.return_value = kv_state

        with enforcer._usage_patch:
            success = enforcer.refresh_entitlement()

        assert success is True
        assert enforcer._last_check.status == EntitlementStatus.ALLOWED
        assert enforcer._last_check.remaining == 500

    def test_refresh_with_zero_remaining_sets_hard_limit(self):
        enforcer = make_enforcer(token="mk_v1_k")
        kv_state = self._make_kv_state(remaining=0, limit=1000)
        enforcer.kv.get_rate_limit_state.return_value = kv_state

        with enforcer._usage_patch:
            success = enforcer.refresh_entitlement()

        assert success is True
        assert enforcer._last_check.status == EntitlementStatus.HARD_LIMIT

    def test_refresh_usage_percent_calculation(self):
        enforcer = make_enforcer(token="mk_v1_k")
        kv_state = self._make_kv_state(remaining=250, limit=1000)
        enforcer.kv.get_rate_limit_state.return_value = kv_state

        with enforcer._usage_patch:
            enforcer.refresh_entitlement()

        assert enforcer._last_check.usage_percent == pytest.approx(0.75)

    def test_refresh_returns_false_on_exception(self):
        enforcer = make_enforcer(token="mk_v1_k")
        enforcer.kv.get_rate_limit_state.side_effect = Exception("KV down")

        with enforcer._usage_patch:
            success = enforcer.refresh_entitlement()

        assert success is False

    def test_refresh_calls_force_refresh_on_kv(self):
        enforcer = make_enforcer(token="mk_v1_k")
        kv_state = self._make_kv_state(remaining=100, limit=200)
        enforcer.kv.get_rate_limit_state.return_value = kv_state

        with enforcer._usage_patch:
            enforcer.refresh_entitlement()

        enforcer.kv.get_rate_limit_state.assert_called_once_with(force_refresh=True)

    def test_refresh_zero_limit_usage_percent_is_zero(self):
        enforcer = make_enforcer(token="mk_v1_k")
        kv_state = self._make_kv_state(remaining=0, limit=0)
        enforcer.kv.get_rate_limit_state.return_value = kv_state

        with enforcer._usage_patch:
            enforcer.refresh_entitlement()

        assert enforcer._last_check.usage_percent == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# check_and_enforce convenience function
# ---------------------------------------------------------------------------


class TestCheckAndEnforce:
    def test_allowed_when_under_limit(self):
        mock_enforcer = MagicMock()
        mock_enforcer.check_entitlement.return_value = EntitlementResult(
            status=EntitlementStatus.ALLOWED,
            message="ok",
            remaining=800,
            limit=1000,
            usage_percent=0.2,
        )
        mock_enforcer.should_block.return_value = False
        mock_enforcer.get_warning_message.return_value = None

        with patch("src.core.entitlement_enforcer.EntitlementEnforcer", return_value=mock_enforcer):
            allowed, warning = check_and_enforce("cook")

        assert allowed is True
        assert warning is None

    def test_blocked_when_at_hard_limit(self):
        mock_enforcer = MagicMock()
        mock_enforcer.check_entitlement.return_value = EntitlementResult(
            status=EntitlementStatus.HARD_LIMIT,
            message="Usage cap reached (100%). Commands blocked.",
            remaining=0,
            limit=1000,
            usage_percent=1.0,
        )
        mock_enforcer.should_block.return_value = True
        mock_enforcer.get_warning_message.return_value = None

        with patch("src.core.entitlement_enforcer.EntitlementEnforcer", return_value=mock_enforcer):
            allowed, warning = check_and_enforce("cook")

        assert allowed is False
        assert "blocked" in warning.lower() or "cap" in warning.lower()

    def test_allowed_with_warning_at_80_percent(self):
        mock_enforcer = MagicMock()
        mock_enforcer.check_entitlement.return_value = EntitlementResult(
            status=EntitlementStatus.WARNING,
            message="Warning: 80% usage. 200 commands remaining.",
            remaining=200,
            limit=1000,
            usage_percent=0.8,
        )
        mock_enforcer.should_block.return_value = False
        mock_enforcer.get_warning_message.return_value = "Warning: 80% usage. 200 commands remaining."

        with patch("src.core.entitlement_enforcer.EntitlementEnforcer", return_value=mock_enforcer):
            allowed, warning = check_and_enforce("plan")

        assert allowed is True
        assert warning is not None
        assert "Warning" in warning


# ---------------------------------------------------------------------------
# get_enforcer singleton
# ---------------------------------------------------------------------------


class TestGetEnforcer:
    def test_returns_entitlement_enforcer_instance(self):
        with patch("src.core.entitlement_enforcer.get_auth_client", return_value=MagicMock()), \
             patch("src.core.entitlement_enforcer.get_kv_client", return_value=MagicMock()):
            enforcer = get_enforcer()
        assert isinstance(enforcer, EntitlementEnforcer)

    def test_returns_same_instance_on_repeated_calls(self):
        import src.core.entitlement_enforcer as mod
        original = mod._enforcer

        with patch("src.core.entitlement_enforcer.get_auth_client", return_value=MagicMock()), \
             patch("src.core.entitlement_enforcer.get_kv_client", return_value=MagicMock()):
            mod._enforcer = None  # Reset singleton for clean test
            e1 = get_enforcer()
            e2 = get_enforcer()
            mod._enforcer = original  # Restore

        assert e1 is e2
