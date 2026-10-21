# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Helpers for Mekong CLI Config commands."""

from __future__ import annotations

import typer
from rich.panel import Panel


def _mod():
    import src.commands.config as mod

    return mod


def mask_value(value: str, visible_chars: int = 4) -> str:
    """Mask sensitive value showing only last few chars."""
    if not value:
        return "(empty)"
    if len(value) <= visible_chars:
        return "*" * len(value)
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]


def run_config_validate() -> None:
    """Validate configuration and check for issues."""
    m = _mod()
    m.load_dotenv(m.ENV_FILE)

    m.console.print(
        Panel(
            "🔍 Configuration Validation",
            border_style="yellow",
        )
    )

    issues = []
    warnings = []

    required = ["ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL"]
    for var in required:
        if not m.os.getenv(var):
            issues.append(f"Missing required: {var}")

    recommended = ["MEKONG_API_TOKEN"]
    for var in recommended:
        if not m.os.getenv(var):
            warnings.append(f"Recommended but not set: {var}")

    base_url = m.os.getenv("ANTHROPIC_BASE_URL", "")
    if base_url and not base_url.startswith(("http://", "https://")):
        issues.append("ANTHROPIC_BASE_URL must start with http:// or https://")

    model = m.os.getenv("ANTHROPIC_MODEL", "")
    if model and " " in model:
        warnings.append("Model name contains spaces - this may cause issues")

    if not issues and not warnings:
        m.console.print("[bold green]✅ Configuration is valid![/bold green]")
        return

    if issues:
        m.console.print(f"[bold red]❌ {len(issues)} critical issue(s):[/bold red]")
        for issue in issues:
            m.console.print(f"  • {issue}")

    if warnings:
        m.console.print(f"\n[yellow]⚠️  {len(warnings)} warning(s):[/yellow]")
        for warning in warnings:
            m.console.print(f"  • {warning}")

    if issues:
        raise typer.Exit(1)


def run_config_export(output: str | None = None) -> None:
    """Export configuration to file (excluding secrets)."""
    m = _mod()
    m.load_dotenv(m.ENV_FILE)

    public_vars = [
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_MODEL",
        "MEKONG_DEBUG",
        "MEKONG_LOG_LEVEL",
    ]

    lines = [
        "# Mekong CLI Configuration Export",
        f"# Generated: {m.Path.cwd()}",
        "",
    ]

    for var in public_vars:
        value = m.os.getenv(var, "")
        if value:
            lines.append(f"{var}={value}")

    content = "\n".join(lines)

    if output:
        output_path = m.Path(output)
        output_path.write_text(content)
        m.console.print(f"[green]✓[/green] Exported to {output}")
    else:
        m.console.print("[bold]Configuration Export:[/bold]")
        m.console.print(content)
