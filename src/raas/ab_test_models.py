# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and schema DDL for the RaaS A/B test service."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_DB_PATH = Path.home() / ".mekong" / "raas" / "tenants.db"

_DDL = """
-- A/B test experiments table
CREATE TABLE IF NOT EXISTS ab_experiments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT UNIQUE NOT NULL,
    description     TEXT,
    variant_a       TEXT DEFAULT 'control',
    variant_b       TEXT DEFAULT 'treatment',
    allocation      INTEGER DEFAULT 50,
    status          TEXT DEFAULT 'draft',
    created_at      TEXT NOT NULL,
    started_at      TEXT,
    ended_at        TEXT
);

-- User experiment assignments table
CREATE TABLE IF NOT EXISTS ab_assignments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT NOT NULL,
    experiment_name TEXT NOT NULL,
    variant         TEXT NOT NULL,
    exposed         INTEGER DEFAULT 0,
    converted       INTEGER DEFAULT 0,
    assigned_at     TEXT NOT NULL,
    exposed_at      TEXT,
    converted_at    TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ab_assignments_user ON ab_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_ab_assignments_experiment ON ab_assignments(experiment_name);
CREATE INDEX IF NOT EXISTS idx_ab_experiments_status ON ab_experiments(status);
"""


@dataclass
class Experiment:
    """An A/B test experiment."""

    name: str
    description: str
    variant_a: str
    variant_b: str
    allocation: int
    status: str
    created_at: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    id: Optional[int] = None


@dataclass
class Assignment:
    """A user's assignment to an experiment variant."""

    user_id: str
    experiment_name: str
    variant: str
    exposed: bool
    converted: bool
    assigned_at: str
    exposed_at: Optional[str] = None
    converted_at: Optional[str] = None
    id: Optional[int] = None


@dataclass
class ExperimentResults:
    """Results from an A/B test experiment."""

    experiment_name: str
    total_users: int
    variant_a_users: int
    variant_b_users: int
    variant_a_conversions: int
    variant_b_conversions: int
    variant_a_rate: float
    variant_b_rate: float
    relative_improvement: float


def _row_to_experiment(row: sqlite3.Row) -> Experiment:
    return Experiment(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        variant_a=row["variant_a"],
        variant_b=row["variant_b"],
        allocation=row["allocation"],
        status=row["status"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
    )


def _row_to_assignment(row: sqlite3.Row) -> Assignment:
    return Assignment(
        id=row["id"],
        user_id=row["user_id"],
        experiment_name=row["experiment_name"],
        variant=row["variant"],
        exposed=bool(row["exposed"]),
        converted=bool(row["converted"]),
        assigned_at=row["assigned_at"],
        exposed_at=row["exposed_at"],
        converted_at=row["converted_at"],
    )
