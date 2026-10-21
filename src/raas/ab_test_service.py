# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""A/B test framework for onboarding optimization."""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3
from typing import List, Optional

from src.raas.ab_test_models import (
    _DB_PATH,
    _DDL,
    Assignment,
    Experiment,
    ExperimentResults,
    _row_to_experiment,
)
from src.raas.ab_test_tracking import ABTestTrackingMixin

logger = logging.getLogger(__name__)

_SELECT_COLS = "SELECT id, name, description, variant_a, variant_b, allocation, status, created_at, started_at, ended_at FROM ab_experiments"


class ABTestService(ABTestTrackingMixin):
    """A/B test service for onboarding optimization."""

    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_COMPLETED = "completed"

    def __init__(self, db_path: Path = _DB_PATH) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        try:
            with self._connect() as conn:
                conn.executescript(_DDL)
                conn.commit()
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to initialize A/B test DB: {exc}") from exc

    def create_experiment(
        self,
        name: str,
        description: str,
        variant_a: str = "control",
        variant_b: str = "treatment",
        allocation: int = 50,
    ) -> Experiment:
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO ab_experiments (name, description, variant_a, variant_b, allocation, status, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (name, description, variant_a, variant_b, allocation, self.STATUS_DRAFT, now),
                )
                conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"Experiment '{name}' already exists") from exc
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to create experiment: {exc}") from exc

        logger.info(f"Created A/B test experiment: {name}")
        return Experiment(
            id=None, name=name, description=description, variant_a=variant_a,
            variant_b=variant_b, allocation=allocation, status=self.STATUS_DRAFT, created_at=now,
        )

    def get_experiment(self, experiment_name: str) -> Optional[Experiment]:
        try:
            with self._connect() as conn:
                row = conn.execute(f"{_SELECT_COLS} WHERE name = ?", (experiment_name,)).fetchone()
                return _row_to_experiment(row) if row else None
        except sqlite3.Error as exc:
            logger.error(f"Failed to get experiment: {exc}")
            return None

    def start_experiment(self, experiment_name: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "UPDATE ab_experiments SET status = ?, started_at = ? WHERE name = ? AND status = ?",
                    (self.STATUS_ACTIVE, now, experiment_name, self.STATUS_DRAFT),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(f"Failed to start experiment: {exc}")
            return False

    def pause_experiment(self, experiment_name: str) -> bool:
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "UPDATE ab_experiments SET status = ? WHERE name = ? AND status = ?",
                    (self.STATUS_PAUSED, experiment_name, self.STATUS_ACTIVE),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(f"Failed to pause experiment: {exc}")
            return False

    def complete_experiment(self, experiment_name: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "UPDATE ab_experiments SET status = ?, ended_at = ? WHERE name = ?",
                    (self.STATUS_COMPLETED, now, experiment_name),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(f"Failed to complete experiment: {exc}")
            return False

    def list_experiments(self, status: Optional[str] = None) -> List[Experiment]:
        try:
            with self._connect() as conn:
                if status:
                    rows = conn.execute(f"{_SELECT_COLS} WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
                else:
                    rows = conn.execute(f"{_SELECT_COLS} ORDER BY created_at DESC").fetchall()
                return [_row_to_experiment(r) for r in rows]
        except sqlite3.Error as exc:
            logger.error(f"Failed to list experiments: {exc}")
            return []


__all__ = [
    "ABTestService", "Assignment", "Experiment", "ExperimentResults", "_DB_PATH", "_DDL",
]
