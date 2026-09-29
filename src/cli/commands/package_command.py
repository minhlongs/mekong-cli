# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/package_command.py — Multi-Platform Release Packaging CLI.

Coordinates deterministic distribution packaging, Homebrew formula generation,
Docker asset synthesis, and release integrity verification.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.packaging_bridge import PackagingBridge

console = Console()


def register_package_command(app: typer.Typer) -> None:
    """Register the 'package' command onto the main Typer application."""

    @app.command(name="package")
    def package(
        output_dir: str = typer.Option(
            "dist",
            "--output-dir",
            "-o",
            help="Destination directory for distribution artifacts",
        ),
        target: str = typer.Option(
            "all",
            "--target",
            "-t",
            help="Target platform: pypi, homebrew, docker, or all",
        ),
        verify: bool = typer.Option(
            False,
            "--verify",
            help="Verify metadata and asset completeness without generating artifacts",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Output machine-readable JSON build manifest",
        ),
    ) -> None:
        """📦 Multi-Platform Packaging: Generate Homebrew formula, Docker assets, and release manifests."""
        bridge = PackagingBridge()

        if verify:
            is_valid, errors = bridge.validate_metadata()
            meta = bridge.read_metadata()
            res = {
                "ok": is_valid,
                "metadata": meta.to_dict(),
                "errors": errors,
            }
            if json_output:
                print(json.dumps(res, indent=2))
                return

            if is_valid:
                console.print(f"[bold green]✓ Package metadata for {meta.name} v{meta.version} is valid.[/bold green]")
            else:
                console.print(f"[bold red]✗ Package metadata validation failed:[/bold red]")
                for err in errors:
                    console.print(f"  • [red]{err}[/red]")
            return

        report = bridge.build_distribution_package(target=target, output_dir=Path(output_dir))

        if json_output:
            print(json.dumps(report.to_dict(), indent=2))
            return

        console.print(
            Panel(
                f"[bold cyan]📦 Mekong Release Packaging[/bold cyan]\n"
                f"[dim]Version:[/dim] {report.version} | [dim]Target:[/dim] {target}\n"
                f"[dim]Output Directory:[/dim] {output_dir}\n"
                f"[dim]Skills Bundled:[/dim] {report.skills_bundled} | [dim]Subagents:[/dim] {report.subagents_bundled}",
                title="Distribution Build System",
                border_style="cyan",
            )
        )

        table = Table(title="Generated Release Artifacts", box=ROUNDED)
        table.add_column("Type", style="cyan")
        table.add_column("Path", style="bold")
        table.add_column("Size", justify="right")
        table.add_column("SHA-256 Checksum", style="dim")

        for art in report.artifacts:
            table.add_row(
                art.artifact_type,
                str(Path(art.file_path).name),
                f"{art.size_bytes} B",
                art.sha256[:16] + "...",
            )

        console.print(table)
        console.print(f"[bold green]✓ Packaging complete. {len(report.artifacts)} artifacts created in {output_dir}/[/bold green]")
