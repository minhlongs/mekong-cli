"""Status inspection and parallel bootstrap entrypoint."""

from __future__ import annotations

from pathlib import Path
import sys
import time
from typing import Any, Optional

from .dag_builder import _resolve_fn, build_bootstrap_dag
from .models import BootstrapContext, BootstrapResult, CyclicDependencyError
from .rollback import rollback_context
from .worker_pool import execute_tasks_parallel

_LAST_BOOTSTRAP_RESULT: Optional[BootstrapResult] = None


def get_bootstrap_status() -> dict[str, Any]:
    """Retrieve current bootstrap engine status and last execution result."""
    pkg = sys.modules.get("src.core.bootstrap_parallel_engine")
    last = getattr(pkg, "_LAST_BOOTSTRAP_RESULT", _LAST_BOOTSTRAP_RESULT) if pkg else _LAST_BOOTSTRAP_RESULT
    if last is None:
        return {
            "status": "idle",
            "last_run": None,
            "version": "1.0.0",
            "supported_profiles": ["smoke", "standard", "full"],
            "supported_templates": ["default", "vas", "fintech", "agent"],
        }
    return {
        "status": "success" if last.ok else "failed",
        "last_run": last.to_dict(),
        "version": "1.0.0",
        "supported_profiles": ["smoke", "standard", "full"],
        "supported_templates": ["default", "vas", "fintech", "agent"],
    }


def execute_bootstrap_parallel(
    goal: str = "",
    target_path: Optional[Path | str] = None,
    workers: int = 4,
    profile: str = "standard",
    template: str = "default",
    dry_run: bool = False,
    force: bool = False,
) -> BootstrapResult:
    """Execute parallel project bootstrap with multi-worker DAG orchestration."""
    global _LAST_BOOTSTRAP_RESULT

    if target_path is None:
        target_path = Path.cwd()
    elif isinstance(target_path, str):
        target_path = Path(target_path)
    target_path = target_path.resolve()

    norm_profile = profile.lower()
    if norm_profile == "minimal":
        norm_profile = "smoke"
    valid_profiles = {"smoke", "standard", "full"}
    if norm_profile not in valid_profiles:
        raise ValueError(
            f"Unknown profile '{profile}'. Expected one of: {', '.join(sorted(valid_profiles))}"
        )

    norm_template = template.lower()
    valid_templates = {"default", "vas", "fintech", "agent"}
    if norm_template not in valid_templates:
        raise ValueError(
            f"Unknown template '{template}'. Expected one of: {', '.join(sorted(valid_templates))}"
        )

    context = BootstrapContext(
        target_path=target_path,
        profile=norm_profile,
        template=norm_template,
        workers=max(1, workers),
        dry_run=dry_run,
        force=force,
        metadata={"goal": goal},
    )

    _resolve_fn("task_validate_workspace")(context)

    tasks = build_bootstrap_dag(context)
    start_time = time.time()

    success = False
    rolled_back = False
    error_msg: Optional[str] = None

    try:
        success = execute_tasks_parallel(tasks, context)
        if not success:
            error_msg = "; ".join(context.errors) if context.errors else "Bootstrap task failed"
            rollback_context(context)
            rolled_back = True
    except CyclicDependencyError:
        rollback_context(context)
        rolled_back = True
        raise
    except Exception as exc:
        error_msg = str(exc)
        rollback_context(context)
        rolled_back = True
        success = False

    duration_ms = round((time.time() - start_time) * 1000, 2)
    result = BootstrapResult(
        ok=success,
        rolled_back=rolled_back,
        error=error_msg,
        target_path=target_path,
        profile=norm_profile,
        template=norm_template,
        workers=workers,
        dry_run=dry_run,
        created_files=list(context.created_files),
        created_directories=list(context.created_directories),
        task_timings=dict(context.task_timings),
        duration_ms=duration_ms,
        stats=dict(context.metadata.get("result_stats", {})),
    )

    _LAST_BOOTSTRAP_RESULT = result
    pkg = sys.modules.get("src.core.bootstrap_parallel_engine")
    if pkg is not None:
        setattr(pkg, "_LAST_BOOTSTRAP_RESULT", result)
    return result
