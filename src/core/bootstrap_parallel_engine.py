# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Parallel Project Bootstrap Engine.

Pure Python standard library implementation (strictly no external vendor SDKs,
no third-party HTTP libraries, no YAML). Provides multi-worker topological
DAG orchestration, workspace scaffolding (skills, subagents, governance
contracts, directory hierarchy, domain templates), atomic checkpointing &
rollback upon task failure, and execution telemetry.
"""

from __future__ import annotations

import concurrent.futures
import dataclasses
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from . import (
    CORE_6_AGENTS,
    CORE_SKILLS,
    FALLBACK_AGENTS_MD,
    FALLBACK_ENV_EXAMPLE,
    FALLBACK_GEMINI_MD,
    FALLBACK_HARNESS_MD,
    FALLBACK_HOOKS_JSON,
    FALLBACK_LICENSE,
    FALLBACK_MCP_CONFIG_JSON,
    FALLBACK_MCP_SERVER_PY,
    FALLBACK_POST_TOOL_AUDIT_PY,
    FALLBACK_PRE_TOOL_GUARDRAIL_PY,
    FALLBACK_PYPROJECT_TOML,
    FULL_25_AGENTS,
    PROTECTED_SYSTEM_DIRS,
    BootstrapContext,
    BootstrapResult,
    BootstrapTask,
    CyclicDependencyError,
    TaskStatus,
    TaskTiming,
    _LAST_BOOTSTRAP_RESULT,
    _find_asset_sources,
    build_bootstrap_dag,
    execute_bootstrap_parallel,
    execute_tasks_parallel,
    get_bootstrap_status,
    resolve_dag,
    resolve_dag_dependencies,
    rollback_context,
    task_finalize_telemetry,
    task_init_git,
    task_scaffold_directories,
    task_scaffold_governance,
    task_scaffold_hooks,
    task_scaffold_mcp,
    task_scaffold_skills,
    task_scaffold_subagents,
    task_scaffold_templates,
    task_snapshot_prestate,
    task_validate_workspace,
    task_verify_integrity,
)

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
    "concurrent",
    "dataclasses",
    "dataclass",
    "field",
    "Enum",
    "hashlib",
    "json",
    "logging",
    "os",
    "Path",
    "shutil",
    "stat",
    "subprocess",
    "sys",
    "tempfile",
    "threading",
    "time",
    "Any",
    "Callable",
    "Dict",
    "List",
    "Optional",
    "Set",
    "Tuple",
]
