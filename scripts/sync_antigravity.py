#!/usr/bin/env python3
# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Synchronize Mekong CLI commands, workflows, and agents into Google Antigravity.

This script materializes:
1. Native Antigravity skills at `.agents/skills/<name>/SKILL.md` (local workspace)
2. Global Antigravity skills at `~/.gemini/config/skills/<name>/SKILL.md` (machine-wide)
3. Global Antigravity plugin at `~/.gemini/config/plugins/mekong-cli/`
4. Declarative subagent specifications at `.agents/subagents/`
5. Antigravity rule configurations at `GEMINI.md`
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
USER_HOME = Path.home()

# Local workspace paths
LOCAL_AGENTS_DIR = PROJECT_ROOT / ".agents"
LOCAL_SKILLS_DIR = LOCAL_AGENTS_DIR / "skills"
LOCAL_SUBAGENTS_DIR = LOCAL_AGENTS_DIR / "subagents"
LOCAL_DEFINITIONS_DIR = LOCAL_SUBAGENTS_DIR / "definitions"

# Global machine-wide paths
GLOBAL_CONFIG_DIR = USER_HOME / ".gemini" / "config"
GLOBAL_SKILLS_DIR = GLOBAL_CONFIG_DIR / "skills"
GLOBAL_SKILLS_JSON = GLOBAL_CONFIG_DIR / "skills.json"
GLOBAL_PLUGIN_DIR = GLOBAL_CONFIG_DIR / "plugins" / "mekong-cli"
AGY_PLUGIN_DIR = USER_HOME / ".gemini" / "antigravity-cli" / "plugins" / "mekong-cli"

INTEGRATION_COMMANDS_DIR = PROJECT_ROOT / ".claude" / "_integration" / "commands"
INTEGRATION_AGENTS_DIR = PROJECT_ROOT / ".claude" / "_integration" / "agents"
REGISTRY_YAML_PATH = PROJECT_ROOT / "agents" / "registry.yaml"

GIT_HISTORIC_TREE = "2f764b9770668f2fad05bdd3ea91f4fbec7ca285"


def normalize_execution_commands(content: str) -> str:
    """Normalize command invocations from repo-specific to portable global binary `mekong`."""
    # Replace python3 -m src.main with mekong
    content = re.sub(r"python3\s+-m\s+src\.main\s+", "mekong ", content)
    content = re.sub(r"python3\s+-m\s+src\.main", "mekong", content)
    return content


def clean_frontmatter(content: str, name: str) -> str:
    """Ensure standard valid YAML frontmatter for Antigravity SKILL.md."""
    content = normalize_execution_commands(content)
    lines = content.splitlines()
    if lines and lines[0].strip() == "---":
        # Find closing ---
        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break
        if end_idx != -1:
            frontmatter_lines = lines[1:end_idx]
            body_lines = lines[end_idx + 1 :]
            # Extract description
            description = ""
            for line in frontmatter_lines:
                if line.startswith("description:"):
                    desc_val = line[len("description:") :].strip()
                    if (desc_val.startswith('"') and desc_val.endswith('"')) or (
                        desc_val.startswith("'") and desc_val.endswith("'")
                    ):
                        desc_val = desc_val[1:-1]
                    description = desc_val
                    break
            if not description:
                description = f"Execute Mekong CLI {name} workflow."

            clean_desc = description.replace('"', '\\"')
            return f"---\nname: {name}\ndescription: >-\n  {clean_desc}\n---\n\n" + "\n".join(
                body_lines
            ).strip() + "\n"

    # No frontmatter found, wrap with default
    clean_desc = f"Execute Mekong CLI {name} workflow."
    return f"---\nname: {name}\ndescription: >-\n  {clean_desc}\n---\n\n" + content.strip() + "\n"


def load_historic_workflows() -> Dict[str, str]:
    """Retrieve the 22 rich workflow files from git history."""
    workflows: Dict[str, str] = {}
    try:
        res = subprocess.run(
            ["git", "ls-tree", GIT_HISTORIC_TREE],
            capture_output=True,
            text=True,
            check=True,
            cwd=PROJECT_ROOT,
        )
        for line in res.stdout.strip().splitlines():
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 4:
                blob_hash = parts[2]
                filename = parts[3]
                if filename.endswith(".md"):
                    name = filename[:-3]
                    content_res = subprocess.run(
                        ["git", "cat-file", "-p", blob_hash],
                        capture_output=True,
                        text=True,
                        check=True,
                        cwd=PROJECT_ROOT,
                    )
                    workflows[name] = content_res.stdout
    except Exception as e:
        print(f"Warning: Could not fetch historic git workflows: {e}", file=sys.stderr)
    return workflows


def get_vietnam_funnel_skills() -> Dict[str, str]:
    """Return specialized Vietnam business funnel skills."""
    return {
        "ke-toan": """---
name: ke-toan
description: >-
  VAS Vietnamese Accounting Standard engine, TT78/2021 electronic invoices, journal entries, and XML reports.
---

# /ke-toan — Vietnam Accounting Standard (VAS) & TT78/2021

Execute Vietnamese accounting operations, TT78 electronic invoices, and VAS-compliant journal entries.

## Capabilities

- `journal`: Generate VAS compliant accounting journal entries
- `create`: Create new electronic invoice draft conforming to Circular 78/2021/TT-BTC
- `xml`: Validate or export XML invoices for General Department of Taxation (Tổng cục Thuế)
- `summary`: General ledger and tax summary

## Usage

```bash
// turbo
mekong ke-toan $ARGUMENTS
```
""",
        "thue": """---
name: thue
description: >-
  Vietnamese tax calculator for personal income tax (TNCN), corporate income tax (TNDN), and VAT (GTGT).
---

# /thue — Vietnam Tax Engine (TNCN, TNDN, GTGT)

Automated calculation engine for Vietnamese tax regulations with up-to-date progressive tax brackets.

## Sub-commands

- `tncn`: Progressive personal income tax calculation with dependent deductions
- `tndn`: Corporate income tax calculation (standard 20%, SME exemptions, incentives)
- `gtgt`: Value added tax (VAT 8%, 10%) calculation and deduction reconciliation

## Usage

```bash
// turbo
mekong thue $ARGUMENTS
```
""",
        "zalo-oa": """---
name: zalo-oa
description: >-
  Zalo Official Account (OA) integration for customer messaging, followers, templates, and broadcast campaigns.
---

# /zalo-oa — Zalo Official Account Suite

Engage Vietnamese customers via Zalo Official Account API.

## Sub-commands

- `broadcast`: Broadcast messages to followers
- `send`: Direct message to customer phone / user ID
- `followers`: Retrieve and sync follower demographics
- `caption`: Generate Vietnamese marketing captions for Zalo posts
- `post`: Publish article or status update to Zalo feed

## Usage

```bash
// turbo
mekong zalo-oa $ARGUMENTS
```
""",
    }


def build_all_skills() -> Dict[str, str]:
    """Compile all skills into memory as {name: formatted_markdown}."""
    skills: Dict[str, str] = {}

    # 1. Historic rich workflows
    historic_workflows = load_historic_workflows()
    for name, content in historic_workflows.items():
        skills[name] = clean_frontmatter(content, name)

    # 2. Vietnam funnels
    for name, content in get_vietnam_funnel_skills().items():
        skills[name] = clean_frontmatter(content, name)

    # 3. All commands in .claude/_integration/commands/*.md
    if INTEGRATION_COMMANDS_DIR.exists():
        for cmd_path in sorted(INTEGRATION_COMMANDS_DIR.glob("*.md")):
            name = cmd_path.stem
            if name not in skills:
                raw_content = cmd_path.read_text(encoding="utf-8")
                formatted_content = clean_frontmatter(raw_content, name)
                if "```bash" not in formatted_content:
                    formatted_content += f"\n## Usage\n\n```bash\n// turbo\nmekong {name.replace('-', ' ')} $ARGUMENTS\n```\n"
                skills[name] = formatted_content

    # Ensure all skills provide portable mekong CLI invocation
    for name, content in list(skills.items()):
        if "mekong" not in content:
            skills[name] = content.rstrip() + f"\n\n## CLI Invocation\n\n```bash\n// turbo\nmekong {name.replace('-', ' ')} $ARGUMENTS\n```\n"

    return skills


def write_skills_to_dir(target_skills_dir: Path, skills: Dict[str, str]) -> int:
    """Write skill dictionary to target directory structure."""
    target_skills_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for name, content in skills.items():
        skill_folder = target_skills_dir / name
        skill_folder.mkdir(parents=True, exist_ok=True)
        skill_file = skill_folder / "SKILL.md"
        skill_file.write_text(content, encoding="utf-8")
        count += 1
    return count


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Simple parser for agents/registry.yaml without requiring PyYAML."""
    agents = []
    current_agent: Dict[str, Any] = {}

    lines = text.splitlines()
    in_agents = False

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped == "agents:":
            in_agents = True
            continue

        if stripped.startswith("delegation_rules:"):
            in_agents = False
            if current_agent:
                agents.append(current_agent)
                current_agent = {}
            break

        if in_agents:
            if stripped.startswith("- id:"):
                if current_agent:
                    agents.append(current_agent)
                current_agent = {"id": stripped[len("- id:") :].strip().strip('"').strip("'")}
            elif ":" in stripped and current_agent:
                parts = stripped.split(":", 1)
                k = parts[0].strip()
                v = parts[1].strip()
                if v.startswith("[") and v.endswith("]"):
                    items = [item.strip().strip('"').strip("'") for item in v[1:-1].split(",") if item.strip()]
                    current_agent[k] = items
                elif v.lower() == "true":
                    current_agent[k] = True
                elif v.lower() == "false":
                    current_agent[k] = False
                elif v.isdigit():
                    current_agent[k] = int(v)
                else:
                    current_agent[k] = v.strip('"').strip("'")

    if current_agent:
        agents.append(current_agent)

    return {"agents": agents}


def sync_subagents(target_subagents_dir: Path) -> int:
    """Synchronize subagent definitions into target subagents directory."""
    target_subagents_dir.mkdir(parents=True, exist_ok=True)
    definitions_dir = target_subagents_dir / "definitions"
    definitions_dir.mkdir(parents=True, exist_ok=True)

    agent_records: List[Dict[str, Any]] = []

    if REGISTRY_YAML_PATH.exists():
        raw_yaml = REGISTRY_YAML_PATH.read_text(encoding="utf-8")
        registry_data = parse_simple_yaml(raw_yaml)
        for agent in registry_data.get("agents", []):
            agent_id = agent.get("id")
            if not agent_id:
                continue

            name = agent.get("name", agent_id)
            role = agent.get("role", "General Assistant")
            desc = agent.get("description", "")
            tools = agent.get("tools", ["Read", "Write", "Bash"])
            context_budget = agent.get("context_budget", 20000)
            sop_fragments = agent.get("sop_fragments", [])
            reports_to = agent.get("reports_to", "ceo")
            can_override = agent.get("can_override", False)
            model_tier = "pro" if agent_id in {"ceo", "sun-tzu", "cto", "planner"} else "inherit"

            system_prompt = f"""You are {name}, serving as {role} in the Mekong CLI CEO Solo Harness.

Description:
{desc}

Role & Authority:
- Reports to: {reports_to}
- Override authority: {'Yes' if can_override else 'No'}
- SOP Fragments: {', '.join(sop_fragments) if sop_fragments else 'Standard'}

Guidelines:
- Follow Mekong harness engineering contracts.
- Strictly adhere to role boundaries and SOP hard gates.
- Verify work objectively before completion.
"""
            definition_file = definitions_dir / f"{agent_id}.md"
            definition_file.write_text(system_prompt, encoding="utf-8")

            record = {
                "id": agent_id,
                "name": name,
                "role": role,
                "description": desc,
                "model_tier": model_tier,
                "context_budget": context_budget,
                "tools": tools,
                "definition_path": f".agents/subagents/definitions/{agent_id}.md",
                "can_override": can_override,
            }
            agent_records.append(record)

    if INTEGRATION_AGENTS_DIR.exists():
        for agent_md in sorted(INTEGRATION_AGENTS_DIR.glob("*.md")):
            agent_id = agent_md.stem
            if not any(a["id"] == agent_id for a in agent_records):
                content = agent_md.read_text(encoding="utf-8")
                definition_file = definitions_dir / f"{agent_id}.md"
                definition_file.write_text(content, encoding="utf-8")

                agent_records.append(
                    {
                        "id": agent_id,
                        "name": agent_id.replace("-", " ").title(),
                        "role": "Specialized Agent",
                        "description": f"Specialized Mekong agent for {agent_id}.",
                        "model_tier": "flash",
                        "context_budget": 16000,
                        "tools": ["Read", "Write", "Bash"],
                        "definition_path": f".agents/subagents/definitions/{agent_id}.md",
                        "can_override": False,
                    }
                )

    registry_json_path = target_subagents_dir / "registry.json"
    registry_json_path.write_text(
        json.dumps(
            {
                "schema": "antigravity.subagents.registry.v1",
                "total_agents": len(agent_records),
                "agents": agent_records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return len(agent_records)


def get_gemini_rules_content() -> str:
    """Return GEMINI.md rules content."""
    return """# GEMINI.md — Mekong CLI Antigravity Rules
# Read by: Google Antigravity, Gemini CLI, Claude Code

## Project Overview
**Mekong CLI: CEO Solo Agentic Harness Engineering Platform.**
One CEO delegates to 4 layer agents (Business, Product, Engineering, Ops).
Embeds the Binh Pháp (Art of War) strategic execution framework for building, testing, and shipping.

## Antigravity Slash Commands (Skills)
All Mekong CLI workflows are mapped to native Antigravity skills in `.agents/skills/<name>/SKILL.md`:

| Command | Layer | Purpose |
|---------|-------|---------|
| `/cook` | Engineering | Feature development & plan execution (PEV engine) |
| `/idea` | Strategy | BizPlan OS Zero→IPO company generation |
| `/binh-phap` | Strategy | Strategic counsel via Sun Tzu agent |
| `/plan` | Product | Implementation planning (hard, fast, standard) |
| `/quick-start` | Product | 5-step project kickoff |
| `/ship` | Engineering | Lint → Test → Commit → Push → Deploy |
| `/daily` | Operations | Daily status report and git activity |
| `/cto` | Engineering | CTO architecture audit and review suite |
| `/ke-toan` | Business | VAS Vietnamese Accounting Standard & TT78 |
| `/thue` | Business | TNCN, TNDN, and GTGT tax calculation |
| `/zalo-oa` | Business | Zalo Official Account messaging & broadcast |
| `/sales` | Business | Lead outreach, deal prep, close reports |
| `/marketing`| Business | Content engine & growth campaigns |
| `/dev` | Engineering | Fullstack engineering commands |
| `/ops` | Operations | Incident response & system monitoring |

## Execution Protocols
- **CLI Invocations**: Execute via `mekong <group> <command> <args>`.
- **Safe Commands**: Commands annotated with `// turbo` can run without interactive confirmation.
- **High-Risk Gates**: Live deployments, financial changes >20%, and force-pushes require explicit user approval.
- **Context Budget**: Observe budget caps per role (CEO ≤ 30k, ENG ≤ 24k, PM ≤ 20k, OPS ≤ 16k).

## Subagent Dispatching
Mekong agent definitions live in `.agents/subagents/registry.json`. Use `define_subagent` and `invoke_subagent` to delegate to specialized roles (e.g., Sun Tzu, PM, QA, CTO).
"""


def sync_global_antigravity(skills: Dict[str, str]) -> None:
    """Deploy skills, plugin, and rules globally so any project in Antigravity has them."""
    print("🌍 Deploying Mekong CLI globally for all Antigravity projects...")

    # 1. Global skills directory: ~/.gemini/config/skills/
    GLOBAL_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    count = write_skills_to_dir(GLOBAL_SKILLS_DIR, skills)
    print(f"  ✓ Installed {count} global skills in {GLOBAL_SKILLS_DIR}")

    # 2. Global skills.json: ~/.gemini/config/skills.json
    skills_json_content = {
        "entries": [
            {
                "path": "~/.gemini/config/skills"
            }
        ]
    }
    GLOBAL_SKILLS_JSON.parent.mkdir(parents=True, exist_ok=True)
    GLOBAL_SKILLS_JSON.write_text(json.dumps(skills_json_content, indent=2) + "\n", encoding="utf-8")
    print(f"  ✓ Configured global skills declaration at {GLOBAL_SKILLS_JSON}")

    # 3. Global Plugin: ~/.gemini/config/plugins/mekong-cli/
    for p_dir in [GLOBAL_PLUGIN_DIR, AGY_PLUGIN_DIR]:
        try:
            p_dir.mkdir(parents=True, exist_ok=True)
            plugin_json = {
                "name": "mekong-cli",
                "description": "Mekong CLI: CEO Solo Agentic Harness Engineering Platform",
                "version": "2.0.0",
                "author": "MekongMind",
            }
            (p_dir / "plugin.json").write_text(json.dumps(plugin_json, indent=2) + "\n", encoding="utf-8")

            # Rules inside plugin
            rules_dir = p_dir / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)
            (rules_dir / "AGENTS.md").write_text((PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8"), encoding="utf-8")
            (rules_dir / "GEMINI.md").write_text(get_gemini_rules_content(), encoding="utf-8")

            # Skills inside plugin
            plugin_skills_dir = p_dir / "skills"
            write_skills_to_dir(plugin_skills_dir, skills)
            print(f"  ✓ Packaged Antigravity plugin at {p_dir}")
        except Exception as e:
            print(f"  ⚠️ Warning creating plugin at {p_dir}: {e}")


def scaffold_target_project(target_dir: Path, skills: Dict[str, str]) -> None:
    """Scaffold .agents/skills, subagents, and GEMINI.md into a new or target project."""
    print(f"📦 Scaffolding Mekong Antigravity into target project: {target_dir}...")
    target_agents = target_dir / ".agents"
    target_skills = target_agents / "skills"
    target_subagents = target_agents / "subagents"

    count = write_skills_to_dir(target_skills, skills)
    agent_count = sync_subagents(target_subagents)
    (target_dir / "GEMINI.md").write_text(get_gemini_rules_content(), encoding="utf-8")

    print(f"  ✓ Scaffolding complete: {count} skills, {agent_count} subagents, and GEMINI.md created in {target_dir}")


def verify_all(check_global: bool = True) -> bool:
    """Verify local and global Antigravity installations."""
    errors = []

    # Check local
    if not LOCAL_SKILLS_DIR.exists():
        errors.append(f"Missing local skills directory: {LOCAL_SKILLS_DIR}")
    else:
        skill_dirs = [d for d in LOCAL_SKILLS_DIR.iterdir() if d.is_dir()]
        print(f"Auditing local workspace: {len(skill_dirs)} skills in {LOCAL_SKILLS_DIR}...")
        for sdir in skill_dirs:
            skill_md = sdir / "SKILL.md"
            if not skill_md.exists():
                errors.append(f"Missing SKILL.md in local {sdir.name}")
                continue
            content = skill_md.read_text(encoding="utf-8")
            if not content.startswith("---") or "name:" not in content or "description:" not in content:
                errors.append(f"Invalid frontmatter in local {sdir.name}/SKILL.md")

    # Check subagents
    registry_file = LOCAL_SUBAGENTS_DIR / "registry.json"
    if not registry_file.exists():
        errors.append(f"Missing local {registry_file}")

    if check_global:
        # Check global skills
        if not GLOBAL_SKILLS_DIR.exists():
            errors.append(f"Missing global skills directory: {GLOBAL_SKILLS_DIR}")
        else:
            global_skill_dirs = [d for d in GLOBAL_SKILLS_DIR.iterdir() if d.is_dir()]
            print(f"Auditing global configuration: {len(global_skill_dirs)} skills in {GLOBAL_SKILLS_DIR}...")
            if len(global_skill_dirs) < 150:
                errors.append(f"Global skills directory has only {len(global_skill_dirs)} skills (expected >= 150)")

        # Check global skills.json
        if not GLOBAL_SKILLS_JSON.exists():
            errors.append(f"Missing global skills.json: {GLOBAL_SKILLS_JSON}")
        else:
            try:
                json.loads(GLOBAL_SKILLS_JSON.read_text(encoding="utf-8"))
            except Exception as e:
                errors.append(f"Invalid JSON in {GLOBAL_SKILLS_JSON}: {e}")

        # Check global plugin
        if not (GLOBAL_PLUGIN_DIR / "plugin.json").exists():
            errors.append(f"Missing global plugin.json: {GLOBAL_PLUGIN_DIR / 'plugin.json'}")

    if errors:
        print(f"❌ Verification failed with {len(errors)} errors:", file=sys.stderr)
        for err in errors[:10]:
            print(f"  - {err}", file=sys.stderr)
        return False

    print("🎉 Verification passed! Antigravity skills are active both locally and globally across all projects!")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize Mekong CLI into Antigravity")
    parser.add_argument("--all", action="store_true", help="Sync skills, subagents, rules, and global configuration")
    parser.add_argument("--global", dest="sync_global", action="store_true", help="Install skills globally for all projects")
    parser.add_argument("--target", type=str, metavar="DIR", help="Scaffold Mekong Antigravity into a target new project directory")
    parser.add_argument("--verify", action="store_true", help="Verify integration without modifying")

    args = parser.parse_args()

    if args.verify:
        success = verify_all(check_global=True)
        sys.exit(0 if success else 1)

    skills = build_all_skills()

    if args.target:
        target_path = Path(args.target).resolve()
        scaffold_target_project(target_path, skills)
        return

    # Sync local workspace
    LOCAL_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    count = write_skills_to_dir(LOCAL_SKILLS_DIR, skills)
    agent_count = sync_subagents(LOCAL_SUBAGENTS_DIR)
    (PROJECT_ROOT / "GEMINI.md").write_text(get_gemini_rules_content(), encoding="utf-8")
    print(f"✅ Local workspace: {count} skills and {agent_count} subagents synced at {PROJECT_ROOT}")

    # Sync global
    sync_global_antigravity(skills)

    if not verify_all(check_global=True):
        sys.exit(1)


if __name__ == "__main__":
    main()
