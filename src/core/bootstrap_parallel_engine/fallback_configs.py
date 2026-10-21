"""Protected system directory constants and fallback governance/config templates."""

from __future__ import annotations

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
