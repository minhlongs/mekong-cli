# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Assignment, exposure, conversion, and results tracking for A/B experiments."""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from src.raas.ab_test_models import (
    Assignment,
    Experiment,
    ExperimentResults,
    _row_to_assignment,
)

logger = logging.getLogger(__name__)


class ABTestTrackingMixin:
    """Tracking and evaluation methods for ABTestService."""

    STATUS_ACTIVE = "active"

    def _connect(self) -> sqlite3.Connection: ...
    def get_experiment(self, experiment_name: str) -> Optional[Experiment]: ...

    def _hash_assignment(self, user_id: str, experiment_name: str) -> int:
        """Generate deterministic hash (0-99) for user assignment."""
        key = f"{user_id}:{experiment_name}"
        hash_bytes = hashlib.md5(key.encode()).hexdigest()
        return int(hash_bytes[:8], 16) % 100

    def get_assignment(self, user_id: str, experiment_name: str) -> Optional[str]:
        """Get deterministic variant assignment for a user."""
        experiment = self.get_experiment(experiment_name)
        if not experiment or experiment.status != self.STATUS_ACTIVE:
            return None

        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT variant FROM ab_assignments WHERE user_id = ? AND experiment_name = ?",
                    (user_id, experiment_name),
                ).fetchone()
                if row:
                    return row["variant"]
        except sqlite3.Error as exc:
            logger.error(f"Failed to check existing assignment: {exc}")

        hash_value = self._hash_assignment(user_id, experiment_name)
        variant = (
            experiment.variant_b if hash_value < experiment.allocation else experiment.variant_a
        )
        self._store_assignment(user_id, experiment_name, variant)
        logger.debug(f"Assigned user {user_id} to variant '{variant}' for {experiment_name}")
        return variant

    def _store_assignment(self, user_id: str, experiment_name: str, variant: str) -> None:
        """Store user assignment to database."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO ab_assignments (user_id, experiment_name, variant, assigned_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, experiment_name, variant, now),
                )
                conn.commit()
        except sqlite3.Error as exc:
            logger.error(f"Failed to store assignment: {exc}")

    def record_exposure(self, user_id: str, experiment_name: str, variant: str) -> bool:
        """Record that a user was exposed to an experiment variant."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE ab_assignments
                    SET exposed = 1, exposed_at = ?
                    WHERE user_id = ? AND experiment_name = ? AND variant = ?
                    """,
                    (now, user_id, experiment_name, variant),
                )
                conn.commit()
                return True
        except sqlite3.Error as exc:
            logger.error(f"Failed to record exposure: {exc}")
            return False

    def record_conversion(self, user_id: str, experiment_name: str) -> bool:
        """Record that a user converted in an experiment."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    UPDATE ab_assignments
                    SET converted = 1, converted_at = ?
                    WHERE user_id = ? AND experiment_name = ?
                    """,
                    (now, user_id, experiment_name),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as exc:
            logger.error(f"Failed to record conversion: {exc}")
            return False

    def get_experiment_results(self, experiment_name: str) -> Optional[ExperimentResults]:
        """Get experiment results with conversion statistics."""
        try:
            with self._connect() as conn:
                exp_row = conn.execute(
                    "SELECT variant_a, variant_b FROM ab_experiments WHERE name = ?",
                    (experiment_name,),
                ).fetchone()
                if not exp_row:
                    return None

                stats_query = """
                    SELECT COUNT(*) as total, SUM(converted) as conversions
                    FROM ab_assignments
                    WHERE experiment_name = ? AND variant = ?
                """
                a_row = conn.execute(stats_query, (experiment_name, exp_row["variant_a"])).fetchone()
                b_row = conn.execute(stats_query, (experiment_name, exp_row["variant_b"])).fetchone()

                va_users = a_row["total"] or 0
                vb_users = b_row["total"] or 0
                va_conv = a_row["conversions"] or 0
                vb_conv = b_row["conversions"] or 0

                va_rate = (va_conv / va_users * 100) if va_users > 0 else 0.0
                vb_rate = (vb_conv / vb_users * 100) if vb_users > 0 else 0.0
                rel_imp = ((vb_rate - va_rate) / va_rate * 100) if va_rate > 0 else 0.0

                return ExperimentResults(
                    experiment_name=experiment_name,
                    total_users=va_users + vb_users,
                    variant_a_users=va_users,
                    variant_b_users=vb_users,
                    variant_a_conversions=va_conv,
                    variant_b_conversions=vb_conv,
                    variant_a_rate=round(va_rate, 2),
                    variant_b_rate=round(vb_rate, 2),
                    relative_improvement=round(rel_imp, 2),
                )
        except sqlite3.Error as exc:
            logger.error(f"Failed to get experiment results: {exc}")
            return None

    def get_user_assignments(self, user_id: str) -> List[Assignment]:
        """Get all experiment assignments for a user."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT id, user_id, experiment_name, variant, exposed, converted,
                           assigned_at, exposed_at, converted_at
                    FROM ab_assignments
                    WHERE user_id = ?
                    ORDER BY assigned_at DESC
                    """,
                    (user_id,),
                ).fetchall()
                return [_row_to_assignment(r) for r in rows]
        except sqlite3.Error as exc:
            logger.error(f"Failed to get user assignments: {exc}")
            return []
