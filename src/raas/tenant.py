# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tenant storage and management for RaaS multi-tenant isolation.

This module is the canonical synchronous tenant store for the RaaS layer.
It backs the FastAPI auth dependency (:func:`src.raas.auth.get_tenant_context`),
the checkout / revenue / dashboard routers, and the RaaS test suite — all of
which call ``TenantStore`` synchronously.

.. deprecated::
    New code should use :mod:`src.models.particle` (``ParticleRepository``)
    for particle-level economic events.  ``TenantStore`` remains the
    authoritative source of tenant identity and API keys and is **not**
    scheduled for removal; the deprecation marker is retained for historical
    accuracy only.

Storage:
    SQLite at ``~/.mekong/raas/tenants.db`` by default.  The path can be
    overridden via the ``db_path`` constructor argument, which makes the
    store trivially testable without touching the real user database.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# Re-export Tenant from the particle module so callers that import
# ``Tenant`` from here continue to work after the Phase 8 consolidation.
from src.models.particle import Tenant  # noqa: F401  (re-export)

logger = logging.getLogger(__name__)

_DB_PATH = Path(os.environ.get("MEKONG_RAAS_DB") or Path.home() / ".mekong" / "raas" / "tenants.db")

_DDL = """
CREATE TABLE IF NOT EXISTS tenants (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    api_key_hash TEXT NOT NULL UNIQUE,
    created_at   TEXT NOT NULL,
    is_active    INTEGER NOT NULL DEFAULT 1,
    -- ISO 3166-1 alpha-2 jurisdiction. Drives which payment rails the tenant
    -- may use: a Vietnamese licensee cannot settle on a crypto rail.
    jurisdiction TEXT NOT NULL DEFAULT 'VN'
);
"""


@dataclass
class _TenantRow:
    """Internal row projection used by :class:`TenantStore`."""

    id: str
    name: str
    api_key_hash: str
    created_at: str
    is_active: int


class TenantStore:
    """Synchronous SQLite-backed tenant store.

    The synchronous API is intentional: the RaaS auth dependency runs inside
    a FastAPI request handler and must not spawn an event loop per request.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialise the store.

        Args:
            db_path: SQLite database path. Defaults to
                ``~/.mekong/raas/tenants.db``.  Pass a ``tmp_path`` in tests
                to isolate them from the real user database.
        """
        self.db_path = Path(db_path) if db_path else _DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _initialise(self) -> None:
        """Create the tenants table if it does not exist."""
        try:
            with self._connect() as conn:
                conn.execute(_DDL)
                conn.commit()
                self._add_jurisdiction_column(conn)
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to initialise tenant DB: {exc}") from exc

    @staticmethod
    def _add_jurisdiction_column(conn: sqlite3.Connection) -> None:
        """Add the jurisdiction column to a pre-existing tenants table.

        Installs created before the column existed keep working: the value is
        backfilled to ``VN`` so the payment-rail policy applies to them too.
        """
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(tenants)")}
        if "jurisdiction" not in columns:
            conn.execute(
                "ALTER TABLE tenants ADD COLUMN jurisdiction TEXT NOT NULL DEFAULT 'VN'"
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_tenant(self, name: str) -> Tenant:
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
        tenant_id = str(uuid.uuid4())
        raw_key = "mk_" + uuid.uuid4().hex
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        created_at = datetime.now(timezone.utc).isoformat()

        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO tenants (id, name, api_key_hash, created_at, "
                    "is_active) VALUES (?, ?, ?, ?, 1)",
                    (tenant_id, name, key_hash, created_at),
                )
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to create tenant '{name}': {exc}") from exc

        return Tenant(
            id=tenant_id,
            name=name,
            api_key=raw_key,
            created_at=created_at,
            is_active=True,
        )

    def get_by_api_key(self, key: str) -> Optional[Tenant]:
        """Return the :class:`Tenant` whose hashed key matches *key*.

        Args:
            key: Plaintext ``mk_``-prefixed API key supplied by the caller.

        Returns:
            Matching :class:`Tenant` or ``None`` if not found.

        Raises:
            RuntimeError: If the DB query fails.
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM tenants WHERE api_key_hash = ?", (key_hash,)
                ).fetchone()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to look up API key: {exc}") from exc

        if row is None:
            return None
        return _row_to_tenant(row)

    def find_by_email(self, email: str) -> Optional[Tenant]:
        """Find a tenant by name (used as email lookup).

        Args:
            email: Tenant name/email to search for.

        Returns:
            Matching :class:`Tenant` or ``None`` if not found.

        Raises:
            RuntimeError: If the DB query fails.
        """
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM tenants WHERE name = ?", (email,)
                ).fetchone()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to look up tenant by email: {exc}") from exc

        return _row_to_tenant(row) if row else None

    def get_persisted_jurisdiction(self, org_id: str) -> Optional[str]:
        """Return the persisted ISO alpha-2 jurisdiction for an active tenant, or None if unverified/ambiguous."""
        clean = (org_id or "").strip()
        if not clean:
            return None
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT jurisdiction FROM tenants WHERE id = ? AND is_active = 1",
                    (clean,),
                ).fetchone()
                if row is None:
                    rows = conn.execute(
                        "SELECT jurisdiction FROM tenants WHERE name = ? AND is_active = 1 LIMIT 2",
                        (clean,),
                    ).fetchall()
                    row = rows[0] if len(rows) == 1 else None
        except sqlite3.Error:
            return None
        if row is None:
            return None
        stored = str(row["jurisdiction"] or "").strip().upper()
        return stored if (len(stored) == 2 and stored.isalpha()) else "VN"

    def ensure_jurisdiction_audit_schema(self) -> None:
        """Idempotently migrate tenant DB to add tenant_jurisdiction_audit table."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tenant_jurisdiction_audit (
                    audit_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    old_jurisdiction TEXT NOT NULL,
                    new_jurisdiction TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    evidence_ref TEXT NOT NULL,
                    changed_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def rollback_jurisdiction_audit_schema(self) -> None:
        """Rollback helper dropping tenant_jurisdiction_audit without touching tenants."""
        with self._connect() as conn:
            conn.execute("DROP TABLE IF EXISTS tenant_jurisdiction_audit")
            conn.commit()

    def update_jurisdiction_admin(
        self,
        tenant_id: str,
        new_jurisdiction: str,
        *,
        actor_id: str,
        evidence_ref: str,
    ) -> dict[str, str]:
        """Administratively update a persisted tenant's jurisdiction with mandatory evidence and audit log."""
        clean_jur = (new_jurisdiction or "").strip().upper()
        if len(clean_jur) != 2 or not clean_jur.isalpha():
            raise ValueError("Jurisdiction must be a 2-letter ISO 3166-1 alpha-2 code.")
        clean_actor = (actor_id or "").strip()
        clean_evidence = (evidence_ref or "").strip()
        if not clean_actor or not clean_evidence:
            raise ValueError("Administrative jurisdiction change requires non-empty actor_id and evidence_ref.")
        clean_tid = (tenant_id or "").strip()
        self.ensure_jurisdiction_audit_schema()
        changed_at = datetime.now(timezone.utc).isoformat()
        audit_id = f"jur_{uuid.uuid4().hex[:16]}"
        conn = sqlite3.connect(str(self.db_path), isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT id, jurisdiction FROM tenants WHERE id = ? AND is_active = 1",
                (clean_tid,),
            ).fetchone()
            if row is None:
                rows = conn.execute(
                    "SELECT id, jurisdiction FROM tenants WHERE name = ? AND is_active = 1 LIMIT 2",
                    (clean_tid,),
                ).fetchall()
                if len(rows) > 1:
                    raise ValueError(f"Ambiguous tenant name '{clean_tid}'; specify primary tenant_id.")
                row = rows[0] if len(rows) == 1 else None
            if row is None:
                raise LookupError(f"Active tenant '{clean_tid}' not found.")
            resolved_id = str(row["id"])
            old_jur = str(row["jurisdiction"] or "VN").strip().upper()
            conn.execute(
                "UPDATE tenants SET jurisdiction = ? WHERE id = ?",
                (clean_jur, resolved_id),
            )
            conn.execute(
                "INSERT INTO tenant_jurisdiction_audit "
                "(audit_id, tenant_id, old_jurisdiction, new_jurisdiction, actor_id, evidence_ref, changed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (audit_id, resolved_id, old_jur, clean_jur, clean_actor, clean_evidence, changed_at),
            )
            conn.execute("COMMIT")
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()
        return {
            "audit_id": audit_id,
            "tenant_id": resolved_id,
            "old_jurisdiction": old_jur,
            "new_jurisdiction": clean_jur,
            "actor_id": clean_actor,
            "evidence_ref": clean_evidence,
            "changed_at": changed_at,
        }

    def jurisdiction_for(self, org_id: str) -> str:
        """Return the ISO 3166-1 alpha-2 jurisdiction governing *org_id* (fail-closed to VN)."""
        return self.get_persisted_jurisdiction(org_id) or "VN"

    def list_tenants(self) -> List[Tenant]:
        """Return all active tenants ordered by creation date.

        Returns:
            List of :class:`Tenant` objects (``api_key`` is empty string).

        Raises:
            RuntimeError: If the DB query fails.
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM tenants WHERE is_active = 1 "
                    "ORDER BY created_at ASC"
                ).fetchall()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to list tenants: {exc}") from exc

        return [_row_to_tenant(r) for r in rows]

    def deactivate_tenant(self, tenant_id: str) -> bool:
        """Soft-delete a tenant by marking it inactive.

        Args:
            tenant_id: UUID4 string of the tenant to deactivate.

        Returns:
            ``True`` if a row was updated, ``False`` if *tenant_id* was not
            found.

        Raises:
            RuntimeError: If the DB update fails.
        """
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "UPDATE tenants SET is_active = 0 WHERE id = ?",
                    (tenant_id,),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as exc:
            raise RuntimeError(
                f"Failed to deactivate tenant '{tenant_id}': {exc}"
            ) from exc

    def tenant_exists(self, tenant_id: str) -> bool:
        """Check whether a tenant id exists.

        Args:
            tenant_id: Tenant UUID string.

        Returns:
            True if the tenant exists, False otherwise.
        """
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT 1 FROM tenants WHERE id = ? LIMIT 1",
                    (tenant_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to check tenant existence: {exc}") from exc
        return row is not None

    def tenant_exists_by_id_or_name(self, org_id: str) -> bool:
        """Return True if any tenant row (active or inactive, unique or duplicate) matches id or name."""
        clean = (org_id or "").strip()
        if not clean:
            return False
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT 1 FROM tenants WHERE id = ? OR name = ? LIMIT 1",
                    (clean, clean),
                ).fetchone()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to verify tenant existence: {exc}") from exc
        return row is not None


def _row_to_tenant(row: sqlite3.Row) -> Tenant:
    """Map a SQLite row to a :class:`Tenant` dataclass instance."""
    return Tenant(
        id=row["id"],
        name=row["name"],
        api_key="",  # plaintext key is never stored; only returned at creation
        created_at=row["created_at"],
        is_active=bool(row["is_active"]),
    )


__all__ = ["Tenant", "TenantStore"]