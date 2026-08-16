# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helix package subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.helix_package import materialize_helix_package


def register_helix_command(app: typer.Typer) -> None:
    """Register Helix package materialization command."""

    @app.command("helix-package")
    def helix_package_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "helix-package", "--out", "-o"),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
    ) -> None:
        """Write Helix package scaffold for command-fabric consumers."""
        records = build_global_command_catalog() if scope == "global" else build_command_catalog()
        typer.echo(json.dumps(materialize_helix_package(output_dir, records), indent=2))


__all__ = ["register_helix_command"]
