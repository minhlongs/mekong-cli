"""Per-user output sandbox.

Lives outside `agent_core.tools.file_system` so workers can point each job at
`outputs/{user_id}/` without mutating agent-core's module-level OUTPUTS_DIR.

Path-traversal guard via `Path.relative_to()`. No Docker isolation in Phase 2.
"""

from __future__ import annotations

from pathlib import Path


class SandboxViolation(ValueError):
    pass


def user_output_dir(base: Path, user_id: str) -> Path:
    if not user_id or "/" in user_id or ".." in user_id or "\x00" in user_id:
        raise SandboxViolation(f"invalid user_id: {user_id!r}")
    resolved_base = Path(base).resolve()
    resolved_base.mkdir(parents=True, exist_ok=True)
    target = (resolved_base / user_id).resolve()
    try:
        target.relative_to(resolved_base)
    except ValueError as exc:
        raise SandboxViolation(f"user_id escapes base: {user_id!r}") from exc
    target.mkdir(parents=True, exist_ok=True)
    return target


def resolve_under(base: Path, rel: str) -> Path:
    resolved_base = Path(base).resolve()
    target = (resolved_base / rel).resolve()
    try:
        target.relative_to(resolved_base)
    except ValueError as exc:
        raise SandboxViolation(f"path escapes base: {rel!r}") from exc
    return target
