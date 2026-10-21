# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

# /// script
# dependencies = [
#   "typer>=0.15",
#   "rich>=13",
# ]
# ///
"""Mekong Doctor — smoke-test command.

Subcommands
-----------
check  Run smoke probes (the ``mekong doctor`` default entry-point).
info   Print basic system information.
deps   List installed Python packages.
"""
from __future__ import annotations

import importlib.util  # noqa: F401 — re-exported for doctor_probes._mod()
import os
import subprocess  # noqa: S603 — only used in deps() for pip listing
import sys
from typing import List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.commands.doctor_probes import (
    Check,
    _probe_core_imports,
    _probe_llm_provider_config,
    _probe_plugin_registry,
)

console = Console()
app = typer.Typer(name="doctor", help="Health check probes (toxicity, dependencies, version).")


@app.command("check")
def check() -> None:
    """Run all smoke-test probes; prints plain ``✅ OK`` / ``❌ FAIL`` lines.

    No HTTP, no subprocess, no plugin instantiation.

    **Exit codes**: 0 — all probes pass; 1 — at least one probe failed.
    Failing details are always written to ``stderr`` in addition to stdout so
    CI log lines that capture ``FAIL`` are easy to grep.
    """
    probes: List[Check] = [
        _probe_core_imports(),
        _probe_plugin_registry(),
        _probe_llm_provider_config(),
    ]

    stdout_lines: List[str] = []
    stderr_lines: List[str] = []

    for p in probes:
        prefix = "✅ OK" if p.passed else "❌ FAIL"
        stdout_lines.append(f"{prefix}: {p.label} — {p.detail}")
        if not p.passed:
            stderr_lines.append(f"{p.label}: {p.detail}")

    if stdout_lines:
        print("\n".join(stdout_lines))
    if stderr_lines:
        print("\n".join(stderr_lines), file=sys.stderr)

    sys.exit(0 if all(p.passed for p in probes) else 1)


@app.command()
def info() -> None:
    """Display basic Python environment information."""
    console.print(
        Panel(
            Text("💻 System Information", style="bold blue"),
            border_style="blue",
        )
    )
    table = Table(title="System Info")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Platform", __import__("platform").platform())
    table.add_row(
        "Python Version",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )
    table.add_row("Python Executable", sys.executable)
    table.add_row("Working Directory", os.getcwd())
    table.add_row("System Encoding", sys.getdefaultencoding())
    console.print(table)


@app.command()
def deps() -> None:
    """List installed Python packages (invokes ``pip list`` via subprocess)."""
    console.print(
        Panel(
            Text("📦 Installed Dependencies", style="bold green"),
            border_style="green",
        )
    )
    try:
        import json as _json

        result = subprocess.run(  # noqa: S603 — no shell injection risk here
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        packages = _json.loads(result.stdout)
        packages.sort(key=lambda x: x["name"].lower())
        table = Table(title=f"Python Packages ({len(packages)} installed)")
        table.add_column("Package", style="cyan")
        table.add_column("Version", style="green")
        for pkg in packages:
            table.add_row(pkg["name"], pkg["version"])
        console.print(table)
    except Exception as exc:  # pragma: no cover — defensive fallback path
        console.print(f"[red]Error listing packages: {exc}[/red]")


def register(container: typer.Typer) -> None:  # pragma: no cover — thin shim
    """Register the ``doctor`` sub-app onto a parent Typer container."""
    container.add_typer(app, name="doctor")


def main() -> None:  # pragma: no cover — entry-point shim
    """Entry point for the ``mekong doctor`` console script."""
    app()


__all__ = [
    "Check",
    "_probe_core_imports",
    "_probe_llm_provider_config",
    "_probe_plugin_registry",
    "app",
    "check",
    "console",
    "deps",
    "info",
    "main",
    "register",
]


if __name__ == "__main__":
    app()
