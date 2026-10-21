"""Checkpoint snapshot capture logic for CheckpointStore."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from pathlib import Path
import subprocess
import time
from typing import Any, Optional
import uuid

from .constants import _utc_now_iso
from .models import MissionStatus
from .store_schema import CheckpointStoreBase

logger = logging.getLogger(__name__)


def capture_checkpoint_impl(
    store: CheckpointStoreBase,
    mission_id: str,
    label: str,
    task_id: Optional[str] = None,
    phase: str = "post_execute",
    files: Optional[list[str | Path]] = None,
    test_results: Optional[dict[str, Any]] = None,
    project_root: Optional[Path] = None,
) -> str:
    """Capture atomic checkpoint with file snapshots and task states."""
    root = Path(project_root or Path.cwd()).resolve()
    now = _utc_now_iso()
    cp_id = f"cp_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    with store._connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO missions (
                mission_id, goal, status, cycle, max_cycles, plan_json,
                created_at, updated_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mission_id,
                f"Mission {mission_id}",
                MissionStatus.CREATED.value,
                1,
                3,
                "{}",
                now,
                now,
                "{}",
            ),
        )

        m_cur = conn.execute(
            "SELECT cycle FROM missions WHERE mission_id = ?", (mission_id,)
        ).fetchone()
        cycle = m_cur["cycle"] if m_cur else 1

        t_rows = conn.execute(
            "SELECT task_id, status FROM tasks WHERE mission_id = ?", (mission_id,)
        ).fetchall()
        task_states = {row["task_id"]: row["status"] for row in t_rows}

        conn.execute(
            """
            INSERT INTO checkpoints (
                checkpoint_id, mission_id, task_id, cycle, phase,
                label, task_states, test_results, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cp_id,
                mission_id,
                task_id,
                cycle,
                phase,
                label,
                json.dumps(task_states),
                json.dumps(test_results or {}),
                now,
            ),
        )

        resolved_files: set[Path] = set()
        if files is not None:
            for f in files:
                p = Path(f)
                full_p = (p if p.is_absolute() else root / p).resolve()
                if full_p.is_file():
                    resolved_files.add(full_p)
        else:
            if (root / ".git").exists():
                try:
                    git_res = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=root,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if git_res.returncode == 0:
                        for line in git_res.stdout.splitlines():
                            line = line.strip()
                            if len(line) > 3:
                                rel = line[3:].strip()
                                if any(
                                    rel.startswith(ign)
                                    for ign in (
                                        ".git",
                                        ".mekong",
                                        ".pytest_cache",
                                        "__pycache__",
                                    )
                                ):
                                    continue
                                target = (root / rel).resolve()
                                if target.is_file():
                                    resolved_files.add(target)
                except Exception as exc:
                    logger.debug("Failed git status discovery for checkpoint: %s", exc)

        for file_path in resolved_files:
            try:
                rel_path = file_path.relative_to(root).as_posix()
            except ValueError:
                rel_path = file_path.name

            raw_bytes = file_path.read_bytes()
            sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
            size_bytes = len(raw_bytes)

            is_text = True
            content_str = ""
            try:
                if b"\x00" in raw_bytes[:4096]:
                    is_text = False
                else:
                    content_str = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                is_text = False

            if is_text:
                content_type = "utf-8"
            else:
                content_type = "base64"
                content_str = base64.b64encode(raw_bytes).decode("ascii")

            conn.execute(
                """
                INSERT INTO file_snapshots (
                    checkpoint_id, relative_path, sha256,
                    content_type, content, size_bytes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cp_id,
                    rel_path,
                    sha256_hash,
                    content_type,
                    content_str,
                    size_bytes,
                    now,
                ),
            )

        conn.commit()

    return cp_id
