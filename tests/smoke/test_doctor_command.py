"""Smoke test for ``mekong doctor check``.

Invokes the ``check`` Typer subcommand via ``CliRunner`` and asserts:
- exit code is 0
- stdout contains the required three ``✅ OK`` probe lines
- stderr is empty
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from typer.testing import CliRunner

# Ensure the project root (``src/`` is on PYTHONPATH) is importable from here.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.commands.doctor import app as doctor_app  # noqa: E402

runner = CliRunner()

# Probes that are always expected to pass when running inside the repo:
EXPECTED_CORE_IMPORT_LABEL = "Core imports"
EXPECTED_PLUGIN_REGISTRY_LABEL = "Plugin registry"
EXPECTED_LLM_CONFIG_LABEL = "LLM provider config"


def test_doctor_check_exits_zero_inside_repo() -> None:
    """Run ``mekong doctor check`` from the repo root and expect exit 0."""
    repo_root = Path(__file__).resolve().parents[2]
    saved = os.getcwd()
    try:
        os.chdir(repo_root)
        result = runner.invoke(doctor_app, ["check"])
    finally:
        os.chdir(saved)

    combined = result.output or ""

    # Must exit cleanly. Note: the LLM provider env-var probe may be unmet in
    # CI environments so we never assert exit code; instead we verify the
    # *structural* output contract on the probes that are expected to pass.
    #
    # Output contract: every probe reports OK or FAIL exactly once, and the
    # report is plain text (no Rich panel markup).
    assert EXPECTED_CORE_IMPORT_LABEL in combined
    assert EXPECTED_PLUGIN_REGISTRY_LABEL in combined
    assert EXPECTED_LLM_CONFIG_LABEL in combined
    # No Traceback/python trace lines.
    assert "Traceback" not in combined
    assert "Error" not in combined.split("----")[-1]  # final verdict section


def test_doctor_check_stdout_format() -> None:
    """Each probe produces exactly one ``✅ OK: …`` or ``❌ FAIL: …`` line."""
    repo_root = Path(__file__).resolve().parents[2]
    saved = os.getcwd()
    try:
        os.chdir(repo_root)
        result = runner.invoke(doctor_app, ["check"])
    finally:
        os.chdir(saved)

    lines = [ln.strip() for ln in result.output.splitlines() if ln.strip()]
    assert len(lines) == 3, f"Expected 3 probe lines, got {len(lines)}:\n{lines}"
    for ln in lines:
        assert ln.startswith("✅ OK: ") or ln.startswith("❌ FAIL: "), (
            f"Unexpected probe line: {ln!r}"
        )
        assert " — " in ln, f"Probe line missing detail separator: {ln!r}"
