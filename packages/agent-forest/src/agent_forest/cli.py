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


@app.command("register-user")
def register_user_cmd(
    username: str = typer.Argument(..., help="Username (a-zA-Z0-9_-, <=64 chars)."),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Secret string (>=8 chars). If omitted, typer prompts interactively.",
    ),
    db_path: str = typer.Option(
        None,
        "--db-path",
        envvar="FOREST_DB_PATH",
        help="SQLite DB path (overrides FOREST_DB_PATH env).",
    ),
) -> None:
    """Bootstrap a user straight into SqliteUserStore (no HTTP required)."""
    if not db_path:
        typer.echo("Error: --db-path or FOREST_DB_PATH is required", err=True)
        raise typer.Exit(code=2)
    if len(password) < 8:
        typer.echo("Error: password must be >=8 characters", err=True)
        raise typer.Exit(code=2)
    from agent_forest.users_db import SqliteUserStore

    store = SqliteUserStore(db_path)
    try:
        user = store.register_user(username, password)
    except ValueError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Da tao user: {user.username} (id={user.user_id})")


if __name__ == "__main__":  # pragma: no cover
    app()
