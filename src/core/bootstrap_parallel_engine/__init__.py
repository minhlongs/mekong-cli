"""Autonomous Parallel Project Bootstrap Engine Package."""

from __future__ import annotations

from .catalog_agents import CORE_6_AGENTS, FULL_25_AGENTS
from .catalog_skills import CORE_SKILLS
from .engine import (
    _LAST_BOOTSTRAP_RESULT,
    build_bootstrap_dag,
    execute_bootstrap_parallel,
    get_bootstrap_status,
)
from .fallback_configs import (
    FALLBACK_AGENTS_MD,
    FALLBACK_GEMINI_MD,
    FALLBACK_HARNESS_MD,
    FALLBACK_HOOKS_JSON,
    FALLBACK_MCP_CONFIG_JSON,
    PROTECTED_SYSTEM_DIRS,
)
from .fallback_scripts import (
    FALLBACK_ENV_EXAMPLE,
    FALLBACK_LICENSE,
    FALLBACK_MCP_SERVER_PY,
    FALLBACK_POST_TOOL_AUDIT_PY,
    FALLBACK_PRE_TOOL_GUARDRAIL_PY,
    FALLBACK_PYPROJECT_TOML,
)
from .graph import _find_asset_sources, resolve_dag, resolve_dag_dependencies
from .models import (
    BootstrapContext,
    BootstrapResult,
    BootstrapTask,
    CyclicDependencyError,
    TaskStatus,
    TaskTiming,
)
from .rollback import rollback_context
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
from .worker_pool import execute_tasks_parallel

__all__ = [
    "BootstrapContext",
    "BootstrapResult",
    "BootstrapTask",
    "CORE_6_AGENTS",
    "CORE_SKILLS",
    "CyclicDependencyError",
    "FALLBACK_AGENTS_MD",
    "FALLBACK_ENV_EXAMPLE",
    "FALLBACK_GEMINI_MD",
    "FALLBACK_HARNESS_MD",
    "FALLBACK_HOOKS_JSON",
    "FALLBACK_LICENSE",
    "FALLBACK_MCP_CONFIG_JSON",
    "FALLBACK_MCP_SERVER_PY",
    "FALLBACK_POST_TOOL_AUDIT_PY",
    "FALLBACK_PRE_TOOL_GUARDRAIL_PY",
    "FALLBACK_PYPROJECT_TOML",
    "FULL_25_AGENTS",
    "PROTECTED_SYSTEM_DIRS",
    "TaskStatus",
    "TaskTiming",
    "_LAST_BOOTSTRAP_RESULT",
    "_find_asset_sources",
    "build_bootstrap_dag",
    "execute_bootstrap_parallel",
    "execute_tasks_parallel",
    "get_bootstrap_status",
    "resolve_dag",
    "resolve_dag_dependencies",
    "rollback_context",
    "task_finalize_telemetry",
    "task_init_git",
    "task_scaffold_directories",
    "task_scaffold_governance",
    "task_scaffold_hooks",
    "task_scaffold_mcp",
    "task_scaffold_skills",
    "task_scaffold_subagents",
    "task_scaffold_templates",
    "task_snapshot_prestate",
    "task_validate_workspace",
    "task_verify_integrity",
]
