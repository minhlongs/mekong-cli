# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin scaffolding helpers and `plugin init` command for `plugin_install`."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from src.core.plugin_schema import PluginManifestSchema

_ISOLATION_MAP: dict[str, str] = {
    "agent": "none",
    "provider": "restricted",
    "hook": "sandboxed",
}

_DEFAULT_MANIFEST_TEMPLATE = """\
{{
  "id": "{plugin_id}",
  "name": "{name}",
  "version": "0.1.0",
  "description": "",
  "author": "",
  "license": "MIT",
  "engines": {{"mekong": "^6.0.0"}},
  "permissions": [],
  "mcu_cost": 1,
  "dependencies": [],
  "hooks": [],
  "entry_point": null,
  "isolation": "{isolation}"
}}
"""

_INIT_PY_TEMPLATE = """\
def register(registry):
    \"\"\"Register this plugin's commands into the Mekong registry.\"\"\"
    # TODO: Implement plugin command registration
    pass
"""

_README_TEMPLATE = """\
# {name}

{description}

## Installation

```bash
mekong plugin install .
```

## Development

Edit `src/__init__.py` to add commands, then reinstall after changes.
"""


def _plugin_id_from_name(name: str) -> str:
    """Derive a reverse-domain plugin id from a short name."""
    if "." in name and not name.startswith("."):
        parts = name.split(".")
        if len(parts) >= 2:
            return name
    return f"com.example.{name}"


def _human_name_from_id(plugin_id: str) -> str:
    """Convert ``com.example.my-plugin`` → ``My Plugin``."""
    slug = plugin_id.rsplit(".", 1)[-1]
    return slug.replace("-", " ").replace("_", " ").title()


def _default_isolation(plugin_type: str) -> str:
    return _ISOLATION_MAP.get(plugin_type, "none")


def _scaffold(
    plugin_id: str,
    target_root: Path,
    *,
    plugin_type: str = "agent",
    dry_run: bool = False,
) -> Path | str:
    """Create plugin directory scaffold."""
    import src.cli.commands.plugin_install as _mod

    isolation = _mod._default_isolation(plugin_type)
    name = _mod._human_name_from_id(plugin_id)
    plugin_dir = target_root / plugin_id

    if plugin_dir.exists():
        _mod.console.print(
            f"[bold red]Plugin directory already exists: {plugin_dir}[/bold red]"
        )
        raise typer.Exit(code=1)

    manifest_json = _DEFAULT_MANIFEST_TEMPLATE.format(
        plugin_id=plugin_id,
        name=name,
        isolation=isolation,
    )
    readme = _README_TEMPLATE.format(name=name, description="Mekong CLI plugin.")

    if dry_run:
        preview = (
            f"[bold cyan]Directory:[/bold cyan] {plugin_dir}\n\n"
            f"[bold].plugin.json[/bold]\n{manifest_json}\n"
            f"[bold]src/__init__.py[/bold]\n{_INIT_PY_TEMPLATE}\n"
            f"[bold]README.md[/bold]\n{readme}"
        )
        _mod.console.print(
            Panel(
                preview,
                title=f"[bold]Preview: {plugin_id}[/bold]",
                border_style="yellow",
            )
        )
        return plugin_dir

    plugin_dir.mkdir(parents=True, exist_ok=False)
    src_dir = plugin_dir / "src"
    src_dir.mkdir()

    (plugin_dir / ".plugin.json").write_text(manifest_json, encoding="utf-8")
    (src_dir / "__init__.py").write_text(_INIT_PY_TEMPLATE, encoding="utf-8")
    (plugin_dir / "README.md").write_text(readme, encoding="utf-8")

    return plugin_dir


def _render_manfiest_info(manifest: PluginManifestSchema) -> None:
    """Print a summary table for a created/scaffolded manifest."""
    import src.cli.commands.plugin_install as _mod

    rows = [
        ("ID", manifest.id),
        ("Name", manifest.name),
        ("Version", manifest.version),
        ("Isolation", manifest.isolation),
        ("MCU cost", str(manifest.mcu_cost)),
        ("Engines", ", ".join(f"{k}={v}" for k, v in manifest.engines.items())),
    ]
    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_column("Key", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="dim")
    for k, v in rows:
        table.add_row(k, v)
    _mod.console.print(table)
