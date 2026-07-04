"""Adapter exporters for global IDE/CLI command surfaces."""

from __future__ import annotations

from typing import Any

from src.command_fabric.adapter_targets import (
    AGENT_CLI_ADAPTERS,
    IDE_ADAPTERS,
    SUPPORTED_ADAPTERS,
    AdapterName,
)
from src.command_fabric.catalog import CommandRecord, build_global_command_catalog


def _agent_command(record: CommandRecord, runtime: str) -> dict[str, Any]:
    """Return a portable command card for agent CLI runtimes."""
    prefix = "/" if runtime in {"claude-code", "gemini-cli", "opencode"} else ""
    return {
        "id": record.name,
        "title": f"{prefix}{record.name}",
        "description": record.description,
        "argument_hint": record.argument_hint,
        "allowed_tools": record.allowed_tools,
        "execution": record.execution,
        "source": record.source,
        "contract": record.contract,
        "layer": record.layer,
    }


def _command_palette_item(record: CommandRecord, host: str) -> dict[str, Any]:
    """Return IDE command-palette metadata."""
    command_id = f"mekong.{record.name.replace('-', '.')}"
    return {
        "command": command_id,
        "title": f"Mekong: {record.name}",
        "category": "Mekong",
        "description": record.description,
        "arguments": {
            "name": record.name,
            "hint": record.argument_hint,
            "execution": record.execution,
        },
        "source": record.source,
        "host": host,
    }


def _mcp_tool(record: CommandRecord) -> dict[str, Any]:
    """Return MCP tool metadata for command invocation gateways."""
    return {
        "name": f"mekong_{record.name.replace('-', '_')}",
        "title": f"Mekong {record.name}",
        "description": record.description or f"Run Mekong command {record.name}",
        "inputSchema": {
            "type": "object",
            "properties": {
                "arguments": {
                    "type": "string",
                    "description": record.argument_hint or "Arguments to pass to the command",
                }
            },
            "required": [],
        },
        "metadata": {
            "command": record.name,
            "execution": record.execution,
            "source": record.source,
            "contract": record.contract,
        },
    }


def _shell_completion(record: CommandRecord) -> dict[str, Any]:
    """Return shell completion metadata for command generators."""
    return {
        "name": record.name,
        "description": record.description,
        "argument_hint": record.argument_hint,
        "completion": f"mekong {record.name}",
    }


def export_adapter_manifest(
    adapter: AdapterName,
    records: list[CommandRecord] | None = None,
) -> dict[str, Any]:
    """Export one adapter-specific manifest from the neutral command catalog."""
    command_records = records if records is not None else build_global_command_catalog()
    if adapter not in SUPPORTED_ADAPTERS:
        raise ValueError(f"Unsupported command fabric adapter: {adapter}")

    if adapter == "canonical":
        from src.command_fabric.catalog import export_command_catalog

        return export_command_catalog(command_records)

    if adapter in AGENT_CLI_ADAPTERS:
        return {
            "schema": f"mekong.command_fabric.adapter.{adapter}.v1",
            "adapter": adapter,
            "command_count": len(command_records),
            "commands": [_agent_command(record, adapter) for record in command_records],
        }

    if adapter in IDE_ADAPTERS:
        return {
            "schema": f"mekong.command_fabric.adapter.{adapter}.v1",
            "adapter": adapter,
            "command_count": len(command_records),
            "commands": [_command_palette_item(record, adapter) for record in command_records],
        }

    if adapter == "mcp":
        return {
            "schema": "mekong.command_fabric.adapter.mcp.v1",
            "adapter": adapter,
            "tool_count": len(command_records),
            "tools": [_mcp_tool(record) for record in command_records],
        }

    return {
        "schema": "mekong.command_fabric.adapter.shell.v1",
        "adapter": adapter,
        "command_count": len(command_records),
        "commands": [_shell_completion(record) for record in command_records],
    }


__all__ = ["AdapterName", "SUPPORTED_ADAPTERS", "export_adapter_manifest"]
