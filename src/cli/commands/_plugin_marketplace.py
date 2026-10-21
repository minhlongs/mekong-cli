# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin marketplace search and publish subcommands."""

from __future__ import annotations

import json as _json
import os as _os
from pathlib import Path
from typing import Any

import typer

DEFAULT_PUBLISH_DIR = Path.home() / ".mekong" / "plugin-publish"


def _register_search(app: typer.Typer) -> None:
    import src.cli.commands.plugin as _plugin_mod

    @app.command("search")
    def search_cmd(
        query: str = typer.Argument(..., help="Search query (matches plugin name or id)"),
        remote: bool = typer.Option(
            False, "--remote", help="Search remote marketplace instead of local plugins"
        ),
        json_output: bool = typer.Option(
            False, "--json", help="Output results as JSON array"
        ),
    ) -> None:
        """Search plugins by name or ID substring."""
        if remote:
            _plugin_mod._search_remote(query, json_output)
        else:
            _plugin_mod._search_local(query, json_output)


def _search_local(query: str, json_output: bool) -> None:
    """Search loaded plugins by substring match."""
    import src.cli.commands.plugin as _plugin_mod

    runtime = _plugin_mod._get_runtime()
    query_lower = query.lower()
    found = False
    results: list[dict[str, Any]] = []

    for loaded in runtime.iter_loaded():
        searchable = f"{loaded.plugin_id} {(loaded.plugin_id or loaded.source)}".lower()
        if query_lower in searchable:
            version = getattr(loaded.manifest, "version", "") if loaded.manifest else ""
            plugin_type = loaded.plugin_type or "unknown"
            entry: dict[str, Any] = {
                "id": loaded.plugin_id,
                "version": version or "?",
                "type": plugin_type,
                "source": loaded.source,
            }
            if json_output:
                results.append(entry)
            else:
                status_icon = "[green]✓[/green]" if not loaded.error_message else "[red]✗[/red]"
                typer.echo(
                    f"{status_icon} {loaded.plugin_id} "
                    f"v{version or '?'} ({plugin_type}) [dim]{loaded.source}[/dim]"
                )
            found = True

    if json_output:
        typer.echo(_json.dumps(results, indent=2, ensure_ascii=False))

    if not found:
        typer.echo(f"No plugins matching '{query}' found.")
        raise typer.Exit(code=1)


def _search_remote(query: str, json_output: bool) -> None:
    """Search marketplace API for plugins."""
    from src.core.plugin_marketplace import DEFAULT_MARKETPLACE_URL, MarketplaceClient

    base_url = _os.environ.get("MEKONG_MARKETPLACE_URL", DEFAULT_MARKETPLACE_URL).rstrip("/")
    client = MarketplaceClient(base_url=base_url)
    try:
        result = client.search(query=query)
    except Exception as exc:
        typer.echo(f"Marketplace search failed: {exc}", err=True)
        raise typer.Exit(code=1)
    finally:
        client.close()

    plugins = result.plugins
    if not plugins:
        typer.echo(f"No marketplace plugins matching '{query}' found.")
        raise typer.Exit(code=1)

    if json_output:
        data = [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "author": p.author,
                "plugin_type": p.plugin_type,
                "downloads": p.downloads,
                "rating": p.rating,
                "tags": p.tags,
            }
            for p in plugins
        ]
        typer.echo(_json.dumps(data, indent=2, ensure_ascii=False))
    else:
        for p in plugins:
            desc = p.description[:80]
            typer.echo(f"{p.name} v{p.version} ({p.plugin_type}) — {desc}")
            if p.tags:
                typer.echo(f" tags: {','.join(p.tags)}")


def _register_publish(app: typer.Typer) -> None:
    import src.cli.commands.plugin as _plugin_mod

    @app.command("publish")
    def publish_cmd(
        path: str = typer.Argument(..., help="Path to plugin directory"),
        version: str = typer.Option(
            "auto",
            "--version",
            "-v",
            help="Version override: semver string or 'auto' for patch bump",
        ),
    ) -> None:
        """Bundle and publish a plugin to the marketplace."""
        plugin_dir = Path(path).resolve()
        if not plugin_dir.is_dir():
            typer.echo(f"Error: '{path}' is not a directory.", err=True)
            raise typer.Exit(code=1)

        manifest_path = plugin_dir / ".plugin.json"
        if not manifest_path.is_file():
            typer.echo(
                f"Error: no .plugin.json found in '{path}'. "
                "Run 'mekong plugin init' first.",
                err=True,
            )
            raise typer.Exit(code=1)

        ver: str | None = None if version == "auto" else version
        try:
            publisher = _plugin_mod.PluginPublisher(plugin_dir)
            zip_path = publisher.bundle(
                output_dir=_plugin_mod.DEFAULT_PUBLISH_DIR, version=ver
            )
        except _plugin_mod.PublishError as exc:
            typer.echo(f"Publish failed: {exc}", err=True)
            raise typer.Exit(code=1)

        plugin_id = publisher.plugin_id
        ver_str = publisher._manifest.get("version", "?")
        typer.echo(f"Published {plugin_id} v{ver_str} -> {zip_path}")
        typer.echo("Note: Marketplace upload is not yet configured. ZIP is queued locally.")
