"""Subagent, skill, MCP, and hook scaffolding tasks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog_agents import CORE_6_AGENTS, FULL_25_AGENTS
from .catalog_skills import CORE_SKILLS
from .fallback_configs import FALLBACK_HOOKS_JSON, FALLBACK_MCP_CONFIG_JSON
from .fallback_scripts import (
    FALLBACK_MCP_SERVER_PY,
    FALLBACK_POST_TOOL_AUDIT_PY,
    FALLBACK_PRE_TOOL_GUARDRAIL_PY,
)
from .graph import _find_asset_sources
from .models import BootstrapContext


def task_scaffold_subagents(context: BootstrapContext) -> None:
    """Scaffold subagent registry and markdown definitions based on profile."""
    sources = _find_asset_sources()
    subagents_dir = sources["subagents_dir"]

    agents_to_scaffold: list[dict[str, Any]] = []
    if context.profile in ("smoke", "minimal"):
        agents_to_scaffold = CORE_6_AGENTS
    else:
        agents_to_scaffold = FULL_25_AGENTS

    source_defs_dir = (Path(subagents_dir) / "definitions") if subagents_dir else None

    reg_data = {
        "schema": "antigravity.subagents.registry.v1",
        "total_agents": len(agents_to_scaffold),
        "agents": agents_to_scaffold,
    }
    context.write_file(
        ".agents/subagents/registry.json",
        json.dumps(reg_data, indent=2) + "\n",
    )

    for ag in agents_to_scaffold:
        ag_id = ag["id"]
        rel_def_path = f".agents/subagents/definitions/{ag_id}.md"

        def_content: str = ""
        if source_defs_dir and (source_defs_dir / f"{ag_id}.md").is_file():
            try:
                def_content = (source_defs_dir / f"{ag_id}.md").read_text(encoding="utf-8")
            except Exception:
                def_content = ""

        if not def_content:
            def_content = f"""# Subagent: {ag['name']}
- **Role**: {ag['role']}
- **Description**: {ag['description']}
- **Context Budget**: {ag['context_budget']} tokens
- **Model Tier**: {ag['model_tier']}

## Tools
{chr(10).join(f"- `{t}`" for t in ag['tools'])}
"""
        context.write_file(rel_def_path, def_content)


def task_scaffold_skills(context: BootstrapContext) -> None:
    """Scaffold native Antigravity skills."""
    sources = _find_asset_sources()
    skills_dir = sources["skills_dir"]

    selected_skills = CORE_SKILLS
    if context.profile in ("smoke", "minimal"):
        selected_skills = CORE_SKILLS[:12]

    skills_map = {name: desc for name, desc in selected_skills}

    if skills_dir and Path(skills_dir).is_dir():
        for item in sorted(Path(skills_dir).iterdir()):
            if item.is_dir() and (item / "SKILL.md").is_file():
                if context.profile in ("smoke", "minimal") and item.name not in skills_map:
                    continue
                try:
                    content = (item / "SKILL.md").read_text(encoding="utf-8")
                    context.write_file(f".agents/skills/{item.name}/SKILL.md", content)
                    skills_map[item.name] = "Discovered skill"
                except Exception:
                    pass

    for skill_name, desc in selected_skills:
        skill_path = f".agents/skills/{skill_name}/SKILL.md"
        if skill_path not in context.created_files:
            fallback_skill = f"""---
name: {skill_name}
description: {desc}
---

# /{skill_name}

{desc}

## Usage
`mekong {skill_name}`
"""
            context.write_file(skill_path, fallback_skill)


def task_scaffold_mcp(context: BootstrapContext) -> None:
    """Scaffold MCP configuration and server script."""
    sources = _find_asset_sources()

    if sources["mcp_config_json"] and Path(sources["mcp_config_json"]).is_file():
        mcp_cfg_text = Path(sources["mcp_config_json"]).read_text(encoding="utf-8")
    else:
        mcp_cfg_text = FALLBACK_MCP_CONFIG_JSON
    context.write_file(".agents/mcp_config.json", mcp_cfg_text)

    if sources["mcp_server_script"] and Path(sources["mcp_server_script"]).is_file():
        mcp_srv_text = Path(sources["mcp_server_script"]).read_text(encoding="utf-8")
    else:
        mcp_srv_text = FALLBACK_MCP_SERVER_PY
    context.write_file("scripts/mcp_server.py", mcp_srv_text)


def task_scaffold_hooks(context: BootstrapContext) -> None:
    """Scaffold lifecycle safety hooks configuration and scripts."""
    sources = _find_asset_sources()

    if sources["hooks_json"] and Path(sources["hooks_json"]).is_file():
        hooks_cfg_text = Path(sources["hooks_json"]).read_text(encoding="utf-8")
    else:
        hooks_cfg_text = FALLBACK_HOOKS_JSON
    context.write_file(".agents/hooks.json", hooks_cfg_text)

    hooks_scripts_dir = sources["hooks_scripts_dir"]
    if hooks_scripts_dir and (Path(hooks_scripts_dir) / "pre_tool_guardrail.py").is_file():
        pre_text = (Path(hooks_scripts_dir) / "pre_tool_guardrail.py").read_text(encoding="utf-8")
    else:
        pre_text = FALLBACK_PRE_TOOL_GUARDRAIL_PY
    context.write_file("scripts/hooks/pre_tool_guardrail.py", pre_text)

    if hooks_scripts_dir and (Path(hooks_scripts_dir) / "post_tool_audit.py").is_file():
        post_text = (Path(hooks_scripts_dir) / "post_tool_audit.py").read_text(encoding="utf-8")
    else:
        post_text = FALLBACK_POST_TOOL_AUDIT_PY
    context.write_file("scripts/hooks/post_tool_audit.py", post_text)
