"""Particle command group — particle-first tenant management.

Replaces org-based commands with particle-centric operations.
Provides create, status, and constitution subcommands.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.helpers import load_jsonl, append_jsonl

console = Console()

# Storage paths
PARTICLES_DIR = Path.home() / ".mekong"
PARTICLES_FILE = PARTICLES_DIR / "particles.jsonl"


def _ensure_storage() -> None:
    """Ensure particles storage directory exists."""
    PARTICLES_DIR.mkdir(parents=True, exist_ok=True)


def _load_particles() -> list[dict[str, Any]]:
    """Load all particles from storage."""
    if not PARTICLES_FILE.exists():
        return []
    return load_jsonl(PARTICLES_FILE)


def _save_particle(particle: dict[str, Any]) -> None:
    """Append a particle to storage."""
    _ensure_storage()
    append_jsonl(PARTICLES_FILE, particle)


def _find_particle(particle_id: str) -> dict[str, Any] | None:
    """Find a particle by ID."""
    particles = _load_particles()
    for p in particles:
        if p.get("particle_id") == particle_id:
            return p
    return None


def _current_particle() -> dict[str, Any] | None:
    """Get the currently active particle from session config."""
    config_file = PARTICLES_DIR / "active_particle.json"
    if config_file.exists():
        try:
            return json.loads(config_file.read_text())
        except (json.JSONDecodeError, KeyError):
            return None
    return None


def _set_current_particle(particle_id: str) -> None:
    """Set the active particle."""
    config_file = PARTICLES_DIR / "active_particle.json"
    particle = _find_particle(particle_id)
    if not particle:
        raise typer.BadParameter(f"Particle not found: {particle_id}")
    config_file.write_text(json.dumps({"particle_id": particle_id, "updated_at": datetime.now(timezone.utc).isoformat()}))


particle_app = typer.Typer(help="Particle management: create, status, constitution")


@particle_app.command(name="create")
def particle_create(
    name: str = typer.Argument(..., help="Particle display name"),
    constitution_version: str = typer.Option("1.0", "--constitution", "-c", help="Constitution version"),
    metadata: str | None = typer.Option(None, "--metadata", "-m", help="JSON metadata string"),
) -> None:
    """Create a new particle (tenant entity).

    A particle represents an isolated economic entity with its own constitution.

    Examples:
        mekong particle create "My Startup"
        mekong particle create "Acme Corp" --constitution 2.0 --metadata '{"industry":"tech"}'
    """
    _ensure_storage()

    # Generate particle_id
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    particle_id = f"particle_{timestamp}_{name.lower().replace(' ', '_')[:20]}"

    # Parse metadata
    meta: dict[str, Any] = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError as exc:
            raise typer.BadParameter(f"Invalid JSON metadata: {exc}") from exc

    particle = {
        "particle_id": particle_id,
        "name": name,
        "constitution_version": constitution_version,
        "metadata": meta,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
    }

    _save_particle(particle)

    # Set as active particle
    _set_current_particle(particle_id)

    console.print(f"[bold green]✓ Particle created:[/bold green] {particle_id}")
    console.print(f"  Name: {name}")
    console.print(f"  Constitution: v{constitution_version}")
    console.print(f"  Status: active")
    if meta:
        console.print(f"  Metadata: {json.dumps(meta, indent=2)}")
    console.print("\n[dim]This particle is now active. Use 'mekong particle status' to view details.[/dim]")


@particle_app.command(name="status")
def particle_status(
    particle_id: str | None = typer.Argument(None, help="Particle ID (defaults to active particle)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON"),
) -> None:
    """Show particle status and details.

    Without particle_id, shows the currently active particle.
    """
    # Resolve particle
    if particle_id is None:
        current = _current_particle()
        if not current:
            console.print("[yellow]⚠️ No active particle. Create one with 'mekong particle create' or specify a particle_id.[/yellow]")
            raise typer.Exit(1)
        particle_id = current["particle_id"]

    particle = _find_particle(particle_id)
    if not particle:
        console.print(f"[bold red]Particle not found:[/bold red] {particle_id}")
        raise typer.Exit(1)

    if json_output:
        typer.echo(json.dumps(particle, indent=2))
        return

    table = Table(title=f"Particle: {particle_id}")
    table.add_column("Property", style="dim")
    table.add_column("Value")

    table.add_row("ID", particle_id)
    table.add_row("Name", particle.get("name", "-"))
    table.add_row("Status", particle.get("status", "unknown"))
    table.add_row("Constitution", f"v{particle.get('constitution_version', '?')}")
    table.add_row("Created", particle.get("created_at", "-"))

    if particle.get("metadata"):
        meta_str = json.dumps(particle["metadata"], indent=2)
        table.add_row("Metadata", meta_str)

    console.print(table)

    # Show constitution summary
    console.print("\n[bold]Constitution Summary[/bold]")
    console.print("  Use 'mekong particle constitution' to view full constitution")
    console.print("  Use 'mekong constitution review' to evaluate actions")


@particle_app.command(name="constitution")
def particle_constitution(
    particle_id: str | None = typer.Argument(None, help="Particle ID (defaults to active particle)"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text, json"),
) -> None:
    """Show the particle's constitution document.

    Displays the constitutional principles and configuration for the particle.
    """
    # Resolve particle
    if particle_id is None:
        current = _current_particle()
        if not current:
            console.print("[yellow]⚠️ No active particle. Create one first.[/yellow]")
            raise typer.Exit(1)
        particle_id = current["particle_id"]

    particle = _find_particle(particle_id)
    if not particle:
        console.print(f"[bold red]Particle not found:[/bold red] {particle_id}")
        raise typer.Exit(1)

    # Get constitution - for now, read from core module or config
    # In a full implementation, this would load particle-specific constitution settings
    from src.core.constitution import get_constitution, Principle

    constitution = get_constitution()
    principles = list(Principle)

    if format == "json":
        output = {
            "particle_id": particle_id,
            "constitution_version": particle.get("constitution_version", "1.0"),
            "principles": [p.value for p in principles],
            "description": "Constitutional AI governance framework",
        }
        typer.echo(json.dumps(output, indent=2))
        return

    # Text format
    panel = Panel.fit(
        f"[bold]Particle Constitution[/bold]\n"
        f"Particle: {particle_id}\n"
        f"Version: v{particle.get('constitution_version', '1.0')}\n\n"
        f"Principles ({len(principles)}):\n"
        + "\n".join(f"  • {p.value}" for p in principles),
        title="Constitutional Framework",
        border_style="cyan",
    )
    console.print(panel)

    console.print("\n[bold]Usage:[/bold]")
    console.print("  mekong constitution review <action> --params '<json>'")
    console.print("  mekong constitution principles --detailed")


# Export the app for registration
def get_particle_app() -> typer.Typer:
    """Return the particle Typer app."""
    return particle_app
