# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helpers for `mekong build info` and `mekong build docker` subcommands."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table


def _mod():
    import src.commands.build as mod

    return mod


def run_build_info() -> None:
    """Show build information and status."""
    m = _mod()
    m.console.print(Panel("[bold]Build Information[/bold]", title="Build Status"))

    table = Table(title="Build Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Location", style="dim")

    dist_path = m.Path("dist")
    if dist_path.exists() and any(dist_path.iterdir()):
        table.add_row("Python Package", "✅ Built", str(dist_path.absolute()))
    else:
        table.add_row("Python Package", "❌ Not built", "Run: mekong build")

    build_path = m.Path("build")
    if build_path.exists():
        table.add_row("JS Frontend", "✅ Built", str(build_path.absolute()))
    else:
        table.add_row("JS Frontend", "❌ Not built", "Requires package.json and build script")

    try:
        result = m.subprocess.run(
            ["docker", "images", "mekong-cli"],
            capture_output=True,
            text=True,
        )
        if "mekong-cli" in result.stdout:
            table.add_row("Docker Image", "✅ Built", "mekong-cli:latest")
        else:
            table.add_row("Docker Image", "❌ Not built", "Requires Dockerfile")
    except FileNotFoundError:
        table.add_row("Docker Image", "❌ Docker not found", "Install Docker first")

    m.console.print(table)


def run_build_docker(tag: str, push: bool, no_cache: bool, verbose: bool) -> None:
    """Build Docker image specifically."""
    m = _mod()
    m.console.print(f"[bold blue]🐳 Building Docker image: {tag}[/bold blue]")

    try:
        cmd = ["docker", "build", "-t", tag]
        if no_cache:
            cmd.append("--no-cache")
        cmd.append(".")

        m.subprocess.run(
            cmd,
            cwd=m.Path.cwd(),
            check=True,
            capture_output=not verbose,
            text=True,
        )

        m.console.print(f"[green]✅ Docker image built: {tag}[/green]")

        if push:
            m.console.print(f"[bold blue]⬆️  Pushing image: {tag}[/bold blue]")
            m.subprocess.run(
                ["docker", "push", tag],
                cwd=m.Path.cwd(),
                check=True,
                capture_output=not verbose,
                text=True,
            )
            m.console.print(f"[green]✅ Docker image pushed: {tag}[/green]")

    except m.subprocess.CalledProcessError as e:
        m.console.print("[red]❌ Docker operation failed![/red]")
        if e.stderr:
            m.console.print(Panel(e.stderr, title="Error"))
    except FileNotFoundError:
        m.console.print("[red]docker not found. Install Docker first[/red]")
