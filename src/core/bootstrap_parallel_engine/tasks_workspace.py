"""Workspace validation, pre-state snapshot, directory, and governance scaffolding tasks."""

from __future__ import annotations

import json
import os
from pathlib import Path
import time

from .fallback_configs import (
    FALLBACK_AGENTS_MD,
    FALLBACK_GEMINI_MD,
    FALLBACK_HARNESS_MD,
    PROTECTED_SYSTEM_DIRS,
)
from .fallback_scripts import (
    FALLBACK_ENV_EXAMPLE,
    FALLBACK_LICENSE,
    FALLBACK_PYPROJECT_TOML,
)
from .graph import _find_asset_sources
from .models import BootstrapContext


def task_validate_workspace(context: BootstrapContext) -> None:
    """Validate target path security, boundary containment, and protected paths."""
    target = context.target_path
    target_resolved = target.resolve()
    target_str = str(target).rstrip(os.sep) or os.sep
    resolved_str = str(target_resolved).rstrip(os.sep) or os.sep

    if (
        target_str.lower() in PROTECTED_SYSTEM_DIRS
        or resolved_str.lower() in PROTECTED_SYSTEM_DIRS
        or target_resolved.parent == target_resolved
    ):
        raise ValueError(
            f"Refusing to scaffold into protected system directory: {target}"
        )

    if target_resolved.exists() and not target_resolved.is_dir():
        raise ValueError(f"Target path exists and is not a directory: {target}")


def task_snapshot_prestate(context: BootstrapContext) -> None:
    """Snapshot pre-execution workspace state before any mutations."""
    target_resolved = context.target_path.resolve()
    target_existed = target_resolved.exists()

    context.metadata["target_existed_before"] = target_existed
    if not target_existed:
        context.metadata["target_was_created_by_us"] = True
        if not context.dry_run:
            target_resolved.mkdir(parents=True, exist_ok=True)
    else:
        context.metadata["target_was_created_by_us"] = False


def task_scaffold_directories(context: BootstrapContext) -> None:
    """Register and create directory hierarchy."""
    directories = [
        "src",
        "tests",
        ".agents/skills",
        ".agents/subagents",
        ".agents/subagents/definitions",
        "dna",
        "reports",
        "scripts/hooks",
        ".mekong",
    ]
    for rel_d in directories:
        context.register_dir(rel_d)


def task_scaffold_governance(context: BootstrapContext) -> None:
    """Scaffold governance rules, runtime contracts, and build configuration."""
    sources = _find_asset_sources()

    if sources["gemini_md"] and Path(sources["gemini_md"]).is_file():
        gemini_text = Path(sources["gemini_md"]).read_text(encoding="utf-8")
    else:
        gemini_text = FALLBACK_GEMINI_MD
    context.write_file("GEMINI.md", gemini_text)

    dev_root = Path(__file__).resolve().parents[3]
    if (dev_root / "AGENTS.md").is_file():
        agents_text = (dev_root / "AGENTS.md").read_text(encoding="utf-8")
    else:
        agents_text = FALLBACK_AGENTS_MD
    context.write_file("AGENTS.md", agents_text)

    if sources["harness_md"] and Path(sources["harness_md"]).is_file():
        harness_text = Path(sources["harness_md"]).read_text(encoding="utf-8")
    else:
        harness_text = FALLBACK_HARNESS_MD
    context.write_file("HARNESS.md", harness_text)

    context.write_file("pyproject.toml", FALLBACK_PYPROJECT_TOML)
    context.write_file(".env.example", FALLBACK_ENV_EXAMPLE)
    context.write_file("LICENSE", FALLBACK_LICENSE)

    dna_content = json.dumps(
        {
            "schema": "mekong.dna.v1",
            "name": "mekong-app",
            "profile": context.profile,
            "template": context.template,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        indent=2,
    ) + "\n"
    context.write_file("dna/core-dna.json", dna_content)
