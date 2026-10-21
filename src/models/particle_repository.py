# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Particle Repository Database Operations."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional, Tuple

from src.models.particle_balance_models import ParticleAggregation
from src.models.particle_models import EconomicParticle
from src.models.particle_tenant_repo import ParticleTenantRepoMixin

try:
    from src.db.database import DatabaseConnection, get_database
    DB_AVAILABLE = True
except ImportError:
    DatabaseConnection = Any  # type: ignore[misc,assignment]
    get_database = None  # type: ignore[assignment]
    DB_AVAILABLE = False


class ParticleRepository(ParticleTenantRepoMixin):
    """Repository for economic_particles table operations."""

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        self._db = db
        self._using_global = db is None

    async def _get_db(self) -> DatabaseConnection:
        """Get database connection, initializing if needed."""
        if self._using_global:
            if not DB_AVAILABLE or get_database is None:
                raise ImportError("Database module not available. Install asyncpg.")
            return get_database()
        return self._db  # type: ignore[return-value]

    async def create_particle(self, particle: EconomicParticle) -> str:
        """Insert a new economic particle."""
        db = await self._get_db()
        if not particle.id:
            particle.id = str(uuid.uuid4())
        query, params = particle.to_insert_sql()
        try:
            result = await db.fetchval(query, *params)
            return str(result) if result else particle.id
        except Exception as exc:
            raise RuntimeError(f"Failed to create economic particle: {exc}") from exc

    async def get_particle(self, particle_id: str) -> Optional[EconomicParticle]:
        """Retrieve a single particle by ID."""
        db = await self._get_db()
        row = await db.fetch_one("SELECT * FROM economic_particles WHERE id = $1", (particle_id,))
        return EconomicParticle.from_dict(row) if row else None

    async def list_particles_by_key(
        self,
        key_id: str,
        particle_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[EconomicParticle]:
        """List particles for a key_id with optional filtering."""
        db = await self._get_db()
        conditions = ["key_id = $1"]
        params: List[Any] = [key_id]
        if particle_type:
            conditions.append(f"particle_type = ${len(params) + 1}")
            params.append(particle_type)
        if start_date:
            conditions.append(f"created_at >= ${len(params) + 1}")
            params.append(start_date)
        if end_date:
            conditions.append(f"created_at <= ${len(params) + 1}")
            params.append(end_date)
        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT * FROM economic_particles
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """
        params.extend([limit, offset])
        rows = await db.fetch_all(query, params)
        return [EconomicParticle.from_dict(row) for row in rows]

    async def get_balance(self, key_id: str, as_of: Optional[datetime] = None) -> Decimal:
        """Calculate current balance for a key_id."""
        db = await self._get_db()
        if as_of:
            row = await db.fetch_one(
                "SELECT SUM(amount) as total FROM economic_particles WHERE key_id = $1 AND created_at <= $2",
                (key_id, as_of),
            )
        else:
            row = await db.fetch_one(
                "SELECT SUM(amount) as total FROM economic_particles WHERE key_id = $1",
                (key_id,),
            )
        total = row.get("total") if row else None
        return Decimal(str(total)) if total is not None else Decimal("0.0")

    async def get_balance_with_snapshot(
        self, key_id: str
    ) -> Tuple[Decimal, Optional[EconomicParticle]]:
        """Get balance and the last particle that affected it."""
        db = await self._get_db()
        last_row = await db.fetch_one(
            "SELECT * FROM economic_particles WHERE key_id = $1 ORDER BY created_at DESC, id DESC LIMIT 1",
            (key_id,),
        )
        if last_row:
            balance = Decimal(str(last_row.get("balance_after", "0.0")))
            return balance, EconomicParticle.from_dict(last_row)
        return Decimal("0.0"), None

    async def aggregate_by_type(
        self,
        key_id: str,
        particle_types: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ParticleAggregation]:
        """Aggregate particles by type for a key_id."""
        db = await self._get_db()
        conditions = ["key_id = $1"]
        params: List[Any] = [key_id]
        if particle_types:
            conditions.append(f"particle_type = ANY(${len(params) + 1})")
            params.append(particle_types)
        if start_date:
            conditions.append(f"created_at >= ${len(params) + 1}")
            params.append(start_date)
        if end_date:
            conditions.append(f"created_at <= ${len(params) + 1}")
            params.append(end_date)
        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT key_id, particle_type, SUM(amount) as total_amount,
                   COUNT(*) as particle_count, currency
            FROM economic_particles
            WHERE {where_clause}
            GROUP BY key_id, particle_type, currency
            ORDER BY particle_type
        """
        rows = await db.fetch_all(query, params)
        return [ParticleAggregation.from_dict(row) for row in rows]

    async def count_particles(
        self,
        key_id: Optional[str] = None,
        particle_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count particles matching criteria."""
        db = await self._get_db()
        conditions = []
        params: List[Any] = []
        if key_id:
            conditions.append(f"key_id = ${len(params) + 1}")
            params.append(key_id)
        if particle_type:
            conditions.append(f"particle_type = ${len(params) + 1}")
            params.append(particle_type)
        if start_date:
            conditions.append(f"created_at >= ${len(params) + 1}")
            params.append(start_date)
        if end_date:
            conditions.append(f"created_at <= ${len(params) + 1}")
            params.append(end_date)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        row = await db.fetch_one(f"SELECT COUNT(*) FROM economic_particles {where_clause}", params)
        return row.get("count", 0) if row else 0
