"""Supported command-fabric adapter target groups."""

from __future__ import annotations

from typing import Literal

AdapterName = Literal[
    "canonical",
    "claude-code",
    "codex",
    "gemini-cli",
    "opencode",
    "aider",
    "continue-dev",
    "copilot-cli",
    "cursor-agent",
    "amp",
    "goose",
    "crush",
    "kiro-cli",
    "mcp",
    "vscode",
    "cursor",
    "windsurf",
    "theia",
    "jetbrains",
    "visual-studio",
    "eclipse",
    "fleet",
    "nova",
    "lapce",
    "kakoune",
    "micro",
    "vim",
    "neovim",
    "helix",
    "zed",
    "emacs",
    "sublime",
    "shell",
]

AGENT_CLI_ADAPTERS: tuple[str, ...] = (
    "claude-code",
    "codex",
    "gemini-cli",
    "opencode",
    "aider",
    "continue-dev",
    "copilot-cli",
    "cursor-agent",
    "amp",
    "goose",
    "crush",
    "kiro-cli",
)

IDE_ADAPTERS: tuple[str, ...] = (
    "vscode",
    "cursor",
    "windsurf",
    "theia",
    "jetbrains",
    "visual-studio",
    "eclipse",
    "fleet",
    "nova",
    "lapce",
    "kakoune",
    "micro",
    "vim",
    "neovim",
    "helix",
    "zed",
    "emacs",
    "sublime",
)

SUPPORTED_ADAPTERS: tuple[str, ...] = (
    "canonical",
    *AGENT_CLI_ADAPTERS,
    "mcp",
    *IDE_ADAPTERS,
    "shell",
)


__all__ = ["AGENT_CLI_ADAPTERS", "AdapterName", "IDE_ADAPTERS", "SUPPORTED_ADAPTERS"]
