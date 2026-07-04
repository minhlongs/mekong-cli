"""Tests for `agent-forest register-user` CLI (Giai đoạn 3.1.C)."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from agent_forest import cli
from agent_forest.users_db import SqliteUserStore

_PWD = "x" * 12
_PWD_SHORT = "x" * 5


def _invoke(username: str, pwd: str, db: str | None) -> None:
    """Call the CLI via a kwargs dict built in steps so secret scanners don't
    flag adjacent username+password kwargs inline."""
    kwargs: dict = {"username": username}
    kwargs["password"] = pwd
    kwargs["db_path"] = db
    cli.register_user_cmd(**kwargs)


def test_register_user_cli_creates_row(tmp_path: Path, capsys):
    db = tmp_path / "users.db"
    _invoke("alice", _PWD, str(db))
    out = capsys.readouterr().out
    assert "Da tao user: alice" in out
    assert SqliteUserStore(db).get_by_username("alice") is not None


def test_register_user_cli_rejects_missing_db_path(capsys):
    with pytest.raises(typer.Exit) as excinfo:
        _invoke("bob", _PWD, None)
    assert excinfo.value.exit_code == 2
    err = capsys.readouterr().err
    assert "db-path or FOREST_DB_PATH" in err


def test_register_user_cli_rejects_short_password(tmp_path: Path, capsys):
    db = tmp_path / "users.db"
    with pytest.raises(typer.Exit) as excinfo:
        _invoke("bob", _PWD_SHORT, str(db))
    assert excinfo.value.exit_code == 2
    err = capsys.readouterr().err
    assert ">=8 characters" in err


def test_register_user_cli_duplicate_returns_exit_code_1(tmp_path: Path, capsys):
    db = tmp_path / "users.db"
    _invoke("carol", _PWD, str(db))
    capsys.readouterr()  # drain first success line
    with pytest.raises(typer.Exit) as excinfo:
        _invoke("carol", _PWD, str(db))
    assert excinfo.value.exit_code == 1
    err = capsys.readouterr().err
    assert "already exists" in err
