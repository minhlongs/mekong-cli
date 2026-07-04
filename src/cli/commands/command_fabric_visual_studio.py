"""Visual Studio package subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.visual_studio_package import materialize_visual_studio_package


def register_visual_studio_command(app: typer.Typer) -> None:
    """Register Visual Studio package materialization command."""

    @app.command("visual-studio-package")
    def visual_studio_package_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "visual-studio-package", "--out", "-o"),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
    ) -> None:
        """Write Visual Studio VSIX scaffold for command-fabric consumers."""
        records = build_global_command_catalog() if scope == "global" else build_command_catalog()
        typer.echo(json.dumps(materialize_visual_studio_package(output_dir, records), indent=2))


__all__ = ["register_visual_studio_command"]
