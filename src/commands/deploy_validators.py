# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Validation and sanitized process helpers for Deploy command."""

from pathlib import Path
import re
import subprocess
import sys

import typer

SAFE_ENV_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")
SAFE_VERSION_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")
SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_./-]{0,127}$")
SAFE_PLATFORM_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")


def _facade():
    return sys.modules["src.commands.deploy"]


def validate_env(env: str) -> str:
    """Validate environment string to prevent flag or command injection."""
    f = _facade()
    cleaned = env.strip()
    if not cleaned or not f.SAFE_ENV_PATTERN.match(cleaned) or cleaned.startswith("-"):
        f.console.print(f"[red]❌ Invalid environment name: {env}[/red]")
        f.console.print("[dim]Environment must be alphanumeric and may contain '.', '_', or '-'.[/dim]")
        raise typer.Exit(code=1)
    return cleaned


def validate_version(version: str) -> str:
    """Validate version/deployment ID to prevent command/argument injection."""
    f = _facade()
    cleaned = version.strip()
    if not cleaned or not f.SAFE_VERSION_PATTERN.match(cleaned) or cleaned.startswith("-"):
        f.console.print(f"[red]❌ Invalid version or deployment ID: {version}[/red]")
        f.console.print("[dim]Version must be alphanumeric and may contain '.', '_', or '-'.[/dim]")
        raise typer.Exit(code=1)
    return cleaned


def validate_identifier(name: str, label: str = "identifier") -> str:
    """Validate general identifiers (image name, namespace, etc.)."""
    f = _facade()
    cleaned = name.strip()
    if not cleaned or not f.SAFE_IDENTIFIER_PATTERN.match(cleaned) or cleaned.startswith("-"):
        f.console.print(f"[red]❌ Invalid {label}: {name}[/red]")
        raise typer.Exit(code=1)
    return cleaned


def validate_platform(platform: str) -> str:
    """Validate platform name string."""
    f = _facade()
    cleaned = platform.strip()
    if not cleaned or not f.SAFE_PLATFORM_PATTERN.match(cleaned) or cleaned.startswith("-"):
        f.console.print(f"[red]Unsupported platform: {platform}[/red]")
        raise typer.Exit(code=1)
    return cleaned


def validate_script_path(script_path_str: str) -> Path:
    """Validate script path to prevent command injection and argv flag smuggling."""
    f = _facade()
    cleaned = script_path_str.strip()
    if not cleaned or cleaned.startswith("-"):
        f.console.print("[red]❌ Invalid characters in custom deployment script path[/red]")
        raise typer.Exit(code=1)

    if any(c in cleaned for c in [";", "&", "|", "`", "$", "\n", "\r", "\0"]):
        f.console.print("[red]❌ Invalid characters in custom deployment script path[/red]")
        raise typer.Exit(code=1)

    script_path = f.Path(cleaned)
    if not script_path.exists():
        f.console.print(f"[red]❌ Custom deployment script not found: {cleaned}[/red]")
        f.console.print("[dim]Set CUSTOM_DEPLOY_SCRIPT environment variable or create ./deploy.sh[/dim]")
        raise typer.Exit(code=1)

    return script_path


def run_sanitized_process(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess:
    """Execute a subprocess command after validating safety via command sanitizer."""
    f = _facade()
    cmd_str = " ".join(cmd)
    check_result = f.sanitize_command(cmd_str)
    if not check_result.is_safe:
        f.console.print(f"[red]❌ Command blocked by security sanitizer: {check_result.blocked_patterns}[/red]")
        raise typer.Exit(code=1)
    return f.subprocess.run(
        cmd,
        cwd=cwd or f.Path.cwd(),
        check=check,
        capture_output=capture_output,
        text=text,
    )
