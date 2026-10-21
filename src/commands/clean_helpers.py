# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helpers and target definitions for Mekong CLI Clean command."""

from __future__ import annotations

from pathlib import Path
from rich.panel import Panel
from rich.table import Table


CLEAN_TARGETS = {
    "cache": [
        ".mekong/cache",
        ".mekong/llm_cache",
        ".mekong/vector_cache",
        "__pycache__",
        "**/__pycache__",
        "*.pyc",
        "**/*.pyc",
    ],
    "build": [
        "build",
        "dist",
        "*.egg-info",
        "**/*.egg-info",
        ".eggs",
    ],
    "temp": [
        ".mekong/tmp",
        ".mekong/temp",
        "*.tmp",
        "**/*.tmp",
        ".pytest_cache",
        ".mypy_cache",
    ],
    "logs": [
        "*.log",
        "**/*.log",
        ".mekong/logs",
    ],
    "all": [],
}


def _mod():
    import src.commands.clean as mod

    return mod


def get_clean_patterns(target: str) -> list:
    """Get clean patterns for a specific target."""
    targets = _mod().CLEAN_TARGETS
    if target == "all":
        all_patterns = []
        for key in ["cache", "build", "temp", "logs"]:
            all_patterns.extend(targets[key])
        return all_patterns
    return targets.get(target, [])


def find_files_to_clean(base_path: Path, patterns: list) -> list:
    """Find files and directories matching patterns."""
    to_clean = []

    for pattern in patterns:
        if "**" in pattern:
            try:
                matches = list(base_path.glob(pattern))
                to_clean.extend(matches)
            except Exception:
                pass
        else:
            matches = list(base_path.glob(pattern))
            to_clean.extend(matches)

    unique = list(set(to_clean))
    unique.sort(key=lambda x: str(x))
    return unique


def human_readable_size(path: Path) -> str:
    """Get human-readable size of a file or directory."""
    try:
        if path.is_file():
            size = path.stat().st_size
        elif path.is_dir():
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        else:
            return "N/A"

        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except Exception:
        return "N/A"


def run_full_clean(dry_run: bool = False) -> None:
    """Execute full clean flow across all targets."""
    m = _mod()
    m.console.print(Panel("🧹 Mekong CLI - Full Clean", border_style="cyan"))

    base_path = m.Path.cwd()
    all_patterns = m.get_clean_patterns("all")

    m.console.print("[bold]Searching for files to clean...[/bold]\n")
    to_clean = m.find_files_to_clean(base_path, all_patterns)

    if not to_clean:
        m.console.print("[green]✓ Nothing to clean![/green]")
        return

    table = Table(
        title=f"{'Would delete' if dry_run else 'Deleting'} ({len(to_clean)} items)"
    )
    table.add_column("Path", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Size", style="dim")

    total_size = 0.0
    for path in to_clean:
        size_str = m.human_readable_size(path)
        try:
            size_num = float(size_str.split()[0])
            size_unit = size_str.split()[1]
            if size_unit == "MB":
                total_size += size_num * 1024 * 1024
            elif size_unit == "KB":
                total_size += size_num * 1024
            elif size_unit == "GB":
                total_size += size_num * 1024 * 1024 * 1024
            else:
                total_size += size_num
        except Exception:
            pass

        file_type = "dir" if path.is_dir() else "file"
        table.add_row(str(path.relative_to(base_path)), file_type, size_str)

    m.console.print(table)

    total_size_str = m.human_readable_size(m.Path(str(total_size)))
    m.console.print(f"\n[bold]Total: {len(to_clean)} items, ~{total_size_str}[/bold]")

    if dry_run:
        m.console.print("\n[yellow]Dry run - nothing was deleted[/yellow]")
        m.console.print("[dim]Run 'mekong clean all' without --dry-run to delete[/dim]")
        return

    if not m.Confirm.ask("\n[yellow]Delete these files?[/yellow]", default=False):
        m.console.print("[dim]Cancelled[/dim]")
        return

    deleted_count = 0
    for path in to_clean:
        try:
            if path.is_dir():
                m.shutil.rmtree(path)
            else:
                path.unlink()
            deleted_count += 1
        except Exception as e:
            m.console.print(f"[red]✗ Failed to delete {path}: {e}[/red]")

    m.console.print(f"\n[green]✓ Deleted {deleted_count}/{len(to_clean)} items[/green]")
