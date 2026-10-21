# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Particle Repository Legacy Tenant Operations Mixin."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Optional

from src.models.particle_balance_models import Tenant, _hash_key, _row_to_tenant
from src.models.particle_models import (
    CURRENCY_USD,
    PARTICLE_TYPE_CREDIT,
    SOURCE_ADMIN,
    SOURCE_MIGRATION,
    EconomicParticle,
)


class ParticleTenantRepoMixin:
    """Mixin for legacy RaaS tenant operations in ParticleRepository."""

    async def _get_db(self) -> Any:
        raise NotImplementedError

    async def create_particle(self, particle: EconomicParticle) -> str:
        raise NotImplementedError

    async def create_tenant(self, name: str, legacy_mode: bool = False) -> Tenant:
        """Create a new tenant and return it with the plaintext API key."""
        db = await self._get_db()
        tenant_id = str(uuid.uuid4())
        raw_key = f"mk_{uuid.uuid4().hex}"
        key_hash = _hash_key(raw_key)
        created_at = datetime.now(timezone.utc)
        query = """
            INSERT INTO tenants (id, name, api_key_hash, created_at, is_active)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, api_key_hash, created_at, is_active
        """
        row = await db.fetch_one(query, (tenant_id, name, key_hash, created_at, True))
        tenant = _row_to_tenant(row, api_key=raw_key)
        if not legacy_mode:
            await self.create_particle(
                EconomicParticle(
                    tenant_id=tenant_id,
                    key_id=f"tenant_{tenant_id}",
                    particle_type=PARTICLE_TYPE_CREDIT,
                    amount=Decimal("0.0"),
                    currency=CURRENCY_USD,
                    source=SOURCE_ADMIN,
                    metadata={"action": "tenant_creation", "tenant_name": name},
                )
            )
        return tenant

    async def get_tenant_by_api_key(self, key: str) -> Optional[Tenant]:
        """Return the Tenant whose hashed key matches *key*."""
        db = await self._get_db()
        row = await db.fetch_one("SELECT * FROM tenants WHERE api_key_hash = $1", (_hash_key(key),))
        return _row_to_tenant(row, api_key=key) if row else None

    async def find_tenant_by_name(self, name: str) -> Optional[Tenant]:
        """Find tenant by name (used as email lookup)."""
        db = await self._get_db()
        row = await db.fetch_one("SELECT * FROM tenants WHERE name = $1", (name,))
        return _row_to_tenant(row) if row else None

    async def list_tenants(self, include_inactive: bool = False) -> List[Tenant]:
        """Return all tenants ordered by creation date."""
        db = await self._get_db()
        query = (
            "SELECT * FROM tenants ORDER BY created_at ASC"
            if include_inactive
            else "SELECT * FROM tenants WHERE is_active = TRUE ORDER BY created_at ASC"
        )
        rows = await db.fetch_all(query)
        return [_row_to_tenant(row) for row in rows]

    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """Soft-delete a tenant by marking it inactive."""
        db = await self._get_db()
        result = await db.execute("UPDATE tenants SET is_active = FALSE WHERE id = $1", (tenant_id,))
        return result != "UPDATE 0"

    async def tenant_exists(self, tenant_id: str) -> bool:
        """Check if a tenant exists."""
        db = await self._get_db()
        row = await db.fetch_one("SELECT 1 FROM tenants WHERE id = $1 LIMIT 1", (tenant_id,))
        return row is not None

    async def migrate_tenant_to_particles(
        self,
        tenant_id: str,
        initial_balance: Decimal = Decimal("0.0"),
        currency: str = CURRENCY_USD,
    ) -> bool:
        """Migrate a legacy tenant to the particle system."""
        db = await self._get_db()
        row = await db.fetch_one("SELECT COUNT(*) as cnt FROM economic_particles WHERE tenant_id = $1", (tenant_id,))
        if row and row.get("cnt", 0) > 0:
            return False
        tenant_row = await db.fetch_one("SELECT * FROM tenants WHERE id = $1", (tenant_id,))
        if not tenant_row:
            return False
        await self.create_particle(
            EconomicParticle(
                tenant_id=tenant_id,
                key_id=f"tenant_{tenant_id}",
                particle_type=PARTICLE_TYPE_CREDIT,
                amount=initial_balance,
                currency=currency,
                balance_after=initial_balance,
                source=SOURCE_MIGRATION,
                metadata={"migration": "tenant_to_particles", "tenant_name": tenant_row["name"]},
            )
        )
        return True
