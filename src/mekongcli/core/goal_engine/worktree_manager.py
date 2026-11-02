# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Isolated git worktree lifecycle manager and path confinement guard (G5 / F02)."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

_SAFE_SEGMENT_RE = re.compile(r"[^a-zA-Z0-9._-]+")
_IGNORED_SEED_NAMES = frozenset({
    ".git",
    ".mekong",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
})


class WorktreeEscapeError(PermissionError):
    """Raised when a mutating worker attempts to escape its isolated worktree."""


class WorktreeMode(str, Enum):
    """Canonical 3-state worktree lifecycle mode."""

    SCRATCH = "SCRATCH"
    ARTIFACT = "ARTIFACT"
    RECOVERY = "RECOVERY"


@dataclass
class ArtifactRecord:
    """Cryptographically verified artifact record harvested from an isolated worktree."""

    ticket_id: str
    task_id: str
    attempt_id: str
    artifact_type: str
    safe_ref: str
    sha256: str
    verification_status: str
    created_at: float = field(default_factory=time.time)
    relative_path: str = ""
    size_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "artifact_type": self.artifact_type,
            "safe_ref": self.safe_ref,
            "sha256": self.sha256,
            "verification_status": self.verification_status,
            "created_at": self.created_at,
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
        }


@dataclass
class WorktreeFinalizationResult:
    """Result of finalizing an isolated worktree through SCRATCH, ARTIFACT, or RECOVERY."""

    mode: WorktreeMode
    cleaned_up: bool
    preserved_path: Path | None = None
    artifact_dir: Path | None = None
    manifest_path: Path | None = None
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "cleaned_up": self.cleaned_up,
            "preserved_path": str(self.preserved_path) if self.preserved_path else None,
            "artifact_dir": str(self.artifact_dir) if self.artifact_dir else None,
            "manifest_path": str(self.manifest_path) if self.manifest_path else None,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "reason": self.reason,
        }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class WorktreeIsolationManager:
    """Manages isolated worktrees, SHA-256 artifact harvesting, and recovery preservation."""

    _git_lock = threading.RLock()

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.worktrees_dir = self.repo_root / ".mekong" / "worktrees"
        self.artifacts_dir = self.repo_root / ".mekong" / "artifacts"
        self.recovery_dir = self.repo_root / ".mekong" / "recovery_worktrees"
        self._active_worktrees: dict[Path, dict[str, Any]] = {}

    @staticmethod
    def _sanitize_segment(raw: str) -> str:
        cleaned = _SAFE_SEGMENT_RE.sub("_", (raw or "").strip()).strip("._-")
        return cleaned[:64] or "wt"

    def worktree_path_for(self, ticket_id: str, task_id: str) -> Path:
        safe_ticket = self._sanitize_segment(ticket_id)
        safe_task = self._sanitize_segment(task_id)
        return (self.worktrees_dir / f"{safe_ticket}_{safe_task}").resolve()

    def _snapshot_tree_hashes(self, root: Path) -> dict[str, str]:
        snapshot: dict[str, str] = {}
        if not root.exists():
            return snapshot
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            rel_parts = path.relative_to(root).parts
            if any(part in _IGNORED_SEED_NAMES for part in rel_parts):
                continue
            rel = path.relative_to(root).as_posix()
            try:
                snapshot[rel] = _sha256_file(path)
            except OSError:
                continue
        return snapshot

    def _seed_fallback_worktree(self, wt_path: Path) -> None:
        """Copy top-level workspace files into a non-git fallback worktree."""
        wt_path.mkdir(parents=True, exist_ok=True)
        for child in self.repo_root.iterdir():
            if child.name in _IGNORED_SEED_NAMES or child.is_symlink():
                continue
            dest = wt_path / child.name
            try:
                if child.is_file():
                    shutil.copy2(child, dest)
                elif child.is_dir():
                    shutil.copytree(
                        child,
                        dest,
                        symlinks=False,
                        ignore=shutil.ignore_patterns(*_IGNORED_SEED_NAMES),
                        dirs_exist_ok=True,
                    )
            except OSError:
                continue

    def allocate(self, ticket_id: str, task_id: str, *, attempt_no: int = 1) -> Path:
        """Create an isolated worktree directory for ``(ticket_id, task_id)``."""
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)
        wt_path = self.worktree_path_for(ticket_id, task_id)
        if wt_path.exists():
            self.cleanup(wt_path)

        git_dir = self.repo_root / ".git"
        used_git = False
        if git_dir.exists():
            with self._git_lock:
                res = subprocess.run(
                    ["git", "worktree", "add", "--detach", str(wt_path), "HEAD"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if res.returncode == 0 and wt_path.exists():
                    used_git = True

        if not used_git:
            self._seed_fallback_worktree(wt_path)

        resolved_wt = wt_path.resolve()
        with self._git_lock:
            self._active_worktrees[resolved_wt] = {
                "ticket_id": ticket_id,
                "task_id": task_id,
                "attempt_no": max(1, int(attempt_no)),
                "created_at": time.time(),
                "used_git": used_git,
                "baseline_hashes": self._snapshot_tree_hashes(resolved_wt),
            }
        return resolved_wt

    def has_uncommitted_or_new_changes(self, wt_path: Path) -> bool:
        """Return True if files in ``wt_path`` were created or modified since allocation."""
        resolved_wt = wt_path.resolve()
        if not resolved_wt.exists():
            return False
        meta = self._active_worktrees.get(resolved_wt, {})
        baseline: dict[str, str] = meta.get("baseline_hashes") or {}
        current = self._snapshot_tree_hashes(resolved_wt)
        if current != baseline:
            return True
        if (resolved_wt / ".git").exists():
            with self._git_lock:
                res = subprocess.run(
                    ["git", "status", "--porcelain=v1"],
                    cwd=resolved_wt,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if res.returncode == 0 and bool(res.stdout.strip()):
                    return True
        return False

    def harvest_artifacts(
        self,
        wt_path: Path,
        *,
        ticket_id: str | None = None,
        task_id: str | None = None,
        attempt_no: int | None = None,
        verification_status: str = "VERIFIED_SUCCESS",
    ) -> tuple[Path, Path, list[ArtifactRecord]]:
        """Harvest modified/created files and git diff patch into ``.mekong/artifacts/`` with SHA-256 verification."""
        resolved_wt = wt_path.resolve()
        self.assert_path_confined(resolved_wt, self.worktrees_dir)
        if not resolved_wt.exists():
            raise FileNotFoundError(f"Worktree does not exist: {resolved_wt}")

        meta = self._active_worktrees.get(resolved_wt, {})
        eff_ticket = str(ticket_id or meta.get("ticket_id") or "ticket")
        eff_task = str(task_id or meta.get("task_id") or resolved_wt.name)
        eff_attempt = int(attempt_no if attempt_no is not None else meta.get("attempt_no", 1))
        attempt_id = f"attempt_{max(1, eff_attempt)}"

        safe_ticket = self._sanitize_segment(eff_ticket)
        safe_task = self._sanitize_segment(eff_task)
        dest_dir = (self.artifacts_dir / safe_ticket / safe_task / attempt_id).resolve()
        self.assert_path_confined(dest_dir, self.artifacts_dir.resolve() if self.artifacts_dir.exists() else (self.repo_root / ".mekong"))
        dest_dir.mkdir(parents=True, exist_ok=True)

        baseline: dict[str, str] = meta.get("baseline_hashes") or {}
        current = self._snapshot_tree_hashes(resolved_wt)

        changed_rel_paths: list[str] = [
            rel for rel, digest in sorted(current.items())
            if baseline.get(rel) != digest
        ]
        # If no baseline was captured or caller harvested explicitly on a populated dir, include all non-ignored files
        if not changed_rel_paths and not baseline:
            changed_rel_paths = sorted(current.keys())

        records: list[ArtifactRecord] = []
        created_ts = time.time()
        files_root = dest_dir / "files"

        for rel in changed_rel_paths:
            src_file = (resolved_wt / rel).resolve()
            self.assert_path_confined(src_file, resolved_wt)
            if not src_file.is_file() or src_file.is_symlink():
                continue
            src_hash = _sha256_file(src_file)
            dst_file = (files_root / rel).resolve()
            self.assert_path_confined(dst_file, dest_dir)
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)

            if not dst_file.exists():
                raise RuntimeError(f"Artifact destination missing after copy: {dst_file}")
            dst_hash = _sha256_file(dst_file)
            if dst_hash != src_hash:
                raise RuntimeError(
                    f"Artifact SHA-256 mismatch for {rel}: expected {src_hash}, got {dst_hash}"
                )

            rel_to_repo = dst_file.relative_to(self.repo_root).as_posix()
            records.append(
                ArtifactRecord(
                    ticket_id=eff_ticket,
                    task_id=eff_task,
                    attempt_id=attempt_id,
                    artifact_type="workspace_file",
                    safe_ref=rel_to_repo,
                    sha256=dst_hash,
                    verification_status=verification_status,
                    created_at=created_ts,
                    relative_path=rel,
                    size_bytes=dst_file.stat().st_size,
                )
            )

        # Also capture git diff patch when running inside a git worktree
        if (resolved_wt / ".git").exists():
            with self._git_lock:
                diff_res = subprocess.run(
                    ["git", "diff", "HEAD"],
                    cwd=resolved_wt,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            if diff_res.returncode == 0 and diff_res.stdout.strip():
                patch_path = (dest_dir / "changes.patch").resolve()
                patch_path.write_text(diff_res.stdout, encoding="utf-8")
                patch_hash = _sha256_file(patch_path)
                records.append(
                    ArtifactRecord(
                        ticket_id=eff_ticket,
                        task_id=eff_task,
                        attempt_id=attempt_id,
                        artifact_type="git_diff_patch",
                        safe_ref=patch_path.relative_to(self.repo_root).as_posix(),
                        sha256=patch_hash,
                        verification_status=verification_status,
                        created_at=created_ts,
                        relative_path="changes.patch",
                        size_bytes=patch_path.stat().st_size,
                    )
                )

        manifest_path = (dest_dir / "manifest.json").resolve()
        manifest_payload = {
            "schema": "mekong.worktree.artifact_manifest.v1",
            "ticket_id": eff_ticket,
            "task_id": eff_task,
            "attempt_id": attempt_id,
            "verification_status": verification_status,
            "created_at": created_ts,
            "artifact_count": len(records),
            "artifacts": [r.to_dict() for r in records],
        }
        manifest_path.write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return dest_dir, manifest_path, records

    def preserve_recovery_worktree(
        self,
        wt_path: Path,
        *,
        ticket_id: str | None = None,
        task_id: str | None = None,
        attempt_no: int | None = None,
        reason: str = "execution_failed",
    ) -> Path:
        """Preserve a dirty, failed, or uncertain worktree under ``.mekong/recovery_worktrees/`` without overwriting prior attempts."""
        resolved_wt = wt_path.resolve()
        self.assert_path_confined(resolved_wt, self.worktrees_dir)
        if not resolved_wt.exists():
            raise FileNotFoundError(f"Cannot preserve missing worktree: {resolved_wt}")

        meta = self._active_worktrees.get(resolved_wt, {})
        eff_ticket = str(ticket_id or meta.get("ticket_id") or "ticket")
        eff_task = str(task_id or meta.get("task_id") or resolved_wt.name)
        eff_attempt = int(attempt_no if attempt_no is not None else meta.get("attempt_no", 1))

        safe_ticket = self._sanitize_segment(eff_ticket)
        safe_task = self._sanitize_segment(eff_task)
        self.recovery_dir.mkdir(parents=True, exist_ok=True)

        base_name = f"{safe_ticket}_{safe_task}_attempt_{max(1, eff_attempt)}"
        candidate = (self.recovery_dir / base_name).resolve()
        collision_idx = 1
        while candidate.exists():
            collision_idx += 1
            candidate = (self.recovery_dir / f"{base_name}_{collision_idx}").resolve()

        shutil.copytree(
            resolved_wt,
            candidate,
            symlinks=False,
            ignore=shutil.ignore_patterns(".git"),
        )
        recovery_manifest = {
            "schema": "mekong.worktree.recovery_manifest.v1",
            "ticket_id": eff_ticket,
            "task_id": eff_task,
            "attempt_no": max(1, eff_attempt),
            "reason": reason,
            "source_worktree": str(resolved_wt),
            "preserved_at": time.time(),
            "files": self._snapshot_tree_hashes(candidate),
        }
        (candidate / "recovery_manifest.json").write_text(
            json.dumps(recovery_manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        # Detach and remove the active worktree slot after recovery copy is verified on disk
        self.cleanup(resolved_wt)
        return candidate

    def finalize_worktree(
        self,
        wt_path: Path,
        *,
        mode: WorktreeMode | str | None = None,
        ticket_id: str | None = None,
        task_id: str | None = None,
        attempt_no: int | None = None,
        success: bool = True,
        verification_status: str = "VERIFIED_SUCCESS",
        side_effect_uncertain: bool = False,
        reason: str | None = None,
    ) -> WorktreeFinalizationResult:
        """Finalize worktree according to the 3-state SCRATCH / ARTIFACT / RECOVERY lifecycle."""
        resolved_wt = wt_path.resolve()
        if not resolved_wt.exists():
            return WorktreeFinalizationResult(
                mode=WorktreeMode.SCRATCH,
                cleaned_up=True,
                reason="already_cleaned",
            )

        resolved_mode: WorktreeMode
        if isinstance(mode, WorktreeMode):
            resolved_mode = mode
        elif isinstance(mode, str) and mode.upper() in WorktreeMode._value2member_map_:
            resolved_mode = WorktreeMode(mode.upper())
        elif not success or side_effect_uncertain:
            resolved_mode = WorktreeMode.RECOVERY
        elif self.has_uncommitted_or_new_changes(resolved_wt):
            resolved_mode = WorktreeMode.ARTIFACT
        else:
            resolved_mode = WorktreeMode.SCRATCH

        if not success or side_effect_uncertain or resolved_mode == WorktreeMode.RECOVERY:
            rec_reason = reason or (
                "side_effect_uncertain" if side_effect_uncertain else "execution_or_verification_failed"
            )
            preserved = self.preserve_recovery_worktree(
                resolved_wt,
                ticket_id=ticket_id,
                task_id=task_id,
                attempt_no=attempt_no,
                reason=rec_reason,
            )
            return WorktreeFinalizationResult(
                mode=WorktreeMode.RECOVERY,
                cleaned_up=False,
                preserved_path=preserved,
                reason=rec_reason,
            )

        if resolved_mode == WorktreeMode.ARTIFACT:
            try:
                art_dir, manifest_path, records = self.harvest_artifacts(
                    resolved_wt,
                    ticket_id=ticket_id,
                    task_id=task_id,
                    attempt_no=attempt_no,
                    verification_status=verification_status,
                )
            except Exception as exc:
                preserved = self.preserve_recovery_worktree(
                    resolved_wt,
                    ticket_id=ticket_id,
                    task_id=task_id,
                    attempt_no=attempt_no,
                    reason=f"artifact_harvest_failed:{exc}",
                )
                return WorktreeFinalizationResult(
                    mode=WorktreeMode.RECOVERY,
                    cleaned_up=False,
                    preserved_path=preserved,
                    reason=f"artifact_harvest_failed:{exc}",
                )
            self.cleanup(resolved_wt)
            return WorktreeFinalizationResult(
                mode=WorktreeMode.ARTIFACT,
                cleaned_up=True,
                artifact_dir=art_dir,
                manifest_path=manifest_path,
                artifacts=records,
                reason=reason,
            )

        self.cleanup(resolved_wt)
        return WorktreeFinalizationResult(
            mode=WorktreeMode.SCRATCH,
            cleaned_up=True,
            reason=reason,
        )

    def cleanup(
        self,
        wt_path: Path,
        *,
        expected_owner: tuple[str, str] | None = None,
    ) -> bool:
        """Clean up an isolated worktree safely, idempotently, and with ownership checks."""
        resolved_wt = wt_path.resolve()
        self.assert_path_confined(resolved_wt, self.worktrees_dir)

        with self._git_lock:
            meta = self._active_worktrees.get(resolved_wt)
            if expected_owner is not None and meta is not None:
                actual_owner = (str(meta.get("ticket_id")), str(meta.get("task_id")))
                if actual_owner != (str(expected_owner[0]), str(expected_owner[1])):
                    raise PermissionError(
                        f"Worktree ownership mismatch for {resolved_wt}: "
                        f"expected {expected_owner}, owned by {actual_owner}"
                    )

            if not resolved_wt.exists():
                self._active_worktrees.pop(resolved_wt, None)
                return False

            if (self.repo_root / ".git").exists():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(resolved_wt)],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            if resolved_wt.exists():
                shutil.rmtree(resolved_wt, ignore_errors=True)
            self._active_worktrees.pop(resolved_wt, None)
            return True

    def list_artifacts(self, ticket_id: str | None = None) -> list[dict[str, Any]]:
        """Return all harvested artifact manifests (optionally filtered by ``ticket_id``)."""
        if not self.artifacts_dir.exists():
            return []
        manifests: list[dict[str, Any]] = []
        search_root = (
            self.artifacts_dir / self._sanitize_segment(ticket_id)
            if ticket_id is not None
            else self.artifacts_dir
        )
        if not search_root.exists():
            return []
        for mf in sorted(search_root.rglob("manifest.json")):
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                if ticket_id is None or data.get("ticket_id") == ticket_id:
                    manifests.append(data)
            except (OSError, json.JSONDecodeError):
                continue
        return manifests

    @staticmethod
    def assert_path_confined(candidate: Path, allowed_root: Path) -> Path:
        """Verify ``candidate`` resolves strictly inside ``allowed_root`` (symlink-aware)."""
        resolved_root = allowed_root.resolve()
        resolved_candidate = candidate.resolve()
        if (
            resolved_candidate != resolved_root
            and resolved_root not in resolved_candidate.parents
        ):
            raise WorktreeEscapeError(
                f"Path '{candidate}' (resolved: '{resolved_candidate}') escapes worktree root '{resolved_root}'"
            )
        return resolved_candidate

    @classmethod
    def validate_path_within_worktree(cls, worktree_root: Path, target_path: str | Path) -> Path:
        """Resolve ``target_path`` relative to ``worktree_root`` and verify it remains strictly confined."""
        resolved_root = worktree_root.resolve()
        candidate = (resolved_root / target_path).resolve()
        return cls.assert_path_confined(candidate, resolved_root)

    @classmethod
    def assert_command_confined(cls, command: str, worktree_root: Path) -> None:
        """Inspect command tokens for path traversal or absolute paths outside ``worktree_root``."""
        import shlex

        resolved_root = worktree_root.resolve()
        try:
            tokens = shlex.split(command)
        except ValueError as exc:
            raise WorktreeEscapeError(f"Malformed command syntax: {exc}") from exc

        allowed_system_prefixes = (
            "/bin/",
            "/usr/bin/",
            "/usr/local/bin/",
            "/opt/homebrew/bin/",
            "/dev/null",
        )

        for idx, tok in enumerate(tokens):
            clean_tok = tok.lstrip(">").lstrip("<")
            if "=" in clean_tok and not clean_tok.startswith("/"):
                _, clean_tok = clean_tok.split("=", 1)

            if ".." in Path(clean_tok).parts:
                candidate = (resolved_root / clean_tok).resolve()
                cls.assert_path_confined(candidate, resolved_root)
            elif clean_tok.startswith("/"):
                if idx == 0 and any(clean_tok.startswith(p) for p in allowed_system_prefixes):
                    continue
                if clean_tok == "/dev/null":
                    continue
                candidate = Path(clean_tok)
                cls.assert_path_confined(candidate, resolved_root)
            else:
                local_path = resolved_root / clean_tok
                if local_path.exists() or local_path.is_symlink():
                    cls.assert_path_confined(local_path, resolved_root)
