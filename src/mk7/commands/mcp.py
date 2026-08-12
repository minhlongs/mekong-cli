"""Mekong CLI 7 — `mcp` command: manage and call MCP servers.

Config: ~/.mekong/config.json -> {"mcp_servers": {"name": {"command": [...], "cwd": "."}}}
"""

from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.config import load
from ..core.mcp import McpClient, McpError, McpServer

console = Console()


def _servers() -> dict[str, dict]:
    cfg = load()
    return cfg.get("mcp_servers", {}) or {}


def _server_for(name: str) -> McpServer:
    servers = _servers()
    if name not in servers:
        raise McpError(f"unknown MCP server '{name}' (configured: {list(servers) or 'none'})")
    spec = servers[name]
    command = spec.get("command", [])
    if isinstance(command, str):
        command = command.split(" ")
    return McpServer(name=name, command=list(command), cwd=str(spec.get("cwd", ".")))


def mcp_list_cmd() -> None:
    """List configured MCP servers and their tools."""
    servers = _servers()
    if not servers:
        console.print("[yellow]No MCP servers configured. Add to ~/.mekong/config.json:[/]")
        console.print('  {"mcp_servers": {"files": {"command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "."]}}}')
        return
    for name, spec in servers.items():
        console.print(f"[bold cyan]{name}[/]  command={spec.get('command')}")
        try:
            with McpClient(_server_for(name)) as client:
                client.initialize()
                tools = client.list_tools()
                for t in tools:
                    console.print(f"  [green]{t.name}[/] — {t.description[:70]}")
                console.print(f"  ({len(tools)} tools)")
        except McpError as e:
            console.print(f"  [red]error: {e}[/]")


def mcp_call_cmd(
    server: str = typer.Argument(..., help="MCP server name"),
    tool: str = typer.Argument(..., help="Tool name"),
    args_json: Optional[str] = typer.Option(None, "--args", help="JSON arguments"),
) -> None:
    """Call a tool on an MCP server (--args '{"path": "/tmp"}' )."""
    import json

    try:
        args = json.loads(args_json) if args_json else {}
        with McpClient(_server_for(server)) as client:
            client.initialize()
            result = client.call_tool(tool, args)
            if result["ok"]:
                console.print(result["output"] or "(empty)")
            else:
                console.print(f"[red]tool error:[/] {result['output'] or '(no message)'}")
                sys.exit(1)
    except (McpError, Exception) as e:
        console.print(f"[red]error:[/] {str(e)[:300]}")
        sys.exit(1)
