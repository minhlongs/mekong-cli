"""Npm package subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.npm_package import materialize_npm_package


def register_npm_command(app: typer.Typer) -> None:
    """Register npm package materialization command."""

    @app.command("npm-package")
    def npm_package_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "npm-package", "--out", "-o"),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
    ) -> None:
        """Write npm package scaffold for command-fabric consumers."""
        records = build_global_command_catalog() if scope == "global" else build_command_catalog()
        typer.echo(json.dumps(materialize_npm_package(output_dir, records, scope=scope), indent=2))


__all__ = ["register_npm_command"]
