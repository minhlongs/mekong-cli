# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for API Key Manager (src/core/api_key_manager.py).

All tests are hermetic and deterministic: filesystem persistence and Fernet
keys are scoped to pytest tmp_path to achieve 100% statement and branch coverage
without side effects.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from src.core.api_key_manager import (
    ApiKey,
    ApiKeyManager,
    KeyStatus,
    RateLimitState,
    ValidationResult,
    generate_api_key,
    get_api_key_manager,
    revoke_api_key,
    validate_api_key,
)


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory for tests."""
    config_dir = tmp_path / "mekong_config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def key_manager(temp_config_dir: Path) -> ApiKeyManager:
    """Create ApiKeyManager with temp directory."""
    return ApiKeyManager(config_dir=temp_config_dir)


# ===========================================================================
# Enum & Dataclass Tests
# ===========================================================================


class TestKeyStatus:
    """Test KeyStatus enum values."""

    def test_values(self) -> None:
        assert KeyStatus.ACTIVE == "active"
        assert KeyStatus.REVOKED == "revoked"
        assert KeyStatus.EXPIRED == "expired"
        assert KeyStatus.SUSPENDED == "suspended"


class TestApiKeyDataclass:
    """Test ApiKey dataclass properties and methods."""

    def test_default_values(self) -> None:
        key = ApiKey(
            key_id="mk_test123",
            key_secret="secret",
            tenant_id="t1",
            tier="pro",
        )
        assert key.status == KeyStatus.ACTIVE
        assert key.rate_limit == 60
        assert key.request_count == 0
        assert key.last_used_at is None
        assert key.metadata == {}

    def test_is_expired_false_when_no_expiry(self) -> None:
        key = ApiKey(
            key_id="mk_test",
            key_secret="secret",
            tenant_id="tenant_1",
            tier="free",
        )
        assert key.is_expired is False

    def test_is_expired_true_when_past_expiry(self) -> None:
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        key = ApiKey(
            key_id="mk_test",
            key_secret="secret",
            tenant_id="tenant_1",
            tier="free",
            expires_at=past,
        )
        assert key.is_expired is True

    def test_is_expired_false_when_future_expiry(self) -> None:
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        key = ApiKey(
            key_id="mk_test",
            key_secret="secret",
            tenant_id="tenant_1",
            tier="free",
            expires_at=future,
        )
        assert key.is_expired is False

    def test_is_expired_catches_value_error(self) -> None:
        key = ApiKey(
            key_id="mk_test",
            key_secret="secret",
            tenant_id="tenant_1",
            tier="free",
            expires_at="not-a-valid-iso-date",
        )
        assert key.is_expired is False

    def test_is_active_when_status_active_and_not_expired(self) -> None:
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        key = ApiKey(
            key_id="mk_test",
            key_secret="secret",
            tenant_id="tenant_1",
            tier="free",
            status=KeyStatus.ACTIVE,
            expires_at=future,
        )
        assert key.is_active is True

    def test_is_active_false_when_revoked(self) -> None:
        key = ApiKey(
            key_id="mk_test",
            key_secret="secret",
            tenant_id="tenant_1",
            tier="free",
            status=KeyStatus.REVOKED,
        )
        assert key.is_active is False

    def test_days_until_expiry_none_when_no_expiry(self) -> None:
        key = ApiKey(
            key_id="mk_test",
            key_secret="secret",
            tenant_id="tenant_1",
            tier="free",
            expires_at=None,
        )
        assert key.days_until_expiry is None

    def test_days_until_expiry_future(self) -> None:
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        key = ApiKey(
            key_id="mk_test",
            key_secret="secret",
            tenant_id="tenant_1",
            tier="free",
            expires_at=future,
        )
        assert key.days_until_expiry in (29, 30, 31)

    def test_days_until_expiry_past_clamped_to_zero(self) -> None:
        past = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        key = ApiKey(
            key_id="mk_test",
            key_secret="secret",
            tenant_id="tenant_1",
            tier="free",
            expires_at=past,
        )
        assert key.days_until_expiry == 0

    def test_days_until_expiry_catches_value_error(self) -> None:
        key = ApiKey(
            key_id="mk_test",
            key_secret="secret",
            tenant_id="tenant_1",
            tier="free",
            expires_at="invalid-date",
        )
        assert key.days_until_expiry is None

    def test_to_public_dict_excludes_secret(self) -> None:
        key = ApiKey(
            key_id="mk_test",
            key_secret="secret123",
            tenant_id="tenant_1",
            tier="pro",
        )
        data = key.to_public_dict()
        assert "key_secret" not in data
        assert data["key_id"] == "mk_test"
        assert data["tier"] == "pro"

    def test_from_dict_full(self) -> None:
        data = {
            "key_id": "mk_test_123",
            "key_secret": "secret_abc",
            "tenant_id": "tenant_xyz",
            "tier": "enterprise",
            "status": "active",
            "created_at": "2026-01-01T00:00:00+00:00",
            "expires_at": "2026-12-31T00:00:00+00:00",
            "last_used_at": "2026-02-01T00:00:00+00:00",
            "rate_limit": 120,
            "request_count": 42,
            "metadata": {"org": "vietnam"},
        }
        key = ApiKey.from_dict(data)
        assert key.key_id == "mk_test_123"
        assert key.key_secret == "secret_abc"
        assert key.tier == "enterprise"
        assert key.status == KeyStatus.ACTIVE
        assert key.rate_limit == 120
        assert key.request_count == 42
        assert key.metadata == {"org": "vietnam"}

    def test_from_dict_defaults(self) -> None:
        key = ApiKey.from_dict({})
        assert key.key_id == ""
        assert key.key_secret == ""
        assert key.tenant_id == ""
        assert key.tier == "free"
        assert key.status == KeyStatus.ACTIVE
        assert key.rate_limit == 60


class TestValidationResultAndRateLimitState:
    """Test ValidationResult and RateLimitState dataclasses."""

    def test_validation_result_fields(self) -> None:
        res = ValidationResult(
            valid=True,
            tenant_id="t1",
            tier="premium",
            rate_limit_remaining=55,
        )
        assert res.valid is True
        assert res.tenant_id == "t1"
        assert res.error is None
        assert res.error_code is None
        assert res.rate_limit_remaining == 55

    def test_rate_limit_state_fields(self) -> None:
        state = RateLimitState(
            window_start=100.0,
            request_count=5,
            rate_limit=60,
        )
        assert state.window_start == 100.0
        assert state.request_count == 5
        assert state.rate_limit == 60


# ===========================================================================
# Storage, Encryption & Decryption Tests
# ===========================================================================


class TestApiKeyManagerStorageAndCrypto:
    """Test storage initialization, encryption, and decryption."""

    def test_get_secure_storage_import_error(self, temp_config_dir: Path) -> None:
        with patch.dict("sys.modules", {"src.auth.secure_storage": None}):
            manager = ApiKeyManager(config_dir=temp_config_dir)
            assert manager._get_secure_storage() is None

    def test_hash_key(self, key_manager: ApiKeyManager) -> None:
        h = key_manager._hash_key("my_secret")
        assert len(h) == 64
        assert h == key_manager._hash_key("my_secret")

    def test_encrypt_with_secure_storage_success(self, key_manager: ApiKeyManager) -> None:
        mock_storage = MagicMock()
        mock_storage.encrypt.return_value = "enc_secret"
        key_manager._storage = mock_storage
        assert key_manager._encrypt("plain") == "enc_secret"
        mock_storage.encrypt.assert_called_once_with("plain")

    def test_encrypt_with_secure_storage_error_falls_back(
        self, key_manager: ApiKeyManager, tmp_path: Path
    ) -> None:
        mock_storage = MagicMock()
        mock_storage.encrypt.side_effect = RuntimeError("vault locked")
        key_manager._storage = mock_storage

        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch("pathlib.Path.home", return_value=fake_home):
            enc = key_manager._encrypt("data123")
            assert enc != "data123"

    def test_encrypt_fallback_creates_new_key_file(
        self, key_manager: ApiKeyManager, tmp_path: Path
    ) -> None:
        key_manager._storage = None
        fake_home = tmp_path / "home_new"
        fake_home.mkdir()
        with patch("pathlib.Path.home", return_value=fake_home):
            enc = key_manager._encrypt("secret_data")
            key_file = fake_home / ".mekong" / ".api_key_fernet_key"
            assert key_file.exists()
            key = key_file.read_text().strip()
            # Verify can decrypt with generated fernet key
            f = Fernet(key.encode())
            assert f.decrypt(enc.encode()).decode() == "secret_data"

    def test_encrypt_fallback_uses_existing_key_file(
        self, key_manager: ApiKeyManager, tmp_path: Path
    ) -> None:
        key_manager._storage = None
        fake_home = tmp_path / "home_existing"
        key_dir = fake_home / ".mekong"
        key_dir.mkdir(parents=True)
        key_file = key_dir / ".api_key_fernet_key"
        gen_key = Fernet.generate_key().decode()
        key_file.write_text(gen_key)

        with patch("pathlib.Path.home", return_value=fake_home):
            enc = key_manager._encrypt("my_secret")
            f = Fernet(gen_key.encode())
            assert f.decrypt(enc.encode()).decode() == "my_secret"

    def test_encrypt_fallback_exception_raises_runtime_error(
        self, key_manager: ApiKeyManager, tmp_path: Path
    ) -> None:
        key_manager._storage = None
        fake_home = tmp_path / "home_err"
        fake_home.mkdir()
        with patch("pathlib.Path.home", return_value=fake_home):
            with patch("cryptography.fernet.Fernet.generate_key", side_effect=Exception("key gen fail")):
                with pytest.raises(RuntimeError, match="Cannot encrypt API key"):
                    key_manager._encrypt("secret")

    def test_decrypt_with_secure_storage_success(self, key_manager: ApiKeyManager) -> None:
        mock_storage = MagicMock()
        mock_storage.decrypt.return_value = "decrypted_secret"
        key_manager._storage = mock_storage
        assert key_manager._decrypt("enc_text") == "decrypted_secret"

    def test_decrypt_with_secure_storage_error_falls_back(
        self, key_manager: ApiKeyManager
    ) -> None:
        mock_storage = MagicMock()
        mock_storage.decrypt.side_effect = RuntimeError("vault error")
        key_manager._storage = mock_storage
        # base64 encoded "hello" is "aGVsbG8="
        assert key_manager._decrypt("aGVsbG8=") == "hello"

    def test_decrypt_base64_fallback_invalid_returns_original(
        self, key_manager: ApiKeyManager
    ) -> None:
        key_manager._storage = None
        # Invalid base64 with non-ascii or bad padding
        bad_encrypted = "not a valid base64 string!!!"
        assert key_manager._decrypt(bad_encrypted) == bad_encrypted


# ===========================================================================
# Generation & Validation Tests
# ===========================================================================


class TestApiKeyManagerGenerate:
    """Test API key generation."""

    def test_generate_key_defaults(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1")
        assert key.key_id.startswith("mk_")
        assert len(key.key_secret) > 0
        assert key.tenant_id == "tenant_1"
        assert key.tier == "free"
        assert key.rate_limit == 30
        assert key.expires_at is None
        assert key.status == KeyStatus.ACTIVE

    def test_generate_key_custom_tier(self, key_manager: ApiKeyManager) -> None:
        key_pro = key_manager.generate_key(tenant_id="t1", tier="pro")
        assert key_pro.rate_limit == 100

        key_enterprise = key_manager.generate_key(tenant_id="t2", tier="enterprise")
        assert key_enterprise.rate_limit == 500

        key_custom = key_manager.generate_key(tenant_id="t3", tier="other")
        assert key_custom.rate_limit == 60

    def test_generate_key_with_expiry(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1", expires_in_days=7)
        assert key.expires_at is not None
        assert key.days_until_expiry in (6, 7, 8)

    def test_generate_key_with_custom_rate_limit(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1", rate_limit=500)
        assert key.rate_limit == 500

    def test_generate_key_with_metadata(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="t1", metadata={"env": "prod"})
        assert key.metadata == {"env": "prod"}


class TestApiKeyManagerValidate:
    """Test API key validation scenarios."""

    def test_validate_valid_key_without_secret(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1")
        result = key_manager.validate_key(key.key_id)
        assert result.valid is True
        assert result.tenant_id == "tenant_1"
        assert result.tier == "free"
        assert result.rate_limit_remaining == 30

    def test_validate_with_matching_secret(self, key_manager: ApiKeyManager) -> None:
        mock_storage = MagicMock()
        mock_storage.encrypt.side_effect = lambda x: base64.b64encode(x.encode()).decode()
        mock_storage.decrypt.side_effect = lambda x: base64.b64decode(x.encode()).decode()
        key_manager._storage = mock_storage

        raw_secret = "test_raw_secret_xyz"
        with patch.object(key_manager, "_generate_key_pair", return_value=("mk_test_pair", raw_secret)):
            key = key_manager.generate_key(tenant_id="t1")
            result = key_manager.validate_key(key.key_id, key_secret=raw_secret)
            assert result.valid is True
            assert result.tenant_id == "t1"

    def test_validate_with_invalid_secret(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1")
        result = key_manager.validate_key(key.key_id, key_secret="wrong_secret")
        assert result.valid is False
        assert result.error_code == "INVALID_SECRET"

    def test_validate_secret_verification_exception_handling(
        self, key_manager: ApiKeyManager
    ) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1")
        with patch.object(key_manager, "_decrypt", side_effect=Exception("decrypt boom")):
            result = key_manager.validate_key(key.key_id, key_secret="any_secret")
            assert result.valid is False
            assert result.error_code == "VERIFICATION_ERROR"

    def test_validate_not_found(self, key_manager: ApiKeyManager) -> None:
        result = key_manager.validate_key("mk_nonexistent")
        assert result.valid is False
        assert result.error_code == "KEY_NOT_FOUND"

    def test_validate_revoked_key(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1")
        key_manager.revoke_key(key.key_id)
        result = key_manager.validate_key(key.key_id)
        assert result.valid is False
        assert result.error_code == "KEY_REVOKED"

    def test_validate_suspended_key(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1")
        key_manager.suspend_key(key.key_id)
        result = key_manager.validate_key(key.key_id)
        assert result.valid is False
        assert result.error_code == "KEY_SUSPENDED"

    def test_validate_expired_key(self, key_manager: ApiKeyManager) -> None:
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        key = key_manager.generate_key(tenant_id="tenant_1")
        key.expires_at = past
        key_manager._save_key(key)

        result = key_manager.validate_key(key.key_id)
        assert result.valid is False
        assert result.error_code == "KEY_EXPIRED"

        # Verify key was marked as EXPIRED
        updated = key_manager.get_key(key.key_id)
        assert updated.status == KeyStatus.EXPIRED

    def test_validate_rate_limit_exceeded_and_reset(
        self, key_manager: ApiKeyManager
    ) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1", rate_limit=2)

        # 1st request
        res1 = key_manager.validate_key(key.key_id)
        assert res1.valid is True
        assert res1.rate_limit_remaining == 2

        # 2nd request
        res2 = key_manager.validate_key(key.key_id)
        assert res2.valid is True
        assert res2.rate_limit_remaining == 1

        # 3rd request exceeds limit
        res3 = key_manager.validate_key(key.key_id)
        assert res3.valid is False
        assert res3.error_code == "RATE_LIMIT_EXCEEDED"
        assert res3.rate_limit_remaining == 0

        # Fast forward time past rate limit window (60s)
        state = key_manager._rate_limits[key.key_id]
        state.window_start -= 61.0

        res4 = key_manager.validate_key(key.key_id)
        assert res4.valid is True

    def test_validate_without_rate_limit_check(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1", rate_limit=1)
        res1 = key_manager.validate_key(key.key_id, check_rate_limit=False)
        assert res1.valid is True
        assert res1.rate_limit_remaining is None

        res2 = key_manager.validate_key(key.key_id, check_rate_limit=False)
        assert res2.valid is True


# ===========================================================================
# Key Lifecycle: Revoke, Suspend, Reactivate, Delete
# ===========================================================================


class TestApiKeyLifecycle:
    """Test key state transitions and deletion."""

    def test_revoke_existing_and_nonexistent(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1")
        assert key_manager.revoke_key(key.key_id) is True

        loaded = key_manager.get_key(key.key_id)
        assert loaded.status == KeyStatus.REVOKED

        assert key_manager.revoke_key("mk_nonexistent") is False

    def test_suspend_existing_and_nonexistent(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1")
        assert key_manager.suspend_key(key.key_id) is True

        loaded = key_manager.get_key(key.key_id)
        assert loaded.status == KeyStatus.SUSPENDED

        assert key_manager.suspend_key("mk_nonexistent") is False

    def test_reactivate_existing_and_nonexistent(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="tenant_1")
        key_manager.suspend_key(key.key_id)
        assert key_manager.reactivate_key(key.key_id) is True

        loaded = key_manager.get_key(key.key_id)
        assert loaded.status == KeyStatus.ACTIVE

        assert key_manager.reactivate_key("mk_nonexistent") is False

    def test_get_keys_for_tenant(self, key_manager: ApiKeyManager) -> None:
        key_manager.generate_key(tenant_id="t1")
        key_manager.generate_key(tenant_id="t1")
        key_manager.generate_key(tenant_id="t2")

        t1_keys = key_manager.get_keys_for_tenant("t1")
        assert len(t1_keys) == 2
        assert all(k.tenant_id == "t1" for k in t1_keys)

    def test_get_key_redacted_secret(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="t1")
        loaded = key_manager.get_key(key.key_id)
        assert loaded is not None
        assert loaded.key_secret == "***REDACTED***"

    def test_get_key_nonexistent(self, key_manager: ApiKeyManager) -> None:
        assert key_manager.get_key("mk_missing") is None

    def test_delete_key(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="t1")
        assert key_manager.delete_key(key.key_id) is True
        assert key_manager.get_key(key.key_id) is None
        assert key_manager.delete_key("mk_missing") is False


# ===========================================================================
# Storage Persistence & Caching Tests
# ===========================================================================


class TestApiKeyPersistence:
    """Test disk operations, error handling, and cache population."""

    def test_load_key_from_disk_populates_cache(self, key_manager: ApiKeyManager) -> None:
        key = key_manager.generate_key(tenant_id="t1")
        # Clear in-memory cache
        key_manager._cache.clear()
        assert key.key_id not in key_manager._cache

        loaded = key_manager._load_key(key.key_id)
        assert loaded is not None
        assert key.key_id in key_manager._cache

    def test_load_all_keys_missing_file_returns_empty(self, temp_config_dir: Path) -> None:
        manager = ApiKeyManager(config_dir=temp_config_dir / "empty_dir")
        assert manager._load_all_keys() == {}

    def test_load_all_keys_corrupted_file_catches_exception(
        self, key_manager: ApiKeyManager
    ) -> None:
        key_manager.keys_path.write_text("invalid json{{", encoding="utf-8")
        assert key_manager._load_all_keys() == {}

    def test_save_all_keys_io_error_catches_exception(
        self, key_manager: ApiKeyManager
    ) -> None:
        with patch("builtins.open", side_effect=OSError("disk full")):
            # Should not raise exception
            key_manager._save_all_keys({})

    def test_clear_all_keys_success(self, key_manager: ApiKeyManager) -> None:
        key_manager.generate_key(tenant_id="t1")
        assert key_manager.keys_path.exists()
        assert key_manager.clear_all_keys() is True
        assert not key_manager.keys_path.exists()
        assert len(key_manager.get_keys_for_tenant("t1")) == 0

    def test_clear_all_keys_exception_returns_false(
        self, key_manager: ApiKeyManager
    ) -> None:
        key_manager.generate_key(tenant_id="t1")
        with patch.object(Path, "unlink", side_effect=OSError("permission denied")):
            assert key_manager.clear_all_keys() is False


# ===========================================================================
# Global Convenience Functions & Singletons Tests
# ===========================================================================


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_get_api_key_manager_singleton(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.core.api_key_manager as akm
        monkeypatch.setattr(akm, "_api_key_manager", None)
        m1 = get_api_key_manager()
        m2 = get_api_key_manager()
        assert m1 is m2
        assert isinstance(m1, ApiKeyManager)

    def test_generate_api_key(self, temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.core.api_key_manager as akm
        manager = ApiKeyManager(config_dir=temp_config_dir)
        monkeypatch.setattr(akm, "_api_key_manager", manager)

        key = generate_api_key(tenant_id="tenant_1")
        assert key.key_id.startswith("mk_")

    def test_validate_api_key(self, temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.core.api_key_manager as akm
        manager = ApiKeyManager(config_dir=temp_config_dir)
        monkeypatch.setattr(akm, "_api_key_manager", manager)

        key = manager.generate_key(tenant_id="tenant_1")
        result = validate_api_key(key.key_id)
        assert result.valid is True

    def test_revoke_api_key(self, temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.core.api_key_manager as akm
        manager = ApiKeyManager(config_dir=temp_config_dir)
        monkeypatch.setattr(akm, "_api_key_manager", manager)

        key = manager.generate_key(tenant_id="tenant_1")
        assert revoke_api_key(key.key_id) is True


# ===========================================================================
# Gateway Integration Tests
# ===========================================================================


class TestGatewayIntegration:
    """Test integration with gateway_api.py."""

    def test_validate_api_key_for_mission_valid(
        self, temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import src.core.api_key_manager as akm
        from src.core import gateway_api

        manager = ApiKeyManager(config_dir=temp_config_dir)
        key = manager.generate_key(tenant_id="tenant_1")
        monkeypatch.setattr(akm, "_api_key_manager", manager)

        valid, error = gateway_api.validate_api_key_for_mission(key.key_id, "tenant_1")
        assert valid is True
        assert error is None

    def test_validate_api_key_for_mission_missing_key(self) -> None:
        from src.core import gateway_api

        valid, error = gateway_api.validate_api_key_for_mission("", "tenant_1")
        assert valid is False
        assert "Missing API key" in error

    def test_validate_api_key_for_mission_tenant_mismatch(
        self, temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import src.core.api_key_manager as akm
        from src.core import gateway_api

        manager = ApiKeyManager(config_dir=temp_config_dir)
        key = manager.generate_key(tenant_id="tenant_1")
        monkeypatch.setattr(akm, "_api_key_manager", manager)

        valid, error = gateway_api.validate_api_key_for_mission(key.key_id, "tenant_2")
        assert valid is False
        assert "mismatch" in error
