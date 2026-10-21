"""BYOK fail-closed gate: a missing API key must raise, never silently default.

The BYOK contract is that the operator supplies their own key. If a key is absent
the agent must fail with a typed error naming the variable — a silent fallback to
an unauthenticated call or a placeholder would leak that failure into a live API
call and produce a confusing downstream error instead of a clear one here.

Both live consumers (`src.mekong.cells.runner_llm`, `src.mekong.graph.network_llm`)
already raise; this test pins that so a refactor cannot quietly relax it.
"""
from __future__ import annotations

import importlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Modules whose `_get_api_key()` must fail closed. Each is imported under a
# cleaned environment so a developer's local key cannot mask the assertion.
BYOK_KEY_MODULES = (
    "src.mekong.cells.runner_llm",
    "src.mekong.graph.network_llm",
)

LLM_KEY_VARS = ("OPENROUTER_API_KEY", "ANTHROPIC_API_KEY")


@pytest.fixture
def cleared_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove every LLM key so the missing-key path is the one under test."""
    for var in LLM_KEY_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)


@pytest.mark.parametrize("module_name", BYOK_KEY_MODULES)
def test_missing_api_key_raises_typed_error(
    module_name: str, cleared_llm_env: None
) -> None:
    module = importlib.import_module(module_name)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        module._get_api_key()


@pytest.mark.parametrize("module_name", BYOK_KEY_MODULES)
def test_error_names_the_variable_not_a_url_or_secret(
    module_name: str, cleared_llm_env: None
) -> None:
    """The message must tell the operator what to set, and leak nothing."""
    module = importlib.import_module(module_name)
    with pytest.raises(ValueError) as excinfo:
        module._get_api_key()
    message = str(excinfo.value)
    for var in LLM_KEY_VARS:
        assert var in message, f"error does not name {var}: {message}"
    assert "http" not in message.lower(), "error should not push a URL at the operator"
    assert "Bearer" not in message, "error must not echo a credential format"


@pytest.mark.parametrize("module_name", BYOK_KEY_MODULES)
def test_present_key_is_returned_verbatim(
    module_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-a-secret")
    module = importlib.import_module(module_name)
    assert module._get_api_key() == "test-key-not-a-secret"
