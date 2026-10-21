# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Python and JS/TS file discovery and linter runners for Lint command."""

import subprocess
import sys

from rich.panel import Panel


def _facade():
    return sys.modules["src.commands.lint"]


def get_python_files(include_extra: bool):
    """Get list of Python files to lint"""
    f = _facade()
    files = list(f.Path(".").glob("**/*.py"))
    if include_extra:
        files.extend(f.Path(".").glob("**/*.pyi"))
        files.extend([f.Path(p) for p in [".pylintrc", "setup.py", "pyproject.toml", "requirements.txt"] if f.Path(p).exists()])

    return [
        str(p) for p in files
        if not any(part.startswith(".") or part in ("__pycache__", "venv", ".venv", "node_modules", "dist", "build") for part in p.parts)
    ]


def get_js_files(include_extra: bool):
    """Get list of JavaScript/TypeScript files to lint"""
    f = _facade()
    files = [p for ext in ("**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx") for p in f.Path(".").glob(ext)]
    if include_extra:
        files.extend([f.Path(p) for p in ["package.json", "package-lock.json", "tsconfig.json", ".eslintrc", ".babelrc"] if f.Path(p).exists()])

    return [str(p) for p in files if not any(part in ("node_modules", "dist", "build", ".next") for part in p.parts)]


def run_formatter(fix: bool = True):
    """Run code formatters"""
    f = _facade()
    f.console.print("[blue]🎨 Formatting code...[/blue]")

    if f.Path(".").glob("**/*.py"):
        try:
            cmd = [f.sys.executable, "-m", "black"] + ([] if fix else ["--diff"]) + f.get_python_files(False)
            result = f.subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                f.console.print("[green]✅ Python code formatted[/green]")
            elif fix:
                f.console.print("[yellow]⚠️  Black made changes[/yellow]")
            else:
                f.console.print("[yellow]⚠️  Black would make changes[/yellow]")
                if result.stdout:
                    f.console.print(Panel(result.stdout, title="Black Diff"))
        except FileNotFoundError:
            f.console.print("[dim]Black not found. Install with: pip install black[/dim]")
        except subprocess.SubprocessError as e:
            f.console.print(f"[red]❌ Black error: {e}[/red]")

    if any(f.Path(".").glob("**/*.{js,jsx,ts,tsx}")):
        try:
            cmd = ["prettier", "--write" if fix else "--check"] + f.get_js_files(False)
            result = f.subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                f.console.print("[green]✅ JavaScript/TypeScript code formatted[/green]")
            elif fix:
                f.console.print("[yellow]⚠️  Prettier made changes[/yellow]")
            else:
                f.console.print("[yellow]⚠️  Prettier would make changes[/yellow]")
                if result.stdout:
                    f.console.print(Panel(result.stdout, title="Prettier Output"))
        except FileNotFoundError:
            f.console.print("[dim]Prettier not found. Install with: npm install -g prettier[/dim]")
        except subprocess.SubprocessError as e:
            f.console.print(f"[red]❌ Prettier error: {e}[/red]")


def run_python_linter(fix: bool, verbose: bool):
    """Run Python linters"""
    f = _facade()
    issues_found = False

    try:
        result = f.subprocess.run(["flake8"] + f.get_python_files(False), check=False, capture_output=True, text=True)
        if result.returncode != 0:
            issues_found = True
            f.console.print("[yellow]⚠️  Flake8 found issues[/yellow]")
            if verbose or result.stdout:
                f.console.print(Panel(result.stdout, title="Flake8 Output"))
    except FileNotFoundError:
        f.console.print("[dim]Flake8 not found. Install with: pip install flake8[/dim]")
    except subprocess.SubprocessError as e:
        f.console.print(f"[red]❌ Flake8 error: {e}[/red]")
        issues_found = True

    try:
        cmd = ["ruff", "check"] + (["--fix"] if fix else []) + f.get_python_files(False)
        result = f.subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            issues_found = True
            f.console.print(f"[yellow]⚠️  Ruff found issues ({'fixed' if fix else 'to fix'})[/yellow]")
            if verbose or (not fix and result.stdout):
                f.console.print(Panel(result.stdout, title="Ruff Output"))
    except FileNotFoundError:
        f.console.print("[dim]Ruff not found. Install with: pip install ruff[/dim]")
    except subprocess.SubprocessError as e:
        f.console.print(f"[red]❌ Ruff error: {e}[/red]")
        issues_found = True

    return issues_found


def run_js_linter(fix: bool, verbose: bool):
    """Run JavaScript linters"""
    f = _facade()
    issues_found = False

    js_files = f.get_js_files(False)
    if not js_files:
        return False

    try:
        cmd = ["eslint"]
        if fix:
            cmd.append("--fix")
        cmd.extend(js_files)

        result = f.subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            issues_found = True
            f.console.print(f"[yellow]⚠️  ESLint found issues ({'fixed' if fix else 'to fix'})[/yellow]")
            if verbose or (not fix and result.stdout):
                f.console.print(Panel(result.stdout, title="ESLint Output"))
    except FileNotFoundError:
        f.console.print("[dim]ESLint not found. Install with: npm install -g eslint[/dim]")
    except subprocess.SubprocessError as e:
        f.console.print(f"[red]❌ ESLint error: {e}[/red]")
        issues_found = True

    try:
        cmd = ["jshint"] + js_files
        result = f.subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            issues_found = True
            f.console.print("[yellow]⚠️  JSHint found issues[/yellow]")
            if verbose or result.stdout:
                f.console.print(Panel(result.stdout, title="JSHint Output"))
    except FileNotFoundError:
        f.console.print("[dim]JSHint not found. Install with: npm install -g jshint[/dim]")
    except subprocess.SubprocessError as e:
        f.console.print(f"[red]❌ JSHint error: {e}[/red]")
        issues_found = True

    return issues_found
