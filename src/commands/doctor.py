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

import importlib.util
import os
import subprocess  # noqa: S603 — only used in deps() for pip listing
import sys
from typing import List, NamedTuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()
app = typer.Typer(name="doctor", help="Health check probes (toxicity, dependencies, version).")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

class Check(NamedTuple):
    label: str
    passed: bool
    detail: str


# ---------------------------------------------------------------------------
# Probes for ``mekong doctor check``
# ---------------------------------------------------------------------------


def _probe_core_imports() -> Check:
    """Core modules required to boot the CLI are importable."""
    required = [
        "typer",
        "rich",
        "pydantic",
        "dotenv",
        "src",
        "src.core",
    ]
    missing = [m for m in required if importlib.util.find_spec(m) is None]
    if missing:
        return Check("Core imports", False, f"missing: {', '.join(missing)}")
    return Check("Core imports", True, "all required modules resolve")


def _probe_plugin_registry() -> Check:
    """Plugin registry package is importable (no plugin instantiation)."""
    try:
        runtime_spec = importlib.util.find_spec("src.core.plugin_runtime")
        if runtime_spec is None:
            return Check("Plugin registry", False, "src.core.plugin_runtime not found")
        # We intentionally do NOT call ``exec_module`` here: that would load
        # ``PluginRuntime`` and the full SDK dependency chain (and could have
        # side effects we explicitly want to avoid in a smoke test). Finding
        # the spec is sufficient to prove the package is installed and on the
        # import path.
        schema_spec = importlib.util.find_spec("src.core.plugin_schema")
        schema_note = (
            "schema module also found"
            if schema_spec is not None
            else "schema module not installed (non-fatal)"
        )
        return Check(
            "Plugin registry",
            True,
            f"spec found ({runtime_spec.origin}); {schema_note}",
        )
    except Exception as exc:
        return Check("Plugin registry", False, str(exc))


def _probe_llm_provider_config() -> Check:
    """At least one LLM provider env var is configured.

    Priority (mirrors the LLM config section in ``CLAUDE.md``):
    LLM_BASE_URL (universal) → OPENROUTER_API_KEY → DASHSCOPE_API_KEY →
    ANTHROPIC_API_KEY → GOOGLE_API_KEY → OLLAMA_BASE_URL.
    """
    env_vars = [
        "LLM_BASE_URL",
        "OPENROUTER_API_KEY",
        "DASHSCOPE_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "OLLAMA_BASE_URL",
    ]
    found = [name for name in env_vars if os.environ.get(name)]
    if found:
        return Check("LLM provider config", True, f"{found[0]} is set")
    return Check(
        "LLM provider config",
        False,
        "none of: " + ", ".join(env_vars),
    )


# ---------------------------------------------------------------------------
# CLI subcommands
# ---------------------------------------------------------------------------


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
    container.add_typer(app, name="doctor")  # --help fallback only


def main() -> None:  # pragma: no cover — entry-point shim
    """Entry point for the ``mekong doctor`` console script."""
    app()


if __name__ == "__main__":
    app()
