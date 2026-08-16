# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Release bundle subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.release_bundle import materialize_release_bundle


def register_bundle_command(app: typer.Typer) -> None:
    """Register full bundle materialization command."""

    @app.command("bundle")
    def bundle_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "bundle", "--out", "-o"),
        scope: Literal["global", "project"] = typer.Option("global", "--scope", "-s"),
        ide_host: list[str] = typer.Option([], "--ide-host"),
        agent_host: list[str] = typer.Option([], "--agent-host"),
    ) -> None:
        """Write all command fabric artifacts for release pipelines."""
        payload = materialize_release_bundle(
            output_dir=output_dir,
            scope=scope,
            ide_hosts=ide_host or None,
            agent_hosts=agent_host or None,
        )
        typer.echo(json.dumps(payload, indent=2))


__all__ = ["register_bundle_command"]
