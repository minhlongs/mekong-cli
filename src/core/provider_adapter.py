# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Provider credential adapter — resolves API keys for plugin/provider pairs."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.core.scoped_credential_vault import ScopedCredentialVault


class CredentialSourceType(str, Enum):
    """Origin of a resolved credential."""

    VAULT = "vault"
    ENV_OVERRIDE = "env_override"
    ENV_GLOBAL = "env_global"
    MISSING = "missing"


@dataclass(frozen=True)
class CredentialSource:
    """Records where a credential was resolved from."""

    source: CredentialSourceType
    provider: str
    plugin_id: str


def resolve_provider_key(
    plugin_id: str, provider: str
) -> tuple[Optional[str], CredentialSource]:
    """Resolve an API key for *plugin_id* using *provider*.

    Resolution order (vault-first when feature flag enabled):

    1. Env var override — ``MEKONG_PLUGIN_{ID}_{PROV}_KEY``
    2. Vault — stored key for this plugin + provider pair
    3. Global env — ``{PROV}_API_KEY``
    4. Missing — none of the above yielded a key

    Returns:
        A ``(key, source)`` tuple. ``key`` is ``None`` when unresolved.
    """
    # 1. Env var override (always checked, highest priority)
    env_key = ScopedCredentialVault.env_key_name(plugin_id, provider)
    env_val = os.environ.get(env_key)
    if env_val:
        return env_val, CredentialSource(
            source=CredentialSourceType.ENV_OVERRIDE,
            provider=provider,
            plugin_id=plugin_id,
        )

    # 2. Vault (only when feature flag is on)
    if ScopedCredentialVault.is_enabled():
        vault = ScopedCredentialVault()
        key = vault.resolve(plugin_id, provider)
        if key is not None:
            # vault.resolve() checks env override, then cache, then storage.
            # If we reach here, env override was already ruled out above,
            # so the key came from vault storage or (if flag off) global env.
            # Because is_enabled() is true here, it came from vault.
            return key, CredentialSource(
                source=CredentialSourceType.VAULT,
                provider=provider,
                plugin_id=plugin_id,
            )

    # 3. Global env fallback (always checked)
    global_key = ScopedCredentialVault._global_env_key(provider)
    global_val = os.environ.get(global_key)
    if global_val:
        return global_val, CredentialSource(
            source=CredentialSourceType.ENV_GLOBAL,
            provider=provider,
            plugin_id=plugin_id,
        )

    # 4. Missing
    return None, CredentialSource(
        source=CredentialSourceType.MISSING,
        provider=provider,
        plugin_id=plugin_id,
    )
