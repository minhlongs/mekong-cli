"""
RaaS Tenant Management — Legacy Compatibility Layer

.. deprecated::
    This module is deprecated. Use :mod:`src.models.particle` for new implementations.
    This module exists for backward compatibility with existing RaaS integrations
    and Vietnam-specific tenant management.

This module provides a thin wrapper around :mod:`src.models.particle` to maintain
the original TenantStore API while using PostgreSQL economic_particles under the hood.
"""

from __future__ import annotations

import warnings
from typing import List, Optional

# Re-export Tenant from particle module for backward compatibility
from src.models.particle import (
    Tenant,
    ParticleRepository,
    _hash_key,
    _row_to_tenant,
)

# SQLite fallback path (kept for local dev without PostgreSQL)
_DB_PATH = None  # Will use PostgreSQL via ParticleRepository


class TenantStore:
    """Legacy tenant store using PostgreSQL economic_particles.

    This class maintains the original API from raas/tenant.py but delegates
    to ParticleRepository for data persistence.

    The database is PostgreSQL with economic_particles table. For backward
    compatibility, a ``tenants`` table is still required (see migration 012).
    """

    def __init__(self, db_path=None) -> None:
        """Initialize the tenant store.

        Args:
            db_path: Kept for signature compatibility, ignored (uses PostgreSQL).
        """
        warnings.warn(
            "TenantStore is deprecated. Use ParticleRepository instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._repo = ParticleRepository()

    # ------------------------------------------------------------------
    # Public API (maintains original TenantStore interface)
    # ------------------------------------------------------------------

    async def create_tenant(self, name: str) -> Tenant:
        """Create a new tenant and return it with the plaintext API key.

        The plaintext key is **only** returned here; subsequent look-ups
        return an empty string for ``api_key``.

        Args:
            name: Human-readable label for the tenant.

        Returns:
            Tenant with ``api_key`` set to the new ``mk_``-prefixed key.

        Raises:
            RuntimeError: If the DB write fails.
        """
        return await self._repo.create_tenant(name, legacy_mode=True)

    async def get_by_api_key(self, key: str) -> Optional[Tenant]:
        """Return the Tenant whose hashed key matches *key*.

        Args:
            key: Plaintext ``mk_``-prefixed API key supplied by the caller.

        Returns:
            Matching Tenant or ``None`` if not found.
        """
        return await self._repo.get_tenant_by_api_key(key)

    async def find_by_email(self, email: str) -> Optional[Tenant]:
        """Find tenant by name (used as email lookup).

        Args:
            email: Tenant name/email to search for

        Returns:
            Tenant or None if not found
        """
        return await self._repo.find_tenant_by_name(email)

    async def list_tenants(self) -> List[Tenant]:
        """Return all active tenants ordered by creation date.

        Returns:
            List of Tenant objects (``api_key`` is empty string).
        """
        return await self._repo.list_tenants(include_inactive=False)

    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """Soft-delete a tenant by marking it inactive.

        Args:
            tenant_id: UUID4 string of the tenant to deactivate.

        Returns:
            ``True`` if a row was updated, ``False`` if *tenant_id* was not found.
        """
        return await self._repo.deactivate_tenant(tenant_id)

    async def tenant_exists(self, tenant_id: str) -> bool:
        """Check if a tenant exists.

        Args:
            tenant_id: Tenant UUID string

        Returns:
            True if tenant exists
        """
        return await self._repo.tenant_exists(tenant_id)

    # ------------------------------------------------------------------
    # Migration helpers (Vietnam compatibility)
    # ------------------------------------------------------------------

    async def migrate_to_particles(self, tenant_id: str, initial_balance: float = 0.0) -> bool:
        """Migrate a legacy tenant to use particle-based balance tracking.

        This method is used during the Vietnam RaaS integration to ensure
        existing tenants have their economic events tracked via particles.

        Args:
            tenant_id: Tenant to migrate
            initial_balance: Starting balance for particle tracking

        Returns:
            True if migration was performed, False if already migrated
        """
        from decimal import Decimal
        return await self._repo.migrate_tenant_to_particles(
            tenant_id, Decimal(str(initial_balance))
        )


# Synchronous wrapper for backward compatibility with old code that doesn't use async
class SyncTenantStore:
    """Synchronous wrapper around async TenantStore for legacy code.

    .. warning::
        This uses an event loop internally and should only be used in
        scripts or contexts where async is not available.
    """

    def __init__(self) -> None:
        import asyncio
        self._loop = asyncio.new_event_loop()
        self._store = TenantStore()

    def __del__(self) -> None:
        self._loop.close()

    def _run(self, coro):
        return self._loop.run_until_complete(coro)

    def create_tenant(self, name: str) -> Tenant:
        return self._run(self._store.create_tenant(name))

    def get_by_api_key(self, key: str) -> Optional[Tenant]:
        return self._run(self._store.get_by_api_key(key))

    def find_by_email(self, email: str) -> Optional[Tenant]:
        return self._run(self._store.find_by_email(email))

    def list_tenants(self) -> List[Tenant]:
        return self._run(self._store.list_tenants())

    def deactivate_tenant(self, tenant_id: str) -> bool:
        return self._run(self._store.deactivate_tenant(tenant_id))


__all__ = [
    "Tenant",
    "TenantStore",
    "SyncTenantStore",
]
