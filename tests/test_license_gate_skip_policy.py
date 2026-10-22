"""The license-gate skip may only happen in a test or CI run."""
from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

_KEYS = ("PYTEST_CURRENT_TEST", "CI", "LICENSE_GATE_ENFORCE")

REPO_ROOT = Path(__file__).resolve().parents[1]
_ROUTE_FILE = REPO_ROOT / "src/api/gateway_mission_routes.py"


def _load_helper():
    """Compile _license_gate_required out of the route file.

    The module cannot be imported here: it builds a tenant database at import
    time, which a unit test must not depend on.
    """
    tree = ast.parse(_ROUTE_FILE.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_license_gate_required")
    namespace: dict = {"os": os}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(_ROUTE_FILE), "exec"), namespace)
    return namespace["_license_gate_required"]


@pytest.fixture
def gate_required():
    helper = _load_helper()

    before = {key: os.environ.get(key) for key in _KEYS}

    def _run(test_context: bool, ci_context: bool, flag: str | None) -> bool:
        for key in _KEYS:
            os.environ.pop(key, None)
        if test_context:
            os.environ["PYTEST_CURRENT_TEST"] = "pytest::gate"
        if ci_context:
            os.environ["CI"] = "true"
        if flag is not None:
            os.environ["LICENSE_GATE_ENFORCE"] = flag
        return helper()

    yield _run

    # Restore only what this test changed, leaving pytest's own variable intact.
    for key, value in before.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.mark.parametrize("flag", [None, "0", "false", "no", "off", "1"])
def test_production_always_enforces_the_gate(gate_required, flag: str | None) -> None:
    """An ambient flag in a production shell must not open the paywall."""
    assert gate_required(test_context=False, ci_context=False, flag=flag) is True


def test_test_run_may_skip_the_gate(gate_required) -> None:
    assert gate_required(test_context=True, ci_context=False, flag="0") is False
    assert gate_required(test_context=True, ci_context=False, flag=None) is False


def test_ci_run_may_skip_the_gate(gate_required) -> None:
    assert gate_required(test_context=False, ci_context=True, flag="0") is False


def test_test_or_ci_run_can_still_enforce_the_gate(gate_required) -> None:
    assert gate_required(test_context=True, ci_context=False, flag="1") is True
    assert gate_required(test_context=False, ci_context=True, flag="1") is True
