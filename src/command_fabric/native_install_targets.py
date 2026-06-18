"""Native install targets for command-fabric packages."""

from __future__ import annotations

from pathlib import Path

from src.command_fabric.agent_cli_package import SUPPORTED_AGENT_CLI_HOSTS


SUPPORTED_INSTALL_HOSTS: tuple[str, ...] = (
    *SUPPORTED_AGENT_CLI_HOSTS,
    "shell",
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


def target_for_host(host: str, target_root: Path | None) -> Path:
    """Return the native install path for one host."""
    root = target_root if target_root is not None else Path.home()
    targets = {
        "claude-code": root / ".claude" / "commands" / "mekong",
        "gemini-cli": root / ".gemini" / "commands" / "mekong",
        "opencode": root / ".config" / "opencode" / "commands" / "mekong",
        "codex": root / ".codex" / "command-fabric" / "mekong",
        "aider": root / ".mekong" / "command-fabric" / "aider",
        "continue-dev": root / ".mekong" / "command-fabric" / "continue-dev",
        "copilot-cli": root / ".mekong" / "command-fabric" / "copilot-cli",
        "cursor-agent": root / ".mekong" / "command-fabric" / "cursor-agent",
        "amp": root / ".mekong" / "command-fabric" / "amp",
        "goose": root / ".mekong" / "command-fabric" / "goose",
        "crush": root / ".mekong" / "command-fabric" / "crush",
        "kiro-cli": root / ".mekong" / "command-fabric" / "kiro-cli",
        "shell": root / ".mekong" / "completions",
        "visual-studio": root / ".mekong" / "command-fabric" / "visual-studio",
        "eclipse": root / "eclipse" / "dropins" / "mekong-command-fabric",
        "fleet": root / ".local" / "share" / "JetBrains" / "Fleet" / "plugins" / "mekong-command-fabric",
        "nova": root / "Library" / "Application Support" / "Nova" / "Extensions" / "mekong-command-fabric.novaextension",
        "lapce": root / ".local" / "share" / "lapce" / "plugins" / "mekong-command-fabric",
        "kakoune": root / ".config" / "kak" / "autoload" / "mekong-command-fabric",
        "micro": root / ".config" / "micro" / "plug" / "mekong-command-fabric",
        "vim": root / ".vim" / "pack" / "mekong" / "start" / "command-fabric",
        "neovim": root / ".local" / "share" / "nvim" / "site" / "pack" / "mekong" / "start" / "command-fabric",
        "helix": root / ".config" / "helix" / "mekong-command-fabric",
        "zed": root / ".local" / "share" / "zed" / "extensions" / "installed" / "mekong-command-fabric",
        "emacs": root / ".emacs.d" / "site-lisp" / "mekong-command-fabric",
        "sublime": root / ".config" / "sublime-text" / "Packages" / "Mekong Command Fabric",
    }
    return targets[host]


__all__ = ["SUPPORTED_INSTALL_HOSTS", "target_for_host"]
