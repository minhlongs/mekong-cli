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

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
USER_HOME = Path.home()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
    content = re.sub(r"python3\s+-m\s+src\.main\s+mk\s+", "mekong ", content)
    content = re.sub(r"python3\s+-m\s+src\.main\s+", "mekong ", content)
    content = re.sub(r"python3\s+-m\s+src\.main", "mekong", content)
    content = re.sub(r"mekong\s+mk\s+", "mekong ", content)
    return content


CURATED_DESCRIPTIONS: Dict[str, str] = {
    "cfo": "Mekong CFO — Binh Pháp Ch2 Tình Hình + Ch5 Căn Cứ: finance, budget, pricing, MRR.",
    "cmo": "Mekong CMO — Binh Pháp Ch11 Hỏa Công + Ch12 Xâm Phạm: marketing, campaign, launch, growth.",
    "cso": "Mekong CSO — Binh Pháp Ch6 Trống Hư + Ch1 Tính Địa: research, competitive, scout, terrain.",
    "agent": "Domain subagent bridge & management — list, run, info, and dynamically define 25 specialized agents.",
    "billing": "Billing operations: usage submission, reconciliation, and event tracking.",
    "company": "Company workspace configuration, initialization, and status monitoring.",
    "dash": "Dash: One-button action menu and system operations overview.",
    "eval-agent": "Offline eval queries on historical missions from local SQLite database.",
    "evolve": "Evolve: Analyze execution patterns, generate recipes, and optimize workflows.",
    "evolve-code": "Analyze source code for self-improvement and refactoring opportunities.",
    "founder": "Founder genome assessment: personality, risk tolerance, and bias profiling.",
    "gateway": "OpenClaw Hybrid Commander HTTP gateway server management.",
    "governance": "ZenOS Commons governance: propose, vote, tally, and inspect proposals.",
    "halt": "Emergency stop: immediately halt all autonomous agent operations.",
    "harness-eval": "Run deterministic harness engineering evals and quality checks.",
    "marketplace": "Plugin marketplace for discovering and installing extensions.",
    "particle": "ZenOS particle lifecycle management, behavior graph, and AI cells.",
    "pev": "Plan-Execute-Verify engine pipeline orchestration, status, and history.",
    "vendor": "Vendor marketplace management and third-party provider onboarding.",
    "version": "Show Mekong CLI version info and AGI subsystem health status.",
    # Vietnamese business funnel skills
    "ke-toan": "VAS Vietnamese Accounting Standard engine, TT78/2021 electronic invoices, journal entries, and XML reports.",
    "thue": "Vietnamese tax calculator for personal income tax (TNCN), corporate income tax (TNDN), and VAT (GTGT).",
    "zalo-oa": "Zalo Official Account (OA) integration for customer messaging, followers, templates, and broadcast campaigns.",
    # Commands with corrupted or missing metadata
    "context-engineering": "Context engineering: token budget, tool allowlists, and prompt architecture.",
    "tech-graph": "Generate and inspect technical architecture dependency graphs.",
    "implement": "SDD: execute implementation from task list via goal engine.",
    "tasks-sdd": "SDD task generation — generate TDD-ordered tasks from feature spec.",
    # Commands with descriptions < 10 characters
    "audit-sox": "SOX compliance audit and internal controls testing.",
    "audit-itgc": "ITGC information technology general controls audit and compliance review.",
}


def clean_frontmatter(content: str, name: str) -> str:
    """Ensure standard valid YAML frontmatter for Antigravity SKILL.md.

    Robustly handles:
    1. Standard YAML frontmatter enclosed by '---'
    2. Malformed frontmatter missing the opening '---'
    3. Multiline block scalars (>- , |, >+, |-, etc.)
    4. Corrupted scalar marker descriptions ('>-') falling back to CURATED_DESCRIPTIONS
    """
    content = normalize_execution_commands(content)
    lines = content.splitlines()
    start_idx = -1
    end_idx = -1

    if lines and lines[0].strip() == "---":
        start_idx = 1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break
    elif lines:
        # Check if file has frontmatter missing opening '---' delimiter
        # e.g. line 0 starts with key: value and line i is '---'
        for i in range(0, min(10, len(lines))):
            if lines[i].strip() == "---":
                has_key = any(":" in lines[j] for j in range(0, i))
                if has_key:
                    start_idx = 0
                    end_idx = i
                break

    description = ""
    body_lines = lines
    if end_idx != -1:
        fm_text = "\n".join(lines[start_idx:end_idx])
        body_lines = lines[end_idx + 1 :]
        # Try YAML parser first if available
        try:
            parsed = yaml.safe_load(fm_text)
            if isinstance(parsed, dict) and "description" in parsed:
                val = str(parsed["description"]).strip()
                if val and val not in (">-", ">+", ">", "|-", "|+", "|"):
                    description = val
        except Exception:
            pass

        # Fallback to pure-Python block scalar line collector
        if not description:
            frontmatter_lines = lines[start_idx:end_idx]
            for idx, line in enumerate(frontmatter_lines):
                if line.startswith("description:"):
                    desc_val = line[len("description:") :].strip()
                    if (desc_val.startswith('"') and desc_val.endswith('"')) or (
                        desc_val.startswith("'") and desc_val.endswith("'")
                    ):
                        desc_val = desc_val[1:-1].strip()

                    # Handle YAML block scalar indicators (>- , |, etc.)
                    if desc_val in (">-", ">+", ">", "|-", "|+", "|", ""):
                        block_lines = []
                        for next_line in frontmatter_lines[idx + 1 :]:
                            if next_line.startswith(" ") or next_line.startswith("\t"):
                                block_lines.append(next_line.strip())
                            else:
                                break
                        if block_lines:
                            desc_val = " ".join(block_lines).strip()
                        else:
                            desc_val = ""

                    if desc_val and desc_val not in (">-", ">+", ">", "|-", "|+", "|"):
                        description = desc_val
                    break

    # Normalize whitespace
    description = " ".join(description.split()).strip()

    # Reject invalid, scalar marker, or short descriptions and fallback to CURATED_DESCRIPTIONS
    if not description or description in (">-", ">+", ">", "|-", "|+", "|") or len(description) < 10:
        description = CURATED_DESCRIPTIONS.get(name, description)

    if not description or description in (">-", ">+", ">", "|-", "|+", "|") or len(description) < 10:
        description = CURATED_DESCRIPTIONS.get(name, f"Mekong CLI {name} command")

    clean_desc = description.replace('"', '\\"')
    return f"---\nname: {name}\ndescription: >-\n  {clean_desc}\n---\n\n" + "\n".join(
        body_lines
    ).strip() + "\n"


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


def get_agent_skill() -> str:
    """Generate native /agent bridge skill with progressive disclosure of 25 subagents."""
    return """---
name: agent
description: >-
  Domain subagent bridge & management — list, run, info, and dynamically define 25 specialized agents.
---

# /agent — Domain Subagent Bridge & Architecture

The `/agent` skill bridges Google Antigravity to Mekong CLI's 25 domain subagents. It provides direct command execution for `mekong agent` CLI and enables dynamic Antigravity subagent definition.

## CLI Commands

### 1. `mekong agent list`
List all domain agents with descriptions, allowed tools, and delegation paths.
```bash
mekong agent list
mekong agent list --verbose
```

### 2. `mekong agent run <agent> <task>`
Spawn an agent to execute a task and emit structured output.
```bash
mekong agent run cto "Review the architecture of src/harness/pev/"
mekong agent run cfo "Analyze runway and pricing structure" --json
```

### 3. `mekong agent info <agent>`
Inspect detailed agent metadata, allowed tools, and delegation paths.
```bash
mekong agent info cto
```

### 4. `mekong agent assemble "<goal>"`
Dynamically assemble an agent using the NLU + PEV + Memory + Factory pipeline:
```bash
mekong agent assemble "Audit security and vulnerabilities in backend"
```

### 5. `mekong agent create <name>`
Scaffold a new agent definition at `.claude/agents/<name>.md`.
```bash
mekong agent create security-auditor
```

### 6. `mekong agent init <dir>`
Bootstrap an agent project directory from a template.
```bash
mekong agent init ./agents
```

## Antigravity Dynamic Subagent Loading

Antigravity agents can dynamically define and invoke any of the 25 specialized subagents at runtime using `scripts/antigravity_agent_loader.py`.

### Dynamic Loading Workflow:
1. **List all registered subagents**:
   ```bash
   python3 scripts/antigravity_agent_loader.py --list
   ```
2. **Extract `define_subagent` payload**:
   ```bash
   python3 scripts/antigravity_agent_loader.py --get <agent_id>
   ```
3. **Define the subagent in Antigravity**:
   Call Antigravity's `define_subagent` tool with the parameters returned by the loader (`name`, `description`, `system_prompt`, `enable_write_tools`, `enable_subagent_tools`, `enable_mcp_tools`).
4. **Delegate the task**:
   Call Antigravity's `invoke_subagent` with `subagent_name` and the specific goal prompt.

## Registered Domain Subagents (25 Total)

### Executive Leadership & Strategic Counsel (7 Agents)
| ID | Role | Model | Budget | Key Capabilities |
|---|---|---|---|---|
| `sun-tzu` | Advisory Strategist | Pro | 30k | High-stakes strategic counsel, single-turn advisory, risk calculus |
| `ceo` | Chief Executive Officer | Pro | 30k | Final authority, team delegation, override authority (`can_override: true`) |
| `cto` | Chief Technology Officer | Pro | 24k | Code architecture, quality standards, engineering SOP enforcement |
| `cmo` | Chief Marketing Officer | Inherit | 20k | Growth positioning, messaging, multi-channel campaigns |
| `coo` | Chief Operating Officer | Inherit | 16k | Daily operations, workflow logistics, cross-functional execution |
| `cfo` | Chief Financial Officer | Inherit | 16k | Financial models, cash runway, pricing levers, capital purity |
| `cso` | Chief Strategy Officer | Inherit | 16k | Market intelligence, competitive terrain, strategic bets |

### Core Operational & Lifecycle Roles (6 Agents)
| ID | Role | Model | Budget | Key Capabilities |
|---|---|---|---|---|
| `ae` | Account Executive | Inherit | 16k | Client lifecycle, proposals, contracts, revenue onboarding |
| `pm` | Product Manager | Inherit | 20k | Product roadmap, specifications, backlog priorities, feature specs |
| `eng` | Engineer | Inherit | 24k | Code implementation, refactoring, bug fixes, deployment |
| `ops` | Operations & SRE | Inherit | 16k | System monitoring, incident response, vendor & cost tracking |
| `tester` | Quality Assurance | Inherit | 16k | Test suite execution, verification evidence, regression validation |
| `planner` | Tech Lead & Planner | Pro | 20k | Architecture review, dependency graphs, failure-mode analysis |

### Specialized Technical & Task Agents (12 Agents)
| ID | Role | Model | Budget | Definition File |
|---|---|---|---|---|
| `brainstormer` | Ideation & Strategy | Flash | 16k | `.agents/subagents/definitions/brainstormer.md` |
| `code-reviewer` | Code Review | Flash | 16k | `.agents/subagents/definitions/code-reviewer.md` |
| `code-simplifier` | Refactoring & Simplification | Flash | 16k | `.agents/subagents/definitions/code-simplifier.md` |
| `debugger` | Root Cause Analysis | Flash | 16k | `.agents/subagents/definitions/debugger.md` |
| `docs-manager` | Documentation & Specs | Flash | 16k | `.agents/subagents/definitions/docs-manager.md` |
| `fullstack-developer` | Fullstack Implementation | Flash | 16k | `.agents/subagents/definitions/fullstack-developer.md` |
| `git-manager` | Git Operations & Branches | Flash | 16k | `.agents/subagents/definitions/git-manager.md` |
| `journal-writer` | Evolution & Logging | Flash | 16k | `.agents/subagents/definitions/journal-writer.md` |
| `kongming` | Tactical Advisor | Flash | 16k | `.agents/subagents/definitions/kongming.md` |
| `project-manager` | Project Coordination | Flash | 16k | `.agents/subagents/definitions/project-manager.md` |
| `researcher` | Deep Research & Analysis | Flash | 16k | `.agents/subagents/definitions/researcher.md` |
| `ui-ux-designer` | UI/UX & Design Systems | Flash | 16k | `.agents/subagents/definitions/ui-ux-designer.md` |

## Usage

```bash
// turbo
mekong agent $ARGUMENTS
```
"""


def discover_typer_commands() -> Dict[str, Dict[str, Any]]:
    """Discover all top-level commands and groups from src.cli.app_setup.build_app()."""
    import click
    import typer.main
    from src.cli.app_setup import build_app

    app = build_app()
    click_app = typer.main.get_command(app)
    discovered: Dict[str, Dict[str, Any]] = {}

    for name, cmd in click_app.commands.items():
        is_group = isinstance(cmd, click.Group)
        help_text = (cmd.help or cmd.short_help or "").strip()
        summary = help_text.splitlines()[0] if help_text else ""
        desc = CURATED_DESCRIPTIONS.get(name) or summary or f"Mekong CLI {name} command"

        subcmds = []
        if is_group and hasattr(cmd, "commands"):
            for sname, scmd in cmd.commands.items():
                shelp = (scmd.help or scmd.short_help or "").strip().splitlines()[0] if (scmd.help or scmd.short_help) else ""
                subcmds.append((sname, shelp))

        discovered[name] = {
            "name": name,
            "type": "group" if is_group else "command",
            "description": desc,
            "subcommands": subcmds,
        }

    return discovered


def generate_skill_content(cmd_info: Dict[str, Any]) -> str:
    """Generate well-formatted SKILL.md for a discovered Typer command."""
    name = cmd_info["name"]
    desc = cmd_info["description"]
    clean_desc = desc.replace('"', '\\"')
    desc_clean = desc.rstrip(".")

    lines = [
        "---",
        f"name: {name}",
        "description: >-",
        f"  {clean_desc}",
        "---",
        "",
        f"# /{name} — {desc_clean}",
        "",
        f"{desc_clean}.",
        "",
        "## Usage",
        "",
        "```bash",
        "// turbo",
        f"mekong {name} $ARGUMENTS",
        "```",
    ]

    subcmds = cmd_info.get("subcommands", [])
    if subcmds:
        lines.append("")
        lines.append("## Subcommands")
        lines.append("")
        lines.append("| Subcommand | Description |")
        lines.append("|------------|-------------|")
        for sc_name, sc_help in subcmds:
            help_display = sc_help if sc_help else f"Execute {name} {sc_name}"
            lines.append(f"| `{sc_name}` | {help_display} |")

    lines.append("")
    return "\n".join(lines)


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

    # 3. Native /agent bridge skill
    skills["agent"] = get_agent_skill()

    # 4. All commands in .claude/_integration/commands/*.md
    if INTEGRATION_COMMANDS_DIR.exists():
        for cmd_path in sorted(INTEGRATION_COMMANDS_DIR.glob("*.md")):
            name = cmd_path.stem
            if name not in skills:
                raw_content = cmd_path.read_text(encoding="utf-8")
                formatted_content = clean_frontmatter(raw_content, name)
                if "```bash" not in formatted_content:
                    cmd_name = name[3:] if name.startswith("mk-") else name
                    formatted_content += f"\n## Usage\n\n```bash\n// turbo\nmekong {cmd_name.replace('-', ' ')} $ARGUMENTS\n```\n"
                skills[name] = formatted_content

    # 5. Typer CLI Auto-Discovery from src.cli.app_setup.build_app()
    # Guarantees 100% direct command parity for all 64 registered commands/groups
    typer_commands = discover_typer_commands()
    for name, cmd_info in typer_commands.items():
        if name not in skills:
            skills[name] = generate_skill_content(cmd_info)

        # For commands that only had mk-<cmd> variants, ensure both direct and legacy aliases exist
        mk_name = f"mk-{name}"
        if mk_name in skills:
            # Normalize legacy alias content so it invokes mekong directly
            legacy_content = skills[mk_name]
            skills[mk_name] = normalize_execution_commands(legacy_content)

    # 6. Global invocation normalization
    for name, content in list(skills.items()):
        content = normalize_execution_commands(content)
        if "mekong" not in content:
            cmd_name = name[3:] if name.startswith("mk-") else name
            content = content.rstrip() + f"\n\n## CLI Invocation\n\n```bash\n// turbo\nmekong {cmd_name.replace('-', ' ')} $ARGUMENTS\n```\n"
        skills[name] = content

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
        if len(skill_dirs) < 220:
            errors.append(f"Local skills directory has only {len(skill_dirs)} skills (expected >= 220)")
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
            if len(global_skill_dirs) < 220:
                errors.append(f"Global skills directory has only {len(global_skill_dirs)} skills (expected >= 220)")

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
        if (GLOBAL_PLUGIN_DIR / "skills").exists():
            p_skill_dirs = [d for d in (GLOBAL_PLUGIN_DIR / "skills").iterdir() if d.is_dir()]
            if len(p_skill_dirs) < 220:
                errors.append(f"Global plugin skills directory has only {len(p_skill_dirs)} skills (expected >= 220)")

        # Check antigravity-cli plugin
        if not (AGY_PLUGIN_DIR / "plugin.json").exists():
            errors.append(f"Missing antigravity-cli plugin.json: {AGY_PLUGIN_DIR / 'plugin.json'}")
        if (AGY_PLUGIN_DIR / "skills").exists():
            agy_p_skill_dirs = [d for d in (AGY_PLUGIN_DIR / "skills").iterdir() if d.is_dir()]
            if len(agy_p_skill_dirs) < 220:
                errors.append(f"Antigravity plugin skills directory has only {len(agy_p_skill_dirs)} skills (expected >= 220)")

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
