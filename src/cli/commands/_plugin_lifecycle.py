# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin lifecycle subcommands: list, remove, install, update."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import typer


def _register_list(app: typer.Typer) -> None:
    import src.cli.commands.plugin as _plugin_mod

    @app.command("list")
    def list_cmd(
        json_output: bool = typer.Option(False, "--json", help="Output as JSON array"),
    ) -> None:
        """List all loaded plugins with their status."""
        runtime = _plugin_mod._get_runtime()
        infos: list[dict] = []

        for loaded in runtime.iter_loaded():
            name = loaded.plugin_id or "unknown"
            version = ""
            if loaded.manifest is not None:
                try:
                    name = getattr(loaded.manifest, "name", name) or name
                    version = getattr(loaded.manifest, "version", "") or ""
                except Exception:
                    pass

            plugin_type = loaded.plugin_type or "unknown"
            if json_output:
                infos.append(
                    {
                        "id": loaded.plugin_id,
                        "name": name,
                        "version": version,
                        "type": plugin_type,
                        "source": loaded.source,
                    }
                )
            else:
                status_icon = "[green]✓[/green]" if not loaded.error_message else "[red]✗[/red]"
                typer.echo(
                    f"{status_icon} {loaded.plugin_id}  "
                    f"v{version or '?'}  ({plugin_type})  [dim]{loaded.source}[/dim]"
                )

        if json_output:
            typer.echo(json.dumps(infos, indent=2, ensure_ascii=False))


def _register_remove(app: typer.Typer) -> None:
    import src.cli.commands.plugin as _plugin_mod

    @app.command("remove")
    def remove_cmd(
        plugin_id: str = typer.Argument(..., help="Plugin ID to remove (e.g. com.example.my-plugin)"),
        force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    ) -> None:
        """Uninstall a plugin by ID."""
        runtime = _plugin_mod._get_runtime()
        loaded = runtime.get_loaded(plugin_id)
        if loaded is not None:
            if not force:
                typer.echo(f"Plugin '{plugin_id}' is currently loaded.")
                if not typer.confirm("Stop and remove it?", default=False):
                    typer.echo("Cancelled.")
                    raise typer.Exit(code=0)

            try:
                if loaded.instance is not None:
                    loaded.instance.stop()
                    loaded.instance.dispose()
            except Exception as exc:
                typer.echo(f"Warning: error stopping plugin: {exc}", err=True)

            runtime.unload_all()
            typer.echo(f"Unloaded: {plugin_id}")

        manifest_path = None
        for base in runtime.plugin_dirs:
            if not base.is_dir():
                continue
            candidate = base / plugin_id.replace("/", "_").replace(".", "_")
            slug = plugin_id.rsplit(".", 1)[-1]
            for c in (candidate, base / f"plugin-{slug}"):
                if c.is_dir() and (c / ".plugin.json").is_file():
                    manifest_path = c / ".plugin.json"
                    break
            if manifest_path:
                break

        if manifest_path is None:
            typer.echo(f"Error: plugin '{plugin_id}' not found in any plugin directory.", err=True)
            raise typer.Exit(code=1)

        plugin_dir = manifest_path.parent
        if not force:
            typer.echo(f"Will remove: {plugin_dir}")
            if not typer.confirm("Proceed?", default=False):
                typer.echo("Cancelled.")
                raise typer.Exit(code=0)

        shutil.rmtree(plugin_dir)
        typer.echo(f"Removed: {plugin_dir}")


def _register_install(app: typer.Typer) -> None:
    import src.cli.commands.plugin as _plugin_mod

    @app.command("install")
    def install_cmd(
        source: str = typer.Argument(..., help="Local path, git URL, ZIP URL, or mekong-plugin-<name> (PyPI)"),
        name: str = typer.Option("", "--name", "-n", help="Override install folder name"),
        force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing plugin"),
    ) -> None:
        """Install a plugin from a local path, git repo, ZIP URL, or PyPI package."""
        runtime = _plugin_mod._get_runtime()
        if runtime is None:
            typer.echo("Error: plugin runtime not initialised.", err=True)
            raise typer.Exit(code=1)

        target_dir = runtime.plugin_dirs[0] if runtime.plugin_dirs else Path.home() / ".mekong" / "plugins"
        result = runtime.install(source, name=name, force=force)
        if result["status"] != "installed":
            typer.echo(f"Error: {result['error_message']}", err=True)
            raise typer.Exit(code=1)

        slug = result.get("install_name", source)
        typer.echo(f"Installed: {slug} -> {target_dir / slug}")
        typer.echo("Restart mekong, or re-run for the plugin to load.")


def _register_update(app: typer.Typer) -> None:
    import src.cli.commands.plugin as _plugin_mod

    @app.command("update")
    def update_cmd(
        plugin_id: str = typer.Argument(..., help="Plugin ID to update (e.g. com.example.my-plugin)"),
        source: str = typer.Option("", "--source", help="Path to updated plugin source"),
    ) -> None:
        """Refresh an installed plugin."""
        runtime = _plugin_mod._get_runtime()
        loaded = runtime.get_loaded(plugin_id)
        if loaded and loaded.instance is not None:
            try:
                loaded.instance.stop()
                loaded.instance.dispose()
            except Exception as exc:
                typer.echo(f"Warning: error stopping plugin: {exc}", err=True)

        if source:
            src_path = Path(source).resolve()
            if not src_path.is_dir():
                typer.echo(f"Error: source '{source}' is not a directory.", err=True)
                raise typer.Exit(code=1)
            target = None
            for base in runtime.plugin_dirs:
                if not base.is_dir():
                    continue
                candidate = base / f"plugin-{plugin_id.rsplit('.', 1)[-1]}"
                if candidate.is_dir() and (candidate / ".plugin.json").is_file():
                    target = candidate
                    break
            if target is None:
                typer.echo(f"Error: plugin '{plugin_id}' not found in plugin directories.", err=True)
                raise typer.Exit(code=1)
            shutil.rmtree(target)
            shutil.copytree(src_path, target)
            typer.echo(f"Updated: {plugin_id} <- {src_path}")
        else:
            typer.echo(f"Plugin '{plugin_id}' will be reloaded on next CLI start.")
            runtime.unload_all()
