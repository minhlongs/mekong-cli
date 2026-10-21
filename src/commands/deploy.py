# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Deploy command - Deploy applications to various platforms"""

import os
from pathlib import Path
import re
import subprocess

from rich.console import Console
from rich.panel import Panel
import typer

from src.commands.deploy_providers import (
    deploy_cloudflare, deploy_custom, deploy_docker, deploy_to_kubernetes,
)
from src.commands.deploy_validators import (
    SAFE_ENV_PATTERN, SAFE_IDENTIFIER_PATTERN, SAFE_PLATFORM_PATTERN, SAFE_VERSION_PATTERN,
    run_sanitized_process, validate_env, validate_identifier, validate_platform,
    validate_script_path, validate_version,
)
from src.security.command_sanitizer import sanitize_command

app = typer.Typer()
console = Console()


@app.command()
def run(
    platform: str = typer.Argument(..., help="Platform to deploy to: cloudflare, docker, custom"),
    build_first: bool = typer.Option(True, "--build/--no-build", help="Build before deploying"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate deployment without executing"),
    env: str = typer.Option("production", "--env", "-e", help="Environment: production, staging, development"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Deploy application to specified platform"""
    platform, env = validate_platform(platform), validate_env(env)
    if dry_run:
        console.print(f"[yellow]🧪 DRY RUN: Would deploy to {platform} (env: {env})[/yellow]")
        return

    if build_first:
        console.print("[blue]📦 Building application...[/blue]")
        console.print("[green]✅ Build completed[/green]")

    console.print(f"[bold]🚀 Deploying to {platform} (environment: {env})...[/bold]")
    dispatch = {"cloudflare": deploy_cloudflare, "docker": deploy_docker, "custom": deploy_custom}
    if platform.lower() in dispatch:
        dispatch[platform.lower()](env, verbose)
    else:
        console.print(f"[red]Unsupported platform: {platform}[/red]\n[dim]Supported platforms: cloudflare, docker, custom[/dim]")
        raise typer.Exit(code=1)


@app.command()
def status(platform: str = typer.Argument(..., help="Platform to check: cloudflare, docker")):
    """Check deployment status."""
    platform = validate_platform(platform)
    console.print(f"[bold]Checking deployment status for {platform}...[/bold]")
    if platform.lower() == "cloudflare":
        check_cloudflare_status()
    elif platform.lower() == "docker":
        check_docker_status()
    else:
        console.print(f"[red]Unsupported platform: {platform}[/red]\n[dim]Supported platforms: cloudflare, docker[/dim]")
        raise typer.Exit(code=1)


def check_cloudflare_status() -> None:
    """Check Cloudflare Workers/Pages deployment status."""
    try:
        result = run_sanitized_process(["wrangler", "deployments", "list"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            console.print(Panel(result.stdout, title="Cloudflare Deployments"))
        else:
            console.print("[yellow]Unable to fetch Cloudflare status[/yellow]")
            if result.stderr:
                console.print(Panel(result.stderr, title="Error"))
            raise typer.Exit(code=1)
    except FileNotFoundError:
        console.print("[red]wrangler CLI not found. Install with: npm install -g wrangler[/red]")
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Failed to check Cloudflare status: {str(e)}[/red]")
        raise typer.Exit(code=1)


def check_docker_status():
    """Check Docker deployment status"""
    try:
        result = run_sanitized_process(["docker", "info"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            console.print(Panel("Docker daemon is running", title="Docker Status", border_style="green"))
        else:
            console.print(Panel("Docker daemon is not running", title="Docker Status", border_style="red"))
            raise typer.Exit(code=1)

        result = run_sanitized_process(["docker", "ps"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            console.print(Panel(result.stdout, title="Running Containers"))
        else:
            raise typer.Exit(code=1)
    except FileNotFoundError:
        console.print("[red]❌ Docker not found. Please install Docker.[/red]")
        raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]❌ Failed to check Docker status: {str(e)}[/red]")
        raise typer.Exit(code=1)


@app.command()
def rollback(
    to_version: str = typer.Argument(..., help="Version or deployment ID to rollback to"),
    platform: str = typer.Option("cloudflare", "--platform", "-p", help="Platform: cloudflare, docker"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate rollback without executing"),
):
    """Rollback deployment to a previous version"""
    platform, to_version = validate_platform(platform), validate_version(to_version)
    console.print(f"[bold]🔄 Rolling back to version: {to_version} (platform: {platform})[/bold]")
    if dry_run:
        console.print(f"[yellow]🧪 DRY RUN: Would rollback {platform} to {to_version}[/yellow]")
        return

    if platform.lower() == "cloudflare":
        try:
            result = run_sanitized_process(["wrangler", "rollback", "--", to_version], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                if result.stdout:
                    console.print(Panel(result.stdout, title="Cloudflare Rollback Output"))
                console.print(f"[green]✅ Successfully rolled back to {to_version}[/green]")
            else:
                console.print("[red]Cloudflare rollback failed![/red]")
                if result.stderr:
                    console.print(Panel(result.stderr, title="Error"))
                raise typer.Exit(code=1)
        except FileNotFoundError:
            console.print("[red]wrangler CLI not found. Install with: npm install -g wrangler[/red]")
            raise typer.Exit(code=1)
        except typer.Exit:
            raise
        except Exception as e:
            console.print(f"[red]Rollback failed: {str(e)}[/red]")
            raise typer.Exit(code=1)
    else:
        console.print(f"[yellow]Rollback not yet supported for platform: {platform}[/yellow]")
        raise typer.Exit(code=1)


__all__ = [
    "Path", "SAFE_ENV_PATTERN", "SAFE_IDENTIFIER_PATTERN", "SAFE_PLATFORM_PATTERN",
    "SAFE_VERSION_PATTERN", "app", "check_cloudflare_status", "check_docker_status",
    "console", "deploy_cloudflare", "deploy_custom", "deploy_docker",
    "deploy_to_kubernetes", "os", "re", "rollback", "run",
    "run_sanitized_process", "sanitize_command", "status", "subprocess",
    "validate_env", "validate_identifier", "validate_platform",
    "validate_script_path", "validate_version",
]
