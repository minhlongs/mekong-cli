"""ACID SQLite store for checkpoints, file snapshots, and mission state."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .models import CheckpointRecord
from .store_capture import capture_checkpoint_impl
from .store_query import get_checkpoint_impl, list_checkpoints_impl
from .store_rollback import rollback_to_checkpoint_impl
from .store_schema import CheckpointStoreBase


class CheckpointStore(CheckpointStoreBase):
    """ACID SQLite store for checkpoints, file snapshots, and mission state."""

    def capture_checkpoint(
        self,
        mission_id: str,
        label: str,
        task_id: Optional[str] = None,
        phase: str = "post_execute",
        files: Optional[list[str | Path]] = None,
        test_results: Optional[dict[str, Any]] = None,
        project_root: Optional[Path] = None,
    ) -> str:
        """Capture atomic checkpoint with file snapshots and task states."""
        return capture_checkpoint_impl(
            self,
            mission_id=mission_id,
            label=label,
            task_id=task_id,
            phase=phase,
            files=files,
            test_results=test_results,
            project_root=project_root,
        )

    def get_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointRecord]:
        """Retrieve a checkpoint record and its associated file snapshots."""
        return get_checkpoint_impl(self, checkpoint_id)

    def list_checkpoints(self, mission_id: Optional[str] = None) -> list[dict[str, Any]]:
        """List checkpoints ordered by newest first."""
        return list_checkpoints_impl(self, mission_id)

    def rollback_to_checkpoint(
        self, checkpoint_id: str, project_root: Optional[Path] = None
    ) -> dict[str, Any]:
        """Atomically restore workspace files and task states to a specific checkpoint."""
        return rollback_to_checkpoint_impl(self, checkpoint_id, project_root=project_root)
