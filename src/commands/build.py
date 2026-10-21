# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Build command - Compile, package, and optimize project"""

import shutil
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.commands.build_docker_helpers import run_build_docker, run_build_info

app = typer.Typer()
console = Console()


@app.command()
def run(
    clean: bool = typer.Option(False, "--clean", help="Clean build artifacts first"),
    optimize: bool = typer.Option(False, "--optimize", "-O", help="Optimize build"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    target: str = typer.Option("all", "--target", "-t", help="Build target: all, python, js, docker"),
):
    """Build the project with various options"""
    if clean:
        clean_build()

    console.print(f"[bold]Building for target: {target}[/bold]")

    if target in ["all", "python"]:
        build_python_package(verbose)
    if target in ["all", "js"]:
        build_js_frontend(verbose)
    if target in ["all", "docker"]:
        build_docker_image(verbose)

    console.print("[green]✅ Build completed![/green]")


@app.command()
def clean():
    """Clean build artifacts and cache"""
    clean_build()


def clean_build():
    """Helper function to clean build artifacts"""
    console.print("[yellow]🧹 Cleaning build artifacts...[/yellow]")

    dirs_to_clean = [
        "dist/", "build/", "*.egg-info/", ".pytest_cache/", ".ruff_cache/",
        "__pycache__/", ".mypy_cache/", ".coverage", "htmlcov/", "coverage.xml", "coverage.json",
    ]

    for pattern in dirs_to_clean:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                console.print(f"  Removed directory: {path}")
            elif path.is_file():
                path.unlink()
                console.print(f"  Removed file: {path}")

    console.print("[green]✅ Clean completed![/green]")


def build_python_package(verbose: bool):
    """Build Python package using Poetry"""
    console.print("[bold blue]📦 Building Python package...[/bold blue]")
    try:
        cmd = [sys.executable, "-m", "poetry", "build"]
        subprocess.run(cmd, cwd=Path.cwd(), check=True, capture_output=not verbose, text=True)
        console.print("[green]✅ Python package built![/green]")
        dist_path = Path("dist")
        if dist_path.exists():
            console.print("\n[bold]Built files:[/bold]")
            for file in dist_path.iterdir():
                console.print(f"  {file.name} ({file.stat().st_size} bytes)")
    except subprocess.CalledProcessError as e:
        console.print("[red]❌ Python build failed![/red]")
        if not verbose and e.stderr:
            console.print(Panel(e.stderr, title="Error"))
    except FileNotFoundError:
        console.print("[red] poetry not found. Install with: pip install poetry[/red]")


def build_js_frontend(verbose: bool):
    """Build JavaScript frontend"""
    console.print("[bold blue]⚡ Building JS frontend...[/bold blue]")
    if not Path("package.json").exists():
        console.print("[dim]No package.json found, skipping JS build[/dim]")
        return
    try:
        subprocess.run(["npm", "run", "build"], cwd=Path.cwd(), check=True, capture_output=not verbose, text=True)
        console.print("[green]✅ JS frontend built![/green]")
    except subprocess.CalledProcessError as e:
        console.print("[red]❌ JS build failed![/red]")
        if not verbose and e.stderr:
            console.print(Panel(e.stderr, title="Error"))
    except FileNotFoundError:
        console.print("[yellow]npm not found, skipping JS build[/yellow]")


def build_docker_image(verbose: bool = False):
    """Build Docker image"""
    console.print("[bold blue]🐳 Building Docker image...[/bold blue]")
    if not Path("Dockerfile").exists():
        console.print("[dim]No Dockerfile found, skipping Docker build[/dim]")
        return
    try:
        image_tag = "mekong-cli:latest"
        subprocess.run(["docker", "build", "-t", image_tag, "."], cwd=Path.cwd(), check=True, capture_output=not verbose, text=True)
        console.print(f"[green]✅ Docker image built: {image_tag}[/green]")
    except subprocess.CalledProcessError as e:
        console.print("[red]❌ Docker build failed![/red]")
        if not verbose and e.stderr:
            console.print(Panel(e.stderr, title="Error"))
    except FileNotFoundError:
        console.print("[yellow]docker not found, skipping Docker build[/yellow]")


@app.command()
def info():
    """Show build information and status"""
    run_build_info()


@app.command()
def docker(
    tag: str = typer.Option("mekong-cli:latest", "--tag", "-t", help="Image tag"),
    push: bool = typer.Option(False, "--push", help="Push image after building"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Build without cache"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Build Docker image specifically"""
    run_build_docker(tag, push, no_cache, verbose)


__all__ = [
    "Console", "Panel", "Path", "Table", "app", "build_docker_image",
    "build_js_frontend", "build_python_package", "clean", "clean_build",
    "console", "docker", "info", "run", "shutil", "subprocess", "sys",
]


if __name__ == "__main__":
    app()
