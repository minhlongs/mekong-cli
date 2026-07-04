"""Universal readiness audit subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.readiness import audit_universal_readiness


def register_readiness_command(app: typer.Typer) -> None:
    """Register universal readiness audit command."""

    @app.command("readiness-audit")
    def readiness_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "readiness", "--out", "-o"),
        target_root: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "readiness-home", "--target-root"),
        scope: Literal["global", "project"] = typer.Option("global", "--scope", "-s"),
    ) -> None:
        """Audit generated command fabric coverage for global IDE/CLI use."""
        payload = audit_universal_readiness(output_dir, target_root, scope=scope)
        typer.echo(json.dumps(payload, indent=2))
        if not payload["ready"]:
            raise typer.Exit(code=2)


__all__ = ["register_readiness_command"]
