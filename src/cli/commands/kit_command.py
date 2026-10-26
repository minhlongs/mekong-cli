# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""AgentKit CLI command group (mekong kit <list|install|export>).

Allows listing the 4 canonical Kits (kit:re, kit:engineer, kit:business, kit:marketing),
installing a kit into the current workspace (.mekong/ownership.json + ~/.mekong),
and exporting kit manifests to 7 native targets (claude-code, codex, cursor, agy, pi, omp, dsh) + portable.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.kit_registry import SUPPORTED_TARGETS, KitRegistry
from src.core.kit_storage import OwnershipLedger, get_global_mekong_dir

console = Console()
kit_app = typer.Typer(
    help="AgentKit Multi-Kit Packaging & Multi-Target Exporter (kit:re, kit:engineer, kit:business, kit:marketing).",
    rich_markup_mode="rich",
)


@kit_app.command("list")
def cmd_list_kits(
    json_output: bool = typer.Option(False, "--json", help="Output kit catalog as JSON"),
) -> None:
    """List the 4 canonical AgentKit kits and supported export targets."""
    registry = KitRegistry()
    kits = registry.list_kits()

    if json_output:
        data = [
            {
                "id": k.id,
                "name": k.name,
                "version": k.version,
                "description": k.description,
                "commands": k.commands,
                "skills": k.skills,
                "mcp_servers": k.mcp_servers,
            }
            for k in kits
        ]
        typer.echo(json.dumps({"kits": data, "targets": list(SUPPORTED_TARGETS)}, indent=2))
        return

    table = Table(title="📦 Mekong AgentKit Catalog (4 Kits)", show_header=True, header_style="bold cyan")
    table.add_column("Kit ID", style="bold green")
    table.add_column("Name", style="bold")
    table.add_column("Commands", style="yellow")
    table.add_column("MCP Bridges", style="magenta")

    for k in kits:
        table.add_row(
            k.id,
            k.name,
            ", ".join(k.commands[:6]) + ("..." if len(k.commands) > 6 else ""),
            ", ".join(k.mcp_servers),
        )

    console.print(table)
    console.print(f"[dim]Supported targets (7 native + portable): {', '.join(SUPPORTED_TARGETS)}[/dim]")


@kit_app.command("install")
def cmd_install_kit(
    kit_id: str = typer.Argument(..., help="Kit ID to install (e.g. kit:re, kit:engineer, kit:business, kit:marketing)"),
    workspace: str = typer.Option(".", "--workspace", "-w", help="Project workspace directory"),
) -> None:
    """Install a Kit into the workspace and record SHA-256 ownership in .mekong/ownership.json."""
    registry = KitRegistry()
    kit = registry.get_kit(kit_id)
    if kit is None:
        console.print(f"[red]Unknown kit '{kit_id}'. Use 'mekong kit list' to view available kits.[/red]")
        raise typer.Exit(1)

    # Ensure global ~/.mekong (0700) is initialized
    global_dir = get_global_mekong_dir()

    ws_path = Path(workspace).resolve()
    mekong_dir = ws_path / ".mekong" / "kits"
    mekong_dir.mkdir(parents=True, exist_ok=True)

    short_id = kit.id.replace("kit:", "")
    manifest_file = mekong_dir / f"{short_id}.json"
    manifest_data = registry.render_target_manifest(kit, "portable")
    manifest_file.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

    ledger = OwnershipLedger(root_dir=ws_path)
    rel_path = manifest_file.relative_to(ws_path).as_posix()
    ledger.register_file(rel_path, owner=kit.id)

    panel = Panel(
        f"[bold green]✓ Installed {kit.id}[/bold green] ({kit.name})\n"
        f"[bold]Global Home:[/bold] {global_dir} (mode 0700)\n"
        f"[bold]Manifest:[/bold] {rel_path}\n"
        f"[bold]Ownership Ledger:[/bold] .mekong/ownership.json (SHA-256 verified)",
        title="🔧 AgentKit Installation",
        expand=False,
    )
    console.print(panel)


@kit_app.command("export")
def cmd_export_kit(
    kit_id: str = typer.Argument(..., help="Kit ID (e.g. kit:re or all)"),
    target: str = typer.Option(
        "portable",
        "--target",
        "-t",
        help="Target agent runtime: claude-code|codex|cursor|agy|pi|omp|dsh|portable|all",
    ),
    out_dir: str = typer.Option(".mekong/exports", "--out", "-o", help="Output directory for exported manifests"),
) -> None:
    """Export Kit manifest(s) to any of the 7 native agent targets or portable format."""
    registry = KitRegistry()
    kits = registry.list_kits() if kit_id == "all" else [registry.get_kit(kit_id)]
    if any(k is None for k in kits):
        console.print(f"[red]Unknown kit '{kit_id}'.[/red]")
        raise typer.Exit(1)

    targets = list(SUPPORTED_TARGETS) if target == "all" else [target]
    for t in targets:
        if t not in SUPPORTED_TARGETS:
            console.print(
                f"[red]Unsupported target '{t}'. Supported: {', '.join(SUPPORTED_TARGETS)}[/red]"
            )
            raise typer.Exit(2)

    out_path = Path(out_dir).resolve()
    exported_files: list[str] = []
    for k in kits:
        assert k is not None
        for t in targets:
            f_path = registry.export_kit(k.id, t, out_path, record_ownership=True)
            exported_files.append(str(f_path.relative_to(out_path)))

    console.print(
        f"[bold green]✓ Exported {len(exported_files)} manifest(s) to {out_path}[/bold green]"
    )
    for ef in exported_files:
        console.print(f"  • {ef}")


__all__ = ["kit_app"]
