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

logger = logging.getLogger(__name__)

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

FALLBACK_AGENTS_MD: str = """# AGENTS.md — Mekong CLI
# Read by: Claude Code, Gemini CLI, OpenCode, Cursor, Codex, Amp

## Project
**CEO Solo Agentic Harness Engineering Platform.**
One CEO delegates to 4 layer agents (Business, Product, Engineering, Ops).
Harness engineering: shape the environment around AI agents for reliability.

## Commands
Execute via: `python3 -m src.main <name> <args>`
Engine: Python CLI (Typer) → Harness PEV → LLM Router → Agent Layer

## Build & Test
```bash
python3 -m pytest tests/
```

## Style
Python: snake_case, type hints. Commits: conventional (feat/fix/refactor/docs/test).
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

---

## 2. CEO Override Clauses
1. **CEO may override any decision** without explanation.
2. CEO may bypass review gates by adding `--ceo-override` to any command.
3. CEO may terminate any running subagent by name via `/abort <agent>`.
"""

FALLBACK_PYPROJECT_TOML: str = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mekong-app"
version = "0.1.0"
description = "Mekong Autonomous Agent Project"
readme = "README.md"
requires-python = ">=3.10"
dependencies = []

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
"""

FALLBACK_ENV_EXAMPLE: str = """MEKONG_ENV=development
MEKONG_DEBUG=1
MEKONG_LOG_LEVEL=INFO
"""

FALLBACK_LICENSE: str = """MIT License

Copyright (c) 2026 MekongMind

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

FALLBACK_PRE_TOOL_GUARDRAIL_PY: str = """#!/usr/bin/env python3
\"\"\"Pre-tool use safety guardrail hook for Mekong Antigravity platform.\"\"\"
import sys
import json

def main() -> int:
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""

FALLBACK_POST_TOOL_AUDIT_PY: str = """#!/usr/bin/env python3
\"\"\"Post-tool audit hook for Mekong Antigravity platform.\"\"\"
import sys

def main() -> int:
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""

FALLBACK_MCP_SERVER_PY: str = """#!/usr/bin/env python3
\"\"\"Standalone MCP stdio JSON-RPC server for Mekong project.\"\"\"
import sys
import json

def main() -> None:
    pass

if __name__ == "__main__":
    main()
"""

# ── Domain Agent Definitions for Registry ────────────────────────────────────
CORE_6_AGENTS: list[dict[str, Any]] = [
    {
        "id": "sun-tzu",
        "name": "Sun Tzu — Strategic Counsel",
        "role": "advisor",
        "description": "Advisory strategist for hard decisions. Concise counsel in single turn.",
        "model_tier": "pro",
        "context_budget": 30000,
        "tools": ["Read", "Bash", "Write", "Task"],
        "definition_path": ".agents/subagents/definitions/sun-tzu.md",
        "can_override": False,
    },
    {
        "id": "ceo",
        "name": "CEO Solo",
        "role": "Chief Executive Officer",
        "description": "Strategic decision-maker and final authority. Delegates to layer agents.",
        "model_tier": "pro",
        "context_budget": 30000,
        "tools": ["Read", "Write", "Edit", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/ceo.md",
        "can_override": True,
    },
    {
        "id": "cto",
        "name": "CTO — Chief Technology Officer",
        "role": "Technology Leadership",
        "description": "Technical architecture, system integrity, engineering standards.",
        "model_tier": "pro",
        "context_budget": 28000,
        "tools": ["Read", "Write", "Edit", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/cto.md",
        "can_override": False,
    },
    {
        "id": "pm",
        "name": "PM — Product Manager",
        "role": "Product",
        "description": "Product specifications, user stories, acceptance criteria.",
        "model_tier": "pro",
        "context_budget": 20000,
        "tools": ["Read", "Write", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/pm.md",
        "can_override": False,
    },
    {
        "id": "eng",
        "name": "ENG — Lead Engineer",
        "role": "Engineering",
        "description": "Software implementation, code review, test suite execution.",
        "model_tier": "pro",
        "context_budget": 24000,
        "tools": ["Read", "Write", "Edit", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/eng.md",
        "can_override": False,
    },
    {
        "id": "ops",
        "name": "OPS — Operations Engineer",
        "role": "Operations",
        "description": "System monitoring, health checks, incident response.",
        "model_tier": "pro",
        "context_budget": 16000,
        "tools": ["Read", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/ops.md",
        "can_override": False,
    },
]

FULL_25_AGENTS: list[dict[str, Any]] = CORE_6_AGENTS + [
    {
        "id": "ae",
        "name": "AE — Account Executive",
        "role": "Business Development",
        "description": "Handles client lifecycle, proposals, contracts.",
        "model_tier": "inherit",
        "context_budget": 16000,
        "tools": ["Read", "Write", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/ae.md",
        "can_override": False,
    },
    {
        "id": "cfo",
        "name": "CFO — Chief Financial Officer",
        "role": "Finance",
        "description": "Financial planning, VAS accounting compliance, tax optimization.",
        "model_tier": "pro",
        "context_budget": 24000,
        "tools": ["Read", "Write", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/cfo.md",
        "can_override": False,
    },
    {
        "id": "cmo",
        "name": "CMO — Chief Marketing Officer",
        "role": "Marketing",
        "description": "Marketing strategy, brand narrative, growth campaigns.",
        "model_tier": "pro",
        "context_budget": 20000,
        "tools": ["Read", "Write", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/cmo.md",
        "can_override": False,
    },
    {
        "id": "coo",
        "name": "COO — Chief Operating Officer",
        "role": "Operations Leadership",
        "description": "Business process optimization, cross-functional execution.",
        "model_tier": "pro",
        "context_budget": 22000,
        "tools": ["Read", "Write", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/coo.md",
        "can_override": False,
    },
    {
        "id": "cso",
        "name": "CSO — Chief Strategy Officer",
        "role": "Strategy",
        "description": "Long-term market positioning, competitive moats.",
        "model_tier": "pro",
        "context_budget": 24000,
        "tools": ["Read", "Write", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/cso.md",
        "can_override": False,
    },
    {
        "id": "planner",
        "name": "Planner — Task Decomposition",
        "role": "Product",
        "description": "Decomposes high-level goals into dependency DAGs.",
        "model_tier": "pro",
        "context_budget": 20000,
        "tools": ["Read", "Write", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/planner.md",
        "can_override": False,
    },
    {
        "id": "tester",
        "name": "QA — Test Engineer",
        "role": "Quality Assurance",
        "description": "Unit, integration, and property-based test suites.",
        "model_tier": "pro",
        "context_budget": 22000,
        "tools": ["Read", "Write", "Edit", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/tester.md",
        "can_override": False,
    },
    {
        "id": "code-reviewer",
        "name": "Code Reviewer — Integrity Auditor",
        "role": "Engineering",
        "description": "Reviews code changes against architectural standards.",
        "model_tier": "pro",
        "context_budget": 24000,
        "tools": ["Read", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/code-reviewer.md",
        "can_override": False,
    },
    {
        "id": "code-simplifier",
        "name": "Code Simplifier — Refactoring",
        "role": "Engineering",
        "description": "Refactors code to reduce cyclomatic complexity.",
        "model_tier": "pro",
        "context_budget": 20000,
        "tools": ["Read", "Write", "Edit", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/code-simplifier.md",
        "can_override": False,
    },
    {
        "id": "debugger",
        "name": "Debugger — Root Cause Analysis",
        "role": "Engineering",
        "description": "Isolates exceptions, inspects stack traces, formulates fixes.",
        "model_tier": "pro",
        "context_budget": 24000,
        "tools": ["Read", "Write", "Edit", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/debugger.md",
        "can_override": False,
    },
    {
        "id": "docs-manager",
        "name": "Docs Manager — Technical Writer",
        "role": "Documentation",
        "description": "Maintains API specs, architectural walk-throughs, and SOPs.",
        "model_tier": "inherit",
        "context_budget": 18000,
        "tools": ["Read", "Write", "Edit", "Bash"],
        "definition_path": ".agents/subagents/definitions/docs-manager.md",
        "can_override": False,
    },
    {
        "id": "fullstack-developer",
        "name": "Fullstack Developer — Feature Builder",
        "role": "Engineering",
        "description": "Implements frontend and backend features end-to-end.",
        "model_tier": "pro",
        "context_budget": 24000,
        "tools": ["Read", "Write", "Edit", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/fullstack-developer.md",
        "can_override": False,
    },
    {
        "id": "git-manager",
        "name": "Git Manager — Version Control",
        "role": "Engineering",
        "description": "Branching strategies, atomic commits, conflict resolution.",
        "model_tier": "inherit",
        "context_budget": 16000,
        "tools": ["Read", "Bash"],
        "definition_path": ".agents/subagents/definitions/git-manager.md",
        "can_override": False,
    },
    {
        "id": "journal-writer",
        "name": "Journal Writer — Execution Chronicler",
        "role": "Operations",
        "description": "Maintains mission history, decision logs, and audit entries.",
        "model_tier": "inherit",
        "context_budget": 16000,
        "tools": ["Read", "Write", "Bash"],
        "definition_path": ".agents/subagents/definitions/journal-writer.md",
        "can_override": False,
    },
    {
        "id": "kongming",
        "name": "Zhuge Liang — Strategic Tactician",
        "role": "advisor",
        "description": "Calculates contingent probabilities and contingency plans.",
        "model_tier": "pro",
        "context_budget": 26000,
        "tools": ["Read", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/kongming.md",
        "can_override": False,
    },
    {
        "id": "project-manager",
        "name": "Project Manager — Sprint Orchestration",
        "role": "Product",
        "description": "Tracks milestone velocity, assigns tickets, unblocks workers.",
        "model_tier": "pro",
        "context_budget": 20000,
        "tools": ["Read", "Write", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/project-manager.md",
        "can_override": False,
    },
    {
        "id": "researcher",
        "name": "Researcher — Deep Domain Inquiry",
        "role": "Research",
        "description": "Synthesizes competitive landscapes and legal standards.",
        "model_tier": "pro",
        "context_budget": 24000,
        "tools": ["Read", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/researcher.md",
        "can_override": False,
    },
    {
        "id": "ui-ux-designer",
        "name": "UI/UX Designer — Interface Architect",
        "role": "Design",
        "description": "User journey wireframing, component tokens, accessibility.",
        "model_tier": "pro",
        "context_budget": 20000,
        "tools": ["Read", "Write", "Bash"],
        "definition_path": ".agents/subagents/definitions/ui-ux-designer.md",
        "can_override": False,
    },
    {
        "id": "brainstormer",
        "name": "Brainstormer — Divergent Ideation",
        "role": "Strategy",
        "description": "Generates multi-perspective solutions for ambiguous problems.",
        "model_tier": "pro",
        "context_budget": 22000,
        "tools": ["Read", "Bash", "Task"],
        "definition_path": ".agents/subagents/definitions/brainstormer.md",
        "can_override": False,
    },
]

# ── Minimal & Core Skill Catalog ─────────────────────────────────────────────
CORE_SKILLS: list[tuple[str, str]] = [
    ("cook", "Feature development and plan execution (PEV engine)."),
    ("plan", "Implementation planning and task backlog breakdown."),
    ("ship", "Production release pipeline: lint, test, commit, deploy."),
    ("doctor", "System diagnostic tool and health check inspection."),
    ("binh-phap", "Sun Tzu Art of War strategic counsel and loop control."),
    ("status", "System health and API connectivity status monitor."),
    ("agent", "Autonomous agent lifecycle and swarm coordination."),
    ("cfo", "CFO financial operations and VAS compliance analysis."),
    ("cmo", "CMO growth marketing campaigns and editorial calendar."),
    ("cto", "CTO architecture audits and engineering standards."),
    ("pm", "Product management specifications and backlog grooming."),
    ("dev", "Fullstack engineering commands and code generation."),
    ("ops", "Operations incident response and system telemetry."),
    ("quick-start", "Interactive 5-step project kickoff walkthrough."),
    ("daily", "Daily status report and activity summary."),
    ("bmad", "BMAD multi-agent workflow orchestration."),
    ("build", "Build task generation from specifications."),
    ("spec", "Feature request to requirements specification compiler."),
    ("mk-clean", "Clean cache, temporary files, and build artifacts."),
    ("mk-test", "Run project test suite and report results."),
    ("mk-lint", "Run static analysis and code quality checks."),
    ("idea", "BizPlan OS Zero-to-IPO company generation engine."),
    ("ke-toan", "VAS Vietnamese Accounting Standards and Circular 200/133."),
    ("thue", "Personal, corporate, and VAT tax calculation engine."),
    ("zalo-oa", "Zalo Official Account messaging and notification gateway."),
]


# ── Custom Exceptions ────────────────────────────────────────────────────────
class CyclicDependencyError(Exception):
    """Raised when circular dependencies exist in the task dependency DAG."""


# ── Data Models ──────────────────────────────────────────────────────────────
class TaskStatus(str, Enum):
    """Execution status of a bootstrap task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskTiming:
    """Execution timing and telemetry for a single task."""
    task_id: str
    name: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    worker_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert task timing to clean dictionary representation."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "worker_id": self.worker_id,
            "status": self.status.value if isinstance(self.status, TaskStatus) else str(self.status),
            "error": self.error,
        }


@dataclass
class BootstrapTask:
    """A single unit of work in the parallel bootstrap pipeline."""
    id: str
    name: str
    dependencies: list[str] = field(default_factory=list)
    action: Callable[["BootstrapContext"], Any] = field(default=lambda ctx: None)
    optional: bool = False
    timeout_seconds: float = 30.0


@dataclass
class BootstrapContext:
    """Thread-safe execution context for workspace scaffolding."""
    target_path: Path
    profile: str = "standard"
    template: str = "default"
    workers: int = 4
    dry_run: bool = False
    force: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)
    created_files: list[str] = field(default_factory=list)
    created_directories: list[str] = field(default_factory=list)
    overwritten_files: dict[str, str] = field(default_factory=dict)
    task_timings: dict[str, TaskTiming] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def write_file(self, rel_path: str, content: str) -> None:
        """Thread-safe file creation with immediate snapshot registration."""
        with self.lock:
            clean_rel = os.path.normpath(rel_path).lstrip(os.sep)
            dest = (self.target_path / clean_rel).resolve()
            target_res = self.target_path.resolve()

            # Boundary verification
            if not dest.is_relative_to(target_res):
                raise ValueError(
                    f"Path traversal detected: {rel_path} escapes target directory {target_res}"
                )

            dest_exists = dest.exists()
            if dest_exists and not self.force:
                # File exists and force=False -> do not overwrite
                return

            if dest_exists:
                if clean_rel not in self.overwritten_files:
                    try:
                        self.overwritten_files[clean_rel] = dest.read_text(encoding="utf-8")
                    except Exception:
                        self.overwritten_files[clean_rel] = ""
            else:
                if clean_rel not in self.created_files:
                    self.created_files.append(clean_rel)

            if not self.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")

                # If script, set executable permissions on POSIX
                if (
                    clean_rel.startswith("scripts/")
                    and clean_rel.endswith(".py")
                    and os.name != "nt"
                ):
                    try:
                        dest.chmod(
                            dest.stat().st_mode
                            | stat.S_IXUSR
                            | stat.S_IXGRP
                            | stat.S_IXOTH
                        )
                    except OSError:
                        pass

    def register_dir(self, rel_dir: str) -> None:
        """Thread-safe directory registration."""
        with self.lock:
            clean_rel = os.path.normpath(rel_dir).lstrip(os.sep)
            dest = (self.target_path / clean_rel).resolve()
            target_res = self.target_path.resolve()

            if not dest.is_relative_to(target_res):
                raise ValueError(
                    f"Path traversal detected: {rel_dir} escapes target directory {target_res}"
                )

            dest_existed = dest.exists()
            if not self.dry_run:
                dest.mkdir(parents=True, exist_ok=True)

            if not dest_existed and clean_rel not in self.created_directories:
                self.created_directories.append(clean_rel)


@dataclass
class BootstrapResult:
    """Result summary of parallel project bootstrap execution."""
    ok: bool
    rolled_back: bool
    error: Optional[str]
    target_path: Path
    profile: str
    template: str
    workers: int
    dry_run: bool
    created_files: list[str] = field(default_factory=list)
    created_directories: list[str] = field(default_factory=list)
    task_timings: dict[str, TaskTiming] = field(default_factory=dict)
    duration_ms: float = 0.0
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Boolean success status."""
        return self.ok

    def to_dict(self) -> dict[str, Any]:
        """Convert result to clean dictionary representation."""
        target_str = str(self.target_path.resolve())
        timings_dict = {
            tid: (timing.to_dict() if hasattr(timing, "to_dict") else dataclasses.asdict(timing))
            for tid, timing in self.task_timings.items()
        }
        return {
            "ok": self.ok,
            "success": self.ok,
            "rolled_back": self.rolled_back,
            "error": self.error,
            "target_path": target_str,
            "target": target_str,
            "profile": self.profile,
            "template": self.template,
            "workers": self.workers,
            "dry_run": self.dry_run,
            "created_files": list(self.created_files),
            "created_directories": list(self.created_directories),
            "task_timings": timings_dict,
            "duration_ms": self.duration_ms,
            "stats": self.stats,
        }


# Global state for MCP status inspection
_LAST_BOOTSTRAP_RESULT: Optional[BootstrapResult] = None


def get_bootstrap_status() -> dict[str, Any]:
    """Retrieve current bootstrap engine status and last execution result."""
    global _LAST_BOOTSTRAP_RESULT
    if _LAST_BOOTSTRAP_RESULT is None:
        return {
            "status": "idle",
            "last_run": None,
            "version": "1.0.0",
            "supported_profiles": ["smoke", "standard", "full"],
            "supported_templates": ["default", "vas", "fintech", "agent"],
        }
    return {
        "status": "success" if _LAST_BOOTSTRAP_RESULT.ok else "failed",
        "last_run": _LAST_BOOTSTRAP_RESULT.to_dict(),
        "version": "1.0.0",
        "supported_profiles": ["smoke", "standard", "full"],
        "supported_templates": ["default", "vas", "fintech", "agent"],
    }


# ── Topological DAG Dependency Resolution ────────────────────────────────────
def resolve_dag_dependencies(tasks: list[BootstrapTask]) -> list[str]:
    """Topologically sort tasks and verify absence of cycles using Kahn's algorithm.

    Raises:
        ValueError: If a task has an unknown dependency.
        CyclicDependencyError: If a circular dependency is detected.

    Returns:
        List of task IDs in topological execution order.
    """
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

    # Queue all nodes with 0 in-degree
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


# Alias for compatibility
resolve_dag = resolve_dag_dependencies


# ── Asset Discovery Helpers ──────────────────────────────────────────────────
def _find_asset_sources() -> dict[str, Any]:
    """Locate source assets using discovery hierarchy."""
    candidate_roots: list[Path] = []

    env_root = os.environ.get("MEKONG_ROOT")
    if env_root:
        candidate_roots.append(Path(env_root).resolve())

    dev_root = Path(__file__).resolve().parents[2]
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


# ── Scaffolding Tasks Implementation ─────────────────────────────────────────
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

    # 1. GEMINI.md
    if sources["gemini_md"] and Path(sources["gemini_md"]).is_file():
        gemini_text = Path(sources["gemini_md"]).read_text(encoding="utf-8")
    else:
        gemini_text = FALLBACK_GEMINI_MD
    context.write_file("GEMINI.md", gemini_text)

    # 2. AGENTS.md
    dev_root = Path(__file__).resolve().parents[2]
    if (dev_root / "AGENTS.md").is_file():
        agents_text = (dev_root / "AGENTS.md").read_text(encoding="utf-8")
    else:
        agents_text = FALLBACK_AGENTS_MD
    context.write_file("AGENTS.md", agents_text)

    # 3. HARNESS.md
    if sources["harness_md"] and Path(sources["harness_md"]).is_file():
        harness_text = Path(sources["harness_md"]).read_text(encoding="utf-8")
    else:
        harness_text = FALLBACK_HARNESS_MD
    context.write_file("HARNESS.md", harness_text)

    # 4. pyproject.toml
    context.write_file("pyproject.toml", FALLBACK_PYPROJECT_TOML)

    # 5. .env.example
    context.write_file(".env.example", FALLBACK_ENV_EXAMPLE)

    # 6. LICENSE
    context.write_file("LICENSE", FALLBACK_LICENSE)

    # 7. dna/core-dna.json
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


def task_scaffold_subagents(context: BootstrapContext) -> None:
    """Scaffold subagent registry and markdown definitions based on profile."""
    sources = _find_asset_sources()
    subagents_dir = sources["subagents_dir"]

    agents_to_scaffold: list[dict[str, Any]] = []
    if context.profile in ("smoke", "minimal"):
        agents_to_scaffold = CORE_6_AGENTS
    else:
        agents_to_scaffold = FULL_25_AGENTS

    # If sources are present, attempt to pull definitions
    source_defs_dir = (Path(subagents_dir) / "definitions") if subagents_dir else None

    # Write registry.json
    reg_data = {
        "schema": "antigravity.subagents.registry.v1",
        "total_agents": len(agents_to_scaffold),
        "agents": agents_to_scaffold,
    }
    context.write_file(
        ".agents/subagents/registry.json",
        json.dumps(reg_data, indent=2) + "\n",
    )

    # Write each definition markdown
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

    # If dev repo skills directory exists, also check for additional skills
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

    # Ensure all selected skills are written
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

    # .agents/mcp_config.json
    if sources["mcp_config_json"] and Path(sources["mcp_config_json"]).is_file():
        mcp_cfg_text = Path(sources["mcp_config_json"]).read_text(encoding="utf-8")
    else:
        mcp_cfg_text = FALLBACK_MCP_CONFIG_JSON
    context.write_file(".agents/mcp_config.json", mcp_cfg_text)

    # scripts/mcp_server.py
    if sources["mcp_server_script"] and Path(sources["mcp_server_script"]).is_file():
        mcp_srv_text = Path(sources["mcp_server_script"]).read_text(encoding="utf-8")
    else:
        mcp_srv_text = FALLBACK_MCP_SERVER_PY
    context.write_file("scripts/mcp_server.py", mcp_srv_text)


def task_scaffold_hooks(context: BootstrapContext) -> None:
    """Scaffold lifecycle safety hooks configuration and scripts."""
    sources = _find_asset_sources()

    # .agents/hooks.json
    if sources["hooks_json"] and Path(sources["hooks_json"]).is_file():
        hooks_cfg_text = Path(sources["hooks_json"]).read_text(encoding="utf-8")
    else:
        hooks_cfg_text = FALLBACK_HOOKS_JSON
    context.write_file(".agents/hooks.json", hooks_cfg_text)

    # scripts/hooks/pre_tool_guardrail.py
    hooks_scripts_dir = sources["hooks_scripts_dir"]
    if hooks_scripts_dir and (Path(hooks_scripts_dir) / "pre_tool_guardrail.py").is_file():
        pre_text = (Path(hooks_scripts_dir) / "pre_tool_guardrail.py").read_text(encoding="utf-8")
    else:
        pre_text = FALLBACK_PRE_TOOL_GUARDRAIL_PY
    context.write_file("scripts/hooks/pre_tool_guardrail.py", pre_text)

    # scripts/hooks/post_tool_audit.py
    if hooks_scripts_dir and (Path(hooks_scripts_dir) / "post_tool_audit.py").is_file():
        post_text = (Path(hooks_scripts_dir) / "post_tool_audit.py").read_text(encoding="utf-8")
    else:
        post_text = FALLBACK_POST_TOOL_AUDIT_PY
    context.write_file("scripts/hooks/post_tool_audit.py", post_text)


def task_scaffold_templates(context: BootstrapContext) -> None:
    """Scaffold domain-specific templates (default, vas, fintech, agent)."""
    tpl = context.template.lower()
    if tpl == "default":
        context.write_file(
            "src/__init__.py",
            '"""Mekong Application Package."""\n__version__ = "0.1.0"\n',
        )
        context.write_file(
            "src/main.py",
            '"""Application entry point."""\n\ndef main() -> int:\n    print("Hello from Mekong CLI Project!")\n    return 0\n\nif __name__ == "__main__":\n    import sys\n    sys.exit(main())\n',
        )
        context.write_file(
            "tests/test_main.py",
            '"""Smoke test for application."""\nfrom src.main import main\n\ndef test_main():\n    assert main() == 0\n',
        )
    elif tpl == "vas":
        context.write_file("src/vas/__init__.py", '"""VAS Accounting Module."""\n')
        context.write_file(
            "src/vas/accounting.py",
            '''"""Vietnamese Accounting System (VAS) core ledger."""
from typing import List, Dict, Any

class VasLedger:
    def __init__(self) -> None:
        self.entries: List[Dict[str, Any]] = []

    def record_entry(self, debit_acc: str, credit_acc: str, amount: float, description: str = "") -> Dict[str, Any]:
        entry = {
            "debit": debit_acc,
            "credit": credit_acc,
            "amount": amount,
            "description": description,
        }
        self.entries.append(entry)
        return entry

    def total_balance(self) -> float:
        return sum(e["amount"] for e in self.entries)
''',
        )
        context.write_file(
            "src/vas/tt78_invoice.py",
            '''"""Circular 78 / Decree 123 E-Invoice validation."""
from typing import Dict, Any

def validate_invoice(invoice: Dict[str, Any]) -> bool:
    required_fields = ["invoice_number", "seller_tax_id", "buyer_tax_id", "total_amount"]
    return all(field in invoice for field in required_fields)
''',
        )
        chart_of_accounts = {
            "standard": "VAS Circular 200/2014/TT-BTC",
            "accounts": {
                "111": "Tien mat (Cash)",
                "112": "Tien gui ngan hang (Bank deposits)",
                "131": "Phai thu khach hang (Receivables)",
                "331": "Phai tra nguoi ban (Payables)",
                "511": "Doanh thu ban hang (Revenue)",
                "642": "Chi phi quan ly doanh nghiep (Management expenses)",
            },
        }
        context.write_file(
            "src/vas/chart_of_accounts.json",
            json.dumps(chart_of_accounts, indent=2) + "\n",
        )
        context.write_file(
            "tests/test_vas.py",
            '''"""Tests for VAS accounting module."""
from src.vas.accounting import VasLedger
from src.vas.tt78_invoice import validate_invoice

def test_vas_ledger():
    ledger = VasLedger()
    entry = ledger.record_entry("111", "511", 1000000.0, "Cash sale")
    assert entry["amount"] == 1000000.0
    assert ledger.total_balance() == 1000000.0

def test_validate_invoice():
    inv = {
        "invoice_number": "HD001",
        "seller_tax_id": "0100109106",
        "buyer_tax_id": "0300123456",
        "total_amount": 5000000.0,
    }
    assert validate_invoice(inv) is True
''',
        )
    elif tpl == "fintech":
        context.write_file("src/fintech/__init__.py", '"""Fintech Payment Module."""\n')
        context.write_file(
            "src/fintech/vietqr.py",
            '''"""VietQR EMVCo specification generator."""
def generate_vietqr_payload(bank_bin: str, account_number: str, amount: float, memo: str = "") -> str:
    return f"00020101021238570010A00000072701270006{bank_bin}01{len(account_number):02d}{account_number}54{len(str(int(amount))):02d}{int(amount)}5802VN62{len(memo):02d}{memo}6304"
''',
        )
        context.write_file(
            "src/fintech/napas247.py",
            '''"""NAPAS 24/7 instant payment reconciliation."""
from typing import Dict, Any

def reconcile_transaction(tx_id: str, status: str) -> Dict[str, Any]:
    return {"tx_id": tx_id, "reconciled": status == "SUCCESS", "status": status}
''',
        )
        context.write_file(
            "src/fintech/pci_tokens.py",
            '''"""PCI-DSS compliant token masking."""
def mask_card(card_number: str) -> str:
    clean = card_number.replace(" ", "").replace("-", "")
    if len(clean) < 10:
        return "****"
    return f"{clean[:6]}******{clean[-4:]}"
''',
        )
        context.write_file(
            "tests/test_fintech.py",
            '''"""Tests for fintech payment module."""
from src.fintech.vietqr import generate_vietqr_payload
from src.fintech.napas247 import reconcile_transaction
from src.fintech.pci_tokens import mask_card

def test_vietqr():
    payload = generate_vietqr_payload("970415", "123456789", 50000.0, "Coffee")
    assert "970415" in payload
    assert "123456789" in payload

def test_reconciliation():
    res = reconcile_transaction("TX1001", "SUCCESS")
    assert res["reconciled"] is True

def test_mask_card():
    assert mask_card("4111222233334444") == "411122******4444"
''',
        )
    elif tpl == "agent":
        context.write_file("src/agents/__init__.py", '"""Agent Swarm Architecture."""\n')
        context.write_file(
            "src/agents/swarm.py",
            '''"""Agent Swarm coordinator."""
from typing import List, Dict, Any

class AgentSwarm:
    def __init__(self) -> None:
        self.agents: Dict[str, Dict[str, Any]] = {}

    def register_agent(self, agent_id: str, role: str, capabilities: List[str]) -> None:
        self.agents[agent_id] = {"id": agent_id, "role": role, "capabilities": capabilities}

    def dispatch(self, task_type: str) -> List[str]:
        return [aid for aid, a in self.agents.items() if task_type in a["capabilities"]]
''',
        )
        context.write_file(
            "src/agents/memory_mesh.py",
            '''"""Federated Memory Mesh for autonomous agents."""
from typing import Dict, Any, Optional

class MemoryMesh:
    def __init__(self) -> None:
        self.store: Dict[str, Any] = {}

    def recall(self, key: str) -> Optional[Any]:
        return self.store.get(key)

    def remember(self, key: str, value: Any) -> None:
        self.store[key] = value
''',
        )
        context.write_file(
            "src/agents/agi_loop.py",
            '''"""Autonomous AGI Plan-Execute-Verify loop runner."""
from typing import Dict, Any

class AgiLoop:
    def __init__(self, agent_name: str = "SoloCEO") -> None:
        self.agent_name = agent_name
        self.cycles = 0

    def step(self, goal: str) -> Dict[str, Any]:
        self.cycles += 1
        return {"cycle": self.cycles, "goal": goal, "status": "completed"}
''',
        )
        context.write_file(
            "tests/test_agent.py",
            '''"""Tests for agent module."""
from src.agents.swarm import AgentSwarm
from src.agents.memory_mesh import MemoryMesh
from src.agents.agi_loop import AgiLoop

def test_swarm():
    swarm = AgentSwarm()
    swarm.register_agent("ceo", "CEO", ["plan", "decide"])
    assert swarm.dispatch("plan") == ["ceo"]

def test_memory():
    mesh = MemoryMesh()
    mesh.remember("key1", "val1")
    assert mesh.recall("key1") == "val1"

def test_agi_loop():
    loop = AgiLoop()
    res = loop.step("Run bootstrap")
    assert res["status"] == "completed"
''',
        )
    else:
        raise ValueError(
            f"Unknown template '{context.template}'. Expected one of: default, vas, fintech, agent"
        )


def task_init_git(context: BootstrapContext) -> None:
    """Initialize git repository and .gitignore (optional task)."""
    git_bin = shutil.which("git")
    target_resolved = context.target_path.resolve()
    git_dir = target_resolved / ".git"

    if git_bin and not git_dir.exists() and not context.dry_run:
        context.metadata["git_dir_created_by_us"] = True
        try:
            subprocess.run(
                [git_bin, "init", str(target_resolved)],
                capture_output=True,
                check=False,
                timeout=10,
            )
        except Exception as exc:
            logger.warning("Git initialization failed: %s", exc)

    gitignore_content = """__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.env
.venv/
env/
venv/
.mekong/
"""
    context.write_file(".gitignore", gitignore_content)


def task_verify_integrity(context: BootstrapContext) -> None:
    """Verify integrity of all created files and valid JSON formatting."""
    if context.dry_run:
        return

    target_resolved = context.target_path.resolve()
    for rel_f in context.created_files:
        f_path = (target_resolved / rel_f).resolve()
        if not f_path.is_file():
            raise RuntimeError(f"Integrity check failed: file missing: {rel_f}")

        # Check non-empty content
        if f_path.stat().st_size == 0 and not rel_f.endswith("__init__.py"):
            raise RuntimeError(f"Integrity check failed: empty file: {rel_f}")

        # If JSON, verify valid parsing
        if rel_f.endswith(".json"):
            try:
                json.loads(f_path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise RuntimeError(
                    f"Integrity check failed: malformed JSON in {rel_f}: {exc}"
                )


def task_finalize_telemetry(context: BootstrapContext) -> None:
    """Calculate execution timings and construct metadata summary."""
    stats = {
        "files_created": len(context.created_files),
        "directories_created": len(context.created_directories),
        "files_overwritten": len(context.overwritten_files),
        "profile": context.profile,
        "template": context.template,
        "workers": context.workers,
    }
    context.metadata["result_stats"] = stats


# ── DAG Builder ──────────────────────────────────────────────────────────────
def build_bootstrap_dag(context: BootstrapContext) -> list[BootstrapTask]:
    """Construct standard topological DAG of bootstrap tasks."""
    return [
        BootstrapTask(
            id="validate_workspace",
            name="Validate Workspace Security",
            dependencies=[],
            action=task_validate_workspace,
        ),
        BootstrapTask(
            id="snapshot_prestate",
            name="Snapshot Pre-Execution State",
            dependencies=["validate_workspace"],
            action=task_snapshot_prestate,
        ),
        BootstrapTask(
            id="scaffold_directories",
            name="Scaffold Directory Structure",
            dependencies=["snapshot_prestate"],
            action=task_scaffold_directories,
        ),
        BootstrapTask(
            id="scaffold_governance",
            name="Scaffold Governance Contracts",
            dependencies=["scaffold_directories"],
            action=task_scaffold_governance,
        ),
        BootstrapTask(
            id="scaffold_subagents",
            name="Scaffold Subagent Catalogs",
            dependencies=["scaffold_directories"],
            action=task_scaffold_subagents,
        ),
        BootstrapTask(
            id="scaffold_skills",
            name="Scaffold Antigravity Skills",
            dependencies=["scaffold_directories", "scaffold_subagents"],
            action=task_scaffold_skills,
        ),
        BootstrapTask(
            id="scaffold_mcp",
            name="Scaffold MCP Configurations",
            dependencies=["scaffold_directories"],
            action=task_scaffold_mcp,
        ),
        BootstrapTask(
            id="scaffold_hooks",
            name="Scaffold Lifecycle Safety Hooks",
            dependencies=["scaffold_directories"],
            action=task_scaffold_hooks,
        ),
        BootstrapTask(
            id="scaffold_templates",
            name="Scaffold Domain Template",
            dependencies=["scaffold_governance", "scaffold_directories"],
            action=task_scaffold_templates,
        ),
        BootstrapTask(
            id="init_git",
            name="Initialize Git Repository",
            dependencies=["scaffold_governance"],
            action=task_init_git,
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
            action=task_verify_integrity,
        ),
        BootstrapTask(
            id="finalize_telemetry",
            name="Finalize Execution Telemetry",
            dependencies=["verify_integrity"],
            action=task_finalize_telemetry,
        ),
    ]


# ── Concurrency Execution Pipeline ───────────────────────────────────────────
def execute_tasks_parallel(
    tasks: list[BootstrapTask],
    context: BootstrapContext,
) -> bool:
    """Dynamically schedule and execute tasks via ThreadPoolExecutor according to DAG.

    Returns:
        True if all non-optional tasks succeeded, False otherwise.
    """
    # 1. Topological cycle detection
    resolve_dag_dependencies(tasks)

    task_map = {t.id: t for t in tasks}
    completed_tasks: set[str] = set()
    failed_tasks: set[str] = set()
    submitted_tasks: set[str] = set()
    active_futures: dict[concurrent.futures.Future, str] = {}

    lock = threading.Lock()
    has_fatal_failure = False

    def run_single_task(task: BootstrapTask) -> tuple[str, bool, Optional[str]]:
        worker_id = threading.current_thread().name
        start_time = time.time()
        timing = TaskTiming(
            task_id=task.id,
            name=task.name,
            start_time=start_time,
            worker_id=worker_id,
            status=TaskStatus.RUNNING,
        )
        with context.lock:
            context.task_timings[task.id] = timing

        err: Optional[str] = None
        success = True
        try:
            task.action(context)
            timing.status = TaskStatus.COMPLETED
        except Exception as exc:
            err = str(exc)
            success = False
            timing.status = TaskStatus.FAILED
            timing.error = err
            with context.lock:
                context.errors.append(f"Task '{task.id}' failed: {err}")
        finally:
            end_time = time.time()
            timing.end_time = end_time
            timing.duration_ms = round((end_time - start_time) * 1000, 2)

        return task.id, success, err

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max(1, context.workers)
    ) as executor:

        def submit_ready_tasks() -> None:
            nonlocal has_fatal_failure
            if has_fatal_failure:
                return
            for t in tasks:
                if t.id not in submitted_tasks:
                    if all(dep in completed_tasks for dep in t.dependencies):
                        submitted_tasks.add(t.id)
                        fut = executor.submit(run_single_task, t)
                        active_futures[fut] = t.id

        with lock:
            submit_ready_tasks()

        while True:
            with lock:
                if not active_futures:
                    break
                futures_to_wait = list(active_futures.keys())

            done, _ = concurrent.futures.wait(
                futures_to_wait,
                return_when=concurrent.futures.FIRST_COMPLETED,
            )

            with lock:
                for fut in done:
                    if fut in active_futures:
                        tid = active_futures.pop(fut)
                        task = task_map[tid]
                        try:
                            _, success, err = fut.result()
                        except Exception as exc:
                            success = False
                            err = str(exc)

                        if success:
                            completed_tasks.add(tid)
                        else:
                            failed_tasks.add(tid)
                            if not task.optional:
                                has_fatal_failure = True
                                for pending_fut in list(active_futures.keys()):
                                    pending_fut.cancel()
                                break

                if not has_fatal_failure:
                    submit_ready_tasks()
                else:
                    break

        # Mark unexecuted tasks as SKIPPED
        for t in tasks:
            with context.lock:
                if t.id not in context.task_timings:
                    context.task_timings[t.id] = TaskTiming(
                        task_id=t.id,
                        name=t.name,
                        start_time=0.0,
                        end_time=0.0,
                        duration_ms=0.0,
                        status=TaskStatus.SKIPPED,
                    )
                elif t.id not in completed_tasks and t.id not in failed_tasks:
                    context.task_timings[t.id].status = TaskStatus.SKIPPED

    return not has_fatal_failure


# ── Atomic Checkpoint & Rollback Mechanics ────────────────────────────────────
def rollback_context(context: BootstrapContext) -> list[str]:
    """Execute atomic rollback restoring workspace to exact pre-execution state.

    1. Unlinks created files in reverse creation order.
    2. Restores overwritten files with original contents.
    3. Removes registered directories in reverse creation order if empty.
    4. If target directory was newly created by us and is now empty, removes it.

    Returns:
        List of unlinked or restored relative file paths.
    """
    reverted_paths: list[str] = []
    with context.lock:
        if context.dry_run:
            return reverted_paths

        target_resolved = context.target_path.resolve()

        # 0. Clean up git repository if created by us
        if context.metadata.get("git_dir_created_by_us", False):
            git_dir = target_resolved / ".git"
            if git_dir.is_dir():
                try:
                    shutil.rmtree(git_dir, ignore_errors=True)
                except OSError:
                    pass

        # 1. Unlink created files
        for rel_file in reversed(context.created_files):
            if rel_file in context.overwritten_files:
                continue
            file_path = (target_resolved / rel_file).resolve()
            if file_path.is_file():
                try:
                    file_path.unlink()
                    reverted_paths.append(rel_file)
                except OSError:
                    pass

        # 2. Restore overwritten files
        for rel_file, orig_content in context.overwritten_files.items():
            file_path = (target_resolved / rel_file).resolve()
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(orig_content, encoding="utf-8")
                reverted_paths.append(rel_file)
            except OSError:
                pass

        # 3. Remove created directories in reverse order if empty
        for rel_dir in reversed(context.created_directories):
            dir_path = (target_resolved / rel_dir).resolve()
            if dir_path.is_dir():
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                except OSError:
                    pass

        # Also clean empty parent directories of created files
        for rel_file in reversed(context.created_files):
            file_path = (target_resolved / rel_file).resolve()
            parent = file_path.parent
            while parent != target_resolved and parent.is_relative_to(target_resolved):
                if parent.is_dir():
                    try:
                        if not any(parent.iterdir()):
                            parent.rmdir()
                        else:
                            break
                    except OSError:
                        break
                parent = parent.parent

        # 4. If target directory itself was created by us and is now empty, remove it
        if context.metadata.get("target_was_created_by_us", False):
            if target_resolved.is_dir():
                try:
                    if not any(target_resolved.iterdir()):
                        target_resolved.rmdir()
                except OSError:
                    pass

    return reverted_paths


# ── Primary Engine Function ──────────────────────────────────────────────────
def execute_bootstrap_parallel(
    goal: str = "",
    target_path: Optional[Path | str] = None,
    workers: int = 4,
    profile: str = "standard",
    template: str = "default",
    dry_run: bool = False,
    force: bool = False,
) -> BootstrapResult:
    """Execute parallel project bootstrap with multi-worker DAG orchestration.

    Args:
        goal: Optional goal description or mission statement.
        target_path: Target directory (Path or str). Defaults to current directory.
        workers: Number of parallel worker threads. Defaults to 4.
        profile: Verification profile ('smoke', 'standard', 'full', 'minimal').
        template: Project template preset ('default', 'vas', 'fintech', 'agent').
        dry_run: If True, simulate execution without modifying disk.
        force: If True, overwrite pre-existing files; otherwise skip them.

    Returns:
        BootstrapResult with ok, rolled_back, timings, created_files, and stats.
    """
    global _LAST_BOOTSTRAP_RESULT

    # Normalize target path
    if target_path is None:
        target_path = Path.cwd()
    elif isinstance(target_path, str):
        target_path = Path(target_path)
    target_path = target_path.resolve()

    # Normalize profile
    norm_profile = profile.lower()
    if norm_profile == "minimal":
        norm_profile = "smoke"
    valid_profiles = {"smoke", "standard", "full"}
    if norm_profile not in valid_profiles:
        raise ValueError(
            f"Unknown profile '{profile}'. Expected one of: {', '.join(sorted(valid_profiles))}"
        )

    # Normalize template
    norm_template = template.lower()
    valid_templates = {"default", "vas", "fintech", "agent"}
    if norm_template not in valid_templates:
        raise ValueError(
            f"Unknown template '{template}'. Expected one of: {', '.join(sorted(valid_templates))}"
        )

    context = BootstrapContext(
        target_path=target_path,
        profile=norm_profile,
        template=norm_template,
        workers=max(1, workers),
        dry_run=dry_run,
        force=force,
        metadata={"goal": goal},
    )

    # Validate workspace security immediately
    task_validate_workspace(context)

    tasks = build_bootstrap_dag(context)
    start_time = time.time()

    success = False
    rolled_back = False
    error_msg: Optional[str] = None

    try:
        success = execute_tasks_parallel(tasks, context)
        if not success:
            error_msg = "; ".join(context.errors) if context.errors else "Bootstrap task failed"
            rollback_context(context)
            rolled_back = True
    except CyclicDependencyError as exc:
        rollback_context(context)
        rolled_back = True
        raise
    except Exception as exc:
        error_msg = str(exc)
        rollback_context(context)
        rolled_back = True
        success = False

    end_time = time.time()
    duration_ms = round((end_time - start_time) * 1000, 2)

    result = BootstrapResult(
        ok=success,
        rolled_back=rolled_back,
        error=error_msg,
        target_path=target_path,
        profile=norm_profile,
        template=norm_template,
        workers=workers,
        dry_run=dry_run,
        created_files=list(context.created_files),
        created_directories=list(context.created_directories),
        task_timings=dict(context.task_timings),
        duration_ms=duration_ms,
        stats=dict(context.metadata.get("result_stats", {})),
    )

    _LAST_BOOTSTRAP_RESULT = result
    return result
