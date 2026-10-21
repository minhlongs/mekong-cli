"""Atomic checkpoint and workspace rollback mechanics for bootstrap engine."""

from __future__ import annotations

import shutil

from .models import BootstrapContext


def rollback_context(context: BootstrapContext) -> list[str]:
    """Execute atomic rollback restoring workspace to exact pre-execution state."""
    reverted_paths: list[str] = []
    with context.lock:
        if context.dry_run:
            return reverted_paths

        target_resolved = context.target_path.resolve()

        if context.metadata.get("git_dir_created_by_us", False):
            git_dir = target_resolved / ".git"
            if git_dir.is_dir():
                try:
                    shutil.rmtree(git_dir, ignore_errors=True)
                except OSError:
                    pass

        for rel_file in reversed(context.created_files):
            if rel_file in context.overwritten_files:
                continue
            file_path = (target_resolved / rel_file).resolve()
            if file_path.is_file():
                try:
                    file_path.unlink()
                    reverted_paths.append(rel_file)
                except OSError:
                    pass

        for rel_file, orig_content in context.overwritten_files.items():
            file_path = (target_resolved / rel_file).resolve()
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(orig_content, encoding="utf-8")
                reverted_paths.append(rel_file)
            except OSError:
                pass

        for rel_dir in reversed(context.created_directories):
            dir_path = (target_resolved / rel_dir).resolve()
            if dir_path.is_dir():
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                except OSError:
                    pass

        for rel_file in reversed(context.created_files):
            file_path = (target_resolved / rel_file).resolve()
            parent = file_path.parent
            while parent != target_resolved and parent.is_relative_to(target_resolved):
                if parent.is_dir():
                    try:
                        if not any(parent.iterdir()):
                            parent.rmdir()
                        else:
                            break
                    except OSError:
                        break
                parent = parent.parent

        if context.metadata.get("target_was_created_by_us", False):
            if target_resolved.is_dir():
                try:
                    if not any(target_resolved.iterdir()):
                        target_resolved.rmdir()
                except OSError:
                    pass

    return reverted_paths
