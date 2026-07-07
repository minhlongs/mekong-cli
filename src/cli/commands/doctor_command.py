"""Diagnostic CLI command that verifies Mekong project health.

Run ``mekong doctor`` to perform a series of environment checks:
1. Project configuration file exists and parses as JSON.
2. ``ruff check src/`` passes with no lint errors.
3. ``pytest --co`` (collection only) succeeds within the timeout.
4. License tier configuration is present.
5. Database layer is detected (Cloudflare D1 if available, else SQLite fallback).

Each check is reported in a Rich panel; the command exits 0 only when every
check passes, otherwise exits 1.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple, Sequence

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()
app = typer.Typer(help="Run a diagnostic check on the Mekong project.")


class CheckResult(NamedTuple):
    """Single diagnostic check result."""

    label: str
    passed: bool
    detail: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _append_result(results: list[CheckResult], label: str, passed: bool, detail: str) -> None:
    results.append(CheckResult(label=label, passed=passed, detail=detail))


def _find_config_file(root: Path) -> Path | None:
    """Return the first parseable JSON config found in common locations."""
    candidates = [
        root / ".mekong" / "company.json",
        root / "mekong" / "config.json",
        root / ".mekong" / "config.json",
        root / "config.json",
    ]
    for path in candidates:
        if path.is_file():
            try:
                with path.open("r", encoding="utf-8") as handle:
                    json.load(handle)
                return path
            except (json.JSONDecodeError, OSError):
                continue
    # fallback: any JSON file matching *config*.json
    fallback = next(
        root.glob(".mekong/*config*.json"),
        next(root.glob("mekong/*config*.json"), None),
    )
    if fallback:
        try:
            with fallback.open("r", encoding="utf-8") as handle:
                json.load(handle)
            return fallback
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _check_config(results: list[CheckResult], root: Path) -> None:
    path = _find_config_file(root)
    if path:
        _append_result(
            results,
            "Config file parseable",
            True,
            f"{path.relative_to(root)}",
        )
    else:
        _append_result(
            results,
            "Config file parseable",
            False,
            "No parseable JSON config found in .mekong/mekong/config.json",
        )


def _check_ruff(results: list[CheckResult], root: Path) -> None:
    ruff = shutil.which("ruff")
    if not ruff:
        _append_result(
            results,
            "Ruff linter",
            False,
            "ruff not found on PATH; is it installed in the active environment?",
        )
        return
    src_dir = root / "src"
    try:
        proc = subprocess.run(
            [ruff, "check", str(src_dir)],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:  # pragma: no cover - defensive
        _append_result(results, "Ruff linter", False, f"subprocess error: {exc}")
        return
    if proc.returncode == 0:
        _append_result(results, "Ruff linter", True, "ruff check src/ passed (0 errors)")
    else:
        output = (proc.stdout or proc.stderr or "").strip()
        headline = output.splitlines()[0] if output else f"exit {proc.returncode}"
        _append_result(results, "Ruff linter", False, headline)


def _check_pytest_collection(results: list[CheckResult], root: Path) -> None:
    pytest = shutil.which("pytest")
    if not pytest:
        _append_result(
            results,
            "Pytest collection",
            False,
            "pytest not found on PATH; is the dev group installed?",
        )
        return
    try:
        proc = subprocess.run(
            [pytest, "--co"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        _append_result(
            results,
            "Pytest collection",
            False,
            "pytest --co timed out after 10s",
        )
        return
    except OSError as exc:  # pragma: no cover - defensive
        _append_result(results, "Pytest collection", False, f"subprocess error: {exc}")
        return
    if proc.returncode == 0:
        collected = len(
            [
                line
                for line in (proc.stdout or "").splitlines()
                if line.startswith("tests/") or line.startswith("test_")
            ]
        )
        _append_result(
            results,
            "Pytest collection",
            True,
            f"collected {collected} candidate(s)",
        )
    else:
        output = (proc.stdout or proc.stderr or "").strip()
        headline = output.splitlines()[0] if output else f"exit {proc.returncode}"
        _append_result(results, "Pytest collection", False, headline)


def _check_license_tier(results: list[CheckResult], root: Path) -> None:
    tier_indicators = [
        root / "mekong" / "tiers.yaml",
        root / "mekong" / "tiers.json",
        root / "mekong" / "tier-config.yaml",
        root / ".mekong" / "tier-config.json",
    ]
    found = next((p for p in tier_indicators if p.is_file()), None)
    if found:
        _append_result(
            results,
            "License tier config",
            True,
            found.relative_to(root).as_posix(),
        )
        return
    # Heuristic: look for tier keywords anywhere in mekong/
    mekong_root = root / "mekong"
    hits: list[Path] = []
    if mekong_root.is_dir():
        hits = [
            p
            for p in mekong_root.rglob("*.{yaml,yml,json,toml}".split(","))
            if "tier" in p.name.lower()
            or "license" in p.name.lower()
            or "license_tier" in p.name.lower()
        ][:10]
    if hits:
        _append_result(
            results,
            "License tier config",
            True,
            ", ".join(p.relative_to(root).as_posix() for p in hits[:3]),
        )
    else:
        _append_result(
            results,
            "License tier config",
            False,
            "No tier / license config found under mekong/ or .mekong/",
        )


def _check_db_connection(results: list[CheckResult], root: Path) -> None:
    d1_available = False
    sqlite_available = False
    d1_detail = ""
    sqlite_detail = ""

    wrangler = root / "wrangler.toml"
    if wrangler.is_file():
        try:
            content = wrangler.read_text(encoding="utf-8")
        except OSError:
            content = ""
        if "[[d1_databases]]" in content:
            d1_available = True
            d1_detail = "wrangler.toml declares [[d1_databases]]"

    db_files: list[Path] = []
    db_locations = [root / ".mekong", root / "mekong"]
    for base in db_locations:
        if base.is_dir():
            db_files.extend(
                list(base.rglob("*.sqlite3")) + list(base.rglob("*.db")) + list(base.rglob("*.sqlite"))
            )
    if db_files:
        sqlite_available = True
        sqlite_detail = f"{db_files[0].relative_to(root).as_posix()} (+{len(db_files)-1} more)"

    if d1_available:
        _append_result(results, "Database (D1 / SQLite)", True, f"Cloudflare D1 configured ({d1_detail})")
    elif sqlite_available:
        _append_result(results, "Database (D1 / SQLite)", True, f"SQLite detected ({sqlite_detail})")
    else:
        _append_result(
            results,
            "Database (D1 / SQLite)",
            False,
            "No Cloudflare D1 binding found and no local SQLite database detected",
        )


CHECKS: Sequence[tuple[str, object]] = (
    ("Config file parseable", _check_config),
    ("Ruff linter", _check_ruff),
    ("Pytest collection", _check_pytest_collection),
    ("License tier config", _check_license_tier),
    ("Database (D1 / SQLite)", _check_db_connection),
)


@app.command()
def run(ctx: typer.Context) -> None:
    """Execute all diagnostic checks and print a summary panel."""
    root = _repo_root()
    results: list[CheckResult] = []

    for label, checker in CHECKS:
        checker(results, root)

    overall = all(result.passed for result in results)

    body_lines: list[str] = []
    body_lines.append("")  # top breathing room
    for result in results:
        status_icon = "[green]✓[/green]" if result.passed else "[red]✗[/red]"
        label_text = Text.assemble(status_icon, " ", result.label)
        body_lines.append(label_text.plain)
        body_lines.append(f"   [dim]{result.detail}[/dim]")

    body_lines.append("")
    verdict = (
        "[bold green]ALL CHECKS PASSED[/bold green]"
        if overall
        else "[bold red]ONE OR MORE CHECKS FAILED[/bold red]"
    )
    body_lines.append(verdict)

    body = "\n".join(body_lines)
    title = Text("Mekong Doctor", style="bold cyan")
    panel = Panel(
        body,
        title=title,
        box=ROUNDED,
        expand=False,
        padding=(1, 2),
    )
    console.print(panel)
    raise typer.Exit(code=0 if overall else 1)


def register(cli: typer.Typer) -> None:
    """Register the top-level ``mekong doctor`` command."""
    cli.add_typer(app, name="doctor", help="Run project diagnostics.")


__all__ = ["register"]
