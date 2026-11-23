"""Kill-switch controls and filesystem/checksum helpers for Pilot A DR backup/restore."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path


class PilotAKillSwitchError(RuntimeError):
    """Raised when the Pilot A product kill switch blocks intake or dispatch."""

    def __init__(self, stage: str, reason: str = "") -> None:
        self.stage = stage
        msg = f"PILOT_A_KILL_SWITCH_ACTIVE ({stage})" + (f": {reason}" if reason else "")
        super().__init__(msg)


def is_pilot_a_kill_switch_active(stage: str = "all") -> bool:
    """Return True when MEKONG_PILOT_A_KILL_SWITCH is active for the requested stage ('intake', 'dispatch', or 'all')."""
    raw = os.getenv("MEKONG_PILOT_A_KILL_SWITCH", "").strip().lower()
    if raw not in ("1", "true", "yes", "on"):
        return False
    mode = os.getenv("MEKONG_PILOT_A_KILL_SWITCH_MODE", "all").strip().lower() or "all"
    if mode not in ("all", "intake", "dispatch"):
        return True
    if mode == "all" or stage == "all":
        return True
    return mode == stage.strip().lower()


def enforce_pilot_a_kill_switch(stage: str) -> None:
    """Raise PilotAKillSwitchError when the kill switch blocks the given stage."""
    if is_pilot_a_kill_switch_active(stage):
        reason = os.getenv("MEKONG_PILOT_A_KILL_SWITCH_REASON", "Emergency operator stop").strip()
        raise PilotAKillSwitchError(stage=stage, reason=reason)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def chmod_safe(path: Path, mode: int) -> None:
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def validate_manifest_filename(fname: str, expected_suffix: str, bdir: Path, rdir: Path) -> tuple[Path, Path]:
    if not fname or "/" in fname or "\\" in fname or ".." in fname or Path(fname).is_absolute():
        raise ValueError(f"Unsafe backup manifest filename: {fname!r}")
    if not fname.endswith(expected_suffix):
        raise ValueError(f"Unexpected backup manifest file suffix for {fname!r}; expected {expected_suffix!r}")
    b_file = bdir / fname
    r_file = rdir / fname
    if b_file.is_symlink() or r_file.is_symlink():
        raise ValueError(f"Symlinks are not allowed in backup/restore: {fname!r}")
    if b_file.resolve().parent != bdir or r_file.resolve().parent != rdir:
        raise ValueError(f"Path traversal detected for manifest filename: {fname!r}")
    return b_file, r_file


def purge_sqlite_sidecars(db_path: Path) -> None:
    """Remove stale SQLite WAL/SHM sidecar files so restored snapshots never replay pre-restore frames."""
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{db_path}{suffix}")
        if sidecar.exists() or sidecar.is_symlink():
            sidecar.unlink()


def validate_source_file(path: Path, src: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"Symlinks are not allowed in backup source: {path.name!r}")
    if path.resolve().parent != src:
        raise ValueError(f"Path traversal detected in backup source: {path.name!r}")
