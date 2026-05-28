"""Tool output validator for LLM-generated JSON.

Schema validation → error feedback → self-correction loop.
Achieves ~80% first-retry fix rate per 2025-2026 research.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result from validating a tool's raw output."""

    success: bool
    data: Any = None
    error: str | None = None
    retryable: bool = False
    raw_output: str | None = None


@dataclass
class ToolOutputSchema:
    """Schema definition for validating a tool's JSON output."""

    name: str
    required_fields: list[str] = field(default_factory=list)
    field_types: dict[str, type] = field(default_factory=dict)
    max_output_size: int = 50_000


def validate_tool_output(raw: str, schema: ToolOutputSchema) -> ToolResult:
    """Validate raw LLM tool output against a schema.

    Args:
        raw: Raw string output from the LLM tool call.
        schema: Expected schema for the output.

    Returns:
        ToolResult with success=True and parsed data, or a descriptive error.
    """
    # Guard: size check before any parsing to avoid OOM on huge payloads
    if len(raw) > schema.max_output_size:
        msg = f"Output exceeds {schema.max_output_size} chars (got {len(raw)})"
        logger.warning("tool=%s size_exceeded=%d", schema.name, len(raw))
        return ToolResult(success=False, error=msg, retryable=False, raw_output=raw)

    # Parse JSON
    try:
        parsed: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"Malformed JSON: {exc}"
        logger.debug("tool=%s json_error=%s", schema.name, exc)
        return ToolResult(success=False, error=msg, retryable=True, raw_output=raw)

    # Required fields
    if schema.required_fields:
        if not isinstance(parsed, dict):
            msg = "Expected a JSON object but got a non-dict value"
            return ToolResult(success=False, error=msg, retryable=True, raw_output=raw)
        missing = [f for f in schema.required_fields if f not in parsed]
        if missing:
            msg = f"Missing fields: {missing}"
            logger.debug("tool=%s missing_fields=%s", schema.name, missing)
            return ToolResult(success=False, error=msg, retryable=True, raw_output=raw)

    # Type checks
    if schema.field_types and isinstance(parsed, dict):
        for fname, expected_type in schema.field_types.items():
            if fname not in parsed:
                continue  # already caught above if required
            actual = parsed[fname]
            if not isinstance(actual, expected_type):
                msg = (
                    f"Type mismatch: {fname} expected {expected_type.__name__}"
                    f" but got {type(actual).__name__}"
                )
                logger.debug("tool=%s type_mismatch field=%s", schema.name, fname)
                return ToolResult(success=False, error=msg, retryable=True, raw_output=raw)

    logger.debug("tool=%s validation=ok", schema.name)
    return ToolResult(success=True, data=parsed)


def format_retry_feedback(result: ToolResult, schema: ToolOutputSchema) -> str:
    """Generate human-readable error feedback to feed back to the LLM.

    The message explains what went wrong, what was expected, and provides
    an example of the correct format so the model can self-correct.

    Args:
        result: Failed ToolResult from validate_tool_output.
        schema: The schema that was used during validation.

    Returns:
        Formatted string suitable for injection into the next LLM prompt.
    """
    example_fields = {f: f"<{schema.field_types.get(f, str).__name__}>" for f in schema.required_fields}
    example_json = json.dumps(example_fields, indent=2)

    lines = [
        f"Your previous output for tool '{schema.name}' was invalid.",
        f"Error: {result.error}",
        "",
        "Expected format:",
        f"  Required fields: {schema.required_fields}",
        f"  Field types: { {k: v.__name__ for k, v in schema.field_types.items()} }",
        "",
        "Example of a valid response:",
        example_json,
        "",
        "Please retry and return only valid JSON matching the schema above.",
    ]
    return "\n".join(lines)
