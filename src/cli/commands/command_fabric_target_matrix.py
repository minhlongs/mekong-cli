# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Target matrix subcommand for command fabric."""

from __future__ import annotations

import json

import typer

from src.command_fabric.target_matrix import target_matrix_summary


def register_target_matrix_command(app: typer.Typer) -> None:
    """Register target matrix inspection command."""

    @app.command("target-matrix")
    def target_matrix_cmd() -> None:
        """Print global IDE/CLI target coverage matrix."""
        typer.echo(json.dumps(target_matrix_summary(), indent=2))


__all__ = ["register_target_matrix_command"]
