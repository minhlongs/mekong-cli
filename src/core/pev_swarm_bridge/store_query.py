"""Checkpoint retrieval and listing operations for CheckpointStore."""

from __future__ import annotations

import binascii
import json
import logging
import sqlite3
from typing import Any, Optional

from .models import CheckpointRecord, FileSnapshot
from .store_schema import CheckpointStoreBase

logger = logging.getLogger(__name__)


def get_checkpoint_impl(store: CheckpointStoreBase, checkpoint_id: str) -> Optional[CheckpointRecord]:
    """Retrieve a checkpoint record and its associated file snapshots."""
    try:
        with store._connect() as conn:
            cp_row = conn.execute(
                "SELECT * FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,)
            ).fetchone()
            if not cp_row:
                return None

            snap_rows = conn.execute(
                "SELECT relative_path, sha256, content_type, content, size_bytes "
                "FROM file_snapshots WHERE checkpoint_id = ? ORDER BY id ASC",
                (checkpoint_id,),
            ).fetchall()

            snapshots = [
                FileSnapshot(
                    relative_path=r["relative_path"],
                    sha256=r["sha256"],
                    content_type=r["content_type"],
                    content=r["content"],
                    size_bytes=r["size_bytes"],
                )
                for r in snap_rows
            ]

            try:
                task_states = json.loads(cp_row["task_states"]) if cp_row["task_states"] else {}
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("Corrupted task_states in checkpoint %s: %s", checkpoint_id, exc)
                return None

            try:
                test_results = json.loads(cp_row["test_results"]) if cp_row["test_results"] else {}
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("Corrupted test_results in checkpoint %s: %s", checkpoint_id, exc)
                return None

            return CheckpointRecord(
                checkpoint_id=cp_row["checkpoint_id"],
                mission_id=cp_row["mission_id"],
                task_id=cp_row["task_id"],
                cycle=cp_row["cycle"],
                phase=cp_row["phase"],
                label=cp_row["label"],
                task_states=task_states,
                test_results=test_results,
                file_snapshots=snapshots,
                created_at=cp_row["created_at"],
            )
    except (json.JSONDecodeError, binascii.Error, ValueError, OSError, sqlite3.Error) as exc:
        logger.warning(
            "Failed to retrieve checkpoint %s due to corrupted data or database error: %s",
            checkpoint_id,
            exc,
        )
        return None


def list_checkpoints_impl(
    store: CheckpointStoreBase, mission_id: Optional[str] = None
) -> list[dict[str, Any]]:
    """List checkpoints ordered by newest first."""
    with store._connect() as conn:
        if mission_id:
            rows = conn.execute(
                """
                SELECT c.*, COUNT(s.id) AS file_count
                FROM checkpoints c
                LEFT JOIN file_snapshots s ON c.checkpoint_id = s.checkpoint_id
                WHERE c.mission_id = ?
                GROUP BY c.checkpoint_id
                ORDER BY c.created_at DESC
                """,
                (mission_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT c.*, COUNT(s.id) AS file_count
                FROM checkpoints c
                LEFT JOIN file_snapshots s ON c.checkpoint_id = s.checkpoint_id
                GROUP BY c.checkpoint_id
                ORDER BY c.created_at DESC
                """
            ).fetchall()

        results: list[dict[str, Any]] = []
        for r in rows:
            try:
                task_states = json.loads(r["task_states"]) if r["task_states"] else {}
            except (json.JSONDecodeError, ValueError):
                task_states = {}
            results.append(
                {
                    "checkpoint_id": r["checkpoint_id"],
                    "mission_id": r["mission_id"],
                    "task_id": r["task_id"],
                    "cycle": r["cycle"],
                    "phase": r["phase"],
                    "label": r["label"],
                    "file_count": r["file_count"],
                    "task_states": task_states,
                    "created_at": r["created_at"],
                }
            )
        return results
