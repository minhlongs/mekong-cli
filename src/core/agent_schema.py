# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Agent Schema Module.

Provides JSON Schema validation for agent definitions,
mirroring Codebuff's AgentDefinition interface.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Default allowed tools when none specified (backward compat: all tools)
ALL_TOOLS = "*"

# Valid output modes
OUTPUT_MODES = ("last_message", "all_messages", "structured")

# Step hook names
STEP_HOOKS = ("on_step_start", "on_step_end", "on_tool_call", "on_error")


def validate_agent_definition(definition: dict[str, Any]) -> list[str]:
    """Validate an agent definition dict against the schema.

    Args:
        definition: Agent definition fields (id, displayName, allowedTools, etc.)

    Returns:
        List of validation error strings. Empty = valid.
    """
    errors: list[str] = []

    # Required fields
    if "id" not in definition:
        errors.append("Missing required field: 'id'")
    elif not isinstance(definition["id"], str) or not definition["id"].strip():
        errors.append("'id' must be a non-empty string")

    if "displayName" not in definition:
        errors.append("Missing required field: 'displayName'")
    elif not isinstance(definition["displayName"], str):
        errors.append("'displayName' must be a string")

    # Optional fields with type checks
    if "allowedTools" in definition:
        at = definition["allowedTools"]
        if not isinstance(at, list):
            errors.append("'allowedTools' must be a list of strings")
        elif not all(isinstance(t, str) for t in at):
            errors.append("'allowedTools' must contain only strings")

    if "spawnableAgents" in definition:
        sa = definition["spawnableAgents"]
        if not isinstance(sa, list):
            errors.append("'spawnableAgents' must be a list of strings")
        elif not all(isinstance(a, str) for a in sa):
            errors.append("'spawnableAgents' must contain only strings")

    if "inputSchema" in definition:
        schema = definition["inputSchema"]
        if not isinstance(schema, dict):
            errors.append("'inputSchema' must be a dict (JSON Schema object)")

    if "outputMode" in definition:
        om = definition["outputMode"]
        if om not in OUTPUT_MODES:
            errors.append(
                f"'outputMode' must be one of {OUTPUT_MODES}, got: {om!r}"
            )

    if "stepHooks" in definition:
        hooks = definition["stepHooks"]
        if not isinstance(hooks, dict):
            errors.append("'stepHooks' must be a dict of async callbacks")
        else:
            for key in hooks:
                if key not in STEP_HOOKS:
                    errors.append(
                        f"Unknown stepHook: '{key}'. "
                        f"Valid hooks: {STEP_HOOKS}"
                    )

    return errors


def merge_definition_defaults(
    definition: dict[str, Any],
) -> dict[str, Any]:
    """Merge safe defaults into an agent definition.

    Ensures all optional fields have sensible defaults so
    existing code doesn't break when new fields are added.

    Args:
        definition: Partial agent definition (e.g. from user config)

    Returns:
        Complete definition with defaults filled in.
    """
    result = dict(definition)  # shallow copy

    result.setdefault("allowedTools", [ALL_TOOLS])
    result.setdefault("spawnableAgents", [])
    result.setdefault("outputMode", "last_message")
    result.setdefault("stepHooks", {})

    return result


__all__ = [
    "ALL_TOOLS",
    "OUTPUT_MODES",
    "STEP_HOOKS",
    "validate_agent_definition",
    "merge_definition_defaults",
]
