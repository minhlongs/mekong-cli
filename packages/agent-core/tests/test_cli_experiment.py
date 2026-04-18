"""Tests for `agent-core experiment` CLI command."""

from __future__ import annotations

import json

import pytest
import typer

from agent_core.cli import experiment_cmd


def test_experiment_prints_default_variant(capsys) -> None:
    experiment_cmd(user="user-1", name="exp-a", variants="control,treatment", json_out=False)
    out = capsys.readouterr().out.strip()
    assert out in {"control", "treatment"}


def test_experiment_deterministic_output(capsys) -> None:
    experiment_cmd(user="user-42", name="exp-a", variants="control,treatment", json_out=False)
    first = capsys.readouterr().out.strip()
    experiment_cmd(user="user-42", name="exp-a", variants="control,treatment", json_out=False)
    second = capsys.readouterr().out.strip()
    assert first == second


def test_experiment_json_output(capsys) -> None:
    experiment_cmd(user="u-x", name="exp-j", variants="a,b,c", json_out=True)
    payload = json.loads(capsys.readouterr().out)
    assert payload["user"] == "u-x"
    assert payload["experiment"] == "exp-j"
    assert payload["variant"] in {"a", "b", "c"}


def test_experiment_rejects_empty_user(capsys) -> None:
    with pytest.raises(typer.Exit) as exc:
        experiment_cmd(user="", name="exp-a", variants="control,treatment", json_out=False)
    assert exc.value.exit_code == 2
    assert "user_id" in capsys.readouterr().err


def test_experiment_rejects_blank_variants(capsys) -> None:
    with pytest.raises(typer.Exit) as exc:
        experiment_cmd(user="user-1", name="exp-a", variants=",,", json_out=False)
    assert exc.value.exit_code == 2
    assert "variants" in capsys.readouterr().err
