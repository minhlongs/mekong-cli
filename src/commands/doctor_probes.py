# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Smoke-test probe functions for `mekong doctor check`."""

from __future__ import annotations

from typing import NamedTuple


def _mod():
    import src.commands.doctor as mod

    return mod


class Check(NamedTuple):
    label: str
    passed: bool
    detail: str


def _probe_core_imports() -> Check:
    """Core modules required to boot the CLI are importable."""
    m = _mod()
    required = [
        "typer",
        "rich",
        "pydantic",
        "dotenv",
        "src",
        "src.core",
    ]
    missing = [mod_name for mod_name in required if m.importlib.util.find_spec(mod_name) is None]
    if missing:
        return Check("Core imports", False, f"missing: {', '.join(missing)}")
    return Check("Core imports", True, "all required modules resolve")


def _probe_plugin_registry() -> Check:
    """Plugin registry package is importable (no plugin instantiation)."""
    m = _mod()
    try:
        runtime_spec = m.importlib.util.find_spec("src.core.plugin_runtime")
        if runtime_spec is None:
            return Check("Plugin registry", False, "src.core.plugin_runtime not found")
        schema_spec = m.importlib.util.find_spec("src.core.plugin_schema")
        schema_note = (
            "schema module also found"
            if schema_spec is not None
            else "schema module not installed (non-fatal)"
        )
        return Check(
            "Plugin registry",
            True,
            f"spec found ({runtime_spec.origin}); {schema_note}",
        )
    except Exception as exc:
        return Check("Plugin registry", False, str(exc))


def _probe_llm_provider_config() -> Check:
    """At least one LLM provider env var is configured."""
    m = _mod()
    env_vars = [
        "LLM_BASE_URL",
        "OPENROUTER_API_KEY",
        "DASHSCOPE_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "OLLAMA_BASE_URL",
    ]
    found = [name for name in env_vars if m.os.environ.get(name)]
    if found:
        return Check("LLM provider config", True, f"{found[0]} is set")
    return Check(
        "LLM provider config",
        False,
        "none of: " + ", ".join(env_vars),
    )
