"""Checkpoint rollback operation for the autonomous watcher."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

from ._watcher_compat import bridge_value
from ._watcher_models import RepairAction

if TYPE_CHECKING:
    from ._watcher_repair import SelfRepairManager


def _action_id() -> str:
    clock = bridge_value("time", time)
    return f"repair_{int(clock.time() * 1000)}_{bridge_value('os', os).urandom(3).hex()}"


def rollback_file_checkpoint(manager: "SelfRepairManager", file_path: str | Path) -> RepairAction:
    """Rollback a corrupted file to its latest CheckpointStore snapshot."""
    path = bridge_value("Path", Path)(file_path).resolve()
    action_id = _action_id()
    store = manager._get_checkpoint_store()
    if not store:
        return manager._record(RepairAction(action_id, str(path), "checkpoint_rollback", "failed",
                               "No CheckpointStore available for rollback"))
    try:
        try:
            rel_path = str(path.relative_to(manager.project_root)).replace("\\", "/")
        except ValueError:
            rel_path = path.name
        with store._connect() as connection:
            row = connection.execute(
                """SELECT content, sha256, checkpoint_id FROM file_snapshots
                   WHERE relative_path = ? ORDER BY id DESC LIMIT 1""", (rel_path,)).fetchone()
        if not row or not row["content"]:
            return manager._record(RepairAction(action_id, str(path), "checkpoint_rollback", "failed",
                                   f"No previous checkpoint snapshot found for {rel_path}"))
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file_handle:
            file_handle.write(row["content"])
        return manager._record(RepairAction(action_id, str(path), "checkpoint_rollback", "success",
                               f"Restored from checkpoint {row['checkpoint_id']} (hash: {row['sha256'][:8]})"))
    except Exception as error:
        return manager._record(RepairAction(action_id, str(path), "checkpoint_rollback", "failed",
                               f"Rollback failed with error: {error}"))
