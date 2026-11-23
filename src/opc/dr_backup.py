"""Operational runtime controls for Pilot A: product kill switch (RT-05) and WAL-consistent SQLite DR backup/restore (RT-06)."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote


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


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _chmod_safe(path: Path, mode: int) -> None:
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def _validate_manifest_filename(fname: str, expected_suffix: str, bdir: Path, rdir: Path) -> tuple[Path, Path]:
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


def _purge_sqlite_sidecars(db_path: Path) -> None:
    """Remove stale SQLite WAL/SHM sidecar files so restored snapshots never replay pre-restore frames."""
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{db_path}{suffix}")
        if sidecar.exists() or sidecar.is_symlink():
            sidecar.unlink()


def _sqlite_online_backup(src_db: Path, dst_db: Path) -> str:
    """Create a WAL-consistent snapshot using sqlite3.Connection.backup and run PRAGMA integrity_check."""
    dst_db.parent.mkdir(parents=True, exist_ok=True)
    _chmod_safe(dst_db.parent, 0o700)
    if dst_db.exists():
        dst_db.unlink()
    _purge_sqlite_sidecars(dst_db)
    src_uri = f"file:{quote(str(src_db), safe='/')}?mode=ro"
    src_conn = sqlite3.connect(src_uri, uri=True, timeout=30.0)
    dst_conn = sqlite3.connect(str(dst_db), timeout=30.0)
    try:
        src_conn.backup(dst_conn)
        dst_conn.commit()
        row = dst_conn.execute("PRAGMA integrity_check").fetchone()
        return str(row[0]) if row else "unknown"
    finally:
        dst_conn.close()
        src_conn.close()
        if dst_db.exists():
            _chmod_safe(dst_db, 0o600)


def _validate_source_file(path: Path, src: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"Symlinks are not allowed in backup source: {path.name!r}")
    if path.resolve().parent != src:
        raise ValueError(f"Path traversal detected in backup source: {path.name!r}")


def backup_tenant_directory(source_dir: Path, backup_dir: Path) -> dict[str, Any]:
    """Create an atomic, online WAL-consistent backup of all SQLite DBs and tenant configs with SHA-256 manifest."""
    src = Path(source_dir).resolve()
    dst = Path(backup_dir).resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{dst.name}.stage-", dir=str(dst.parent)))
    _chmod_safe(staging, 0o700)
    db_entries: list[dict[str, Any]] = []
    cfg_entries: list[dict[str, Any]] = []

    try:
        for db_file in sorted(src.glob("*.db")):
            _validate_source_file(db_file, src)
            out_db = staging / db_file.name
            integrity = _sqlite_online_backup(db_file, out_db)
            if integrity.lower() != "ok":
                raise RuntimeError(f"Backup integrity check failed for {db_file.name}: {integrity}")
            db_entries.append({"file": db_file.name, "sha256": _sha256_file(out_db), "bytes": out_db.stat().st_size, "integrity": integrity})

        for cfg_file in sorted(src.glob("*.tenant.json")):
            _validate_source_file(cfg_file, src)
            out_cfg = staging / cfg_file.name
            shutil.copy2(cfg_file, out_cfg)
            _chmod_safe(out_cfg, 0o600)
            cfg_entries.append({"file": cfg_file.name, "sha256": _sha256_file(out_cfg), "bytes": out_cfg.stat().st_size})

        manifest = {
            "schema_version": "sc11-dr-v1",
            "created_at": int(time.time()),
            "source_dir": str(src),
            "databases": db_entries,
            "configs": cfg_entries,
        }
        manifest_file = staging / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        _chmod_safe(manifest_file, 0o600)

        dst.mkdir(parents=True, exist_ok=True)
        _chmod_safe(dst, 0o700)
        for staged_file in sorted(staging.iterdir()):
            target = dst / staged_file.name
            os.replace(staged_file, target)
            _chmod_safe(target, 0o600)
        return manifest
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def restore_tenant_directory(backup_dir: Path, restore_dir: Path) -> dict[str, Any]:
    """Verify full SHA-256 manifest, stage + integrity-check all SQLite DBs, then atomically promote into restore_dir."""
    bdir = Path(backup_dir).resolve()
    rdir = Path(restore_dir).resolve()
    manifest_path = bdir / "manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise FileNotFoundError(f"Backup manifest missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Phase 1: Pre-validate all manifest entries & SHA-256 checksums before mutating any destination file
    validated_dbs: list[tuple[str, Path, Path]] = []
    for entry in manifest.get("databases", []):
        fname = str(entry["file"])
        b_file, r_file = _validate_manifest_filename(fname, ".db", bdir, rdir)
        if not b_file.is_file():
            raise FileNotFoundError(f"Missing backup DB file: {fname}")
        if _sha256_file(b_file) != entry["sha256"]:
            raise ValueError(f"SHA-256 checksum mismatch for backup DB: {fname}")
        validated_dbs.append((fname, b_file, r_file))

    validated_cfgs: list[tuple[str, Path, Path]] = []
    for entry in manifest.get("configs", []):
        fname = str(entry["file"])
        b_file, r_file = _validate_manifest_filename(fname, ".tenant.json", bdir, rdir)
        if not b_file.is_file() or _sha256_file(b_file) != entry["sha256"]:
            raise ValueError(f"Backup config missing or checksum mismatch: {fname}")
        validated_cfgs.append((fname, b_file, r_file))

    # Phase 2: Stage all restored DBs and configs in an isolated sibling directory
    rdir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{rdir.name}.restore-", dir=str(rdir.parent)))
    _chmod_safe(staging, 0o700)
    restored_dbs: list[str] = []
    restored_cfgs: list[str] = []
    integrity_results: dict[str, str] = {}

    try:
        for fname, b_file, _r_file in validated_dbs:
            staged_db = staging / fname
            integrity = _sqlite_online_backup(b_file, staged_db)
            if integrity.lower() != "ok":
                raise RuntimeError(f"Restored DB failed integrity check: {fname} ({integrity})")
            restored_dbs.append(fname)
            integrity_results[fname] = integrity

        for fname, b_file, _r_file in validated_cfgs:
            staged_cfg = staging / fname
            shutil.copy2(b_file, staged_cfg)
            _chmod_safe(staged_cfg, 0o600)
            restored_cfgs.append(fname)

        # Phase 3: Promote verified files atomically and purge stale -wal/-shm sidecars
        rdir.mkdir(parents=True, exist_ok=True)
        _chmod_safe(rdir, 0o700)
        for fname, _b_file, r_file in validated_dbs:
            _purge_sqlite_sidecars(r_file)
            os.replace(staging / fname, r_file)
            _chmod_safe(r_file, 0o600)
        for fname, _b_file, r_file in validated_cfgs:
            os.replace(staging / fname, r_file)
            _chmod_safe(r_file, 0o600)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    return {
        "ok": True,
        "backup_dir": str(bdir),
        "restore_dir": str(rdir),
        "databases_restored": restored_dbs,
        "configs_restored": restored_cfgs,
        "integrity_checks": integrity_results,
        "checksums_verified": len(restored_dbs) + len(restored_cfgs),
    }


__all__ = [
    "PilotAKillSwitchError",
    "backup_tenant_directory",
    "enforce_pilot_a_kill_switch",
    "is_pilot_a_kill_switch_active",
    "restore_tenant_directory",
]
