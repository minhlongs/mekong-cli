"""Package-manager metadata subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.package_managers import materialize_package_manager_metadata


def register_package_managers_command(app: typer.Typer) -> None:
    """Register package-manager metadata materialization."""

    @app.command("package-managers")
    def package_managers_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "package-managers", "--out", "-o"),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
    ) -> None:
        """Write 23 package-manager targets for global CLI installation."""
        records = build_global_command_catalog() if scope == "global" else build_command_catalog()
        typer.echo(json.dumps(materialize_package_manager_metadata(output_dir, records), indent=2))


__all__ = ["register_package_managers_command"]
