# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Universal Antigravity project scaffolding engine.

Pure Python standard library implementation (strictly no external vendor SDKs,
no HTTP libraries, no YAML). Provides full-fidelity project scaffolding:
234 native skills, 2 domain subagent catalogs (25 definitions), lifecycle safety
hooks, stdio MCP manifests, and workspace rules (GEMINI.md, HARNESS.md).
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import shutil
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ── Protected system directories for path traversal security ────────────────
PROTECTED_SYSTEM_DIRS: frozenset[str] = frozenset({
    "/",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/private/etc",
    "/lib",
    "/lib64",
    "/opt",
    "/proc",
    "/root",
    "/run",
    "/sbin",
    "/sys",
    "/system",
    "/library",
    "/usr",
    "/var",
    "/private/var",
})

# ── Minimal profile definitions ──────────────────────────────────────────────
MINIMAL_SKILLS: frozenset[str] = frozenset({
    "cook",
    "plan",
    "ship",
    "doctor",
    "binh-phap",
    "status",
    "agent",
    "cfo",
    "cmo",
    "cto",
    "pm",
    "dev",
    "ops",
    "idea",
    "ke-toan",
    "thue",
    "zalo-oa",
    "quick-start",
    "daily",
    "bmad",
    "build",
    "spec",
    "mk-clean",
    "mk-test",
    "mk-lint",
})

MINIMAL_SUBAGENTS: frozenset[str] = frozenset({
    "ceo",
    "cto",
    "pm",
    "eng",
    "ops",
    "sun-tzu",
})

# ── Fallback templates ───────────────────────────────────────────────────────
FALLBACK_HOOKS_JSON: str = """{
  "mekong-harness": {
    "enabled": true,
    "PreToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          {
            "type": "command",
            "command": "if [ -f scripts/hooks/pre_tool_guardrail.py ]; then python3 scripts/hooks/pre_tool_guardrail.py; elif [ -f ../scripts/hooks/pre_tool_guardrail.py ]; then python3 ../scripts/hooks/pre_tool_guardrail.py; else python3 scripts/hooks/pre_tool_guardrail.py; fi",
            "timeout": 30
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "run_command",
        "hooks": [
          {
            "type": "command",
            "command": "if [ -f scripts/hooks/post_tool_audit.py ]; then python3 scripts/hooks/post_tool_audit.py; elif [ -f ../scripts/hooks/post_tool_audit.py ]; then python3 ../scripts/hooks/post_tool_audit.py; else python3 scripts/hooks/post_tool_audit.py; fi",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
"""

FALLBACK_MCP_CONFIG_JSON: str = """{
  "mcpServers": {
    "mekong-core": {
      "command": "python3",
      "args": [
        "scripts/mcp_server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    },
    "mekong-fabric": {
      "command": "python3",
      "args": [
        "scripts/mcp_server.py",
        "--fabric"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
"""

FALLBACK_GEMINI_MD: str = """# GEMINI.md — Mekong CLI Antigravity Rules
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

FALLBACK_HARNESS_MD: str = """# HARNESS.md — CEO Solo Agentic Harness Configuration

This file is the **runtime contract** for the mekong-cli agent harness.
It defines context budget, guardrails, delegation rules, and escalation
paths for the CEO Solo operating model.

---

## 1. Context Budget

| Slot | Budget | Notes |
|------|--------|-------|
| System prompt | ≤ 4 000 tokens | HARNESS.md, AGENTS.md, active SOP |
| Conversation history | ≤ 12 000 tokens | Compaction trigger at 10 000 |
| Tool output | ≤ 8 000 tokens | Truncate long bash/grep output |
| Active file context | ≤ 16 000 tokens | One primary file at a time |
| **Total context ceiling** | **≤ 40 000 tokens** | Hard stop; compact before hitting |

**Rule:** Every subagent receives only the SOP fragment relevant to its task, never the full HARNESS.md.

---

## 2. Tool Allowlist by Layer

| Tool | CEO | Business | Product | Engineering | Ops |
|------|-----|----------|---------|-------------|-----|
| Bash | ✓ read-only | ✓ scoped | ✓ scoped | ✓ full | ✓ read-only |
| Read | ✓ | ✓ | ✓ | ✓ | ✓ |
| Write | ask | ask | ✓ | ✓ | ask |
| Edit | ask | ask | ✓ | ✓ | ask |
| Task (subagent) | ✓ | ✓ | ✓ | ✓ | ✓ |
| WebFetch | ✓ | ✓ | ✓ | ✓ | ✗ |

---

## 3. CEO Override Clauses

1. **CEO may override any decision** without explanation.
2. CEO may bypass review gates by adding `--ceo-override` to any command.
3. CEO may terminate any running subagent by name via `/abort <agent>`.
4. CEO may set `risk-gate.autoStopRequired = false` for low-risk tasks.

---

## 4. High-Risk Gate Definitions

A **high-risk** action requires explicit CEO approval before execution:

- Deleting or modifying production database records
- Pushing to `main` branch (force or non-force)
- Publishing packages to public registries
- Modifying billing or payment configuration
- Sending external communications (emails, API calls to clients)
- Rotating secrets or credentials

High-risk actions: `ask` in permissions → CEO approval required.

---

## 5. Agent Delegation Matrix

```
CEO Solo
 ├── Layer: Business      → AE (Account Executive) agent
 │                            Handles: deals, contracts, invoices
 ├── Layer: Product       → PM (Product Manager) agent
 │                            Handles: roadmap, specs, priorities
 ├── Layer: Engineering   → ENG (Engineer) agent
 │                            Handles: code, review, deployment
 └── Layer: Ops           → OPS (Operations) agent
                              Handles: monitoring, incidents, vendor
```

Each subagent receives:
- Relevant SOP fragment (`sops/<layer>/`)
- Task context from CEO
- Budget envelope (token + time limits)

---

## 6. Escalation Path

| Situation | Action |
|-----------|--------|
| Subagent returns `verification_passed: false` | CEO reviews → decide: retry, modify, abort |
| Subagent fails ≥3 times on same task | CEO decides: escalate to human, decompose, deprioritize |
| Context budget exceeded | Auto-compact → resume with summary |
| External API rate limit hit | Backoff + retry (max 3) → escalate if persists |
| Ambiguous intent detected | STOP → Ask CEO via AskUserQuestion |

---

## 7. Observability Integration

Traces are written to `observability/traces/` in OpenTelemetry JSON format:
- `span_id`, `parent_span_id`, `agent_name`, `tool`, `duration_ms`
- `tokens_used`, `verification_passed`, `error`

Eval runs use `evals/solo-ceo-eval.md` as the test suite.

---

## 8. SOP Invocation Rules

- Always load SOP before starting task in that domain
- Reference SOP section explicitly: "Per SOP §X.Y: …"
- Update SOP after task completion if process was found inadequate
- SOP version tracked in frontmatter; bump when behavior changes

---

## 9. Core DNA and Contribution Gate

Mekong is open source, but the official runtime feature surface is governed
by `dna/core-dna.json`.

---

## 10. Runtime Core Contract (v0.1)

The agent lifecycle executed by `src/core/runtime_adapter.py` is a pinned
contract, documented in `docs/core-contract.md`.

HARNESS.md v1.2.0 — CEO Solo Agentic Platform — Mekong CLI
"""


@dataclass
class ScaffoldResult:
    """Result of project scaffolding operation."""

    target_path: Path
    profile: str
    dry_run: bool
    force: bool
    created_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)
    modified_files: list[str] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)
    success: bool = True
    error: str | None = None

    @property
    def counts(self) -> dict[str, int]:
        """Alias for stats for testing compatibility."""
        return self.stats

    @counts.setter
    def counts(self, value: dict[str, int]) -> None:
        self.stats = value

    @property
    def ok(self) -> bool:
        """Boolean success status."""
        return self.success

    def to_dict(self) -> dict[str, Any]:
        """Convert result to clean dictionary representation."""
        target_str = (
            str(self.target_path.resolve())
            if isinstance(self.target_path, Path)
            else str(self.target_path)
        )
        status_val = (
            "dry_run"
            if self.dry_run
            else ("scaffolded" if self.success else "error")
        )
        return {
            "ok": self.success,
            "status": status_val,
            "target": target_str,
            "profile": self.profile,
            "dry_run": self.dry_run,
            "force": self.force,
            "stats": self.stats,
            "counts": self.stats,
            "created_files": list(self.created_files),
            "skipped_files": list(self.skipped_files),
            "modified_files": list(self.modified_files),
            "error": self.error,
        }


def _find_asset_sources() -> dict[str, Any]:
    """Locate source assets using discovery hierarchy.

    Hierarchy:
    1. MEKONG_ROOT environment variable (if set and valid).
    2. Repo root via Path(__file__).resolve().parents[2].
    3. Global plugin directory ~/.gemini/config/plugins/mekong-cli.
    4. Secondary plugin directory ~/.gemini/antigravity-cli/plugins/mekong-cli.
    """
    candidate_roots: list[Path] = []

    env_root = os.environ.get("MEKONG_ROOT")
    if env_root:
        candidate_roots.append(Path(env_root).resolve())

    # Dev repo root (two levels up from src/core/scaffold.py)
    dev_root = Path(__file__).resolve().parents[2]
    candidate_roots.append(dev_root)

    # Global plugin directories
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

        # Skills directory
        if assets["skills_dir"] is None:
            if (root / ".agents" / "skills").is_dir():
                assets["skills_dir"] = (root / ".agents" / "skills").resolve()
            elif (root / "skills").is_dir():
                assets["skills_dir"] = (root / "skills").resolve()

        # Subagents directory
        if assets["subagents_dir"] is None:
            if (root / ".agents" / "subagents").is_dir():
                assets["subagents_dir"] = (root / ".agents" / "subagents").resolve()
            elif (root / "subagents").is_dir():
                assets["subagents_dir"] = (root / "subagents").resolve()

        # Hooks JSON
        if assets["hooks_json"] is None:
            if (root / ".agents" / "hooks.json").is_file():
                assets["hooks_json"] = (root / ".agents" / "hooks.json").resolve()
            elif (root / "hooks.json").is_file():
                assets["hooks_json"] = (root / "hooks.json").resolve()

        # Hooks scripts dir
        if assets["hooks_scripts_dir"] is None:
            if (root / "scripts" / "hooks").is_dir():
                assets["hooks_scripts_dir"] = (root / "scripts" / "hooks").resolve()

        # MCP config JSON
        if assets["mcp_config_json"] is None:
            if (root / ".agents" / "mcp_config.json").is_file():
                assets["mcp_config_json"] = (root / ".agents" / "mcp_config.json").resolve()
            elif (root / "mcp_config.json").is_file():
                assets["mcp_config_json"] = (root / "mcp_config.json").resolve()

        # MCP server script
        if assets["mcp_server_script"] is None:
            if (root / "scripts" / "mcp_server.py").is_file():
                assets["mcp_server_script"] = (root / "scripts" / "mcp_server.py").resolve()

        # GEMINI.md
        if assets["gemini_md"] is None:
            if (root / "GEMINI.md").is_file():
                assets["gemini_md"] = (root / "GEMINI.md").resolve()
            elif (root / "rules" / "GEMINI.md").is_file():
                assets["gemini_md"] = (root / "rules" / "GEMINI.md").resolve()

        # HARNESS.md
        if assets["harness_md"] is None:
            if (root / "HARNESS.md").is_file():
                assets["harness_md"] = (root / "HARNESS.md").resolve()
            elif (root / "rules" / "HARNESS.md").is_file():
                assets["harness_md"] = (root / "rules" / "HARNESS.md").resolve()

    return assets


def scaffold_antigravity_project(
    target_path: Path | str,
    profile: str = "full",
    dry_run: bool = False,
    force: bool = False,
) -> ScaffoldResult:
    """Scaffold a full Antigravity project environment into target directory.

    Args:
        target_path: Destination directory path (relative or absolute).
        profile: Scaffolding preset ('full', 'minimal', 'antigravity').
        dry_run: If True, preview created files without touching disk.
        force: If True, overwrite pre-existing files; otherwise skip them.

    Returns:
        ScaffoldResult with execution statistics and created/skipped/modified files.

    Raises:
        ValueError: If target_path is invalid, attempts path traversal,
                    or an unsupported profile is requested.
    """
    valid_profiles = {"full", "minimal", "antigravity"}
    if profile not in valid_profiles:
        raise ValueError(
            f"Unknown profile '{profile}'. Expected one of: "
            f"{', '.join(sorted(valid_profiles))}"
        )

    target_resolved = Path(target_path).resolve()

    # Path traversal and system directory protection
    target_path_str = str(target_path).rstrip(os.sep) or os.sep
    resolved_str = str(target_resolved).rstrip(os.sep) or os.sep
    if (
        target_path_str.lower() in PROTECTED_SYSTEM_DIRS
        or resolved_str.lower() in PROTECTED_SYSTEM_DIRS
        or target_resolved.parent == target_resolved
    ):
        raise ValueError(
            f"Refusing to scaffold into protected system directory: {target_path}"
        )

    # Reject if target exists as a regular file
    if target_resolved.exists() and not target_resolved.is_dir():
        raise ValueError(
            f"Target path exists and is not a directory: {target_path}"
        )

    sources = _find_asset_sources()

    # Plan items: (relative_path_str, content_or_source_file, is_script)
    # If content_or_source_file is Path -> copy from source Path
    # If content_or_source_file is str -> write text content
    plan: list[tuple[str, Path | str, bool]] = []

    # 1. Rules: GEMINI.md & HARNESS.md
    if sources["gemini_md"] and Path(sources["gemini_md"]).is_file():
        plan.append(("GEMINI.md", Path(sources["gemini_md"]), False))
    else:
        plan.append(("GEMINI.md", FALLBACK_GEMINI_MD, False))

    if sources["harness_md"] and Path(sources["harness_md"]).is_file():
        plan.append(("HARNESS.md", Path(sources["harness_md"]), False))
    else:
        plan.append(("HARNESS.md", FALLBACK_HARNESS_MD, False))

    # 2. Hooks: .agents/hooks.json & scripts/hooks/*.py
    if sources["hooks_json"] and Path(sources["hooks_json"]).is_file():
        plan.append((".agents/hooks.json", Path(sources["hooks_json"]), False))
    else:
        plan.append((".agents/hooks.json", FALLBACK_HOOKS_JSON, False))

    hooks_scripts_dir = sources["hooks_scripts_dir"]
    if hooks_scripts_dir and Path(hooks_scripts_dir).is_dir():
        for script_file in sorted(Path(hooks_scripts_dir).glob("*.py")):
            rel_hook_script = f"scripts/hooks/{script_file.name}"
            plan.append((rel_hook_script, script_file, True))

    # 3. MCP: .agents/mcp_config.json & scripts/mcp_server.py
    if sources["mcp_config_json"] and Path(sources["mcp_config_json"]).is_file():
        plan.append((".agents/mcp_config.json", Path(sources["mcp_config_json"]), False))
    else:
        plan.append((".agents/mcp_config.json", FALLBACK_MCP_CONFIG_JSON, False))

    mcp_script = sources["mcp_server_script"]
    if mcp_script and Path(mcp_script).is_file():
        plan.append(("scripts/mcp_server.py", Path(mcp_script), True))

    # 4. Subagents: .agents/subagents/registry.json & definitions/*.md
    subagents_dir = sources["subagents_dir"]
    subagent_count = 0
    if subagents_dir and Path(subagents_dir).is_dir():
        reg_file = Path(subagents_dir) / "registry.json"
        defs_dir = Path(subagents_dir) / "definitions"

        if reg_file.is_file():
            reg_data = json.loads(reg_file.read_text(encoding="utf-8"))
            agents_list = reg_data.get("agents", [])

            if profile == "minimal":
                filtered_agents = [
                    a for a in agents_list
                    if a.get("id") in MINIMAL_SUBAGENTS
                ]
                reg_data["agents"] = filtered_agents
                reg_data["total_agents"] = len(filtered_agents)
                plan.append((
                    ".agents/subagents/registry.json",
                    json.dumps(reg_data, indent=2) + "\n",
                    False,
                ))
                if defs_dir.is_dir():
                    for ag_id in sorted(MINIMAL_SUBAGENTS):
                        def_file = defs_dir / f"{ag_id}.md"
                        if def_file.is_file():
                            plan.append((
                                f".agents/subagents/definitions/{ag_id}.md",
                                def_file,
                                False,
                            ))
                            subagent_count += 1
            else:
                plan.append((".agents/subagents/registry.json", reg_file, False))
                if defs_dir.is_dir():
                    for def_file in sorted(defs_dir.glob("*.md")):
                        plan.append((
                            f".agents/subagents/definitions/{def_file.name}",
                            def_file,
                            False,
                        ))
                        subagent_count += 1

    # 5. Skills: .agents/skills/<name>/SKILL.md
    skills_dir = sources["skills_dir"]
    skill_count = 0
    if skills_dir and Path(skills_dir).is_dir():
        for item in sorted(Path(skills_dir).iterdir()):
            if not item.is_dir():
                continue
            skill_md = item / "SKILL.md"
            if not skill_md.is_file():
                continue

            if profile == "minimal" and item.name not in MINIMAL_SKILLS:
                continue

            rel_skill_path = f".agents/skills/{item.name}/SKILL.md"
            plan.append((rel_skill_path, skill_md, False))
            skill_count += 1

    # Execute plan
    created_files: list[str] = []
    skipped_files: list[str] = []
    modified_files: list[str] = []

    for rel_path, src, is_script in plan:
        dest_path = (target_resolved / rel_path).resolve()

        # Security: verify destination is strictly confined to target
        if not dest_path.is_relative_to(target_resolved):
            raise ValueError(
                f"Path traversal detected: {rel_path} escapes target {target_resolved}"
            )

        dest_exists = dest_path.exists()

        if dest_exists:
            if not force:
                skipped_files.append(rel_path)
                continue
            else:
                modified_files.append(rel_path)
        else:
            created_files.append(rel_path)

        if not dry_run:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(src, Path):
                shutil.copy2(src, dest_path)
            else:
                dest_path.write_text(src, encoding="utf-8")

            if is_script and os.name != "nt":
                try:
                    dest_path.chmod(
                        dest_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                    )
                except OSError:
                    pass

    # Ensure .mekong metadata directory exists when scaffolding live
    if not dry_run:
        (target_resolved / ".mekong").mkdir(parents=True, exist_ok=True)

    stats: dict[str, int] = {
        "skills": skill_count,
        "subagents": subagent_count,
        "hooks": len([p for p, _, _ in plan if "hooks" in p]),
        "mcp": len([p for p, _, _ in plan if "mcp" in p]),
        "rules": len([p for p, _, _ in plan if p in ("GEMINI.md", "HARNESS.md")]),
        "total_files": len(plan),
    }

    return ScaffoldResult(
        target_path=target_resolved,
        profile=profile,
        dry_run=dry_run,
        force=force,
        created_files=created_files,
        skipped_files=skipped_files,
        modified_files=modified_files,
        stats=stats,
        success=True,
    )
