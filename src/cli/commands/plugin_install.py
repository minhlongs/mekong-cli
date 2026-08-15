"""Plugin management commands — `mekong plugin {init|install|list|uninstall}`.

Regroups all plugin sub-commands under a single Typer app and exposes
``register_plugin_commands(root)`` for wiring in ``app_setup.py``.

Source file for the ``plugin`` Typer sub-app.  DO NOT create another
``app = typer.Typer(name="plugin", ...)`` in any other module — it would
conflict with this one at the same ``root.add_typer`` registration level.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# ---------------------------------------------------------------------------
# Canonical owner of the ``plugin`` Typer sub-app.
# All other .claude files must NOT create another ``app = typer.Typer(name="plugin")``.
# ---------------------------------------------------------------------------
from src.core.plugin_runtime import PluginRuntime
from src.core.plugin_schema import PluginManifestSchema

app = typer.Typer(
    name="plugin",
    help=(
        "Plugin management — "
        "init | install | list | uninstall | publish"
    ),
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

# Default isolation per plugin type for the scaffolder.
_ISOLATION_MAP: dict[str, str] = {
    "agent": "none",
    "provider": "restricted",
    "hook": "sandboxed",
}
console = Console()


# ---- init sub‑command -------------------------------------------------------

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
    """Derive a reverse-domain plugin id from a short name.

    If the name already looks like a reverse-domain (has >=2 dots), use it
    directly. Otherwise, derive ``com.example.<name>``.
    """
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
    """Create plugin directory scaffold.

    Returns path to created dir or rendered content when *dry_run*.
    """
    isolation = _default_isolation(plugin_type)
    name = _human_name_from_id(plugin_id)
    plugin_dir = target_root / plugin_id

    if plugin_dir.exists():
        console.print(
            f"[bold red]Plugin directory already exists: {plugin_dir}[/bold red]"
        )
        raise typer.Exit(code=1)

    manifest_json = _DEFAULT_MANIFEST_TEMPLATE.format(
        plugin_id=plugin_id,
        name=name,
        isolation=isolation,
    )
    readme = _README_TEMPLATE.format(
        name=name, description="Mekong CLI plugin."
    )

    if dry_run:
        preview = (
            f"[bold cyan]Directory:[/bold cyan] {plugin_dir}\n\n"
            f"[bold].plugin.json[/bold]\n{manifest_json}\n"
            f"[bold]src/__init__.py[/bold]\n{_INIT_PY_TEMPLATE}\n"
            f"[bold]README.md[/bold]\n{readme}"
        )
        console.print(
            Panel(preview, title=f"[bold]Preview: {plugin_id}[/bold]", border_style="yellow")
        )
        return plugin_dir

    # Create files
    plugin_dir.mkdir(parents=True, exist_ok=False)
    src_dir = plugin_dir / "src"
    src_dir.mkdir()

    (plugin_dir / ".plugin.json").write_text(manifest_json, encoding="utf-8")
    (src_dir / "__init__.py").write_text(_INIT_PY_TEMPLATE, encoding="utf-8")
    (plugin_dir / "README.md").write_text(readme, encoding="utf-8")

    return plugin_dir


def _render_manfiest_info(manifest: PluginManifestSchema) -> None:
    """Print a summary table for a created/scaffolded manifest."""
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
    console.print(table)


@app.command("init")
def plugin_init(
    name: str = typer.Argument(
        ...,
        help="Plugin short name or reverse-domain id (e.g. 'my-plugin' or 'com.example.my-plugin')",
    ),
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Target parent directory (default: current working directory)",
    ),
    plugin_type: str = typer.Option(
        "agent",
        "--type",
        "-t",
        help="Plugin type: agent | provider | hook (controls default isolation)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview scaffold content without writing files",
    ),
) -> None:
    """Scaffold a new Mekong CLI plugin directory.

    VN: Khoi tao thu muc plugin moi.
    EN: Scaffold a new Mekong CLI plugin directory.
    """
    if plugin_type not in _ISOLATION_MAP:
        console.print(
            f"[bold red]Invalid type: {plugin_type!r}[/bold red]\n"
            f"Loại không hợp lệ. Chọn: {', '.join(_ISOLATION_MAP.keys())}"
        )
        raise typer.Exit(code=1)

    plugin_id = _plugin_id_from_name(name)
    target_root = path or Path.cwd()

    if not target_root.is_dir():
        console.print(f"[bold red]Target directory not found: {target_root}[/bold red]")
        raise typer.Exit(code=1)

    result = _scaffold(
        plugin_id,
        target_root,
        plugin_type=plugin_type,
        dry_run=dry_run,
    )

    if dry_run:
        console.print("[yellow]No files written.[/yellow]")
        return

    plugin_dir = result if isinstance(result, Path) else target_root / plugin_id

    console.print(
        f"[bold green]{plugin_id}[/bold green] — [dim]{plugin_dir}[/dim]"
    )
    console.print("[dim]Scaffolded plugin directory. / Đã khởi tạo plugin.[/dim]")

    # Show manifest summary
    manifest = PluginManifestSchema.from_file(plugin_dir)
    _render_manfiest_info(manifest)


def _get_plugins_dir() -> Path:
    return Path.home() / ".mekong" / "plugins"


def _get_runtime(plugins_dir: Optional[Path] = None) -> PluginRuntime:
    target = plugins_dir or _get_plugins_dir()
    return PluginRuntime(plugin_dirs=[target])


def _detect_source(source: str) -> tuple[str, str]:
    s = source.strip()
    if s.startswith("git+") or (
        "github.com" in s or "gitlab.com" in s or "bitbucket.org" in s
    ):
        return "git", s
    if s.startswith("https://") and s.endswith(".zip"):
        return "zip", s
    if s.startswith("https://"):
        return "git", s
    p = Path(s)
    if p.exists():
        return "local", s
    return "pypi", s


def _clone_git(url: str, dest: Path) -> Path:
    """Clone a git repo, stripping `git+` prefix if present."""
    repo_url = url.removeprefix("git+")
    clone_path = dest / "repo"
    console.print(f"[dim]Cloning {repo_url} ...[/dim]")
    subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(clone_path)],
        check=True,
        capture_output=True,
    )
    return clone_path


def _fetch_zip(url: str, dest: Path) -> Path:
    import hashlib
    import urllib.request  # noqa: S310

    url_hash = hashlib.sha256(url.encode()).hexdigest()[:8]
    extract_path = dest / f"zip-{url_hash}"
    if not extract_path.exists():
        extract_path.mkdir(parents=True, exist_ok=True)
    console.print(f"[dim]Fetching {url} ...[/dim]")
    with urllib.request.urlopen(url) as resp:  # noqa: S310
        data = resp.read()
    zip_path = dest / f"{url_hash}.zip"
    zip_path.write_bytes(data)
    shutil.unpack_archive(zip_path, extract_path)
    return extract_path


def _install_source(source: str, name: str, force: bool) -> dict:
    plugins_dir = _get_plugins_dir()
    runtime = _get_runtime(plugins_dir)
    plugins_dir.mkdir(parents=True, exist_ok=True)

    source_type, resolved = _detect_source(source)

    with tempfile.TemporaryDirectory(prefix="mekong-install-") as tmp:
        tmp_path = Path(tmp)

        if source_type == "git":
            try:
                work_dir = _clone_git(resolved, tmp_path)
            except subprocess.CalledProcessError as exc:
                # Mask credentials in error output
                err_msg = exc.stderr.decode(errors="replace") if exc.stderr else str(exc)
                return {
                    "status": "error",
                    "source_type": "git",
                    "error_message": f"Git clone failed: {err_msg}",
                }
        elif source_type == "zip":
            try:
                work_dir = _fetch_zip(resolved, tmp_path)
            except Exception as exc:  # noqa: BLE001
                return {
                    "status": "error",
                    "source_type": "zip",
                    "error_message": f"ZIP fetch failed: {exc}",
                }
        else:
            work_dir = Path(resolved)

        manifest = work_dir / ".plugin.json"
        if not manifest.is_file():
            return {
                "status": "error",
                "source_type": source_type,
                "error_message": f"No .plugin.json found in {work_dir}",
            }

        temps = list(work_dir.iterdir())
        plugin_src = work_dir
        if len(temps) == 1 and temps[0].is_dir():
            plugin_src = temps[0]

        return runtime.install(
            plugin_src,
            name=name or "",
            force=force,
        )


# ---- CLI commands -----------------------------------------------------------------


@app.command("install")
def plugin_install(
    source: str = typer.Argument(
        ...,
        help="Plugin source: local path, git URL, ZIP URL, or PyPI package name",
    ),
    name: str = typer.Option(
        "",
        "--name",
        "-n",
        help="Install as this name (default: from manifest)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing plugin with same name",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate source without writing files",
    ),
) -> None:
    """Install a Mekong CLI plugin from a local path, git repo, ZIP, or PyPI.

    VN: Cai dat plugin tu duong dan local, git, ZIP, hoac PyPI.
    EN: Install a Mekong CLI plugin from local path, git, ZIP, or PyPI.
    """
    with console.status("[bold cyan]Detecting source type...", spinner="dots"):
        source_type, _ = _detect_source(source)

    console.print(
        f"[bold]Source:[/bold] [{source_type}]{source}[/{source_type}]"
    )

    if dry_run:
        plugins_dir = _get_plugins_dir()
        console.print(
            f"[dim]Plugins root: {plugins_dir}\n"
            f"[yellow]Dry-run—no files written.[/yellow]"
        )
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Installing plugin...", total=None)
        result = _install_source(source, name, force)
        progress.remove_task(task)

    if result.get("status") == "installed":
        install_name = result.get("install_name", "?")
        plugin_id = result.get("plugin_id", "?")
        console.print(
            f"\n[bold green]Installed[/bold green] [bold]{install_name}[/bold]"
        )
        console.print(
            f"[dim]ID: {plugin_id}  |  Source: {source_type}"
        )
    else:
        err = result.get("error_message", "Unknown error")
        console.print(f"\n[bold red]Install failed:[/bold red] {err}")
        raise typer.Exit(code=1)


@app.command("list")
def plugin_list(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show plugin details"),
) -> None:
    """List installed Mekong CLI plugins.

    VN: Liet ke plugin da cai dat.
    EN: List installed Mekong CLI plugins.
    """
    plugins_dir = _get_plugins_dir()
    runtime = _get_runtime(plugins_dir)
    runtime.discover_manifests()
    installed = runtime.loaded_plugins()

    if not installed:
        console.print(f"[yellow]No plugins installed in {plugins_dir}[/yellow]")
        return

    table = Table(
        title=f"Installed plugins ({len(installed)})",
        box=None,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name", style="bold")
    table.add_column("ID", style="dim")
    table.add_column("Version", justify="right")
    table.add_column("Isolation")

    for info in installed:
        manifest = info.manifest
        table.add_row(
            manifest.name or manifest.id.rsplit(".", 1)[-1],
            manifest.id,
            manifest.version,
            manifest.isolation,
        )

    console.print(table)


@app.command("uninstall")
def plugin_uninstall(
    name: str = typer.Argument(
        ...,
        help="Plugin name or id to remove",
    ),
) -> None:
    """Remove an installed plugin.

    VN: Xoa plugin da cai dat.
    EN: Remove an installed plugin.
    """
    plugins_dir = _get_plugins_dir()
    target = plugins_dir / name
    if not target.exists():
        # Try to find by id
        runtime = _get_runtime(plugins_dir)
        runtime.discover_manifests()
        for info in runtime.loaded_plugins():
            if info.manifest.id == name or info.manifest.name == name:
                target = info.manifest_path.parent
                break

    if not target.exists():
        console.print(f"[bold red]Plugin not found: {name}[/bold red]")
        raise typer.Exit(code=1)

    if not typer.confirm(
        f"Remove plugin [bold]{name}[/bold] at {target}?"
    ):
        console.print("[yellow]Cancelled.[/yellow]")
        return

    shutil.rmtree(target)
    console.print(
        f"[bold green]Uninstalled[/bold green] [dim]{target}[/dim]"
    )


def register_plugin_commands(root: typer.Typer) -> None:
    """Add the ``plugin`` sub-app to the root Typer app.

    Idempotent: safe to call multiple times (returns early if already wired).
    """
    if getattr(root, "_mekong_plugin_wired", False):
        return
    root._mekong_plugin_wired = True  # type: ignore[attr-defined]
    root.add_typer(
        app,
        name="plugin",
        help="Plugin management — init | install | list | uninstall | publish",
    )


__all__ = ["app", "register_plugin_commands"]
