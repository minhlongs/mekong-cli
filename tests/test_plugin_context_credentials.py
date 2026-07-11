"""Tests for PluginContext credential methods (Phase 2 + Phase 3 integration).

Phase 2: PluginContext.resolve_provider_key() + has_credential()
Phase 3: Full resolution chain (env_override > vault > global_env > missing)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.plugins.credential_schema import CredentialRequirement, PluginCredentials
from src.plugins.types import PluginContext

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PLUGIN_ID = "com.example.test-plugin"
PROVIDER = "openrouter"


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("MEKONG_") or key.endswith("_API_KEY") or key.endswith("_KEY"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture(autouse=True)
def _isolate_vault(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    from src.core.scoped_credential_vault import ScopedCredentialVault
    ScopedCredentialVault._VAULT_DIR = None


# ---------------------------------------------------------------------------
# T13: resolve_provider_key via lazy import
# ---------------------------------------------------------------------------
class TestResolveProviderKey:
    def test_returns_none_when_no_key_anywhere(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.delenv("MEKONG_CREDENTIAL_VAULT", raising=False)

        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
        )
        key = ctx.resolve_provider_key(PROVIDER)
        assert key is None

    def test_returns_none_when_provider_adapter_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)

        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
        )

        with patch.dict(sys.modules, {"src.core.provider_adapter": None}):
            result = ctx.resolve_provider_key(PROVIDER)
            assert result is None


# ---------------------------------------------------------------------------
# T14: has_credential boolean check
# ---------------------------------------------------------------------------
class TestHasCredential:
    def test_returns_true_when_key_resolvable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        from src.core.scoped_credential_vault import ScopedCredentialVault

        env_key = ScopedCredentialVault.env_key_name(PLUGIN_ID, PROVIDER)
        monkeypatch.setenv(env_key, "override-key")

        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
        )

        assert ctx.has_credential(PROVIDER) is True

    def test_returns_false_when_no_key_available(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.delenv("MEKONG_CREDENTIAL_VAULT", raising=False)

        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
        )

        assert ctx.has_credential(PROVIDER) is False

    def test_returns_false_when_provider_adapter_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)

        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
        )

        with patch.dict(
            sys.modules,
            {"src.core.provider_adapter": None},
        ):
            assert ctx.has_credential(PROVIDER) is False


# ---------------------------------------------------------------------------
# T15: isolation field
# ---------------------------------------------------------------------------
class TestIsolationField:
    def test_default_isolation_none(self) -> None:
        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
        )
        assert ctx.isolation == "none"

    def test_can_set_restricted(self) -> None:
        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
            isolation="restricted",
        )
        assert ctx.isolation == "restricted"

    def test_can_set_sandboxed(self) -> None:
        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
            isolation="sandboxed",
        )
        assert ctx.isolation == "sandboxed"


# ---------------------------------------------------------------------------
# T16-T19: Full Phase 3 resolution chain via PluginContext
# ---------------------------------------------------------------------------
class TestResolutionChain:
    def test_env_override_wins(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        from src.core.scoped_credential_vault import ScopedCredentialVault

        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        env_key = ScopedCredentialVault.env_key_name(PLUGIN_ID, PROVIDER)
        monkeypatch.setenv(env_key, "override-key")

        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
        )

        key = ctx.resolve_provider_key(PROVIDER)
        assert key == "override-key"

    def test_vault_key_wins_over_global_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        from src.core.scoped_credential_vault import ScopedCredentialVault

        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        monkeypatch.setenv(f"{PROVIDER.upper()}_API_KEY", "global-env-key")
        vault = ScopedCredentialVault()
        vault.store(PLUGIN_ID, PROVIDER, "vault-key")

        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
        )

        key = ctx.resolve_provider_key(PROVIDER)
        assert key == "vault-key"

    def test_global_env_fallback_when_no_vault_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.setenv("MEKONG_CREDENTIAL_VAULT", "1")
        monkeypatch.setenv(f"{PROVIDER.upper()}_API_KEY", "global-env-key")

        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
        )

        key = ctx.resolve_provider_key(PROVIDER)
        assert key == "global-env-key"

    def test_returns_none_when_no_key_anywhere(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_env(monkeypatch)
        monkeypatch.delenv("MEKONG_CREDENTIAL_VAULT", raising=False)

        ctx = PluginContext(
            registry=MagicMock(),
            commands=MagicMock(),
            config={"plugin_id": PLUGIN_ID},
        )

        key = ctx.resolve_provider_key(PROVIDER)
        assert key is None


# ---------------------------------------------------------------------------
# T20-T22: Manifest credentials integration (Phase 1 + Phase 2)
# ---------------------------------------------------------------------------
class TestManifestCredentialsIntegration:
    def test_manifest_with_credentials_field(self) -> None:
        creds = PluginCredentials(
            requirements=[
                CredentialRequirement(
                    provider="openrouter",
                    required=True,
                    scope="read",
                    description="OpenRouter API key",
                )
            ]
        )
        assert creds is not None
        assert "openrouter" in creds.provider_names()
        assert "openrouter" in creds.required_providers()

    def test_credential_requirement_dataclass(self) -> None:
        req = CredentialRequirement(
            provider="anthropic",
            env_fallback="ANTHROPIC_API_KEY",
            required=True,
            scope="full",
            description="Anthropic API key for Claude",
        )
        assert req.provider == "anthropic"
        assert req.env_fallback == "ANTHROPIC_API_KEY"
        assert req.required is True
        assert req.scope == "full"
