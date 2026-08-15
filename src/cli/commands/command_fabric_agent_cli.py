"""Agent CLI package subcommand for the Mekong command fabric CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR, materialize_agent_cli_packages


def register_agent_cli_command(app: typer.Typer) -> None:
    """Register agent CLI package materialization command."""

    @app.command("agent-cli-package")
    def agent_cli_package_cmd(
        output_dir: Path = typer.Option(
            DEFAULT_ARTIFACT_DIR / "agent-cli", "--out", "-o"
        ),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
        host: list[str] = typer.Option([], "--host", "-h"),
    ) -> None:
        """Write agent CLI command packages and command-card manifests."""
        selected = host or None
        payload = materialize_agent_cli_packages(output_dir, scope=scope, hosts=selected)
        typer.echo(json.dumps(payload, indent=2))


__all__ = ["register_agent_cli_command"]
