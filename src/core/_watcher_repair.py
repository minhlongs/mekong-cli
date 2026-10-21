"""Self-repair coordination for the autonomous watcher."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, List, Optional

from ._watcher_compat import bridge_value
from ._watcher_models import DiagnosticResult, RepairAction
from ._watcher_repair_checkpoint import rollback_file_checkpoint
from ._watcher_repair_syntax import auto_fix_syntax

logger = logging.getLogger(__name__)


class SelfRepairManager:
    """Coordinates automated code repair and durable checkpoint rollback."""

    def __init__(self, project_root: Optional[Path] = None, checkpoint_store: Any = None) -> None:
        self.project_root = bridge_value("Path", Path)(project_root or Path.cwd()).resolve()
        self._store = checkpoint_store
        self._repairs: List[RepairAction] = []
        self._lock = bridge_value("threading", threading).Lock()

    def _record(self, action: RepairAction) -> RepairAction:
        with self._lock:
            self._repairs.append(action)
        return action

    def _get_checkpoint_store(self) -> Any:
        if self._store is None:
            try:
                from src.core.pev_swarm_bridge import CheckpointStore

                store_class = bridge_value("CheckpointStore", CheckpointStore)
                self._store = store_class(db_path=self.project_root / ".mekong" / "pev_checkpoints.db")
            except Exception as error:
                bridge_value("logger", logger).warning(f"Could not initialize CheckpointStore: {error}")
                self._store = None
        return self._store

    def auto_fix_syntax(self, file_path: str | Path, diagnostic: DiagnosticResult) -> RepairAction:
        return auto_fix_syntax(self, file_path, diagnostic)

    def rollback_file_checkpoint(self, file_path: str | Path) -> RepairAction:
        return rollback_file_checkpoint(self, file_path)

    def diagnose_and_repair(self, file_path: str | Path, diagnostic: DiagnosticResult) -> RepairAction:
        if diagnostic.is_valid:
            return RepairAction(f"noop_{int(bridge_value('time', __import__('time')).time() * 1000)}", str(file_path),
                                "noop", "success", "File is valid, no repair needed")
        fix_action = self.auto_fix_syntax(file_path, diagnostic)
        return fix_action if fix_action.status == "success" else self.rollback_file_checkpoint(file_path)
