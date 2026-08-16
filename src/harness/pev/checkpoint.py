# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - PEV Checkpoint/Resume Protocol

Persists pipeline execution state to disk so interrupted pipelines can resume
from the last completed step rather than restarting from scratch.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class PipelineCheckpoint:
    """Snapshot of a pipeline's execution progress."""

    pipeline_id: str
    completed_steps: list[int]  # step orders that completed successfully
    last_step_order: int
    status: str  # "running", "paused", "completed", "failed"
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _utc_now() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(tz=timezone.utc).isoformat()


class CheckpointStore:
    """Persists pipeline checkpoints to ~/.mekong/checkpoints/ as JSON files."""

    def __init__(self, storage_dir: str | None = None) -> None:
        """Initialize the store.

        Args:
            storage_dir: Override directory path. Defaults to ~/.mekong/checkpoints/.
        """
        if storage_dir is None:
            storage_dir = str(Path.home() / ".mekong" / "checkpoints")
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, pipeline_id: str) -> Path:
        return self._dir / f"{pipeline_id}.json"

    def save(self, checkpoint: PipelineCheckpoint) -> None:
        """Persist checkpoint to disk.

        Args:
            checkpoint: The checkpoint to save.

        Raises:
            OSError: If the file cannot be written.
        """
        checkpoint.updated_at = _utc_now()
        data = asdict(checkpoint)
        tmp = self._path(checkpoint.pipeline_id).with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp.replace(self._path(checkpoint.pipeline_id))
        except OSError:
            tmp.unlink(missing_ok=True)
            raise

    def load(self, pipeline_id: str) -> PipelineCheckpoint | None:
        """Load a checkpoint from disk.

        Args:
            pipeline_id: The pipeline whose checkpoint to load.

        Returns:
            PipelineCheckpoint if found, None otherwise.
        """
        path = self._path(pipeline_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return PipelineCheckpoint(**data)
        except (json.JSONDecodeError, TypeError, KeyError):
            return None

    def delete(self, pipeline_id: str) -> None:
        """Remove a checkpoint file.

        Args:
            pipeline_id: The pipeline whose checkpoint to delete.
        """
        self._path(pipeline_id).unlink(missing_ok=True)

    def list_checkpoints(self) -> list[str]:
        """Return pipeline IDs that have active checkpoints on disk.

        Returns:
            Sorted list of pipeline_id strings.
        """
        return sorted(p.stem for p in self._dir.glob("*.json"))
