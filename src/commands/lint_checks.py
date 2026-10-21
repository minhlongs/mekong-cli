# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Type checking, security scanning, and reporting helpers for Lint command."""

import subprocess
import sys

from rich.panel import Panel
from rich.table import Table


def _facade():
    return sys.modules["src.commands.lint"]


def run_type_checker():
    """Run type checker"""
    f = _facade()
    f.console.print("[blue]🏷️  Running type checker...[/blue]")

    if f.Path(".").glob("**/*.py"):
        try:
            cmd = [f.sys.executable, "-m", "mypy"]
            py_paths = [".", "src", "lib", "tests"]
            existing_paths = [p for p in py_paths if f.Path(p).exists()]
            cmd.extend(existing_paths)

            result = f.subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                f.console.print("[green]✅ Type checking passed[/green]")
            else:
                f.console.print("[red]❌ Type checking failed[/red]")
                if result.stdout:
                    f.console.print(Panel(result.stdout, title="MyPy Output"))
        except FileNotFoundError:
            f.console.print("[dim]MyPy not found. Install with: pip install mypy[/dim]")
        except subprocess.SubprocessError as e:
            f.console.print(f"[red]❌ MyPy error: {e}[/red]")

    if any(f.Path(".").glob("**/*.ts")):
        try:
            cmd = ["tsc", "--noEmit"]
            result = f.subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                f.console.print("[green]✅ TypeScript type checking passed[/green]")
            else:
                f.console.print("[red]❌ TypeScript type checking failed[/red]")
                if result.stdout or result.stderr:
                    output = result.stdout or result.stderr
                    f.console.print(Panel(output, title="TypeScript Output"))
        except FileNotFoundError:
            f.console.print("[dim]TypeScript compiler not found. Install with: npm install -g typescript[/dim]")
        except subprocess.SubprocessError as e:
            f.console.print(f"[red]❌ TypeScript error: {e}[/red]")


def run_security_scan():
    """Run security vulnerability scans"""
    f = _facade()
    f.console.print("[blue]🔒 Running security scan...[/blue]")

    if f.Path(".").glob("**/*.py"):
        try:
            cmd = ["bandit", "-r", "."]
            result = f.subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                f.console.print("[green]✅ Security scan passed[/green]")
            else:
                f.console.print("[red]⚠️  Security issues found[/red]")
                if result.stdout:
                    f.console.print(Panel(result.stdout, title="Bandit Security Report"))
        except FileNotFoundError:
            f.console.print("[dim]Bandit not found. Install with: pip install bandit[/dim]")
        except subprocess.SubprocessError as e:
            f.console.print(f"[red]❌ Bandit error: {e}[/red]")

    if f.Path("package-lock.json").exists() or f.Path("yarn.lock").exists():
        try:
            cmd = ["npm", "audit"]
            result = f.subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                f.console.print("[green]✅ Dependency audit passed[/green]")
            else:
                f.console.print("[yellow]⚠️  Dependency vulnerabilities found[/yellow]")
                if result.stdout:
                    f.console.print(Panel(result.stdout, title="NPM Audit Report"))
        except FileNotFoundError:
            f.console.print("[dim]npm not found or package-lock.json/yarn.lock missing[/dim]")
        except subprocess.SubprocessError as e:
            f.console.print(f"[red]❌ NPM audit error: {e}[/red]")


def report():
    """Generate a linting report"""
    f = _facade()
    f.console.print(Panel("[bold]Linting Report[/bold]", title="Code Quality Status"))

    table = Table(title="Analysis Results")
    table.add_column("Tool", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Issues Found", style="dim")

    python_formatted = True
    if list(f.Path(".").glob("**/*.py")):
        try:
            result = f.subprocess.run(
                [f.sys.executable, "-m", "black", "--check"] + f.get_python_files(False),
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            python_formatted = result.returncode == 0
            status = "✅ OK" if python_formatted else "❌ Needs fix"
            issues = "0" if python_formatted else "See black output"
            table.add_row("Python Format", status, issues)
        except FileNotFoundError:
            table.add_row("Python Format", "❌ Not available", "Install black")
        except subprocess.TimeoutExpired:
            table.add_row("Python Format", "❌ Timeout", "Check took > 30s")
        except subprocess.SubprocessError as e:
            table.add_row("Python Format", f"❌ Error: {e}", "")

    try:
        result = f.subprocess.run(
            ["ruff", "check"] + f.get_python_files(False),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        python_linted = result.returncode == 0
        status = "✅ OK" if python_linted else "❌ Issues found"
        issues = "0" if python_linted else f"{result.stdout.count('error') if result.stdout else '?'}"
        table.add_row("Python Lint", status, issues)
    except FileNotFoundError:
        table.add_row("Python Lint", "❌ Not available", "Install ruff")
    except subprocess.TimeoutExpired:
        table.add_row("Python Lint", "❌ Timeout", "Check took > 30s")
    except subprocess.SubprocessError as e:
        table.add_row("Python Lint", f"❌ Error: {e}", "")

    try:
        result = f.subprocess.run(
            [f.sys.executable, "-m", "mypy", "."],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        types_ok = result.returncode == 0
        status = "✅ OK" if types_ok else "❌ Type errors"
        issues = "0" if types_ok else f"{result.stdout.count('error') if result.stdout else '?'}"
        table.add_row("Type Check", status, issues)
    except FileNotFoundError:
        table.add_row("Type Check", "❌ Not available", "Install mypy")
    except subprocess.TimeoutExpired:
        table.add_row("Type Check", "❌ Timeout", "Check took > 60s")
    except subprocess.SubprocessError as e:
        table.add_row("Type Check", f"❌ Error: {e}", "")

    f.console.print(table)
