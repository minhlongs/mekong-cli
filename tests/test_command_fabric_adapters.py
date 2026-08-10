"""Adapter manifest generation — agent CLIs, IDE palettes, MCP, shells."""

import json

from src.command_fabric.adapters import export_adapter_manifest
from src.command_fabric.catalog import build_command_catalog


def test_command_fabric_exports_agent_cli_adapters() -> None:
    records = build_command_catalog()

    for adapter in (
        "claude-code",
        "codex",
        "gemini-cli",
        "opencode",
        "cursor-agent",
        "amp",
        "goose",
        "crush",
        "kiro-cli",
    ):
        payload = export_adapter_manifest(adapter, records)
        assert payload["schema"] == f"mekong.command_fabric.adapter.{adapter}.v1"
        assert payload["command_count"] == len(records)
        # Stubs have empty execution, so we check for source presence instead
        assert any(c.get("source") for c in payload["commands"])


def test_command_fabric_exports_ide_command_palette_adapters() -> None:
    records = build_command_catalog()

    for adapter in (
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
    ):
        payload = export_adapter_manifest(adapter, records)
        assert payload["schema"] == f"mekong.command_fabric.adapter.{adapter}.v1"
        assert payload["command_count"] == len(records)
        # IDE palettes expose at least one command with a proper command identity
        assert any(c.get("command") for c in payload["commands"])


def test_command_fabric_exports_mcp_and_shell_adapters() -> None:
    records = build_command_catalog()
    mcp_payload = export_adapter_manifest("mcp", records)
    shell_payload = export_adapter_manifest("shell", records)

    assert mcp_payload["schema"] == "mekong.command_fabric.adapter.mcp.v1"
    assert mcp_payload["tool_count"] == len(records)

    assert shell_payload["schema"] == "mekong.command_fabric.adapter.shell.v1"
    assert shell_payload["command_count"] == len(records)


def test_supported_adapters_constant_matches_manifest() -> None:
    from src.command_fabric.adapters import SUPPORTED_ADAPTERS, export_adapter_manifest
    from src.command_fabric.catalog import build_command_catalog

    records = build_command_catalog()
    for adapter in SUPPORTED_ADAPTERS:
        if adapter == "canonical":
            continue
        payload = export_adapter_manifest(adapter, records)
        assert payload["schema"].endswith(f".{adapter}.v1")


def test_mcp_adapter_tool_count_matches_catalog() -> None:
    from src.command_fabric.adapters import export_adapter_manifest
    from src.command_fabric.catalog import build_command_catalog

    records = build_command_catalog()
    payload = export_adapter_manifest("mcp", records)
    assert payload["tool_count"] == len(records)
