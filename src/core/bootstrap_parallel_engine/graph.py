"""Topological DAG dependency resolution and asset source discovery."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .models import BootstrapTask, CyclicDependencyError


def resolve_dag_dependencies(tasks: list[BootstrapTask]) -> list[str]:
    """Topologically sort tasks and verify absence of cycles using Kahn's algorithm."""
    task_map = {t.id: t for t in tasks}
    for t in tasks:
        for dep in t.dependencies:
            if dep not in task_map:
                raise ValueError(
                    f"Task '{t.id}' references unknown dependency '{dep}'"
                )

    in_degree: dict[str, int] = {t.id: len(t.dependencies) for t in tasks}
    dependents: dict[str, list[str]] = {t.id: [] for t in tasks}
    for t in tasks:
        for dep in t.dependencies:
            dependents[dep].append(t.id)

    queue: list[str] = [t.id for t in tasks if in_degree[t.id] == 0]
    sorted_order: list[str] = []

    while queue:
        node = queue.pop(0)
        sorted_order.append(node)
        for m in dependents[node]:
            in_degree[m] -= 1
            if in_degree[m] == 0:
                queue.append(m)

    if len(sorted_order) < len(tasks):
        unvisited = [t.id for t in tasks if in_degree[t.id] > 0]
        raise CyclicDependencyError(
            f"Cyclic dependency detected among tasks: {', '.join(sorted(unvisited))}"
        )

    return sorted_order


resolve_dag = resolve_dag_dependencies


def _find_asset_sources() -> dict[str, Any]:
    """Locate source assets using discovery hierarchy."""
    candidate_roots: list[Path] = []

    env_root = os.environ.get("MEKONG_ROOT")
    if env_root:
        candidate_roots.append(Path(env_root).resolve())

    dev_root = Path(__file__).resolve().parents[3]
    candidate_roots.append(dev_root)

    home = Path.home()
    candidate_roots.append(home / ".gemini" / "config" / "plugins" / "mekong-cli")
    candidate_roots.append(home / ".gemini" / "antigravity-cli" / "plugins" / "mekong-cli")

    assets: dict[str, Any] = {
        "skills_dir": None,
        "subagents_dir": None,
        "hooks_json": None,
        "hooks_scripts_dir": None,
        "mcp_config_json": None,
        "mcp_server_script": None,
        "gemini_md": None,
        "harness_md": None,
    }

    for root in candidate_roots:
        if not root.is_dir():
            continue

        if assets["skills_dir"] is None:
            if (root / ".agents" / "skills").is_dir():
                assets["skills_dir"] = (root / ".agents" / "skills").resolve()
            elif (root / "skills").is_dir():
                assets["skills_dir"] = (root / "skills").resolve()

        if assets["subagents_dir"] is None:
            if (root / ".agents" / "subagents").is_dir():
                assets["subagents_dir"] = (root / ".agents" / "subagents").resolve()
            elif (root / "subagents").is_dir():
                assets["subagents_dir"] = (root / "subagents").resolve()

        if assets["hooks_json"] is None:
            if (root / ".agents" / "hooks.json").is_file():
                assets["hooks_json"] = (root / ".agents" / "hooks.json").resolve()
            elif (root / "hooks.json").is_file():
                assets["hooks_json"] = (root / "hooks.json").resolve()

        if assets["hooks_scripts_dir"] is None:
            if (root / "scripts" / "hooks").is_dir():
                assets["hooks_scripts_dir"] = (root / "scripts" / "hooks").resolve()

        if assets["mcp_config_json"] is None:
            if (root / ".agents" / "mcp_config.json").is_file():
                assets["mcp_config_json"] = (root / ".agents" / "mcp_config.json").resolve()
            elif (root / "mcp_config.json").is_file():
                assets["mcp_config_json"] = (root / "mcp_config.json").resolve()

        if assets["mcp_server_script"] is None:
            if (root / "scripts" / "mcp_server.py").is_file():
                assets["mcp_server_script"] = (root / "scripts" / "mcp_server.py").resolve()

        if assets["gemini_md"] is None:
            if (root / "GEMINI.md").is_file():
                assets["gemini_md"] = (root / "GEMINI.md").resolve()
            elif (root / "rules" / "GEMINI.md").is_file():
                assets["gemini_md"] = (root / "rules" / "GEMINI.md").resolve()

        if assets["harness_md"] is None:
            if (root / "HARNESS.md").is_file():
                assets["harness_md"] = (root / "HARNESS.md").resolve()
            elif (root / "rules" / "HARNESS.md").is_file():
                assets["harness_md"] = (root / "rules" / "HARNESS.md").resolve()

    return assets
