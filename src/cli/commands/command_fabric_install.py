"""Native install subcommand for command fabric packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from src.command_fabric.artifacts import DEFAULT_ARTIFACT_DIR
from src.command_fabric.native_install import materialize_native_install


def register_install_command(app: typer.Typer) -> None:
    """Register native install command."""

    @app.command("install")
    def install_cmd(
        output_dir: Path = typer.Option(DEFAULT_ARTIFACT_DIR / "install", "--out", "-o"),
        scope: Literal["global", "project"] = typer.Option("project", "--scope", "-s"),
        host: list[str] = typer.Option([], "--host", "-h"),
        target_root: Path | None = typer.Option(None, "--target-root"),
        dry_run: bool = typer.Option(True, "--dry-run/--write"),
    ) -> None:
        """Install generated command packages into native runtime locations."""
        payload = materialize_native_install(
            output_dir=output_dir,
            scope=scope,
            hosts=host or None,
            target_root=target_root,
            dry_run=dry_run,
        )
        typer.echo(json.dumps(payload, indent=2))


__all__ = ["register_install_command"]
