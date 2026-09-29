# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
core/worktree_manager.py — Isolated Git Worktree Mesh.

Manages isolated git worktrees for parallel agent swarms and multi-branch
development, eliminating checkout and staging conflicts.
Pure Python standard library with zero external dependencies.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class WorktreeRecord:
    """Normalized git worktree record."""

    path: str
    commit: str
    branch: str
    bare: bool = False
    locked: bool = False
    lock_reason: str = ""
    prunable: bool = False
    prune_reason: str = ""
    is_main: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "commit": self.commit,
            "branch": self.branch,
            "bare": self.bare,
            "locked": self.locked,
            "lock_reason": self.lock_reason,
            "prunable": self.prunable,
            "prune_reason": self.prune_reason,
            "is_main": self.is_main,
        }


def slugify(text: str, max_length: int = 50) -> str:
    """Convert input string to a clean kebab-case branch/worktree slug."""
    # Strip extensions like .py, .ts, etc.
    cleaned = re.sub(r"\.[a-zA-Z0-9]+$", "", text.strip())
    # Replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", cleaned).strip("-").lower()
    if not slug:
        slug = "feature"
    return slug[:max_length].rstrip("-")


def detect_prefix(description: str) -> str:
    """Auto-detect branch prefix type from description keywords."""
    desc_lower = description.lower()
    if any(k in desc_lower for k in ("fix", "bug", "issue", "error", "patch", "hotfix", "fail")):
        return "fix"
    if any(k in desc_lower for k in ("refactor", "cleanup", "restructure", "rewrite", "simplify")):
        return "refactor"
    if any(k in desc_lower for k in ("doc", "docs", "readme", "guide", "manual")):
        return "docs"
    if any(k in desc_lower for k in ("test", "spec", "eval", "benchmark", "chaos")):
        return "test"
    if any(k in desc_lower for k in ("perf", "optimize", "speed", "latency", "scale")):
        return "perf"
    if any(k in desc_lower for k in ("chore", "deps", "bump", "dependency")):
        return "chore"
    return "feat"


class WorktreeManager:
    """Core manager for Git worktrees and parallel workspace isolation."""

    def __init__(self, repo_dir: str | Path | None = None) -> None:
        self.repo_dir = Path(repo_dir or os.getcwd()).resolve()

    def _run_git(
        self,
        args: list[str],
        cwd: Path | None = None,
        timeout: int = 60,
    ) -> tuple[int, str, str]:
        """Execute a git command and return (returncode, stdout, stderr)."""
        target_cwd = cwd or self.repo_dir
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=target_cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as exc:
            return 1, "", str(exc)

    def get_repo_info(self) -> dict[str, Any]:
        """Inspect repository topology, root path, base branch, and dirty status."""
        code, root_out, err = self._run_git(["rev-parse", "--show-toplevel"])
        if code != 0:
            return {
                "ok": False,
                "error": err or f"Not a git repository: {self.repo_dir}",
                "repo_path": str(self.repo_dir),
            }

        repo_root = Path(root_out).resolve()
        _, curr_branch, _ = self._run_git(["branch", "--show-current"], cwd=repo_root)

        # Detect base branch: priority main -> master -> dev -> develop -> current
        base_branch = "main"
        code, branches_out, _ = self._run_git(["branch", "--list"], cwd=repo_root)
        local_branches = [
            b.strip().lstrip("* ").strip()
            for b in branches_out.split("\n")
            if b.strip()
        ]

        if "main" in local_branches:
            base_branch = "main"
        elif "master" in local_branches:
            base_branch = "master"
        elif "develop" in local_branches:
            base_branch = "develop"
        elif "dev" in local_branches:
            base_branch = "dev"
        elif curr_branch:
            base_branch = curr_branch

        # Check dirty files
        _, status_out, _ = self._run_git(["status", "--porcelain"], cwd=repo_root)
        dirty_files = [line.strip().split()[-1] for line in status_out.split("\n") if line.strip()]

        worktree_root = repo_root.parent / f"{repo_root.name}-worktrees"

        return {
            "ok": True,
            "repo_path": str(repo_root),
            "current_branch": curr_branch,
            "base_branch": base_branch,
            "dirty": bool(dirty_files),
            "dirty_count": len(dirty_files),
            "dirty_files": dirty_files[:20],
            "worktree_root": str(worktree_root),
        }

    def list_worktrees(self) -> list[WorktreeRecord]:
        """List all registered git worktrees using git worktree list --porcelain."""
        code, out, _ = self._run_git(["worktree", "list", "--porcelain"])
        if code != 0 or not out:
            return []

        info = self.get_repo_info()
        main_root = info.get("repo_path", str(self.repo_dir))

        records: list[WorktreeRecord] = []
        blocks = out.split("\n\n")

        for block in blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            if not lines:
                continue

            path = ""
            commit = ""
            branch = ""
            bare = False
            locked = False
            lock_reason = ""
            prunable = False
            prune_reason = ""

            for line in lines:
                if line.startswith("worktree "):
                    path = line[9:].strip()
                elif line.startswith("HEAD "):
                    commit = line[5:].strip()
                elif line.startswith("branch "):
                    ref = line[7:].strip()
                    # Strip refs/heads/ prefix
                    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
                elif line == "bare":
                    bare = True
                elif line.startswith("locked"):
                    locked = True
                    lock_reason = line[6:].strip()
                elif line.startswith("prunable"):
                    prunable = True
                    prune_reason = line[8:].strip()
                elif line == "detached":
                    branch = "HEAD (detached)"

            if path:
                is_main = os.path.realpath(path) == os.path.realpath(main_root)
                records.append(
                    WorktreeRecord(
                        path=path,
                        commit=commit,
                        branch=branch,
                        bare=bare,
                        locked=locked,
                        lock_reason=lock_reason,
                        prunable=prunable,
                        prune_reason=prune_reason,
                        is_main=is_main,
                    )
                )

        return records

    def create_worktree(
        self,
        feature: str,
        prefix: str | None = None,
        base_branch: str | None = None,
        no_prefix: bool = False,
        worktree_root: str | None = None,
        dry_run: bool = False,
    ) -> WorktreeRecord:
        """Create a new isolated git worktree branching from the specified base branch."""
        info = self.get_repo_info()
        if not info.get("ok"):
            raise RuntimeError(info.get("error", "Not a git repository"))

        repo_root = Path(info["repo_path"])
        base = base_branch or info.get("base_branch", "main")

        # Determine branch name and directory slug
        feature_clean = feature.strip()
        if no_prefix:
            branch_name = feature_clean
            dir_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", feature_clean).strip("-").lower()
        else:
            resolved_prefix = prefix or detect_prefix(feature_clean)
            slug = slugify(feature_clean)
            if slug.startswith(f"{resolved_prefix}-"):
                slug = slug[len(resolved_prefix) + 1 :]
            if not slug:
                slug = "task"
            branch_name = f"{resolved_prefix}/{slug}"
            dir_slug = f"{resolved_prefix}-{slug}"

        # Determine worktree destination path
        if worktree_root:
            target_path = Path(worktree_root).resolve() / dir_slug
        else:
            # Sibling to the current repository
            target_path = repo_root.parent / f"{repo_root.name}-{dir_slug}"

        if dry_run:
            return WorktreeRecord(
                path=str(target_path),
                commit="DRY_RUN",
                branch=branch_name,
                is_main=False,
            )

        if target_path.exists():
            raise FileExistsError(f"Target worktree directory already exists: {target_path}")

        # Check if branch already exists
        code, _, _ = self._run_git(["rev-parse", "--verify", branch_name], cwd=repo_root)
        branch_exists = (code == 0)

        # Run git worktree add
        # If branch already exists, attach to it; otherwise create branch -b
        if branch_exists:
            cmd = ["worktree", "add", str(target_path), branch_name]
        else:
            cmd = ["worktree", "add", "-b", branch_name, str(target_path), base]

        add_code, add_out, add_err = self._run_git(cmd, cwd=repo_root)
        if add_code != 0:
            raise RuntimeError(f"Failed to create worktree: {add_err or add_out}")

        # Automatically copy .env*.example to .env in the new worktree if found
        for cand in repo_root.glob(".env*.example"):
            dest_env = target_path / ".env"
            if not dest_env.exists():
                try:
                    shutil.copy2(cand, dest_env)
                except Exception:
                    pass
                break

        # Get HEAD commit of new worktree
        _, head_commit, _ = self._run_git(["rev-parse", "HEAD"], cwd=target_path)

        return WorktreeRecord(
            path=str(target_path),
            commit=head_commit or "HEAD",
            branch=branch_name,
            is_main=False,
        )

    def remove_worktree(
        self,
        path_or_name: str,
        force: bool = False,
    ) -> bool:
        """Remove a git worktree by path, branch name, or directory basename."""
        records = self.list_worktrees()
        target_record: WorktreeRecord | None = None

        search = path_or_name.strip()
        search_path = os.path.realpath(search)

        for rec in records:
            if rec.is_main:
                continue
            if os.path.realpath(rec.path) == search_path:
                target_record = rec
                break
            if rec.branch == search or rec.branch.endswith(f"/{search}"):
                target_record = rec
                break
            if Path(rec.path).name == search:
                target_record = rec
                break

        if target_record is None:
            raise ValueError(f"Worktree not found matching: '{path_or_name}'")

        cmd = ["worktree", "remove", target_record.path]
        if force:
            cmd.append("--force")

        code, out, err = self._run_git(cmd)
        if code != 0:
            if force:
                # Force cleanup directory if git refuses
                p = Path(target_record.path)
                if p.exists():
                    shutil.rmtree(p, ignore_errors=True)
                self.prune_worktrees()
                return True
            raise RuntimeError(f"Failed to remove worktree: {err or out}")

        return True

    def prune_worktrees(self, dry_run: bool = False) -> list[str]:
        """Prune stale worktree administrative tracking files."""
        cmd = ["worktree", "prune"]
        if dry_run:
            cmd.append("--dry-run")
            cmd.append("-v")

        code, out, _ = self._run_git(cmd)
        if code != 0:
            return []
        lines = [line.strip() for line in out.split("\n") if line.strip()]
        return lines

    def status(self, path_or_branch: str | None = None) -> dict[str, Any]:
        """Evaluate worktree health, uncommitted status, and branch divergence."""
        records = self.list_worktrees()
        if not records:
            return {"ok": False, "error": "No worktrees found"}

        target = records[0]
        if path_or_branch:
            matched = False
            search = path_or_branch.strip()
            search_path = os.path.realpath(search)
            for r in records:
                if os.path.realpath(r.path) == search_path or r.branch == search or Path(r.path).name == search:
                    target = r
                    matched = True
                    break
            if not matched:
                return {"ok": False, "error": f"Worktree '{path_or_branch}' not found"}

        target_path = Path(target.path)
        if not target_path.exists():
            return {
                "ok": True,
                "worktree": target.to_dict(),
                "exists": False,
                "status": "missing_directory",
            }

        _, status_out, _ = self._run_git(["status", "--porcelain"], cwd=target_path)
        dirty_files = [line.strip().split()[-1] for line in status_out.split("\n") if line.strip()]

        info = self.get_repo_info()
        base = info.get("base_branch", "main")

        # Compare commit divergence against base
        _, ahead_behind, _ = self._run_git(
            ["rev-list", "--left-right", "--count", f"{base}...{target.commit}"],
            cwd=target_path,
        )
        behind, ahead = 0, 0
        if ahead_behind and "\t" in ahead_behind:
            parts = ahead_behind.split("\t")
            try:
                behind, ahead = int(parts[0]), int(parts[1])
            except ValueError:
                pass

        return {
            "ok": True,
            "worktree": target.to_dict(),
            "exists": True,
            "dirty": bool(dirty_files),
            "dirty_count": len(dirty_files),
            "dirty_files": dirty_files,
            "base_branch": base,
            "ahead": ahead,
            "behind": behind,
            "all_worktrees_count": len(records),
        }


_worktree_manager_instance: WorktreeManager | None = None


def get_worktree_manager(repo_dir: str | Path | None = None) -> WorktreeManager:
    """Return the WorktreeManager singleton instance."""
    global _worktree_manager_instance
    if _worktree_manager_instance is None or repo_dir is not None:
        _worktree_manager_instance = WorktreeManager(repo_dir=repo_dir)
    return _worktree_manager_instance


__all__ = [
    "WorktreeManager",
    "WorktreeRecord",
    "detect_prefix",
    "get_worktree_manager",
    "slugify",
]
