"""agent-forest CLI: `gateway` (uvicorn) + `worker` (BRPOP loop)."""

from __future__ import annotations

import logging

import typer
import uvicorn

from agent_forest import __version__

app = typer.Typer(no_args_is_help=True, help="agent-forest — Phase 2 multi-tenant runtime.")


@app.callback()
def _root(
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()


@app.command()
def gateway(
    host: str = typer.Option("0.0.0.0", envvar="FOREST_HOST"),  # noqa: S104
    port: int = typer.Option(8000, envvar="FOREST_PORT"),
    reload: bool = typer.Option(False, help="Enable auto-reload (dev only)."),
) -> None:
    """Run the FastAPI gateway via uvicorn."""
    uvicorn.run("agent_forest.gateway.app:app", host=host, port=port, reload=reload)


@app.command()
def worker(
    log_level: str = typer.Option("INFO", envvar="FOREST_LOG_LEVEL"),
) -> None:
    """Run the Redis-backed worker loop."""
    from agent_forest.worker.main import run_loop

    logging.basicConfig(level=log_level.upper())
    run_loop()


if __name__ == "__main__":  # pragma: no cover
    app()
