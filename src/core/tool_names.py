"""Mekong CLI - Tool Names Module.

Canonical tool name constants, mirroring Codebuff's ToolName union.
Provides a single source of truth for tool identifiers used in
agent allowedTools lists and tool restriction enforcement.
"""

from __future__ import annotations

# File operations
READ_FILES = "read_files"
WRITE_FILE = "write_file"
STR_REPLACE = "str_replace"
APPLY_PATCH = "apply_patch"
READ_SUBTREE = "read_subtree"
FILE_LIST = "file:list"

# Search
CODE_SEARCH = "code_search"
FIND_FILES = "find_files"
GLOB = "glob"

# Terminal
RUN_TERMINAL_COMMAND = "run_terminal_command"
SHELL_RUN = "shell:run"

# Web
WEB_SEARCH = "web_search"
READ_URL = "read_url"
READ_DOCS = "read_docs"

# Agent management
SPAWN_AGENTS = "spawn_agents"
LOOKUP_AGENT_INFO = "lookup_agent_info"

# Control
END_TURN = "end_turn"
TASK_COMPLETED = "task_completed"
THINK_DEEPLY = "think_deeply"
WRITE_TODOS = "write_todos"
ASK_USER = "ask_user"

# UI
RENDER_UI = "render_ui"
SUGGEST_FOLLOWUPS = "suggest_followups"

# Git (builtin)
GIT_STATUS = "git:status"
GIT_DIFF = "git:diff"
GIT_LOG = "git:log"
GIT_COMMIT = "git:commit"
GIT_PUSH = "git:push"
GIT_PULL = "git:pull"

# All canonical names (for validation)
ALL_TOOL_NAMES: tuple[str, ...] = (
    # File
    READ_FILES,
    WRITE_FILE,
    STR_REPLACE,
    APPLY_PATCH,
    READ_SUBTREE,
    FILE_LIST,
    # Search
    CODE_SEARCH,
    FIND_FILES,
    GLOB,
    # Terminal
    RUN_TERMINAL_COMMAND,
    SHELL_RUN,
    # Web
    WEB_SEARCH,
    READ_URL,
    READ_DOCS,
    # Agent mgmt
    SPAWN_AGENTS,
    LOOKUP_AGENT_INFO,
    # Control
    END_TURN,
    TASK_COMPLETED,
    THINK_DEEPLY,
    WRITE_TODOS,
    ASK_USER,
    # UI
    RENDER_UI,
    SUGGEST_FOLLOWUPS,
    # Git
    GIT_STATUS,
    GIT_DIFF,
    GIT_LOG,
    GIT_COMMIT,
    GIT_PUSH,
    GIT_PULL,
)

# Tool name aliases (legacy → canonical)
ALIASES: dict[str, str] = {
    "git_status": GIT_STATUS,
    "git_diff": GIT_DIFF,
    "git_log": GIT_LOG,
    "git_commit": GIT_COMMIT,
    "git_push": GIT_PUSH,
    "git_pull": GIT_PULL,
    "shell_run": SHELL_RUN,
    "read_file": READ_FILES,
    "list_dir": FILE_LIST,
    # Codebuff-style aliases
    "file:read": READ_FILES,
    "file:write": WRITE_FILE,
    "file:list": FILE_LIST,
}


def resolve_tool_name(name: str) -> str:
    """Resolve a tool name alias to its canonical form.

    Args:
        name: Tool name or alias.

    Returns:
        Canonical tool name.
    """
    return ALIASES.get(name, name)


__all__ = [
    "ALL_TOOL_NAMES",
    "ALIASES",
    "APPLY_PATCH",
    "ASK_USER",
    "CODE_SEARCH",
    "END_TURN",
    "FILE_LIST",
    "FIND_FILES",
    "GIT_COMMIT",
    "GIT_DIFF",
    "GIT_LOG",
    "GIT_PULL",
    "GIT_PUSH",
    "GIT_STATUS",
    "GLOB",
    "LOOKUP_AGENT_INFO",
    "READ_DOCS",
    "READ_FILES",
    "READ_SUBTREE",
    "READ_URL",
    "RUN_TERMINAL_COMMAND",
    "SHELL_RUN",
    "SPAWN_AGENTS",
    "STR_REPLACE",
    "SUGGEST_FOLLOWUPS",
    "TASK_COMPLETED",
    "THINK_DEEPLY",
    "WEB_SEARCH",
    "WRITE_FILE",
    "WRITE_TODOS",
    "resolve_tool_name",
]
