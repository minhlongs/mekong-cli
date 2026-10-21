# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tenant storage models, DDL, and row helpers for RaaS multi-tenant isolation."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from src.models.particle import Tenant

_DDL = """
CREATE TABLE IF NOT EXISTS tenants (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    api_key_hash TEXT NOT NULL UNIQUE,
    created_at   TEXT NOT NULL,
    is_active    INTEGER NOT NULL DEFAULT 1
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


def _row_to_tenant(row: sqlite3.Row) -> Tenant:
    """Map a SQLite row to a :class:`Tenant` dataclass instance."""
    return Tenant(
        id=row["id"],
        name=row["name"],
        api_key="",  # plaintext key is never stored; only returned at creation
        created_at=row["created_at"],
        is_active=bool(row["is_active"]),
    )
