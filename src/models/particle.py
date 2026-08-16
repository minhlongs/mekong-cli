# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Economic Particle ORM Model

Atomic economic units representing financial events:
- Usage consumption (negative amounts)
- Credit additions (positive amounts)
- Manual adjustments
- Payment records
- Refunds

Legacy Vietnam compatibility: Includes tenant_id field for RaaS integration.
"""

from __future__ import annotations

import uuid
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

# Import database connection (lazy to avoid circular imports)
try:
    from src.db.database import DatabaseConnection, get_database
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Particle type constants
PARTICLE_TYPE_USAGE = "usage"
PARTICLE_TYPE_CREDIT = "credit"
PARTICLE_TYPE_ADJUSTMENT = "adjustment"
PARTICLE_TYPE_ADJUSTMENT_POSITIVE = "adjustment_positive"
PARTICLE_TYPE_ADJUSTMENT_NEGATIVE = "adjustment_negative"
PARTICLE_TYPE_PAYMENT = "payment"
PARTICLE_TYPE_REFUND = "refund"
PARTICLE_TYPE_FEE = "fee"
PARTICLE_TYPE_SUBSCRIPTION = "subscription"

# Source constants
SOURCE_API = "api"
SOURCE_MANUAL = "manual"
SOURCE_WEBHOOK = "webhook"
SOURCE_CRON = "cron"
SOURCE_ADMIN = "admin"
SOURCE_MIGRATION = "migration"
SOURCE_RECONCILIATION = "reconciliation"

# Currency constants
CURRENCY_USD = "USD"
CURRENCY_VND = "VND"
CURRENCY_EUR = "EUR"

# Valid particle types and sources for validation
VALID_PARTICLE_TYPES = {
    PARTICLE_TYPE_USAGE,
    PARTICLE_TYPE_CREDIT,
    PARTICLE_TYPE_ADJUSTMENT,
    PARTICLE_TYPE_ADJUSTMENT_POSITIVE,
    PARTICLE_TYPE_ADJUSTMENT_NEGATIVE,
    PARTICLE_TYPE_PAYMENT,
    PARTICLE_TYPE_REFUND,
    PARTICLE_TYPE_FEE,
    PARTICLE_TYPE_SUBSCRIPTION,
}

VALID_SOURCES = {
    SOURCE_API,
    SOURCE_MANUAL,
    SOURCE_WEBHOOK,
    SOURCE_CRON,
    SOURCE_ADMIN,
    SOURCE_MIGRATION,
    SOURCE_RECONCILIATION,
}

VALID_CURRENCIES = {CURRENCY_USD, CURRENCY_VND, CURRENCY_EUR}


@dataclass
class EconomicParticle:
    """Immutable snapshot of an economic particle (atomic financial event).

    Particles are append-only for audit trail integrity. Each particle represents
    a single economic event that affects a key_id's balance.

    Attributes:
        id: UUIDv7 or UUIDv4 identifier (auto-generated if not provided)
        tenant_id: Legacy RaaS tenant reference (nullable, for Vietnam compatibility)
        key_id: License key identifier (preferred modern identifier)
        particle_type: Classification of economic event
        amount: Signed decimal value (positive = credit, negative = debit)
        currency: ISO currency code (USD, VND, EUR)
        balance_after: Balance snapshot after this particle (denormalized for performance)
        metadata: Flexible JSONB payload (rate card, usage details, etc.)
        source: Origin of the particle (api, manual, webhook, etc.)
        reference_id: External reference (payment tx, invoice, Stripe PI)
        created_at: UTC timestamp of particle creation
        updated_at: Auto-updated timestamp (for row modification tracking)
        tenant_reference_id: Alternative tenant linkage (for multi-tenancy)
    """

    id: Optional[str] = None
    tenant_id: Optional[str] = None
    key_id: str = ""
    particle_type: str = PARTICLE_TYPE_USAGE
    amount: Decimal = field(default_factory=lambda: Decimal("0.0"))
    currency: str = CURRENCY_USD
    balance_after: Optional[Decimal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = SOURCE_API
    reference_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_reference_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate particle data after initialization."""
        # Generate ID if not set
        if self.id is None:
            self.id = str(uuid.uuid4())

        # Validate particle_type
        if self.particle_type not in VALID_PARTICLE_TYPES:
            raise ValueError(
                f"Invalid particle_type: {self.particle_type}. "
                f"Valid types: {', '.join(VALID_PARTICLE_TYPES)}"
            )

        # Validate source
        if self.source not in VALID_SOURCES:
            raise ValueError(
                f"Invalid source: {self.source}. "
                f"Valid sources: {', '.join(VALID_SOURCES)}"
            )

        # Validate currency
        if self.currency not in VALID_CURRENCIES:
            raise ValueError(
                f"Invalid currency: {self.currency}. "
                f"Valid currencies: {', '.join(VALID_CURRENCIES)}"
            )

        # Ensure amount is Decimal
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))

        # Ensure balance_after is Decimal if set
        if self.balance_after is not None and not isinstance(self.balance_after, Decimal):
            self.balance_after = Decimal(str(self.balance_after))

        # Ensure timezone-aware datetimes
        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)
        if self.updated_at.tzinfo is None:
            self.updated_at = self.updated_at.replace(tzinfo=timezone.utc)

    @classmethod
    def from_dict(cls, data: dict) -> "EconomicParticle":
        """Create EconomicParticle from database row dict.

        Args:
            data: Dictionary with column names as keys (from PostgreSQL row)

        Returns:
            EconomicParticle instance
        """
        # Handle Decimal conversion
        amount = data.get("amount", Decimal("0.0"))
        balance_after = data.get("balance_after")

        # Parse timestamps
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        elif updated_at is None:
            updated_at = datetime.now(timezone.utc)

        return cls(
            id=str(data.get("id", uuid.uuid4())),
            tenant_id=data.get("tenant_id"),
            key_id=data.get("key_id", ""),
            particle_type=data.get("particle_type", PARTICLE_TYPE_USAGE),
            amount=Decimal(amount) if amount is not None else Decimal("0.0"),
            currency=data.get("currency", CURRENCY_USD),
            balance_after=Decimal(balance_after) if balance_after is not None else None,
            metadata=data.get("metadata", {}),
            source=data.get("source", SOURCE_API),
            reference_id=data.get("reference_id"),
            created_at=created_at,
            updated_at=updated_at,
            tenant_reference_id=data.get("tenant_reference_id"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert EconomicParticle to dict for database insertion/update.

        Returns:
            Dictionary with keys matching PostgreSQL column names
        """
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "key_id": self.key_id,
            "particle_type": self.particle_type,
            "amount": str(self.amount),
            "currency": self.currency,
            "balance_after": str(self.balance_after) if self.balance_after is not None else None,
            "metadata": self.metadata,
            "source": self.source,
            "reference_id": self.reference_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tenant_reference_id": self.tenant_reference_id,
        }

    def to_insert_sql(self) -> tuple[str, List[Any]]:
        """Generate SQL insert statement and parameters.

        Returns:
            Tuple of (SQL query string, parameter list)
        """
        query = """
            INSERT INTO economic_particles (
                id, tenant_id, key_id, particle_type, amount, currency,
                balance_after, metadata, source, reference_id, created_at, updated_at,
                tenant_reference_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
        """
        params = [
            self.id,
            self.tenant_id,
            self.key_id,
            self.particle_type,
            self.amount,
            self.currency,
            self.balance_after,
            self.metadata,
            self.source,
            self.reference_id,
            self.created_at,
            self.updated_at,
            self.tenant_reference_id,
        ]
        return query, params

    def is_credit(self) -> bool:
        """Check if this particle represents a credit (balance increase)."""
        return self.amount > Decimal("0")

    def is_debit(self) -> bool:
        """Check if this particle represents a debit (balance decrease)."""
        return self.amount < Decimal("0")

    def is_usage(self) -> bool:
        """Check if this particle is a usage consumption event."""
        return self.particle_type == PARTICLE_TYPE_USAGE

    def get_effective_amount(self) -> Decimal:
        """Get amount with sign for balance calculations (debits are negative)."""
        return self.amount


@dataclass
class ParticleBalance:
    """Balance snapshot for a key_id at a point in time."""

    key_id: str
    balance: Decimal = field(default_factory=lambda: Decimal("0.0"))
    currency: str = CURRENCY_USD
    last_particle_id: Optional[str] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    particle_count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "ParticleBalance":
        """Create ParticleBalance from database row dict."""
        balance = data.get("balance", Decimal("0.0"))
        return cls(
            key_id=data.get("key_id", ""),
            balance=Decimal(balance) if balance is not None else Decimal("0.0"),
            currency=data.get("currency", CURRENCY_USD),
            last_particle_id=data.get("last_particle_id"),
            last_updated=data.get("last_updated") or datetime.now(timezone.utc),
            particle_count=data.get("particle_count", 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key_id": self.key_id,
            "balance": str(self.balance),
            "currency": self.currency,
            "last_particle_id": self.last_particle_id,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "particle_count": self.particle_count,
        }


@dataclass
class ParticleAggregation:
    """Aggregated particle statistics for reporting."""

    key_id: str
    particle_type: str
    total_amount: Decimal = field(default_factory=lambda: Decimal("0.0"))
    particle_count: int = 0
    currency: str = CURRENCY_USD
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ParticleAggregation":
        """Create from database aggregation result."""
        total = data.get("total_amount", Decimal("0.0"))
        return cls(
            key_id=data.get("key_id", ""),
            particle_type=data.get("particle_type", ""),
            total_amount=Decimal(total) if total is not None else Decimal("0.0"),
            particle_count=data.get("particle_count", 0),
            currency=data.get("currency", CURRENCY_USD),
            period_start=data.get("period_start"),
            period_end=data.get("period_end"),
        )


# ============================================================================
# LEGACY TENANT MODEL (RaaS Compatibility - Vietnam Integration)
# ============================================================================
# The Tenant model is kept for backward compatibility with the existing RaaS
# multi-tenant isolation system. New systems should use key_id with particles.
# ============================================================================


@dataclass
class Tenant:
    """Legacy tenant record for RaaS multi-tenant isolation.

    .. deprecated::
        Use key_id with EconomicParticle for new implementations.
        Kept for Vietnam compatibility and migration support.

    Attributes:
        id: UUID4 string identifier (legacy tenant_id)
        name: Human-readable tenant name
        api_key: Plaintext ``mk_``-prefixed key (only available at creation time)
        created_at: ISO-8601 UTC timestamp string
        is_active: Whether the tenant is allowed to use the API
    """

    id: str
    name: str
    api_key: str
    created_at: str
    is_active: bool = True


def _hash_key(key: str) -> str:
    """Return the SHA-256 hex digest of *key*."""
    return hashlib.sha256(key.encode()).hexdigest()


def _row_to_tenant(row: dict, api_key: str = "") -> Tenant:
    """Convert a DB row to a Tenant instance.

    Args:
        row: Row dict from PostgreSQL with tenant columns
        api_key: Plaintext key to embed in the result (empty after creation)

    Returns:
        Tenant instance
    """
    return Tenant(
        id=row["id"],
        name=row["name"],
        api_key=api_key,
        created_at=row["created_at"].isoformat() if isinstance(row["created_at"], datetime) else row["created_at"],
        is_active=bool(row["is_active"]),
    )


# ============================================================================
# PARTICLE REPOSITORY - Database Operations
# ============================================================================


class ParticleRepository:
    """Repository for economic_particles table operations.

    Handles all database interactions for EconomicParticle, Tenant, and
    balance calculations. Supports both direct PostgreSQL access and
    dependency injection for testing.
    """

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        """Initialize repository with database connection.

        Args:
            db: DatabaseConnection instance. If None, uses global get_database().
        """
        self._db = db
        self._using_global = db is None

    async def _get_db(self) -> DatabaseConnection:
        """Get database connection, initializing if needed."""
        if self._using_global:
            if not DB_AVAILABLE:
                raise ImportError("Database module not available. Install asyncpg.")
            return get_database()
        return self._db

    # ----------------------------------------------------------------------
    # EconomicParticle operations
    # ----------------------------------------------------------------------

    async def create_particle(self, particle: EconomicParticle) -> str:
        """Insert a new economic particle.

        Args:
            particle: EconomicParticle instance (id will be generated if empty)

        Returns:
            The particle ID (UUID string)

        Raises:
            RuntimeError: If database operation fails
        """
        db = await self._get_db()

        # Generate ID if not set
        if not particle.id:
            particle.id = str(uuid.uuid4())

        query, params = particle.to_insert_sql()
        try:
            result = await db.fetchval(query, *params)
            return str(result) if result else particle.id
        except Exception as exc:
            raise RuntimeError(f"Failed to create economic particle: {exc}") from exc

    async def get_particle(self, particle_id: str) -> Optional[EconomicParticle]:
        """Retrieve a single particle by ID.

        Args:
            particle_id: UUID string of the particle

        Returns:
            EconomicParticle or None if not found
        """
        db = await self._get_db()
        query = "SELECT * FROM economic_particles WHERE id = $1"
        row = await db.fetch_one(query, (particle_id,))
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
        """List particles for a key_id with optional filtering.

        Args:
            key_id: License key identifier
            particle_type: Filter by particle type (optional)
            limit: Maximum results to return
            offset: Pagination offset
            start_date: Filter particles created on or after this date
            end_date: Filter particles created on or before this date

        Returns:
            List of EconomicParticle instances (newest first by default)
        """
        db = await self._get_db()

        conditions = ["key_id = $1"]
        params: List[Any] = [key_id]
        param_count = 1

        if particle_type:
            param_count += 1
            conditions.append(f"particle_type = ${param_count}")
            params.append(particle_type)

        if start_date:
            param_count += 1
            conditions.append(f"created_at >= ${param_count}")
            params.append(start_date)

        if end_date:
            param_count += 1
            conditions.append(f"created_at <= ${param_count}")
            params.append(end_date)

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT * FROM economic_particles
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        params.extend([limit, offset])

        rows = await db.fetch_all(query, params)
        return [EconomicParticle.from_dict(row) for row in rows]

    async def get_balance(self, key_id: str, as_of: Optional[datetime] = None) -> Decimal:
        """Calculate current balance for a key_id.

        Args:
            key_id: License key identifier
            as_of: Calculate balance as of this datetime (optional, default: now)

        Returns:
            Current balance as Decimal
        """
        db = await self._get_db()

        if as_of:
            query = """
                SELECT SUM(amount) as total
                FROM economic_particles
                WHERE key_id = $1 AND created_at <= $2
            """
            row = await db.fetch_one(query, (key_id, as_of))
        else:
            query = """
                SELECT SUM(amount) as total
                FROM economic_particles
                WHERE key_id = $1
            """
            row = await db.fetch_one(query, (key_id,))

        total = row.get("total") if row else None
        return Decimal(str(total)) if total is not None else Decimal("0.0")

    async def get_balance_with_snapshot(
        self, key_id: str
    ) -> Tuple[Decimal, Optional[EconomicParticle]]:
        """Get balance and the last particle that affected it.

        Returns:
            Tuple of (balance, last_particle)
        """
        db = await self._get_db()
        query = """
            SELECT * FROM economic_particles
            WHERE key_id = $1
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        """
        last_row = await db.fetch_one(query, (key_id,))

        balance = Decimal("0.0")
        if last_row:
            balance = Decimal(str(last_row.get("balance_after", "0.0")))
            last_particle = EconomicParticle.from_dict(last_row)
            return balance, last_particle

        return balance, None

    async def aggregate_by_type(
        self,
        key_id: str,
        particle_types: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ParticleAggregation]:
        """Aggregate particles by type for a key_id.

        Args:
            key_id: License key identifier
            particle_types: Filter to specific types (None = all)
            start_date: Start of period (inclusive)
            end_date: End of period (inclusive)

        Returns:
            List of ParticleAggregation grouped by particle_type
        """
        db = await self._get_db()

        conditions = ["key_id = $1"]
        params: List[Any] = [key_id]
        param_count = 1

        if particle_types:
            param_count += 1
            conditions.append(f"particle_type = ANY(${param_count})")
            params.append(particle_types)

        if start_date:
            param_count += 1
            conditions.append(f"created_at >= ${param_count}")
            params.append(start_date)

        if end_date:
            param_count += 1
            conditions.append(f"created_at <= ${param_count}")
            params.append(end_date)

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT
                key_id,
                particle_type,
                SUM(amount) as total_amount,
                COUNT(*) as particle_count,
                currency
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
        """Count particles matching criteria.

        Args:
            key_id: Filter by key_id
            particle_type: Filter by particle type
            start_date: Start of period
            end_date: End of period

        Returns:
            Count of matching particles
        """
        db = await self._get_db()

        conditions = []
        params: List[Any] = []
        param_count = 0

        if key_id:
            param_count += 1
            conditions.append(f"key_id = ${param_count}")
            params.append(key_id)

        if particle_type:
            param_count += 1
            conditions.append(f"particle_type = ${param_count}")
            params.append(particle_type)

        if start_date:
            param_count += 1
            conditions.append(f"created_at >= ${param_count}")
            params.append(start_date)

        if end_date:
            param_count += 1
            conditions.append(f"created_at <= ${param_count}")
            params.append(end_date)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT COUNT(*) FROM economic_particles {where_clause}"
        row = await db.fetch_one(query, params)
        return row.get("count", 0) if row else 0

    # ----------------------------------------------------------------------
    # Legacy Tenant operations (refactored from raas/tenant.py)
    # ----------------------------------------------------------------------

    async def create_tenant(self, name: str, legacy_mode: bool = False) -> Tenant:
        """Create a new tenant and return it with the plaintext API key.

        .. deprecated::
            Use create_particle with PARTICLE_TYPE_CREDIT for new systems.
            Kept for Vietnam RaaS compatibility.

        Args:
            name: Human-readable label for the tenant
            legacy_mode: If True, creates minimal tenant record without particles

        Returns:
            Tenant instance with api_key set to the new ``mk_``-prefixed key

        Raises:
            RuntimeError: If the DB write fails
        """
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
        row = await db.fetch_one(
            query,
            (tenant_id, name, key_hash, created_at, True),
        )

        tenant = _row_to_tenant(row, api_key=raw_key)

        # Also create initial credit particle if not legacy mode
        if not legacy_mode:
            await self.create_particle(
                EconomicParticle(
                    tenant_id=tenant_id,
                    key_id=f"tenant_{tenant_id}",
                    particle_type=PARTICLE_TYPE_CREDIT,
                    amount=Decimal("0.0"),  # Zero initial credit (configurable)
                    currency=CURRENCY_USD,
                    source=SOURCE_ADMIN,
                    metadata={"action": "tenant_creation", "tenant_name": name},
                )
            )

        return tenant

    async def get_tenant_by_api_key(self, key: str) -> Optional[Tenant]:
        """Return the Tenant whose hashed key matches *key*.

        Args:
            key: Plaintext ``mk_``-prefixed API key supplied by the caller

        Returns:
            Matching Tenant or None if not found
        """
        db = await self._get_db()
        key_hash = _hash_key(key)

        query = "SELECT * FROM tenants WHERE api_key_hash = $1"
        row = await db.fetch_one(query, (key_hash,))

        return _row_to_tenant(row, api_key=key) if row else None

    async def find_tenant_by_name(self, name: str) -> Optional[Tenant]:
        """Find tenant by name (used as email lookup).

        Args:
            name: Tenant name to search for

        Returns:
            Tenant or None if not found
        """
        db = await self._get_db()
        query = "SELECT * FROM tenants WHERE name = $1"
        row = await db.fetch_one(query, (name,))
        return _row_to_tenant(row) if row else None

    async def list_tenants(self, include_inactive: bool = False) -> List[Tenant]:
        """Return all tenants ordered by creation date.

        Args:
            include_inactive: If False, only return active tenants

        Returns:
            List of Tenant objects (api_key is empty string)
        """
        db = await self._get_db()

        if include_inactive:
            query = "SELECT * FROM tenants ORDER BY created_at ASC"
            rows = await db.fetch_all(query)
        else:
            query = "SELECT * FROM tenants WHERE is_active = TRUE ORDER BY created_at ASC"
            rows = await db.fetch_all(query)

        return [_row_to_tenant(row) for row in rows]

    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """Soft-delete a tenant by marking it inactive.

        Args:
            tenant_id: UUID4 string of the tenant to deactivate

        Returns:
            True if a row was updated, False if tenant_id was not found
        """
        db = await self._get_db()
        query = "UPDATE tenants SET is_active = FALSE WHERE id = $1"
        result = await db.execute(query, (tenant_id,))
        return result != "UPDATE 0"

    async def tenant_exists(self, tenant_id: str) -> bool:
        """Check if a tenant exists.

        Args:
            tenant_id: Tenant UUID string

        Returns:
            True if tenant exists
        """
        db = await self._get_db()
        query = "SELECT 1 FROM tenants WHERE id = $1 LIMIT 1"
        row = await db.fetch_one(query, (tenant_id,))
        return row is not None

    # ----------------------------------------------------------------------
    # Utility methods
    # ----------------------------------------------------------------------

    async def migrate_tenant_to_particles(
        self,
        tenant_id: str,
        initial_balance: Decimal = Decimal("0.0"),
        currency: str = CURRENCY_USD,
    ) -> bool:
        """Migrate a legacy tenant to the particle system.

        Creates an initial credit particle to establish balance tracking
        for tenants that were created before particles existed.

        Args:
            tenant_id: Tenant to migrate
            initial_balance: Starting balance for the tenant
            currency: Currency for the balance

        Returns:
            True if migration was performed, False if already migrated
        """
        db = await self._get_db()

        # Check if tenant already has particles
        count_query = "SELECT COUNT(*) as cnt FROM economic_particles WHERE tenant_id = $1"
        row = await db.fetch_one(count_query, (tenant_id,))
        if row and row.get("cnt", 0) > 0:
            return False

        # Get tenant data
        tenant_query = "SELECT * FROM tenants WHERE id = $1"
        tenant_row = await db.fetch_one(tenant_query, (tenant_id,))
        if not tenant_row:
            return False

        # Create migration credit particle
        await self.create_particle(
            EconomicParticle(
                tenant_id=tenant_id,
                key_id=f"tenant_{tenant_id}",
                particle_type=PARTICLE_TYPE_CREDIT,
                amount=initial_balance,
                currency=currency,
                balance_after=initial_balance,
                source=SOURCE_MIGRATION,
                metadata={
                    "migration": "tenant_to_particles",
                    "tenant_name": tenant_row["name"],
                },
            )
        )
        return True


__all__ = [
    "EconomicParticle",
    "ParticleBalance",
    "ParticleAggregation",
    "Tenant",
    "ParticleRepository",
    # Constants
    "PARTICLE_TYPE_USAGE",
    "PARTICLE_TYPE_CREDIT",
    "PARTICLE_TYPE_ADJUSTMENT",
    "PARTICLE_TYPE_ADJUSTMENT_POSITIVE",
    "PARTICLE_TYPE_ADJUSTMENT_NEGATIVE",
    "PARTICLE_TYPE_PAYMENT",
    "PARTICLE_TYPE_REFUND",
    "PARTICLE_TYPE_FEE",
    "PARTICLE_TYPE_SUBSCRIPTION",
    "SOURCE_API",
    "SOURCE_MANUAL",
    "SOURCE_WEBHOOK",
    "SOURCE_CRON",
    "SOURCE_ADMIN",
    "SOURCE_MIGRATION",
    "SOURCE_RECONCILIATION",
    "CURRENCY_USD",
    "CURRENCY_VND",
    "CURRENCY_EUR",
    "VALID_PARTICLE_TYPES",
    "VALID_SOURCES",
    "VALID_CURRENCIES",
]


__all__ = [
    "EconomicParticle",
    "ParticleBalance",
    "ParticleAggregation",
    # Constants
    "PARTICLE_TYPE_USAGE",
    "PARTICLE_TYPE_CREDIT",
    "PARTICLE_TYPE_ADJUSTMENT",
    "PARTICLE_TYPE_ADJUSTMENT_POSITIVE",
    "PARTICLE_TYPE_ADJUSTMENT_NEGATIVE",
    "PARTICLE_TYPE_PAYMENT",
    "PARTICLE_TYPE_REFUND",
    "PARTICLE_TYPE_FEE",
    "PARTICLE_TYPE_SUBSCRIPTION",
    "SOURCE_API",
    "SOURCE_MANUAL",
    "SOURCE_WEBHOOK",
    "SOURCE_CRON",
    "SOURCE_ADMIN",
    "SOURCE_MIGRATION",
    "SOURCE_RECONCILIATION",
    "CURRENCY_USD",
    "CURRENCY_VND",
    "CURRENCY_EUR",
    "VALID_PARTICLE_TYPES",
    "VALID_SOURCES",
    "VALID_CURRENCIES",
]
