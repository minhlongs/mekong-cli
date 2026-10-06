# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""AGY (Agent Governance YAML & Antigravity CLI) Operations Engine.

Pure standard-library implementation compliant with tests/test_core_boundary.py.
Deep-configured Antigravity stack:
- Agent binary: ~/.local/bin/agy (Go runtime, 51 hardcoded slash commands)
- Macro wrapper: ~/.local/bin/agym (PTY shim — adds 500+ /mekong-* slash macros)
- Sidecar: ~/.local/bin/agy-task -> antigravity-cli/antigravity-cli.py
- Plugin directory: ~/.gemini/antigravity-cli/plugins/mekong-cli/
- Config paths: ~/.config/agy/ and ~/.antigravity/
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
USER_HOME = Path.home()

AGY_BIN_PATH = USER_HOME / ".local" / "bin" / "agy"
AGYM_BIN_PATH = USER_HOME / ".local" / "bin" / "agym"
AGY_TASK_BIN_PATH = USER_HOME / ".local" / "bin" / "agy-task"

AGY_CONFIG_DIR = USER_HOME / ".config" / "agy"
ANTIGRAVITY_DIR = USER_HOME / ".antigravity"
AGY_PLUGIN_DIR = USER_HOME / ".gemini" / "antigravity-cli" / "plugins" / "mekong-cli"
GLOBAL_SKILLS_DIR = USER_HOME / ".gemini" / "config" / "skills"
LOCAL_SKILLS_DIR = PROJECT_ROOT / ".agents" / "skills"


class AGYEngine:
    """Core engine for AGY workflows, macros, and Antigravity CLI integration."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = workspace_root or PROJECT_ROOT
        self.skills_dir = self.workspace_root / ".agents" / "skills"

    def get_status(self) -> Dict[str, Any]:
        """Inspect AGY environment, binary paths, configs, and registered macros."""
        agy_bin = shutil.which("agy") or (str(AGY_BIN_PATH) if AGY_BIN_PATH.exists() else None)
        agym_bin = shutil.which("agym") or (str(AGYM_BIN_PATH) if AGYM_BIN_PATH.exists() else None)
        agy_task_bin = shutil.which("agy-task") or (str(AGY_TASK_BIN_PATH) if AGY_TASK_BIN_PATH.exists() else None)

        local_skills_count = len([d for d in self.skills_dir.iterdir() if d.is_dir()]) if self.skills_dir.exists() else 0
        global_skills_count = len([d for d in GLOBAL_SKILLS_DIR.iterdir() if d.is_dir()]) if GLOBAL_SKILLS_DIR.exists() else 0

        config_exists = AGY_CONFIG_DIR.exists()
        antigravity_exists = ANTIGRAVITY_DIR.exists()
        plugin_exists = AGY_PLUGIN_DIR.exists()

        is_healthy = bool(local_skills_count > 0)

        return {
            "status": "HEALTHY" if is_healthy else "DEGRADED",
            "timestamp": datetime.datetime.now().isoformat(),
            "binaries": {
                "agy": {
                    "path": agy_bin,
                    "installed": agy_bin is not None,
                    "description": "Go runtime agent binary (51 hardcoded slash commands)",
                },
                "agym": {
                    "path": agym_bin,
                    "installed": agym_bin is not None,
                    "description": "PTY macro wrapper shim (500+ /mekong-* slash macros)",
                },
                "agy_task": {
                    "path": agy_task_bin,
                    "installed": agy_task_bin is not None,
                    "description": "Sidecar daemon runner",
                },
            },
            "directories": {
                "agy_config_dir": str(AGY_CONFIG_DIR),
                "agy_config_exists": config_exists,
                "antigravity_dir": str(ANTIGRAVITY_DIR),
                "antigravity_exists": antigravity_exists,
                "agy_plugin_dir": str(AGY_PLUGIN_DIR),
                "agy_plugin_exists": plugin_exists,
                "local_skills_dir": str(self.skills_dir),
                "global_skills_dir": str(GLOBAL_SKILLS_DIR),
            },
            "metrics": {
                "local_skills_count": local_skills_count,
                "global_skills_count": global_skills_count,
                "slash_macros_count": local_skills_count,
                "hardcoded_commands_count": 51,
                "active_agents": ["CEO", "Product", "Engineering", "Ops", "Business", "Sun Tzu"],
            },
            "governance": {
                "framework": "AGY (Agent Governance YAML)",
                "contract": "HARNESS.md",
                "rules": "GEMINI.md",
                "autonomy_model": "docs/autonomy-model.md",
            },
        }

    def list_workflows(
        self,
        category: Optional[str] = None,
        layer: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List available AGY workflow specifications, skills, and macro bindings."""
        workflows: List[Dict[str, Any]] = []

        if not self.skills_dir.exists():
            return workflows

        cat_lower = category.lower() if category else None
        layer_lower = layer.lower() if layer else None

        for item in sorted(self.skills_dir.iterdir()):
            if not item.is_dir():
                continue
            skill_name = item.name
            skill_file = item / "SKILL.md"

            desc = "AGY operational workflow"
            skill_layer = "engineering"

            if skill_file.exists():
                try:
                    content = skill_file.read_text(encoding="utf-8")
                    desc_match = re.search(r"description:\s*(?:>-\s*)?(.*)", content)
                    if desc_match:
                        desc = desc_match.group(1).strip()
                    if "layer: business" in content or any(k in skill_name for k in ["ke-toan", "thue", "sales", "marketing"]):
                        skill_layer = "business"
                    elif "layer: product" in content or any(k in skill_name for k in ["plan", "spec", "product"]):
                        skill_layer = "product"
                    elif "layer: ops" in content or any(k in skill_name for k in ["daily", "ops", "monitor"]):
                        skill_layer = "operations"
                    elif "binh-phap" in skill_name or "idea" in skill_name:
                        skill_layer = "strategy"
                except Exception:
                    pass

            if layer_lower and layer_lower not in skill_layer.lower():
                continue
            if cat_lower and cat_lower not in skill_name.lower() and cat_lower not in desc.lower():
                continue

            workflows.append({
                "name": skill_name,
                "layer": skill_layer,
                "macro": f"/mekong-{skill_name}",
                "short_macro": f"/m-{skill_name}",
                "description": desc,
                "path": str(skill_file),
            })

            if len(workflows) >= limit:
                break

        return workflows

    def show_workflow(self, name: str) -> Dict[str, Any]:
        """Retrieve detailed AGY specification for a named workflow or skill."""
        target_dir = self.skills_dir / name
        skill_file = target_dir / "SKILL.md"

        if not skill_file.exists():
            # Check global skills
            global_file = GLOBAL_SKILLS_DIR / name / "SKILL.md"
            if global_file.exists():
                skill_file = global_file
            else:
                return {
                    "ok": False,
                    "error": f"Workflow or skill specification '{name}' not found in {self.skills_dir}",
                }

        content = skill_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        description = ""
        for line in lines:
            if line.startswith("description:"):
                description = line.replace("description:", "").strip()
                break

        return {
            "ok": True,
            "name": name,
            "macro_binding": f"/mekong-{name}",
            "short_macro": f"/m-{name}",
            "file_path": str(skill_file),
            "description": description or f"AGY workflow for {name}",
            "content": content,
            "lines_count": len(lines),
            "governance_gate": "HIGH_RISK_REQUIRE_CEO" if any(k in name for k in ["deploy", "ship", "billing", "destroy"]) else "AUTO_APPROVE",
        }

    def plan_workflow(self, goal: str) -> Dict[str, Any]:
        """Synthesize an AGY multi-agent plan for a given goal."""
        plan_id = f"AGY-PLAN-{uuid.uuid4().hex[:8].upper()}"
        goal_clean = goal.strip()

        # Deterministic decomposition based on intent
        is_build = any(k in goal_clean.lower() for k in ["build", "create", "make", "phát triển", "tạo"])
        is_fix = any(k in goal_clean.lower() for k in ["fix", "debug", "sửa", "lỗi", "bug"])
        is_audit = any(k in goal_clean.lower() for k in ["audit", "check", "kiểm tra", "đánh giá"])

        tasks = []
        if is_fix:
            tasks = [
                {
                    "step": 1,
                    "layer": "Product",
                    "role": "PM Agent",
                    "action": "Diagnose root cause and capture failure reproduction",
                    "macro": "/mekong-debug",
                    "budget_tokens": 12000,
                    "gate": "AUTO_APPROVE",
                },
                {
                    "step": 2,
                    "layer": "Engineering",
                    "role": "Lead Developer",
                    "action": f"Apply surgical fix for: {goal_clean}",
                    "macro": "/mekong-fix",
                    "budget_tokens": 20000,
                    "gate": "AUTO_APPROVE",
                },
                {
                    "step": 3,
                    "layer": "Engineering",
                    "role": "QA Agent",
                    "action": "Run regression test suite and verify boundary integrity",
                    "macro": "/mekong-test",
                    "budget_tokens": 8000,
                    "gate": "AUTO_APPROVE",
                },
            ]
        elif is_audit:
            tasks = [
                {
                    "step": 1,
                    "layer": "Operations",
                    "role": "SRE & Auditor",
                    "action": f"Audit system state and compliance for: {goal_clean}",
                    "macro": "/mekong-audit",
                    "budget_tokens": 14000,
                    "gate": "AUTO_APPROVE",
                },
                {
                    "step": 2,
                    "layer": "CEO",
                    "role": "Solo CEO",
                    "action": "Synthesize executive findings and approve mitigation roadmap",
                    "macro": "/mekong-status",
                    "budget_tokens": 10000,
                    "gate": "HIGH_RISK_REQUIRE_CEO",
                },
            ]
        else:
            tasks = [
                {
                    "step": 1,
                    "layer": "Product",
                    "role": "Product Strategist",
                    "action": f"Define requirements and spec for: {goal_clean}",
                    "macro": "/mekong-spec",
                    "budget_tokens": 15000,
                    "gate": "AUTO_APPROVE",
                },
                {
                    "step": 2,
                    "layer": "Engineering",
                    "role": "Senior Engineer",
                    "action": "Execute implementation plan via PEV engine",
                    "macro": "/mekong-cook",
                    "budget_tokens": 25000,
                    "gate": "AUTO_APPROVE",
                },
                {
                    "step": 3,
                    "layer": "Engineering",
                    "role": "QA Engineer",
                    "action": "Verify tests, lint, and boundary contracts",
                    "macro": "/mekong-test",
                    "budget_tokens": 10000,
                    "gate": "AUTO_APPROVE",
                },
                {
                    "step": 4,
                    "layer": "Operations",
                    "role": "DevOps Lead",
                    "action": "Stage, commit, and ship deployment",
                    "macro": "/mekong-ship",
                    "budget_tokens": 8000,
                    "gate": "HIGH_RISK_REQUIRE_CEO",
                },
            ]

        total_budget = sum(t["budget_tokens"] for t in tasks)

        return {
            "plan_id": plan_id,
            "goal": goal_clean,
            "tasks_count": len(tasks),
            "estimated_total_tokens": total_budget,
            "tasks": tasks,
            "delegation_layers": list({t["layer"] for t in tasks}),
            "governance": {
                "context_budget_cap": 40000,
                "high_risk_gates": [t["step"] for t in tasks if t["gate"] == "HIGH_RISK_REQUIRE_CEO"],
                "ceo_override_flag": "MEKONG_CEO_OVERRIDE=1",
            },
        }

    def get_walkthrough(self) -> Dict[str, Any]:
        """Return structural architecture walkthrough of the AGY integration."""
        return {
            "title": "AGY Antigravity Deep-Configured Architecture Walkthrough",
            "components": [
                {
                    "name": "agy",
                    "binary": "~/.local/bin/agy",
                    "description": "Go runtime agent binary with 51 hardcoded slash commands.",
                },
                {
                    "name": "agym",
                    "binary": "~/.local/bin/agym",
                    "description": "PTY shim wrapper adding 500+ /mekong-* and /m-* slash macros.",
                },
                {
                    "name": "agy-task",
                    "binary": "~/.local/bin/agy-task",
                    "description": "Sidecar daemon dispatcher for autonomous goal and benchmark execution.",
                },
                {
                    "name": "Plugin",
                    "path": "~/.gemini/antigravity-cli/plugins/mekong-cli/",
                    "description": "Packaged Antigravity plugin with skills, subagents, and hooks.",
                },
                {
                    "name": "Configurations",
                    "paths": ["~/.config/agy/", "~/.antigravity/"],
                    "description": "Parallel agent pool configs and runtime settings.",
                },
            ],
            "macro_patterns": [
                "/mekong-<slug> — Execute full named skill via AGY macro",
                "/m-<slug>      — Shorthand skill execution alias",
                "/mk-list       — Interactive macro discovery list",
                "/mk-help       — Help and usage matrix",
            ],
            "slash_commands": [
                "/agy status — Inspect AGY stack health, paths, and macro metrics",
                "/agy list   — List available workflows and macro bindings",
                "/agy show   — Inspect detailed specification of a workflow",
                "/agy plan   — Synthesize multi-agent AGY execution plan",
                "/agy walk   — Interactive walkthrough of AGY architecture",
                "/agy new    — Scaffold new AGY workflow specification",
                "/agy bin    — Verify binary paths, runtime versions, and permissions",
                "/agy chat   — Execute prompt via AGY print-mode runner",
                "/agy sync   — Reconcile configuration files, macros, and skills",
            ],
        }

    def scaffold_spec(self, name: str, layer: str = "engineering", description: str = "") -> Dict[str, Any]:
        """Scaffold a new AGY specification structure."""
        slug = re.sub(r"[^a-z0-9\-]", "-", name.lower().strip())
        desc = description.strip() or f"AGY operational workflow specification for {slug}"
        layer_norm = layer.lower().strip()

        yaml_content = f"""---
name: {slug}
layer: {layer_norm}
description: >-
  {desc}
allowed-tools:
  - Read
  - Write
  - Bash
governance:
  risk_level: {"HIGH" if any(k in slug for k in ["deploy", "ship", "delete"]) else "LOW"}
  requires_approval: {"true" if any(k in slug for k in ["deploy", "ship", "delete"]) else "false"}
---

# /{slug} — {slug.title()} Workflow

{desc}

## Execution Steps

1. **Plan**: Identify target files and establish baseline tests.
2. **Execute**: Apply targeted modifications.
3. **Verify**: Ensure 100% test pass rate and boundary integrity.

## Usage

```bash
mekong agy show {slug}
/mekong-{slug}
```
"""
        return {
            "name": slug,
            "layer": layer_norm,
            "macro": f"/mekong-{slug}",
            "description": desc,
            "yaml_spec": yaml_content,
        }

    def get_binary_info(self) -> Dict[str, Any]:
        """Inspect binary paths, version information, and execute permissions."""
        binaries = {
            "agy": {"path": str(AGY_BIN_PATH), "exists": AGY_BIN_PATH.exists()},
            "agym": {"path": str(AGYM_BIN_PATH), "exists": AGYM_BIN_PATH.exists()},
            "agy_task": {"path": str(AGY_TASK_BIN_PATH), "exists": AGY_TASK_BIN_PATH.exists()},
        }

        for name, info in binaries.items():
            p = Path(info["path"])
            info["executable"] = os.access(p, os.X_OK) if p.exists() else False

        which_agy = shutil.which("agy")
        which_agym = shutil.which("agym")

        return {
            "binaries": binaries,
            "which_agy": which_agy,
            "which_agym": which_agym,
            "hardcoded_commands": 51,
            "macro_wrapper_enabled": which_agym is not None or AGYM_BIN_PATH.exists(),
        }

    def execute_chat(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Execute a prompt via AGY print-mode runner or simulated response."""
        agy_bin = shutil.which("agy") or (str(AGY_BIN_PATH) if AGY_BIN_PATH.exists() else None)
        selected_model = model or "gemini-3-flash-preview"

        if agy_bin and os.access(agy_bin, os.X_OK):
            try:
                cmd = [agy_bin, "--dangerously-skip-permissions", "--model", selected_model, "-p", prompt]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                return {
                    "ok": proc.returncode == 0,
                    "mode": "live",
                    "model": selected_model,
                    "prompt": prompt,
                    "response": proc.stdout.strip(),
                    "stderr": proc.stderr.strip() if proc.stderr else None,
                    "exit_code": proc.returncode,
                }
            except Exception as exc:
                return {
                    "ok": False,
                    "mode": "live_failed",
                    "error": str(exc),
                    "prompt": prompt,
                }

        # Standalone simulated execution
        return {
            "ok": True,
            "mode": "simulated",
            "model": selected_model,
            "prompt": prompt,
            "response": f"[AGY Simulated Response] Processed: '{prompt}' via {selected_model}.",
        }

    def sync_integration(self) -> Dict[str, Any]:
        """Reconcile AGY configuration files, macros, and plugin mappings."""
        AGY_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        ANTIGRAVITY_DIR.mkdir(parents=True, exist_ok=True)
        AGY_PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

        # Write or update AGY macro map
        macro_map = {}
        if self.skills_dir.exists():
            for item in self.skills_dir.iterdir():
                if item.is_dir():
                    macro_map[f"/mekong-{item.name}"] = f"mekong {item.name}"
                    macro_map[f"/m-{item.name}"] = f"mekong {item.name}"

        macro_file = AGY_CONFIG_DIR / "macros.json"
        macro_file.write_text(json.dumps(macro_map, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "ok": True,
            "synced_at": datetime.datetime.now().isoformat(),
            "macros_registered": len(macro_map),
            "macro_file": str(macro_file),
            "config_dirs": [str(AGY_CONFIG_DIR), str(ANTIGRAVITY_DIR), str(AGY_PLUGIN_DIR)],
        }
