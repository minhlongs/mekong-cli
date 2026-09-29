# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Particle init Typer sub-app — ZenOS particle scaffolding.

Registers the ``mekong particle init`` command that creates a new ZenOS particle
directory from the skeleton template in ``mekong/skel/``. This is a ZenOS
particle scaffold, **not** AgentKit ``ak new``. For AgentKit ownership
tracking use ``/ak:init`` or ``$HOME/bin/ak``.

Commands:
    init    Create a new particle directory with constitution and AI cell configs.
            ``--dry-run`` previews skeleton files without creating them.

Import path used by ``src/cli/app_setup.py``::

    from src.cli.commands.particle_init import particle_app
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

# ---------------------------------------------------------------------------
# App wiring
# ---------------------------------------------------------------------------

particle_app = typer.Typer(
    name="particle",
    help="ZenOS particle management",
    no_args_is_help=False,
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()


@particle_app.callback(invoke_without_command=True)
def particle_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """ZenOS particle lifecycle, trust relationships, and AI cell management."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.particle_engine import ParticleEngine
    engine = ParticleEngine()
    status_data = engine.get_status()

    if json_mode:
        import json
        typer.echo(json.dumps(status_data, indent=2))
        return

    from rich.table import Table
    console.print(
        Panel(
            f"[bold cyan]ZenOS Particle Topology & AI Cell Engine[/]\n\n"
            f"  Total Particles:     [green]{status_data['total_particles']}[/]\n"
            f"  Active Connections:  [cyan]{status_data['active_connections']}[/]\n"
            f"  Behaviors Recorded:  [yellow]{status_data['recorded_behaviors']}[/]\n"
            f"  Average Trust Score: [magenta]{status_data['average_trust_score']}[/]\n"
            f"  AI Cell Executions:  [bold]{status_data['cell_executions']['total']}[/] ([green]{status_data['cell_executions']['compliance_passed']} passed[/])",
            title="[bold blue]ZenOS Particle Overview[/]",
            border_style="blue",
        )
    )

    table = Table(title="Registered Particles", show_header=True, header_style="bold magenta")
    table.add_column("Particle ID", style="dim", width=22)
    table.add_column("Name", style="cyan", width=20)
    table.add_column("Trust", justify="right", width=8)
    table.add_column("Status", width=10)
    table.add_column("Mission", style="dim")

    for p in status_data.get("recent_particles", []):
        table.add_row(
            p["particle_id"],
            p["name"],
            f"{p['trust_score']:.1f}",
            f"[green]{p['status']}[/]" if p["status"] == "active" else f"[yellow]{p['status']}[/]",
            p["mission"][:45] + "..." if len(p["mission"]) > 45 else p["mission"],
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

SKEL_DIR = Path(__file__).resolve().parent.parent.parent.parent / "mekong" / "skel"


def _find_mekong_root() -> Path:
    """Walk up from this file to find the mekong-cli root (where mekong/ lives)."""
    return Path(__file__).resolve().parent.parent.parent.parent


def _replace_placeholders(text: str, replacements: dict[str, str]) -> str:
    """Replace ``{{KEY}}`` placeholders in *text* with *replacements* values."""
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _copy_and_interpolate(
    src_dir: Path,
    dst_dir: Path,
    replacements: dict[str, str],
) -> list[Path]:
    """Recursively copy *src_dir* to *dst_dir*, replacing placeholders in each file.

    Returns a list of every file created.
    """
    created: list[Path] = []

    for root, dirs, files in os.walk(src_dir):
        rel = Path(root).relative_to(src_dir)
        target_dir = dst_dir / rel
        target_dir.mkdir(parents=True, exist_ok=True)

        for name in files:
            src_path = Path(root) / name
            dst_path = target_dir / name
            content = src_path.read_text(encoding="utf-8")
            content = _replace_placeholders(content, replacements)
            dst_path.write_text(content, encoding="utf-8")
            created.append(dst_path)

    return created


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@particle_app.command(name="init")
def init_cmd(
    name: str = typer.Argument(..., help="Name of the ZenOS particle"),
    mission: str = typer.Option(
        "",
        "--mission",
        "-m",
        help="Mission statement for the particle constitution",
    ),
    template: str = typer.Option(
        "skel",
        "--template",
        "-t",
        help="Template name (default: skel). Reserved for future curated templates.",
    ),
    review: Optional[str] = typer.Option(
        None,
        "--review",
        help="Path to ZENOS.md constitution file for constitutional review",
    ),
    output_dir: str = typer.Option(
        ".",
        "--dir",
        "-d",
        help="Parent directory to create the particle in (default: CWD).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview ZenOS particle files without creating them.",
    ),
    json_mode: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON",
    ),
) -> None:
    """Create a new ZenOS particle from the skeleton template.

    Copies ``mekong/skel/`` to *output_dir*/*name*/, replaces ``{{PARTICLE_NAME}}``,
    ``{{MISSION_STATEMENT}}``, ``{{PARTICLE_ID}}``, and other placeholders, and
    prints the newly generated particle ID.

    Use ``--dry-run`` to preview the skeleton files that would be created
    without writing anything to disk. This is distinct from AgentKit
    ``ak new`` (fresh scaffold) — ZenOS particles are a MekOS construct.
    """
    if review:
        from src.mekong.constitution.review import review_constitution

        try:
            result = review_constitution(review)
        except ValueError as exc:
            console.print(f"[bold red]Error:[/] {exc}")
            raise typer.Exit(code=1)
        print(result.format())
        raise typer.Exit(code=0)

    target = Path(output_dir).resolve() / name

    if not SKEL_DIR.exists():
        console.print(
            f"[bold red]Error:[/] Skeleton template not found at {SKEL_DIR}. "
            "Is mekong-cli installed correctly?"
        )
        raise typer.Exit(code=1)

    # --dry-run: list files that *would* be created from mekong/skel/
    if dry_run:
        rel_name = name
        if json_mode:
            import json
            typer.echo(json.dumps({
                "status": "dry_run",
                "name": rel_name,
                "target": str(target),
                "template": str(SKEL_DIR),
            }, indent=2))
            raise typer.Exit(code=0)

        console.print("[bold yellow][DRY RUN][/] Preview only — nothing will be created.\n")
        console.print(f"  Particle:  [cyan]{rel_name}[/]")
        console.print(f"  Target:    [cyan]{target}[/]")
        console.print(f"  Template:  [cyan]{SKEL_DIR}[/]\n")
        console.print("[bold]Files that would be created:[/]")
        preview_count = 0
        for root, _dirs, files in os.walk(SKEL_DIR):
            for fname in files:
                rel = Path(root).relative_to(SKEL_DIR) / fname
                console.print(f"    - {rel_name}/{rel}")
                preview_count += 1
        console.print(f"\n[dim]Total: {preview_count} files. Run without --dry-run to scaffold.[/]")
        raise typer.Exit(code=0)

    if target.exists():
        console.print(
            f"[bold red]Error:[/] {target} already exists. "
            "Choose a different name or remove it first."
        )
        raise typer.Exit(code=1)

    # Generate particle identity
    particle_id = str(uuid.uuid4())
    created_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    mission_text = mission or f"{name} — ZenOS Particle"

    replacements = {
        "PARTICLE_ID": particle_id,
        "PARTICLE_NAME": name,
        "MISSION_STATEMENT": mission_text,
        "CREATED_DATE": created_date,
        "TEMPLATE_NAME": template,
    }

    created_files = _copy_and_interpolate(SKEL_DIR, target, replacements)

    # Register in ParticleEngine
    try:
        from src.core.particle_engine import ParticleEngine
        ParticleEngine().init_particle(name=name, mission=mission_text, template=template)
    except Exception:
        pass

    if json_mode:
        import json
        typer.echo(json.dumps({
            "particle_id": particle_id,
            "name": name,
            "mission": mission_text,
            "path": str(target),
            "files_count": len(created_files),
            "created_at": created_date,
        }, indent=2))
        raise typer.Exit(code=0)

    console.print(
        Panel(
            f"[bold green]Particle Initialized[/]\n\n"
            f"  Name:       [cyan]{name}[/]\n"
            f"  ID:         [cyan]{particle_id}[/]\n"
            f"  Mission:    [cyan]{mission_text}[/]\n"
            f"  Path:       [cyan]{target}[/]\n"
            f"  Files:      [cyan]{len(created_files)}[/]\n\n"
            f"[dim]Next steps:[/]\n"
            f"  cd {name}\n"
            f"  mekong particle status {name}\n"
            f"  mekong particle list",
            title="[bold]ZenOS Init Complete[/]",
            border_style="green",
        )
    )

    typer.echo(particle_id)


@particle_app.command(name="list")
def list_cmd(
    status: str = typer.Option("all", "--status", "-s", help="Filter by status (active, dormant, revoked, all)"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum particles to return"),
    json_mode: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """List registered ZenOS particles."""
    from src.core.particle_engine import ParticleEngine
    engine = ParticleEngine()
    particles = engine.list_particles(status=status, limit=limit)

    if json_mode:
        import json
        typer.echo(json.dumps(particles, indent=2))
        return

    from rich.table import Table
    table = Table(title=f"ZenOS Particles (status: {status})", show_header=True, header_style="bold magenta")
    table.add_column("Particle ID", style="dim", width=22)
    table.add_column("Name", style="cyan", width=20)
    table.add_column("Trust", justify="right", width=8)
    table.add_column("Status", width=10)
    table.add_column("Mission", style="dim")

    for p in particles:
        table.add_row(
            p["particle_id"],
            p["name"],
            f"{p['trust_score']:.1f}",
            f"[green]{p['status']}[/]" if p["status"] == "active" else f"[yellow]{p['status']}[/]",
            p["mission"][:45] + "..." if len(p["mission"]) > 45 else p["mission"],
        )

    console.print(table)

