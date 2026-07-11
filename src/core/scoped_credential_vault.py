"""Per-plugin scoped credential vault for BYOK support."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class VaultEntry:
    """A single stored credential."""

    provider: str
    api_key: str
    scope: Optional[str] = None
    stored_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) >= self.expires_at


class ScopedCredentialVault:
    """Resolve and store per-plugin API keys behind MEKONG_CREDENTIAL_VAULT."""

    _VAULT_PREFIX = "mekong.plugin.cred"
    _VAULT_DIR: Optional[str] = None

    def __init__(self, owner: str = "cli") -> None:
        self._owner = owner
        self._cache: dict[tuple[str, str], VaultEntry] = {}

    # ------------------------------------------------------------------
    # Class-level helpers
    # ------------------------------------------------------------------
    @classmethod
    def env_key_name(cls, plugin_id: str, provider: str) -> str:
        """Env var override name for a plugin/provider pair."""
        slug = plugin_id.upper().replace(".", "_").replace("-", "_")
        return f"MEKONG_PLUGIN_{slug}_{provider.upper()}_KEY"

    @classmethod
    def _global_env_key(cls, provider: str) -> str:
        """Conventional global env var name for a provider."""
        return f"{provider.upper()}_API_KEY"

    @classmethod
    def _storage_key(cls, plugin_id: str, provider: str) -> str:
        """File-safe key for persistent storage (dots, no colons)."""
        return f"{cls._VAULT_PREFIX}.{plugin_id}.{provider}"

    # ------------------------------------------------------------------
    # Feature flag
    # ------------------------------------------------------------------
    @staticmethod
    def is_enabled() -> bool:
        """True when MEKONG_CREDENTIAL_VAULT signals vault activation."""
        return os.environ.get("MEKONG_CREDENTIAL_VAULT", "").lower() in (
            "1",
            "true",
            "yes",
        )

    # ------------------------------------------------------------------
    # Local file-based persistence
    # ------------------------------------------------------------------
    @classmethod
    def _vault_dir(cls) -> str:
        if cls._VAULT_DIR is None:
            home = os.path.expanduser("~")
            cls._VAULT_DIR = os.path.join(home, ".mekong", "vault")
        return cls._VAULT_DIR

    @classmethod
    def _vault_file(cls, plugin_id: str, provider: str) -> str:
        return os.path.join(cls._vault_dir(), cls._storage_key(plugin_id, provider))

    def _load_from_storage(self, plugin_id: str, provider: str) -> Optional[VaultEntry]:
        filepath = self._vault_file(plugin_id, provider)
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            expires = data.get("expires_at")
            return VaultEntry(
                provider=data["provider"],
                api_key=data["api_key"],
                scope=data.get("scope"),
                expires_at=datetime.fromisoformat(expires) if expires else None,
            )
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None

    def _save_to_storage(self, plugin_id: str, provider: str, entry: VaultEntry) -> None:
        filepath = self._vault_file(plugin_id, provider)
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            payload = {
                "provider": entry.provider,
                "api_key": entry.api_key,
                "scope": entry.scope,
                "stored_at": entry.stored_at.isoformat(),
                "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
            }
            tmp = filepath + ".tmp"
            with open(tmp, "w") as f:
                json.dump(payload, f)
            os.replace(tmp, filepath)
        except OSError:
            pass  # Non-fatal — memory cache still works

    def _delete_from_storage(self, plugin_id: str, provider: str) -> None:
        filepath = self._vault_file(plugin_id, provider)
        try:
            os.remove(filepath)
        except FileNotFoundError:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def resolve(self, plugin_id: str, provider: str) -> Optional[str]:
        """Resolve API key for plugin/provider pair.

        None if not found.
        """
        # 1. Env var override (highest priority, always bypass vault)
        env_key = self.env_key_name(plugin_id, provider)
        env_val = os.environ.get(env_key)
        if env_val:
            return env_val

        # 2. Instance cache (fast path for same-session store/resolve)
        cache_key = (plugin_id, provider)
        cached = self._cache.get(cache_key)
        if cached and not cached.is_expired:
            return cached.api_key

        # 3. Persistent storage (only when feature flag is on)
        if self.is_enabled():
            entry = self._load_from_storage(plugin_id, provider)
            if entry and not entry.is_expired:
                self._cache[cache_key] = entry
                return entry.api_key

        # 4. No key found — None is correct; global env is handled by provider_adapter
        return None

    def store(
        self,
        plugin_id: str,
        provider: str,
        api_key: str,
        scope: Optional[str] = None,
        ttl_days: Optional[int] = None,
    ) -> None:
        """Store an API key in secure storage."""
        expires_at = None
        if ttl_days is not None:
            from datetime import timedelta

            expires_at = datetime.now(timezone.utc) + timedelta(days=ttl_days)

        entry = VaultEntry(
            provider=provider,
            api_key=api_key,
            scope=scope,
            expires_at=expires_at,
        )
        self._save_to_storage(plugin_id, provider, entry)
        self._cache[(plugin_id, provider)] = entry

    def revoke(self, plugin_id: str, provider: str) -> bool:
        """Remove a stored credential. Returns True if it existed."""
        cache_key = (plugin_id, provider)
        existed = cache_key in self._cache or self._load_from_storage(
            plugin_id, provider
        ) is not None
        self._cache.pop(cache_key, None)
        self._delete_from_storage(plugin_id, provider)
        return existed

    def list_credentials(self, plugin_id: str) -> list[VaultEntry]:
        """List all non-expired stored credentials for a plugin."""
        entries: list[VaultEntry] = []
        vault_dir = self._vault_dir()
        if not os.path.isdir(vault_dir):
            return entries
        prefix = f"{self._VAULT_PREFIX}.{plugin_id}."
        try:
            for filename in os.listdir(vault_dir):
                if not filename.startswith(prefix):
                    continue
                filepath = os.path.join(vault_dir, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                    expires = data.get("expires_at")
                    entry = VaultEntry(
                        provider=data["provider"],
                        api_key=data["api_key"],
                        scope=data.get("scope"),
                        expires_at=datetime.fromisoformat(expires)
                        if expires
                        else None,
                    )
                    if not entry.is_expired:
                        entries.append(entry)
                except Exception:
                    continue
        except OSError:
            pass
        return entries
