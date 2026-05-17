"""mekongd CLI — typer entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from mekongd import __version__
from mekongd.config import load_config
from mekongd.stats import aggregate_stats

app = typer.Typer(help="mekongd — Qwen3.6 local daemon for CC CLI cost savings")
config_app = typer.Typer(help="Config inspection")
stats_app = typer.Typer(help="Routing stats")
app.add_typer(config_app, name="config")
app.add_typer(stats_app, name="stats")

console = Console()


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Print version and exit"),
) -> None:
    if version:
        console.print(f"mekongd {__version__}")
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(0)


@app.command("serve")
def serve(
    host: Optional[str] = typer.Option(None, "--host", help="Bind host"),
    port: Optional[int] = typer.Option(None, "--port", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload (dev only)"),
) -> None:
    """Start the Anthropic-compat proxy server."""
    import uvicorn

    cfg = load_config()
    uvicorn.run(
        "mekongd.proxy:app",
        host=host or cfg.api_host,
        port=port or cfg.api_port,
        reload=reload,
        log_level="info",
    )


@config_app.command("show")
def config_show(as_json: bool = typer.Option(False, "--json", help="Emit JSON")) -> None:
    """Print effective config (redacting secrets)."""
    cfg = load_config()
    data = cfg.model_dump()
    if data.get("anthropic_api_key"):
        data["anthropic_api_key"] = "***"
    if as_json:
        console.print_json(data=_json_safe(data))
        return
    for k, v in data.items():
        console.print(f"[bold cyan]{k}[/] = {v}")


@stats_app.command("show")
def stats_show() -> None:
    """Print routing stats aggregate."""
    cfg = load_config()
    summary = aggregate_stats(cfg.stats_db_path)
    table = Table(title="mekongd routing stats")
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", style="green")
    table.add_row("Total requests", str(summary.total_requests))
    table.add_row("Local (Qwen)", f"{summary.local_requests} ({summary.local_pct:.1f}%)")
    table.add_row("Cloud (Anthropic)", str(summary.cloud_requests))
    table.add_row("Tokens in", f"{summary.total_tokens_in:,}")
    table.add_row("Tokens out", f"{summary.total_tokens_out:,}")
    table.add_row("USD saved (est.)", f"${summary.total_cost_saved_usd:,.2f}")
    console.print(table)


def _json_safe(obj):
    """Recursively stringify Path to make JSON-serializable."""
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj


if __name__ == "__main__":
    app()
