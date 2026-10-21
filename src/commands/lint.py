# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Lint command - Static analysis and code quality checks"""

from pathlib import Path
import subprocess
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from src.commands.lint_checks import (
    report,
    run_security_scan,
    run_type_checker,
)
from src.commands.lint_runners import (
    get_js_files,
    get_python_files,
    run_formatter,
    run_js_linter,
    run_python_linter,
)

app = typer.Typer()
console = Console()


@app.command()
def run(
    fix: bool = typer.Option(False, "--fix", help="Automatically fix issues where possible"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    format_only: bool = typer.Option(False, "--format", help="Format code only"),
    check_type: bool = typer.Option(False, "--type-check", help="Run type checker only"),
    security_check: bool = typer.Option(False, "--security", help="Run security checks only"),
    python: bool = typer.Option(True, "--python/--no-python", help="Check Python files"),
    js: bool = typer.Option(True, "--js/--no-js", help="Check JavaScript/TypeScript files"),
    all_files: bool = typer.Option(False, "--all", help="Check all file types including docs/configs"),
):
    """Run linting tools on project files"""
    if security_check:
        run_security_scan()
        return

    if check_type:
        run_type_checker()
        return

    if format_only:
        run_formatter(fix)
        return

    targets = []
    if python:
        targets.extend(get_python_files(all_files))
    if js:
        targets.extend(get_js_files(all_files))

    if not targets:
        console.print("[yellow]⚠️  No files found to lint[/yellow]")
        return

    console.print(f"[bold]🔍 Linting {len(targets)} files...[/bold]")

    if fix:
        run_formatter(fix=True)

    issues_found = False

    if python:
        if run_python_linter(fix, verbose):
            issues_found = True

    if js:
        if run_js_linter(fix, verbose):
            issues_found = True

    if not issues_found:
        console.print("[green]✅ No issues found![/green]")
    else:
        console.print("[red]❌ Some issues found and fixed (where possible)[/red]")


@app.command()
def autofix():
    """Apply automatic fixes to code"""
    console.print("[bold]🔧 Running automatic fixes...[/bold]")
    run_formatter(fix=True)
    run_python_linter(fix=True, verbose=False)


@app.command()
def check_formatting():
    """Check if code is properly formatted"""
    console.print("[bold]🔍 Checking code formatting...[/bold]")

    if Path(".").glob("**/*.py"):
        try:
            cmd = [sys.executable, "-m", "black", "--check"]
            cmd.extend(get_python_files(False))

            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                console.print("[green]✅ Python code is properly formatted[/green]")
            else:
                console.print("[red]❌ Python code needs formatting[/red]")
        except FileNotFoundError:
            console.print("[dim]Black not found. Install with: pip install black[/dim]")

    if any(Path(".").glob("**/*.{js,jsx,ts,tsx}")):
        try:
            cmd = ["prettier", "--check"]
            cmd.extend(get_js_files(False))

            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                console.print("[green]✅ JavaScript/TypeScript code is properly formatted[/green]")
            else:
                console.print("[red]❌ JavaScript/TypeScript code needs formatting[/red]")
        except FileNotFoundError:
            console.print("[dim]Prettier not found. Install with: npm install -g prettier[/dim]")


app.command()(report)

__all__ = [
    "Panel", "Table", "app", "autofix", "check_formatting", "console",
    "get_js_files", "get_python_files", "report", "run", "run_formatter",
    "run_js_linter", "run_python_linter", "run_security_scan", "run_type_checker",
    "subprocess", "sys",
]
