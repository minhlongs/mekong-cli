# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Stdlib JSON-Schema subset validator for capability operation inputs.

Only the keywords Mekong operation contracts use are implemented, and they are
implemented *strictly*: a parameter of the wrong type is rejected with a
field-level error instead of being silently coerced. The single exception is
``coerce_from_cli`` — the CLI transports every argument as a string, so an
explicit, schema-driven conversion step is provided and audited.

Supported keywords: ``type``, ``properties``, ``required``,
``additionalProperties``, ``enum``, ``const``, ``minimum``, ``maximum``,
``exclusiveMinimum``, ``exclusiveMaximum``, ``minLength``, ``maxLength``,
``pattern``, ``items``, ``minItems``, ``maxItems``, ``format``, ``default``.
"""

from __future__ import annotations

import datetime
import decimal
import re
import typing

Scalar = str | int | float | bool | None

_TYPE_CHECKS: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "array": (list, tuple),
    "object": (dict,),
    "null": (type(None),),
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?")


class SchemaValidationError(ValueError):
    """Raised when an operation payload fails contract validation."""

    def __init__(self, errors: list[dict[str, str]]) -> None:
        self.errors = errors
        summary = "; ".join(f"{e['field']}: {e['message']}" for e in errors[:6])
        super().__init__(f"Input validation failed -> {summary}")


def _type_name(value: typing.Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (list, tuple)):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return type(value).__name__


def _check_format(value: str, fmt: str, field: str, errors: list[dict[str, str]]) -> None:
    if fmt in ("date", "date-iso8601"):
        if not _DATE_RE.match(value):
            errors.append({"field": field, "message": f"must be an ISO-8601 date (YYYY-MM-DD), got '{value}'"})
            return
        try:
            datetime.date.fromisoformat(value)
        except ValueError:
            errors.append({"field": field, "message": f"'{value}' is not a real calendar date"})
    elif fmt in ("date-time", "datetime"):
        if not _DATETIME_RE.match(value):
            errors.append({"field": field, "message": f"must be an ISO-8601 datetime, got '{value}'"})
    elif fmt == "decimal":
        try:
            decimal.Decimal(str(value))
        except (decimal.InvalidOperation, ValueError):
            errors.append({"field": field, "message": f"must be a decimal amount, got '{value}'"})
    elif fmt == "currency-code":
        if not re.match(r"^[A-Z]{3}$", value):
            errors.append({"field": field, "message": f"must be an ISO-4217 currency code, got '{value}'"})


def _validate_node(
    schema: dict[str, typing.Any],
    value: typing.Any,
    field: str,
    errors: list[dict[str, typing.Any]],
) -> None:
    expected = schema.get("type")
    nullable = bool(schema.get("nullable", False))

    if value is None:
        if nullable or schema.get("default") is not None or "default" in schema:
            return
        if expected and expected != "null":
            errors.append({"field": field, "message": "must not be null"})
        return

    if expected:
        allowed = _TYPE_CHECKS.get(expected, ())
        if expected == "integer" and isinstance(value, bool):
            allowed = ()
        if expected == "number" and isinstance(value, bool):
            allowed = ()
        if not isinstance(value, allowed):
            errors.append(
                {
                    "field": field,
                    "message": f"expected type '{expected}', got '{_type_name(value)}'",
                }
            )
            return

    if "enum" in schema and value not in schema["enum"]:
        errors.append({"field": field, "message": f"must be one of {schema['enum']}, got '{value}'"})
    if "const" in schema and value != schema["const"]:
        errors.append({"field": field, "message": f"must equal '{schema['const']}'"})

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append({"field": field, "message": f"must be >= {schema['minimum']}, got {value}"})
        if "maximum" in schema and value > schema["maximum"]:
            errors.append({"field": field, "message": f"must be <= {schema['maximum']}, got {value}"})
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append({"field": field, "message": f"must be > {schema['exclusiveMinimum']}, got {value}"})
        if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
            errors.append({"field": field, "message": f"must be < {schema['exclusiveMaximum']}, got {value}"})

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append({"field": field, "message": f"must be at least {schema['minLength']} characters"})
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append({"field": field, "message": f"must be at most {schema['maxLength']} characters"})
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append({"field": field, "message": f"must match pattern /{schema['pattern']}/"})
        if "format" in schema:
            _check_format(value, schema["format"], field, errors)

    if isinstance(value, (list, tuple)):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append({"field": field, "message": f"must contain at least {schema['minItems']} items"})
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append({"field": field, "message": f"must contain at most {schema['maxItems']} items"})
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for idx, item in enumerate(value):
                _validate_node(item_schema, item, f"{field}[{idx}]", errors)

    if isinstance(value, dict):
        props: dict[str, typing.Any] = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in value or value[req] is None:
                errors.append({"field": f"{field}.{req}" if field != "$" else req, "message": "is required"})
        for key, sub_value in value.items():
            sub_field = f"{field}.{key}" if field != "$" else key
            if key in props:
                _validate_node(props[key], sub_value, sub_field, errors)
            elif schema.get("additionalProperties") is False:
                errors.append({"field": sub_field, "message": "is not an accepted parameter for this operation"})


def apply_defaults(schema: dict[str, typing.Any], params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    """Return a copy of ``params`` with schema defaults filled in."""
    out = dict(params)
    for key, sub in (schema.get("properties") or {}).items():
        if (key not in out or out[key] is None) and "default" in sub:
            out[key] = sub["default"]
    return out


def coerce_from_cli(
    schema: dict[str, typing.Any],
    raw: dict[str, typing.Any],
) -> tuple[dict[str, typing.Any], list[dict[str, str]]]:
    """Convert CLI string arguments using the declared schema types.

    Conversion is explicit and schema-driven (never ``eval``/shell parsing).
    Values that cannot be converted are returned as errors.
    """
    errors: list[dict[str, str]] = []
    converted: dict[str, typing.Any] = {}
    props: dict[str, typing.Any] = schema.get("properties") or {}

    for key, value in raw.items():
        sub = props.get(key)
        if sub is None or not isinstance(value, str):
            converted[key] = value
            continue
        target = sub.get("type")
        text = value.strip()
        try:
            if target == "integer":
                converted[key] = int(text.replace("_", ""), 10)
            elif target == "number":
                converted[key] = float(text.replace("_", ""))
            elif target == "boolean":
                lowered = text.lower()
                if lowered in ("1", "true", "yes", "y", "on"):
                    converted[key] = True
                elif lowered in ("0", "false", "no", "n", "off"):
                    converted[key] = False
                else:
                    raise ValueError(f"cannot read '{text}' as boolean")
            elif target == "array":
                converted[key] = [p.strip() for p in text.split(",") if p.strip()]
            elif target == "object":
                import json

                converted[key] = json.loads(text)
            else:
                converted[key] = value
        except (ValueError, TypeError) as exc:
            errors.append({"field": key, "message": f"cannot convert '{text}' to {target}: {exc}"})
    return converted, errors


def validate_params(
    schema: dict[str, typing.Any],
    params: dict[str, typing.Any] | None,
    *,
    fill_defaults: bool = True,
) -> dict[str, typing.Any]:
    """Validate ``params`` against ``schema``; raise :class:`SchemaValidationError`."""
    payload: dict[str, typing.Any] = dict(params or {})
    if fill_defaults:
        payload = apply_defaults(schema, payload)
    errors: list[dict[str, typing.Any]] = []
    _validate_node(schema, payload, "$", errors)
    if errors:
        raise SchemaValidationError([{k: str(v) for k, v in e.items()} for e in errors])
    return payload


__all__ = [
    "SchemaValidationError",
    "apply_defaults",
    "coerce_from_cli",
    "validate_params",
]
