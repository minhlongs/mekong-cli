"""Tests for ScopedCredentialVault and provider_adapter.

TDD: These tests MUST fail before Phase 1 implementation begins.
After implementation, all tests must pass with ruff 0 errors.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.core.scoped_credential_vault import (
    ScopedCredentialVault,
    VaultEntry,
)
from src.core.provider_adapter import (
    CredentialSource,
    resolve_provider_key,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PLUGIN_ID = "com.example.test-plugin"
PROVIDER = "openrouter"


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove all credential-related env vars that tests may set."""
    for key in list(os.environ):
        if (
            key.startswith("MEKONG_")
            or key.endswith("_API_KEY")
            or key.endswith("_KEY")
        ):
            monkeypatch.delenv(key, raising=False)


# ---------------------------------------------------------------------------
# Autouse fixture: isolate vault storage to tmp_path per test module
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _isolate_vault_storage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Redirect vault dir to a temp dir so tests don't share disk state."""
    monkeypatch.setenv("HOME", str(tmp_path))
    # Reset class-level cached dir so _vault_dir() picks up new HOME
    ScopedCredentialVault._VAULT_DIR = None


# ===========================================================================
# T01: Feature flag OFF → vault not instantiated, global env used
# ===========================================================================
class TestFeatureFlag:
    def test_vault_disabled_returns_global_env(self) -> None:
        _clear_env(pytest.MonkeyPatch())  # type: ignore[call-arg]
        os.environ["OPENROUTER_API_KEY"] = "env-global-key"
        os.environ.pop("MEKONG_CREDENTIAL_VAULT", None)

        key, source = resolve_provider_key(PLUGIN_ID, PROVIDER)

        assert key == "env-global-key"
        assert source.source == "env_global"

    def test_feature_flag_truthy_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_env(monkeypatch)
        for truthy in ("1", "true", "yes"):
            monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", truthy)
            key, source = resolve_provider_key(PLUGIN_ID, PROVIDER)
            assert source.source in ("vault", "env_override", "env_global", "missing")

    def test_feature_flag_falsy_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("OPENROUTER_API_KEY", "env-global-key")
        for falsy in ("0", "false", ""):
            monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", falsy)
            key, source = resolve_provider_key(PLUGIN_ID, PROVIDER)
            assert source.source == "env_global"


# ===========================================================================
# T02: No key anywhere → returns None, source="missing"
# ===========================================================================
class TestMissingCredential:
    def test_vault_enabled_returns_none_when_no_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")

        key, source = resolve_provider_key(PLUGIN_ID, PROVIDER)

        assert key is None
        assert source.source == "missing"
        assert source.provider == PROVIDER
        assert source.plugin_id == PLUGIN_ID


# ===========================================================================
# T03: Env var override wins over vault
# ===========================================================================
class TestEnvOverride:
    def test_env_override_wins_over_vault(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        env_key = ScopedCredentialVault.env_key_name(PLUGIN_ID, PROVIDER)
        monkeypatch.setenv(env_key, "env-override-key")
        vault = ScopedCredentialVault()
        vault.store(PLUGIN_ID, PROVIDER, "vault-key")

        key, source = resolve_provider_key(PLUGIN_ID, PROVIDER)

        assert key == "env-override-key"
        assert source.source == "env_override"


# ===========================================================================
# T04: Vault key wins over global env
# ===========================================================================
class TestVaultPriority:
    def test_vault_wins_over_global_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        monkeypatch.setenv("OPENROUTER_API_KEY", "global-env-key")
        vault = ScopedCredentialVault()
        vault.store(PLUGIN_ID, PROVIDER, "vault-key")

        key, source = resolve_provider_key(PLUGIN_ID, PROVIDER)

        assert key == "vault-key"
        assert source.source == "vault"

    def test_global_env_fallback_when_no_vault(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        monkeypatch.setenv("OPENROUTER_API_KEY", "global-env-key")

        key, source = resolve_provider_key(PLUGIN_ID, PROVIDER)

        assert key == "global-env-key"
        assert source.source == "env_global"


# ===========================================================================
# T06-T07: Store / revoke round-trip
# ===========================================================================
class TestStoreRevoke:
    def test_store_then_resolve(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        vault = ScopedCredentialVault()
        vault.store(PLUGIN_ID, PROVIDER, "stored-key", scope="read-only")

        resolved = vault.resolve(PLUGIN_ID, PROVIDER)

        assert resolved == "stored-key"

    def test_revoke_removes_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        vault = ScopedCredentialVault()
        vault.store(PLUGIN_ID, PROVIDER, "to-revoke")

        result = vault.revoke(PLUGIN_ID, PROVIDER)

        assert result is True
        assert vault.resolve(PLUGIN_ID, PROVIDER) is None

    def test_revoke_nonexistent_returns_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        vault = ScopedCredentialVault()

        result = vault.revoke(PLUGIN_ID, PROVIDER)

        assert result is False


# ===========================================================================
# T08: CredentialSource tracking
# ===========================================================================
class TestCredentialSource:
    def test_credential_source_tracking(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        env_key = ScopedCredentialVault.env_key_name(PLUGIN_ID, PROVIDER)
        monkeypatch.setenv(env_key, "override-key")

        key, source = resolve_provider_key(PLUGIN_ID, PROVIDER)

        assert isinstance(source, CredentialSource)
        assert source.source == "env_override"
        assert source.provider == PROVIDER
        assert source.plugin_id == PLUGIN_ID

    def test_credential_source_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)

        key, source = resolve_provider_key(PLUGIN_ID, PROVIDER)

        assert source.source == "missing"


# ===========================================================================
# T09: Env key name formatting
# ===========================================================================
class TestEnvKeyNaming:
    def test_env_key_name_format(self) -> None:
        expected = "MEKONG_PLUGIN_COM_EXAMPLE_TEST_PLUGIN_OPENROUTER_KEY"
        result = ScopedCredentialVault.env_key_name(PLUGIN_ID, PROVIDER)
        assert result == expected

    def test_env_key_name_dots_to_underscores(self) -> None:
        result = ScopedCredentialVault.env_key_name("com.example.my-plugin", "anthropic")
        assert "." not in result
        assert "COM_EXAMPLE_MY_PLUGIN" in result


# ===========================================================================
# T11: Expired entries are skipped
# ===========================================================================
class TestExpiration:
    def test_expired_entry_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        monkeypatch.setenv("OPENROUTER_API_KEY", "global-key")
        vault = ScopedCredentialVault()
        vault.store(PLUGIN_ID, PROVIDER, "expired-key", ttl_days=-1)

        key, source = resolve_provider_key(PLUGIN_ID, PROVIDER)

        assert key == "global-key"
        assert source.source == "env_global"


# ===========================================================================
# T12: File-based storage works (self-contained vault)
# ===========================================================================
class TestFileBasedStorage:
    def test_store_creates_file_on_disk(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        vault = ScopedCredentialVault()
        vault.store(PLUGIN_ID, PROVIDER, "disk-key")

        # New instance should read from disk
        vault2 = ScopedCredentialVault()
        resolved = vault2.resolve(PLUGIN_ID, PROVIDER)

        assert resolved == "disk-key"

    def test_revoke_deletes_file_on_disk(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        vault = ScopedCredentialVault()
        vault.store(PLUGIN_ID, PROVIDER, "to-delete")

        vault.revoke(PLUGIN_ID, PROVIDER)

        # File should be gone
        filepath = vault._vault_file(PLUGIN_ID, PROVIDER)
        assert not Path(filepath).exists()

    def test_list_credentials_returns_stored(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        vault = ScopedCredentialVault()
        vault.store(PLUGIN_ID, PROVIDER, "key-1", scope="read")
        vault.store(
            PLUGIN_ID,
            "anthropic",
            "key-2",
            scope="write",
        )

        entries = vault.list_credentials(PLUGIN_ID)

        assert len(entries) == 2
        providers = {e.provider for e in entries}
        assert PROVIDER in providers
        assert "anthropic" in providers
