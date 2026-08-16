# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Diagnostic CLI command that verifies Mekong project health.

Run ``mekong doctor`` to perform environment checks:
- ruff lint on ``src/`` (exit 0 if 0 errors)
- config validation (JSON config files parseable)
- database connectivity (D1/SQLite detection)

Bilingual Vietnamese + English output.

Examples:
    mekong doctor                  # all checks
    mekong doctor --check ruff     # lint only
    mekong doctor --check config   # config only
    mekong doctor --check db       # DB connectivity only
    mekong doctor -v               # verbose detail per check
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()
app = typer.Typer(
    help="Kiểm tra sức khỏe dự án / Run project health checks.",
    rich_markup_mode="rich",
)

_CHECK_CHOICES = ("ruff", "config", "db", "all")

_VN = {
    "title": "🐛 Mekong Doctor",
    "passed": "✓ Đạt / Passed",
    "failed": "✗ Lỗi / Failed",
    "summary_pass": "TẤT CẢ KIỂM TRA ĐỀU ĐẠT / ALL CHECKS PASSED",
    "summary_fail": "MỘT SỐ KIỂM TRA THẤT BẠI / SOME CHECKS FAILED",
    "check_ruff": "Kiểm tra lint / Lint check",
    "check_config": "Kiểm tra cấu hình / Config check",
    "check_db": "Kiểm tra kết nối DB / DB check",
    "ruff_not_found": "ruff không có sẵn trên PATH",
    "ruff_pass": "ruff check src/ thành công (0 lỗi / errors)",
    "ruff_fail": "Lỗi lint:",
    "config_not_found": "Không tìm thấy file cấu hình hợp lệ",
    "config_found": "Tìm thấy cấu hình:",
    "config_parse_fail": "Không phân tích được:",
    "db_not_found": "Không phát hiện D1 hoặc SQLite",
    "db_d1": "Cloudflare D1 được cấu hình",
    "db_sqlite": "SQLite được phát hiện",
    "error_subprocess": "Lỗi subprocess:",
}


class CheckResult(NamedTuple):
    """Single diagnostic check result."""

    key: str
    passed: bool
    detail: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _bilingual(key: str) -> str:
    return _VN.get(key, key)


# ─── Individual checks ──────────────────────────────────────────────────────


def _check_ruff(verbose: bool) -> CheckResult:
    ruff = shutil.which("ruff")
    if not ruff:
        return CheckResult("ruff", False, _bilingual("ruff_not_found"))

    try:
        proc = subprocess.run(
            [ruff, "check", "src/"],
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return CheckResult("ruff", False, f"{_bilingual('error_subprocess')} {exc}")

    if proc.returncode == 0:
        return CheckResult("ruff", True, _bilingual("ruff_pass"))
    output = (proc.stdout or proc.stderr or "").strip()
    headline = output.splitlines()[0] if output else f"exit {proc.returncode}"
    detail = f"{_bilingual('ruff_fail')} {headline}"
    if verbose:
        detail += f"\n{output[:500]}"
    return CheckResult("ruff", False, detail)


def _find_config_file(root: Path) -> Path | None:
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
    return None


def _check_config(verbose: bool) -> CheckResult:
    root = _repo_root()
    path = _find_config_file(root)
    if path:
        rel = path.relative_to(root).as_posix()
        return CheckResult("config", True, f"{_bilingual('config_found')} {rel}")
    return CheckResult("config", False, _bilingual("config_not_found"))


def _check_db(verbose: bool) -> CheckResult:
    root = _repo_root()
    wrangler = root / "wrangler.toml"
    d1_available = False
    sqlite_files: list[Path] = []

    if wrangler.is_file():
        try:
            content = wrangler.read_text(encoding="utf-8")
        except OSError:
            content = ""
        d1_available = "[[d1_databases]]" in content

    for base in (root / ".mekong", root / "mekong"):
        if base.is_dir():
            sqlite_files.extend(
                list(base.rglob("*.sqlite3"))
                + list(base.rglob("*.db"))
                + list(base.rglob("*.sqlite"))
            )

    if d1_available:
        return CheckResult("db", True, f"{_bilingual('db_d1')} (wrangler.toml)")
    if sqlite_files:
        rel = sqlite_files[0].relative_to(root).as_posix()
        n = len(sqlite_files)
        detail = f"{_bilingual('db_sqlite')}: {rel}"
        if n > 1:
            detail += f" (+{n - 1} more)"
        return CheckResult("db", True, detail)
    return CheckResult("db", False, _bilingual("db_not_found"))


# ─── Command ────────────────────────────────────────────────────────────────


@app.command()
def doctor(
    check: str = typer.Option(
        None,
        "--check",
        "-c",
        help="Kiểm tra cụ thể / Specific check: ruff|config|db|all",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Chi tiết / Verbose output",
    ),
) -> None:
    """Kiểm tra sức khỏe dự án / Run project health checks."""
    normalized = (check or "all").strip().lower()
    if normalized not in _CHECK_CHOICES:
        console.print(f"[red]Invalid --check value. Choose from: {', '.join(_CHECK_CHOICES)}[/red]")
        raise typer.Exit(2)

    check_map = {
        "ruff": lambda v: [_check_ruff(v)],
        "config": lambda v: [_check_config(v)],
        "db": lambda v: [_check_db(v)],
        "all": lambda v: [_check_ruff(v), _check_config(v), _check_db(v)],
    }

    results: list[CheckResult] = check_map[normalized](verbose)
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    lines: list[str] = [""]
    for r in results:
        icon = "[green]✓[/green]" if r.passed else "[red]✗[/red]"
        label_vi = _bilingual(f"check_{r.key}")
        lines.append(f"  {icon} {label_vi}")
        detail_indent = "    [dim]" + r.detail.replace("\n", "\n    [/dim][dim]") + "[/dim]"
        lines.append(detail_indent)

    if failed == 0:
        lines.append(f"\n[bold green]{_bilingual('summary_pass')}[/bold green]")
    else:
        lines.append(
            f"\n[bold red]{_bilingual('summary_fail')}[/bold red]  "
            f"[yellow]{failed}/{len(results)} failed[/yellow]"
        )

    body = "\n".join(lines)
    title = Text(_bilingual("title"), style="bold cyan")
    panel = Panel(body, title=title, box=ROUNDED, expand=False, padding=(1, 2))
    console.print(panel)

    raise typer.Exit(code=0 if failed == 0 else 1)


# Register helper (kept for backward compat with app_setup.py)
_check_impl_fns = {
    "ruff": _check_ruff,
    "config": _check_config,
    "db": _check_db,
}

# Backward-compat stubs (older callers expected these helpers to exist)


# Backward-compat stubs
def _info() -> None:
    console.print("[yellow]doctor info[/yellow]")


def _deps() -> None:
    console.print("[yellow]doctor deps[/yellow]")


def register(app: typer.Typer) -> None:
    """Register doctor command on the root app."""
    doctor_app = typer.Typer(
        name="doctor",
        help="Kiểm tra sức khỏe dự án / Run project health checks.",
        rich_markup_mode="rich",
    )

    doctor_app.command("check")(doctor)
      
    app.add_typer(doctor_app, name="doctor", help="Doctor: run health checks")

__all__ = ["app", "_check_impl_fns", "register"]
