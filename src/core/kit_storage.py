# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""AgentKit storage and file ownership management.

Standardizes storage locations and permissions following the AgentKit architecture:
- Global config directory: ~/.mekong (mode 0700)
- Auth session file: ~/.mekong/auth/session.json (mode 0600, schema-v2)
- Project-level file ownership tracking: .mekong/ownership.json (SHA-256 tracking)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import stat
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "schema-v2"


class KitStorageError(Exception):
    """Base error for kit storage operations."""


def get_global_mekong_dir() -> Path:
    """Return the canonical global mekong home path ~/.mekong, ensuring 0700 mode."""
    home = Path.home()
    global_dir = home / ".mekong"
    if not global_dir.exists():
        global_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    # Ensure permissions are strictly 0700
    try:
        os.chmod(global_dir, stat.S_IRWXU)
    except OSError as exc:
        logger.warning("Could not set 0700 permissions on %s: %s", global_dir, exc)
    return global_dir


def get_auth_session_path() -> Path:
    """Return canonical path to ~/.mekong/auth/session.json, ensuring directory exists."""
    global_dir = get_global_mekong_dir()
    auth_dir = global_dir / "auth"
    if not auth_dir.exists():
        auth_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    try:
        os.chmod(auth_dir, stat.S_IRWXU)
    except OSError:
        pass
    return auth_dir / "session.json"


def save_auth_session(
    token_or_payload: Dict[str, Any],
    principal: str = "default",
    metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """Save auth session payload to ~/.mekong/auth/session.json with strict 0600 mode and schema-v2."""
    session_path = get_auth_session_path()
    data = {
        "version": SCHEMA_VERSION,
        "principal": principal,
        "session": token_or_payload,
        "metadata": metadata or {},
    }
    content = json.dumps(data, indent=2, ensure_ascii=False)

    # Atomic write with 0600 permissions
    temp_path = session_path.with_suffix(".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    mode = stat.S_IRUSR | stat.S_IWUSR  # 0600
    fd = os.open(str(temp_path), flags, mode)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(str(temp_path), str(session_path))
    except Exception as exc:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise KitStorageError(f"Failed to write auth session: {exc}") from exc

    # Guarantee 0600 mode
    try:
        os.chmod(session_path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass

    return session_path


def load_auth_session() -> Optional[Dict[str, Any]]:
    """Load auth session from ~/.mekong/auth/session.json if present and valid."""
    session_path = get_auth_session_path()
    if not session_path.is_file():
        return None
    try:
        with open(session_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data.get("version") == SCHEMA_VERSION:
            return data
        # Fallback or upgrade older schema
        return {"version": SCHEMA_VERSION, "session": data}
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to parse auth session file %s: %s", session_path, exc)
        return None


class OwnershipLedger:
    """Tracks project file ownership and SHA-256 integrity in .mekong/ownership.json."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root_dir = (root_dir or Path.cwd()).resolve()
        self.mekong_dir = self.root_dir / ".mekong"
        self.ownership_file = self.mekong_dir / "ownership.json"
        self._records: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.ownership_file.is_file():
            self._records = {}
            return
        try:
            with open(self.ownership_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._records = data.get("files", {}) if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            self._records = {}

    def _save(self) -> None:
        self.mekong_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": SCHEMA_VERSION,
            "files": self._records,
        }
        temp_file = self.ownership_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        temp_file.replace(self.ownership_file)

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Calculate SHA-256 of file contents."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _resolve_safe_path(self, rel_path: str) -> Path:
        """Resolve rel_path and ensure it stays strictly inside self.root_dir."""
        rel = Path(rel_path)
        if rel.is_absolute() or ".." in rel.parts:
            raise KitStorageError(f"Path traversal blocked: '{rel_path}' is outside workspace root")
        target = (self.root_dir / rel).resolve()
        try:
            target.relative_to(self.root_dir)
        except ValueError as exc:
            raise KitStorageError(
                f"Path traversal blocked: '{rel_path}' resolves outside {self.root_dir}"
            ) from exc
        return target

    def register_file(self, rel_path: str, owner: str = "agentkit") -> None:
        """Register a file's SHA-256 and ownership."""
        target = self._resolve_safe_path(rel_path)
        if not target.is_file():
            raise FileNotFoundError(f"File not found: {rel_path}")
        sha = self.compute_sha256(target)
        self._records[rel_path] = {
            "owner": owner,
            "sha256": sha,
            "size": target.stat().st_size,
        }
        self._save()

    def check_integrity(self, rel_path: str) -> bool:
        """Check if file matches stored SHA-256. Returns True if matching, False if modified or absent."""
        rec = self._records.get(rel_path)
        if not rec:
            return False
        try:
            target = self._resolve_safe_path(rel_path)
        except KitStorageError:
            return False
        if not target.is_file():
            return False
        return self.compute_sha256(target) == rec.get("sha256")

    def get_ownership(self, rel_path: str) -> Optional[str]:
        """Return owner identifier for a registered file."""
        rec = self._records.get(rel_path)
        return rec.get("owner") if rec else None

    def list_tracked(self) -> List[str]:
        """List relative paths of all tracked files."""
        return sorted(self._records.keys())


__all__ = [
    "SCHEMA_VERSION",
    "KitStorageError",
    "get_global_mekong_dir",
    "get_auth_session_path",
    "save_auth_session",
    "load_auth_session",
    "OwnershipLedger",
]
