# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Filesystem and process management facades for LocalExecutionRuntime."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.core.exec_runtime.types import SandboxSpec

if TYPE_CHECKING:
    from .local import LocalExecutionRuntime


@dataclass
class LocalFilesystem:
    """Filesystem ops facade confined to a sandbox root."""

    spec: SandboxSpec

    def read_text(self, rel_path: str) -> str:
        return self.spec.resolve_in_root(rel_path).read_text(encoding="utf-8")

    def write_text(self, rel_path: str, content: str) -> int:
        target = self.spec.resolve_in_root(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return len(content)

    def list_dir(self, rel_path: str = ".") -> list[str]:
        base = self.spec.resolve_in_root(rel_path)
        return sorted(entry.name for entry in base.iterdir())

    def delete(self, rel_path: str) -> bool:
        target = self.spec.resolve_in_root(rel_path)
        if target.is_dir():
            target.rmdir()
            return True
        target.unlink(missing_ok=True)
        return True

    def exists(self, rel_path: str) -> bool:
        return self.spec.resolve_in_root(rel_path).exists()


class LocalProcessControl:
    """Process-management facade: enumerate and terminate tracked children."""

    def __init__(self, runtime: LocalExecutionRuntime) -> None:
        self._runtime = runtime

    def active_pids(self) -> list[int]:
        return self._runtime._snapshot_pids()

    def terminate(self, pid: int) -> bool:
        """SIGTERM then SIGKILL one tracked child."""
        found = self._lookup(pid)
        if found is None or found.poll() is not None:
            return False
        self._runtime._mark_terminated(pid)
        found.terminate()
        try:
            found.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            found.kill()
            found.wait(timeout=2.0)
        return True

    def terminate_all(self) -> int:
        count = 0
        for pid in self.active_pids():
            if self.terminate(pid):
                count += 1
        return count

    def _lookup(self, pid: int) -> subprocess.Popen[Any] | None:
        with self._runtime._lock:
            return self._runtime._processes.get(pid)


__all__ = ["LocalFilesystem", "LocalProcessControl"]
