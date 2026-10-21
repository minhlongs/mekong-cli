"""Git initialization, integrity verification, and telemetry finalization tasks."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess

from .models import BootstrapContext

logger = logging.getLogger(__name__)


def task_init_git(context: BootstrapContext) -> None:
    """Initialize git repository and .gitignore (optional task)."""
    git_bin = shutil.which("git")
    target_resolved = context.target_path.resolve()
    git_dir = target_resolved / ".git"

    if git_bin and not git_dir.exists() and not context.dry_run:
        context.metadata["git_dir_created_by_us"] = True
        try:
            subprocess.run(
                [git_bin, "init", str(target_resolved)],
                capture_output=True,
                check=False,
                timeout=10,
            )
        except Exception as exc:
            logger.warning("Git initialization failed: %s", exc)

    gitignore_content = """__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.env
.venv/
env/
venv/
.mekong/
"""
    context.write_file(".gitignore", gitignore_content)


def task_verify_integrity(context: BootstrapContext) -> None:
    """Verify integrity of all created files and valid JSON formatting."""
    if context.dry_run:
        return

    target_resolved = context.target_path.resolve()
    for rel_f in context.created_files:
        f_path = (target_resolved / rel_f).resolve()
        if not f_path.is_file():
            raise RuntimeError(f"Integrity check failed: file missing: {rel_f}")

        if f_path.stat().st_size == 0 and not rel_f.endswith("__init__.py"):
            raise RuntimeError(f"Integrity check failed: empty file: {rel_f}")

        if rel_f.endswith(".json"):
            try:
                json.loads(f_path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise RuntimeError(
                    f"Integrity check failed: malformed JSON in {rel_f}: {exc}"
                )


def task_finalize_telemetry(context: BootstrapContext) -> None:
    """Calculate execution timings and construct metadata summary."""
    stats = {
        "files_created": len(context.created_files),
        "directories_created": len(context.created_directories),
        "files_overwritten": len(context.overwritten_files),
        "profile": context.profile,
        "template": context.template,
        "workers": context.workers,
    }
    context.metadata["result_stats"] = stats
