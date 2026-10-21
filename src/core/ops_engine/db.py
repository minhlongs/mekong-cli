"""Database schema initialization for ops engine."""

from __future__ import annotations

import sqlite3


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize tables for incidents, health sweeps, and disaster recovery runs."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            severity TEXT NOT NULL,
            service TEXT NOT NULL,
            status TEXT NOT NULL,
            summary TEXT,
            root_cause TEXT,
            mitigation TEXT,
            created_at TEXT NOT NULL,
            resolved_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS health_sweeps (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            overall_status TEXT NOT NULL,
            score INTEGER NOT NULL,
            summary TEXT,
            checks_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dr_runs (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            readiness_score INTEGER NOT NULL,
            notes TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents (status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_sev ON incidents (severity)")
    conn.commit()
