"""Package build verification subcommand for command fabric."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from src.command_fabric.package_build import verify_package_builds


def register_package_build_command(app: typer.Typer) -> None:
    """Register package build contract verification command."""

    @app.command("package-build-check")
    def package_build_cmd(
        bundle_dir: Path = typer.Option(..., "--bundle", "-b"),
    ) -> None:
        """Verify generated IDE package build contracts."""
        typer.echo(json.dumps(verify_package_builds(bundle_dir), indent=2))


__all__ = ["register_package_build_command"]
