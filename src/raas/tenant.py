# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tenant storage and management for RaaS multi-tenant isolation.

This module is the canonical synchronous tenant store for the RaaS layer.
It backs the FastAPI auth dependency (:func:`src.raas.auth.get_tenant_context`),
the checkout / revenue / dashboard routers, and the RaaS test suite — all of
which call ``TenantStore`` synchronously.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import logging
import os
from pathlib import Path
import sqlite3
from typing import List, Optional
import uuid

from src.models.particle import Tenant  # noqa: F401  (re-export)
from src.raas.tenant_models import _DDL, _row_to_tenant, _TenantRow

logger = logging.getLogger(__name__)

_DB_PATH = Path(os.environ.get("MEKONG_RAAS_DB") or Path.home() / ".mekong" / "raas" / "tenants.db")


class TenantStore:
    """Synchronous SQLite-backed tenant store."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else _DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialise(self) -> None:
        """Create the tenants table if it does not exist."""
        try:
            with self._connect() as conn:
                conn.execute(_DDL)
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to initialise tenant DB: {exc}") from exc

    def create_tenant(self, name: str) -> Tenant:
        """Create a new tenant and return it with the plaintext API key."""
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
        """Return the :class:`Tenant` whose hashed key matches *key*."""
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
        """Find a tenant by name (used as email lookup)."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM tenants WHERE name = ?", (email,)
                ).fetchone()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to look up tenant by email: {exc}") from exc

        return _row_to_tenant(row) if row else None

    def list_tenants(self) -> List[Tenant]:
        """Return all active tenants ordered by creation date."""
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
        """Soft-delete a tenant by marking it inactive."""
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
        """Check whether a tenant id exists."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT 1 FROM tenants WHERE id = ? LIMIT 1",
                    (tenant_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to check tenant existence: {exc}") from exc
        return row is not None


__all__ = ["Tenant", "TenantStore", "_TenantRow", "_row_to_tenant", "_DB_PATH", "_DDL"]
