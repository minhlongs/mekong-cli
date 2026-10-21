"""Atomic workspace and task state rollback implementation for CheckpointStore."""

from __future__ import annotations

import base64
import binascii
import json
import logging
from pathlib import Path
import sqlite3
from typing import Any, Optional

from .constants import _utc_now_iso
from .models import MissionStatus
from .store_query import get_checkpoint_impl
from .store_schema import CheckpointStoreBase

logger = logging.getLogger(__name__)


def rollback_to_checkpoint_impl(
    store: CheckpointStoreBase,
    checkpoint_id: str,
    project_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Atomically restore workspace files and task states to a specific checkpoint."""
    root = Path(project_root or Path.cwd()).resolve()
    root_resolved = root.resolve()
    restored_files: list[str] = []
    removed_files: list[str] = []

    try:
        with store._connect() as conn:
            cp_row = conn.execute(
                "SELECT checkpoint_id FROM checkpoints WHERE checkpoint_id = ?",
                (checkpoint_id,),
            ).fetchone()

        if not cp_row:
            return {
                "ok": False,
                "error": f"Checkpoint {checkpoint_id} not found",
                "restored_files": restored_files,
            }

        cp = get_checkpoint_impl(store, checkpoint_id)
        if not cp:
            return {
                "ok": False,
                "error": f"Rollback failed: Checkpoint {checkpoint_id} contains corrupted data",
                "restored_files": restored_files,
            }

        now = _utc_now_iso()

        with store._connect() as conn:
            target_snapshot_paths: set[str] = set()
            for snap in cp.file_snapshots:
                try:
                    dest = (root / snap.relative_path).resolve()
                    dest.relative_to(root_resolved)
                except (ValueError, Exception) as p_exc:
                    logger.warning(
                        "Rejecting unsafe snapshot path outside workspace root: %s (%s)",
                        snap.relative_path,
                        p_exc,
                    )
                    continue

                if dest == root_resolved:
                    logger.warning(
                        "Rejecting unsafe snapshot path matching root directory: %s",
                        snap.relative_path,
                    )
                    continue

                dest.parent.mkdir(parents=True, exist_ok=True)

                if snap.content_type == "utf-8":
                    dest.write_text(snap.content, encoding="utf-8")
                elif snap.content_type == "base64":
                    try:
                        decoded_bytes = base64.b64decode(
                            snap.content.encode("ascii"), validate=True
                        )
                    except (binascii.Error, ValueError) as b64_exc:
                        logger.warning(
                            "Corrupted base64 content in snapshot %s for checkpoint %s: %s",
                            snap.relative_path,
                            checkpoint_id,
                            b64_exc,
                        )
                        return {
                            "ok": False,
                            "error": (
                                f"Rollback failed: Corrupted base64 content for file "
                                f"'{snap.relative_path}': {b64_exc}"
                            ),
                            "restored_files": restored_files,
                        }
                    dest.write_bytes(decoded_bytes)
                else:
                    dest.write_text(snap.content, encoding="utf-8")

                restored_files.append(snap.relative_path)
                target_snapshot_paths.add(snap.relative_path)

            post_rows = conn.execute(
                """
                SELECT DISTINCT s.relative_path
                FROM file_snapshots s
                JOIN checkpoints c ON s.checkpoint_id = c.checkpoint_id
                WHERE c.mission_id = ? AND c.created_at > ?
                """,
                (cp.mission_id, cp.created_at),
            ).fetchall()

            for r in post_rows:
                rel = r["relative_path"]
                if rel not in target_snapshot_paths:
                    try:
                        candidate = (root / rel).resolve()
                        candidate.relative_to(root_resolved)
                    except (ValueError, Exception) as p_exc:
                        logger.warning(
                            "Rejecting unsafe candidate path outside workspace root: %s (%s)",
                            rel,
                            p_exc,
                        )
                        continue

                    if candidate == root_resolved:
                        continue

                    if candidate.is_file():
                        try:
                            candidate.unlink()
                            removed_files.append(rel)
                        except OSError as exc:
                            logger.warning("Could not remove newly created file %s: %s", rel, exc)

            for task_id, status_val in cp.task_states.items():
                conn.execute(
                    "UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?",
                    (status_val, now, task_id),
                )

            conn.execute(
                "UPDATE missions SET status = ?, updated_at = ? WHERE mission_id = ?",
                (MissionStatus.ROLLED_BACK.value, now, cp.mission_id),
            )
            conn.commit()

        return {
            "ok": True,
            "checkpoint_id": checkpoint_id,
            "mission_id": cp.mission_id,
            "restored_files": restored_files,
            "removed_files": removed_files,
            "task_states": cp.task_states,
            "rolled_back_at": now,
        }

    except (json.JSONDecodeError, binascii.Error, ValueError, OSError, sqlite3.Error) as exc:
        logger.error("Rollback to checkpoint %s failed: %s", checkpoint_id, exc)
        return {
            "ok": False,
            "error": f"Rollback failed: {exc}",
            "restored_files": restored_files,
        }
