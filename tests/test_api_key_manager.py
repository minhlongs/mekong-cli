"""Tests for API Key Manager — Condition C3 API bridge."""

import time

import pytest

from src.core.api_key_manager import (
    ApiKey,
    ApiKeyManager,
    KeyStatus,
    ValidationResult,
    RateLimitState,
)


class TestKeyStatus:
    """Test KeyStatus enum."""

    def test_active_value(self):
        assert KeyStatus.ACTIVE == "active"

    def test_revoked_value(self):
        assert KeyStatus.REVOKED == "revoked"

    def test_expired_value(self):
        assert KeyStatus.EXPIRED == "expired"

    def test_suspended_value(self):
        assert KeyStatus.SUSPENDED == "suspended"


class TestApiKey:
    """Test ApiKey dataclass."""

    def test_create_active_key(self):
        key = ApiKey(
            key_id="mk_test123",
            key_secret="secret",
            tenant_id="t1",
            tier="pro",
        )
        assert key.status == KeyStatus.ACTIVE
        assert key.rate_limit == 60
        assert key.request_count == 0

    def test_is_active_true(self):
        key = ApiKey(
            key_id="mk_test",
            key_secret="s",
            tenant_id="t1",
            tier="free",
        )
        assert key.is_active is True

    def test_is_active_false_when_revoked(self):
        key = ApiKey(
            key_id="mk_test",
            key_secret="s",
            tenant_id="t1",
            tier="free",
            status=KeyStatus.REVOKED,
        )
        assert key.is_active is False

    def test_is_expired_false_no_expiry(self):
        key = ApiKey(
            key_id="mk_test",
            key_secret="s",
            tenant_id="t1",
            tier="free",
        )
        assert key.is_expired is False

    def test_is_expired_true_past_date(self):
        key = ApiKey(
            key_id="mk_test",
            key_secret="s",
            tenant_id="t1",
            tier="free",
            expires_at="2020-01-01T00:00:00+00:00",
        )
        assert key.is_expired is True

    def test_days_until_expiry_none(self):
        key = ApiKey(
            key_id="mk_test",
            key_secret="s",
            tenant_id="t1",
            tier="free",
        )
        assert key.days_until_expiry is None

    def test_days_until_expiry_past(self):
        key = ApiKey(
            key_id="mk_test",
            key_secret="s",
            tenant_id="t1",
            tier="free",
            expires_at="2020-01-01T00:00:00+00:00",
        )
        assert key.days_until_expiry == 0

    def test_to_public_dict_no_secret(self):
        key = ApiKey(
            key_id="mk_test",
            key_secret="super_secret",
            tenant_id="t1",
            tier="pro",
        )
        d = key.to_public_dict()
        assert "key_secret" not in d
        assert d["key_id"] == "mk_test"
        assert d["tenant_id"] == "t1"

    def test_from_dict(self):
        data = {
            "key_id": "mk_abc",
            "key_secret": "sec",
            "tenant_id": "t1",
            "tier": "enterprise",
            "status": "active",
            "rate_limit": 500,
        }
        key = ApiKey.from_dict(data)
        assert key.key_id == "mk_abc"
        assert key.tier == "enterprise"
        assert key.rate_limit == 500

    def test_from_dict_defaults(self):
        key = ApiKey.from_dict({})
        assert key.key_id == ""
        assert key.tier == "free"
        assert key.status == KeyStatus.ACTIVE


class TestApiKeyManager:
    """Test ApiKeyManager core operations."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create manager with temp config dir."""
        return ApiKeyManager(config_dir=tmp_path)

    def test_generate_key(self, manager):
        key = manager.generate_key(tenant_id="t1", tier="pro")
        assert key.key_id.startswith("mk_")
        assert key.tenant_id == "t1"
        assert key.tier == "pro"
        assert key.status == KeyStatus.ACTIVE

    def test_generate_key_rate_limit_by_tier(self, manager):
        free_key = manager.generate_key("t1", tier="free")
        pro_key = manager.generate_key("t2", tier="pro")
        ent_key = manager.generate_key("t3", tier="enterprise")
        assert free_key.rate_limit == 30
        assert pro_key.rate_limit == 100
        assert ent_key.rate_limit == 500

    def test_generate_key_custom_rate_limit(self, manager):
        key = manager.generate_key("t1", tier="free", rate_limit=42)
        assert key.rate_limit == 42

    def test_generate_key_with_expiry(self, manager):
        key = manager.generate_key("t1", expires_in_days=30)
        assert key.expires_at is not None

    def test_generate_key_with_metadata(self, manager):
        key = manager.generate_key("t1", metadata={"env": "test"})
        assert key.metadata == {"env": "test"}

    def test_validate_key_valid(self, manager):
        key = manager.generate_key("t1", tier="pro")
        result = manager.validate_key(key.key_id, check_rate_limit=False)
        assert result.valid is True
        assert result.tenant_id == "t1"
        assert result.tier == "pro"

    def test_validate_key_not_found(self, manager):
        result = manager.validate_key("mk_nonexistent")
        assert result.valid is False
        assert result.error_code == "KEY_NOT_FOUND"

    def test_revoke_key(self, manager):
        key = manager.generate_key("t1")
        assert manager.revoke_key(key.key_id) is True
        result = manager.validate_key(key.key_id)
        assert result.valid is False
        assert result.error_code == "KEY_REVOKED"

    def test_revoke_nonexistent(self, manager):
        assert manager.revoke_key("mk_ghost") is False

    def test_suspend_key(self, manager):
        key = manager.generate_key("t1")
        assert manager.suspend_key(key.key_id) is True
        result = manager.validate_key(key.key_id)
        assert result.valid is False
        assert result.error_code == "KEY_SUSPENDED"

    def test_reactivate_key(self, manager):
        key = manager.generate_key("t1")
        manager.suspend_key(key.key_id)
        assert manager.reactivate_key(key.key_id) is True
        result = manager.validate_key(key.key_id, check_rate_limit=False)
        assert result.valid is True

    def test_delete_key(self, manager):
        key = manager.generate_key("t1")
        assert manager.delete_key(key.key_id) is True
        result = manager.validate_key(key.key_id)
        assert result.valid is False

    def test_delete_nonexistent(self, manager):
        assert manager.delete_key("mk_ghost") is False

    def test_get_keys_for_tenant(self, manager):
        manager.generate_key("t1", tier="free")
        manager.generate_key("t1", tier="pro")
        manager.generate_key("t2", tier="free")
        keys = manager.get_keys_for_tenant("t1")
        assert len(keys) == 2

    def test_get_key_redacted(self, manager):
        key = manager.generate_key("t1")
        retrieved = manager.get_key(key.key_id)
        assert retrieved is not None
        assert retrieved.key_secret == "***REDACTED***"

    def test_get_key_nonexistent(self, manager):
        assert manager.get_key("mk_ghost") is None

    def test_clear_all_keys(self, manager):
        manager.generate_key("t1")
        manager.generate_key("t2")
        assert manager.clear_all_keys() is True
        keys = manager.get_keys_for_tenant("t1")
        assert len(keys) == 0


class TestRateLimiting:
    """Test rate limiting logic."""

    @pytest.fixture
    def manager(self, tmp_path):
        return ApiKeyManager(config_dir=tmp_path)

    def test_within_rate_limit(self, manager):
        within, remaining = manager._check_rate_limit("k1", 60)
        assert within is True
        assert remaining == 60

    def test_rate_limit_increment(self, manager):
        manager._increment_rate_limit("k1", 10)
        within, remaining = manager._check_rate_limit("k1", 10)
        assert within is True
        assert remaining == 9

    def test_rate_limit_exceeded(self, manager):
        for _ in range(10):
            manager._increment_rate_limit("k1", 10)
        within, remaining = manager._check_rate_limit("k1", 10)
        assert within is False
        assert remaining == 0

    def test_rate_limit_window_reset(self, manager):
        """After window expires, counter resets."""
        manager._rate_limits["k1"] = RateLimitState(
            window_start=time.time() - 120,  # 2 min ago (window=60s)
            request_count=999,
            rate_limit=10,
        )
        within, remaining = manager._check_rate_limit("k1", 10)
        assert within is True
        assert remaining == 10


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_valid_result(self):
        r = ValidationResult(valid=True, tenant_id="t1", tier="pro")
        assert r.valid is True
        assert r.error is None

    def test_invalid_result(self):
        r = ValidationResult(
            valid=False,
            error="Rate limit exceeded",
            error_code="RATE_LIMIT_EXCEEDED",
        )
        assert r.valid is False
        assert r.error_code == "RATE_LIMIT_EXCEEDED"
