"""Role context budgets, tool allowlists, and timestamp helpers for PEV Swarm Bridge."""

from __future__ import annotations

from datetime import datetime, timezone

# Pinned Context Budget definitions matching HARNESS.md §1
ROLE_CONTEXT_BUDGETS: dict[str, int] = {
    "ceo": 30000,
    "sun-tzu": 30000,
    "cto": 24000,
    "eng": 24000,
    "fullstack-developer": 24000,
    "debugger": 24000,
    "pm": 20000,
    "planner": 20000,
    "cmo": 20000,
    "ops": 16000,
    "coo": 16000,
    "ae": 16000,
    "cfo": 16000,
    "tester": 16000,
    "code-reviewer": 16000,
    "code-simplifier": 16000,
    "docs-manager": 16000,
    "git-manager": 16000,
    "journal-writer": 16000,
    "kongming": 16000,
    "project-manager": 20000,
    "researcher": 20000,
    "ui-ux-designer": 20000,
    "brainstormer": 20000,
    "cso": 20000,
}

# Role to layer tool allowlists matching HARNESS.md §2
ROLE_TOOL_ALLOWLISTS: dict[str, list[str]] = {
    "ceo": ["Read", "Write", "Edit", "Bash", "Task", "AskUserQuestion"],
    "sun-tzu": ["Read", "Glob", "Grep", "Bash", "WebFetch", "WebSearch", "Task"],
    "pm": ["Read", "Write", "Edit", "Bash", "Task"],
    "planner": ["Read", "Write", "Edit", "Bash", "Task"],
    "cto": ["Read", "Write", "Edit", "Bash", "Task"],
    "eng": ["Read", "Write", "Edit", "Bash", "Task"],
    "fullstack-developer": ["Read", "Write", "Edit", "Bash", "Task"],
    "debugger": ["Read", "Write", "Edit", "Bash", "Task"],
    "ops": ["Read", "Bash", "Task"],
    "coo": ["Read", "Bash", "Task"],
    "tester": ["Read", "Bash", "Task"],  # Read-only verifier! Strictly NO Write/Edit
    "code-reviewer": ["Read", "Bash", "Task"],  # Read-only verifier! Strictly NO Write/Edit
    "cfo": ["Read", "Bash", "Task"],
    "cmo": ["Read", "Bash", "Task"],
    "cso": ["Read", "Bash", "Task"],
    "ae": ["Read", "Bash", "Task"],
    "code-simplifier": ["Read", "Write", "Edit", "Bash", "Task"],
    "docs-manager": ["Read", "Write", "Edit", "Bash", "Task"],
    "git-manager": ["Read", "Bash", "Task"],
    "journal-writer": ["Read", "Write", "Edit", "Task"],
    "kongming": ["Read", "Bash", "Task"],
    "project-manager": ["Read", "Write", "Edit", "Bash", "Task"],
    "researcher": ["Read", "Bash", "Task"],
    "ui-ux-designer": ["Read", "Write", "Edit", "Bash", "Task"],
    "brainstormer": ["Read", "Bash", "Task"],
}

# Verifier roles that must NEVER be granted Write or Edit tools
VERIFIER_ROLES: set[str] = {"tester", "code-reviewer", "qa", "auditor"}


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()
