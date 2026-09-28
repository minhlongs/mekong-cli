# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Antigravity project scaffolding CLI command (`mekong init`).

Provides universal project scaffolding into any designated directory:
- 234 native skills
- 25 domain subagents
- Lifecycle safety hooks (.agents/hooks.json & scripts/hooks/)
- Stdio MCP manifests (.agents/mcp_config.json & scripts/mcp_server.py)
- Workspace rules (GEMINI.md, HARNESS.md)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.box import SIMPLE_HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.core.scaffold import scaffold_antigravity_project

console = Console()


def register_init_command(root: typer.Typer) -> None:
    """Attach the `init` command to the root Typer application."""

    @root.command(name="init")
    def init_cmd(
        path: Path = typer.Argument(
            Path("."),
            help="Target directory to initialize (default: current directory)",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Preview scaffolding manifest without modifying disk",
        ),
        force: bool = typer.Option(
            False,
            "--force",
            "-f",
            help="Overwrite existing files in target directory",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            "-j",
            help="Output machine-readable JSON summary",
        ),
        profile: str = typer.Option(
            "full",
            "--profile",
            "--mode",
            help="Scaffolding preset: full | minimal | antigravity",
        ),
    ) -> None:
        """Initialize and scaffold a full Antigravity project environment."""
        try:
            result = scaffold_antigravity_project(
                target_path=path,
                profile=profile,
                dry_run=dry_run,
                force=force,
            )
        except Exception as exc:
            if json_output:
                err_payload = {
                    "ok": False,
                    "status": "error",
                    "target": str(path.resolve() if isinstance(path, Path) else path),
                    "profile": profile,
                    "dry_run": dry_run,
                    "force": force,
                    "error": str(exc),
                }
                print(json.dumps(err_payload, indent=2))
                raise typer.Exit(code=1)
            else:
                console.print(f"[bold red]Initialization Error:[/bold red] {exc}")
                raise typer.Exit(code=1)

        if json_output:
            # Emit pure, unstyled JSON to stdout
            print(json.dumps(result.to_dict(), indent=2))
            if not result.success:
                raise typer.Exit(code=1)
            return

        # Interactive / Rich presentation
        target_disp = str(result.target_path)
        if dry_run:
            console.print(
                Panel(
                    Text.from_markup(
                        f"🔎 [bold yellow]Antigravity Scaffolding Preview (Dry Run)[/bold yellow]\n"
                        f"[dim]Target: {target_disp}[/dim]\n"
                        f"[dim]Profile: {profile} | Zero files written to disk[/dim]"
                    ),
                    title="Genesis Preview (Dry Run)",
                    border_style="yellow",
                )
            )
        else:
            console.print(
                Panel(
                    Text.from_markup(
                        f"🎯 [bold green]Genesis Complete: Initialized Antigravity Project[/bold green]\n"
                        f"[dim]Target: {target_disp}[/dim]\n"
                        f"[dim]Profile: {profile}[/dim]"
                    ),
                    title="Genesis Complete",
                    border_style="green",
                )
            )

        # Summary statistics table
        table = Table(
            title=f"Scaffolding Summary ({result.profile} profile)",
            box=SIMPLE_HEAVY,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Asset Category", style="bold")
        table.add_column("Status / Count", style="dim")

        table.add_row(
            "Native Skills",
            f"{result.stats.get('skills', 0)} skills (.agents/skills/*/SKILL.md)",
        )
        table.add_row(
            "Domain Subagents",
            f"{result.stats.get('subagents', 0)} subagents (registry.json + definitions)",
        )
        table.add_row(
            "Lifecycle Hooks",
            f"{result.stats.get('hooks', 0)} hooks (hooks.json + scripts/hooks/)",
        )
        table.add_row(
            "Stdio MCP Server",
            f"{result.stats.get('mcp', 0)} configs (mcp_config.json + scripts/mcp_server.py)",
        )
        table.add_row(
            "Runtime Rules",
            f"{result.stats.get('rules', 0)} rules (GEMINI.md, HARNESS.md)",
        )
        table.add_row(
            "Total Files",
            f"{result.stats.get('total_files', 0)} files in manifest",
        )

        console.print(table)

        if result.skipped_files:
            console.print(
                f"[yellow]⚠️  Skipped {len(result.skipped_files)} existing file(s). Use --force to overwrite.[/yellow]"
            )
        if result.modified_files:
            console.print(
                f"[cyan]🔄 Overwrote {len(result.modified_files)} existing file(s) (--force).[/cyan]"
            )

        if not dry_run:
            console.print("\n[bold green]✨ Next steps:[/bold green]")
            console.print(f"  1. [bold cyan]cd {path}[/bold cyan]")
            console.print("  2. [bold cyan]mekong doctor[/bold cyan]         # Verify system health")
            console.print("  3. [bold cyan]mekong cook \"your goal\"[/bold cyan] # Start building autonomously\n")
