# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Core autonomous manager for Vietnamese Inheritance, Wills & Estate Administration."""

from __future__ import annotations

import os
import sqlite3

from .db import create_connection, init_db
from .engine_operations import InheritanceOperationsMixin
from .engine_queries import InheritanceQueryMixin


class InheritanceEngine(InheritanceQueryMixin, InheritanceOperationsMixin):
    """Production-grade Vietnamese Inheritance, Wills & Estate Administration Engine."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or os.environ.get("MEKONG_INHERITANCE_DB", "inheritance.db")
        self._memory_conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn, self._memory_conn = create_connection(self.db_path, self._memory_conn)
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            init_db(conn)


__all__ = ["InheritanceEngine"]
