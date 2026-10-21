# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin CLI command implementations for `plugin_install`."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


def plugin_init(
    name: str = typer.Argument(..., help="Plugin short name or reverse-domain id (e.g. 'my-plugin' or 'com.example.my-plugin')"),
    path: Path = typer.Option(None, "--path", "-p", help="Target parent directory (default: current working directory)"),
    plugin_type: str = typer.Option("agent", "--type", "-t", help="Plugin type: agent | provider | hook (controls default isolation)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview scaffold content without writing files"),
) -> None:
    """Scaffold a new Mekong CLI plugin directory."""
    import src.cli.commands.plugin_install as _mod

    if plugin_type not in _mod._ISOLATION_MAP:
        _mod.console.print(f"[bold red]Invalid type: {plugin_type!r}[/bold red]\nLoại không hợp lệ. Chọn: {', '.join(_mod._ISOLATION_MAP.keys())}")
        raise typer.Exit(code=1)

    plugin_id = _mod._plugin_id_from_name(name)
    target_root = path or Path.cwd()
    if not target_root.is_dir():
        _mod.console.print(f"[bold red]Target directory not found: {target_root}[/bold red]")
        raise typer.Exit(code=1)

    result = _mod._scaffold(plugin_id, target_root, plugin_type=plugin_type, dry_run=dry_run)
    if dry_run:
        _mod.console.print("[yellow]No files written.[/yellow]")
        return

    plugin_dir = result if isinstance(result, Path) else target_root / plugin_id
    _mod.console.print(f"[bold green]{plugin_id}[/bold green] — [dim]{plugin_dir}[/dim]")
    _mod.console.print("[dim]Scaffolded plugin directory. / Đã khởi tạo plugin.[/dim]")
    _mod._render_manfiest_info(_mod.PluginManifestSchema.from_file(plugin_dir))


def plugin_install(
    source: str = typer.Argument(..., help="Plugin source: local path, git URL, ZIP URL, or PyPI package name"),
    name: str = typer.Option("", "--name", "-n", help="Install as this name (default: from manifest)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing plugin with same name"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate source without writing files"),
) -> None:
    """Install a Mekong CLI plugin from a local path, git repo, ZIP, or PyPI."""
    import src.cli.commands.plugin_install as _mod

    with _mod.console.status("[bold cyan]Detecting source type...", spinner="dots"):
        source_type, _ = _mod._detect_source(source)
    _mod.console.print(f"[bold]Source:[/bold] [{source_type}]{source}[/{source_type}]")

    if dry_run:
        _mod.console.print(f"[dim]Plugins root: {_mod._get_plugins_dir()}\n[yellow]Dry-run—no files written.[/yellow]")
        return

    with Progress(SpinnerColumn(), TextColumn("[bold cyan]{task.description}"), console=_mod.console) as progress:
        task = progress.add_task("Installing plugin...", total=None)
        result = _mod._install_source(source, name, force)
        progress.remove_task(task)

    if result.get("status") == "installed":
        _mod.console.print(f"\n[bold green]Installed[/bold green] [bold]{result.get('install_name', '?')}[/bold]")
        _mod.console.print(f"[dim]ID: {result.get('plugin_id', '?')}  |  Source: {source_type}")
    else:
        _mod.console.print(f"\n[bold red]Install failed:[/bold red] {result.get('error_message', 'Unknown error')}")
        raise typer.Exit(code=1)


def plugin_list(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show plugin details"),
) -> None:
    """List installed Mekong CLI plugins."""
    import src.cli.commands.plugin_install as _mod

    plugins_dir = _mod._get_plugins_dir()
    runtime = _mod._get_runtime(plugins_dir)
    runtime.discover_manifests()
    installed = runtime.loaded_plugins()
    if not installed:
        _mod.console.print(f"[yellow]No plugins installed in {plugins_dir}[/yellow]")
        return

    table = Table(title=f"Installed plugins ({len(installed)})", box=None, show_header=True, header_style="bold cyan")
    for col, kw in [("Name", {"style": "bold"}), ("ID", {"style": "dim"}), ("Version", {"justify": "right"}), ("Isolation", {})]:
        table.add_column(col, **kw)
    for info in installed:
        m = info.manifest
        table.add_row(m.name or m.id.rsplit(".", 1)[-1], m.id, m.version, m.isolation)
    _mod.console.print(table)


def plugin_uninstall(
    name: str = typer.Argument(..., help="Plugin name or id to remove"),
) -> None:
    """Remove an installed plugin."""
    import src.cli.commands.plugin_install as _mod

    plugins_dir = _mod._get_plugins_dir()
    target = plugins_dir / name
    if not target.exists():
        runtime = _mod._get_runtime(plugins_dir)
        runtime.discover_manifests()
        for info in runtime.loaded_plugins():
            if info.manifest.id == name or info.manifest.name == name:
                target = info.manifest_path.parent
                break
    if not target.exists():
        _mod.console.print(f"[bold red]Plugin not found: {name}[/bold red]")
        raise typer.Exit(code=1)
    if not typer.confirm(f"Remove plugin [bold]{name}[/bold] at {target}?"):
        _mod.console.print("[yellow]Cancelled.[/yellow]")
        return
    _mod.shutil.rmtree(target)
    _mod.console.print(f"[bold green]Uninstalled[/bold green] [dim]{target}[/dim]")
