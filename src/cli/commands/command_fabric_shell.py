# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Shell completion subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.catalog import build_command_catalog, build_global_command_catalog
from src.command_fabric.shell_package import materialize_shell_completion


def register_shell_command(app: typer.Typer) -> None:
    """Register shell completion materialization command."""

    @app.command("shell-completion")
    def shell_completion_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "shell-completion", "--out", "-o"),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
    ) -> None:
        """Write cross-shell completions and installer."""
        records = build_global_command_catalog() if scope == "global" else build_command_catalog()
        typer.echo(json.dumps(materialize_shell_completion(output_dir, records), indent=2))


__all__ = ["register_shell_command"]
