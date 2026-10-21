"""DAG builder and dynamic function lookup for the parallel bootstrap engine."""

from __future__ import annotations

import sys
from typing import Any, Callable

from .models import BootstrapContext, BootstrapTask
from .tasks_agents_mcp import (
    task_scaffold_hooks,
    task_scaffold_mcp,
    task_scaffold_skills,
    task_scaffold_subagents,
)
from .tasks_templates import task_scaffold_templates
from .tasks_verify import (
    task_finalize_telemetry,
    task_init_git,
    task_verify_integrity,
)
from .tasks_workspace import (
    task_scaffold_directories,
    task_scaffold_governance,
    task_snapshot_prestate,
    task_validate_workspace,
)

_DEFAULT_TASK_FNS: dict[str, Callable[[BootstrapContext], Any]] = {
    "task_validate_workspace": task_validate_workspace,
    "task_snapshot_prestate": task_snapshot_prestate,
    "task_scaffold_directories": task_scaffold_directories,
    "task_scaffold_governance": task_scaffold_governance,
    "task_scaffold_subagents": task_scaffold_subagents,
    "task_scaffold_skills": task_scaffold_skills,
    "task_scaffold_mcp": task_scaffold_mcp,
    "task_scaffold_hooks": task_scaffold_hooks,
    "task_scaffold_templates": task_scaffold_templates,
    "task_init_git": task_init_git,
    "task_verify_integrity": task_verify_integrity,
    "task_finalize_telemetry": task_finalize_telemetry,
}


def _resolve_fn(attr_name: str) -> Callable[[BootstrapContext], Any]:
    pkg = sys.modules.get("src.core.bootstrap_parallel_engine")
    if pkg is not None and hasattr(pkg, attr_name):
        return getattr(pkg, attr_name)
    return _DEFAULT_TASK_FNS[attr_name]


def build_bootstrap_dag(context: BootstrapContext) -> list[BootstrapTask]:
    """Construct standard topological DAG of bootstrap tasks."""
    return [
        BootstrapTask(
            id="validate_workspace",
            name="Validate Workspace Security",
            dependencies=[],
            action=_resolve_fn("task_validate_workspace"),
        ),
        BootstrapTask(
            id="snapshot_prestate",
            name="Snapshot Pre-Execution State",
            dependencies=["validate_workspace"],
            action=_resolve_fn("task_snapshot_prestate"),
        ),
        BootstrapTask(
            id="scaffold_directories",
            name="Scaffold Directory Structure",
            dependencies=["snapshot_prestate"],
            action=_resolve_fn("task_scaffold_directories"),
        ),
        BootstrapTask(
            id="scaffold_governance",
            name="Scaffold Governance Contracts",
            dependencies=["scaffold_directories"],
            action=_resolve_fn("task_scaffold_governance"),
        ),
        BootstrapTask(
            id="scaffold_subagents",
            name="Scaffold Subagent Catalogs",
            dependencies=["scaffold_directories"],
            action=_resolve_fn("task_scaffold_subagents"),
        ),
        BootstrapTask(
            id="scaffold_skills",
            name="Scaffold Antigravity Skills",
            dependencies=["scaffold_directories", "scaffold_subagents"],
            action=_resolve_fn("task_scaffold_skills"),
        ),
        BootstrapTask(
            id="scaffold_mcp",
            name="Scaffold MCP Configurations",
            dependencies=["scaffold_directories"],
            action=_resolve_fn("task_scaffold_mcp"),
        ),
        BootstrapTask(
            id="scaffold_hooks",
            name="Scaffold Lifecycle Safety Hooks",
            dependencies=["scaffold_directories"],
            action=_resolve_fn("task_scaffold_hooks"),
        ),
        BootstrapTask(
            id="scaffold_templates",
            name="Scaffold Domain Template",
            dependencies=["scaffold_governance", "scaffold_directories"],
            action=_resolve_fn("task_scaffold_templates"),
        ),
        BootstrapTask(
            id="init_git",
            name="Initialize Git Repository",
            dependencies=["scaffold_governance"],
            action=_resolve_fn("task_init_git"),
            optional=True,
        ),
        BootstrapTask(
            id="verify_integrity",
            name="Verify Scaffolding Integrity",
            dependencies=[
                "scaffold_governance",
                "scaffold_subagents",
                "scaffold_skills",
                "scaffold_mcp",
                "scaffold_hooks",
                "scaffold_templates",
            ],
            action=_resolve_fn("task_verify_integrity"),
        ),
        BootstrapTask(
            id="finalize_telemetry",
            name="Finalize Execution Telemetry",
            dependencies=["verify_integrity"],
            action=_resolve_fn("task_finalize_telemetry"),
        ),
    ]
