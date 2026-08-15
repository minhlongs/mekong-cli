"""MCP package subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.mcp_package import materialize_mcp_package


def register_mcp_command(app: typer.Typer) -> None:
    """Register MCP package materialization command."""

    @app.command("mcp-package")
    def mcp_package_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "mcp-package", "--out", "-o"),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
    ) -> None:
        """Write MCP stdio package scaffold for command-fabric consumers."""
        records = build_global_command_catalog() if scope == "global" else build_command_catalog()
        typer.echo(json.dumps(materialize_mcp_package(output_dir, records), indent=2))


__all__ = ["register_mcp_command"]
