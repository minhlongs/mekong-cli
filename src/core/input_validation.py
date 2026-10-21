# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Reusable input validation helpers for Mekong CLI API."""

import re
from typing import Any, Optional
from src.core.error_responses import (
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    error_response,
)

# Maximum string length for any input field
MAX_STRING_LENGTH = 4096

# Characters to strip from input (control chars except tab/newline)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def strip_control_chars(value: str) -> str:
    """Remove control characters from a string (except tab and newline)."""
    return _CONTROL_CHAR_RE.sub("", value)


def reject_null_bytes(value: str) -> str:
    """Reject null bytes from a string. Raises ValueError if found."""
    if "\x00" in value:
        raise ValueError("Null byte detected in input — rejected for security.")
    return value


def limit_string_length(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
    """Truncate a string to max_length characters."""
    if len(value) > max_length:
        return value[:max_length]
    return value


def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
    """Full sanitization: strip null bytes, strip control chars, limit length."""
    reject_null_bytes(value)
    return limit_string_length(strip_control_chars(value), max_length)


def validate_required(value: Any, field_name: str) -> Optional[ErrorResponse]:
    """Check that a required field is not null, empty string, or empty list."""
    if value is None:
        return error_response(
            ErrorCode.MISSING_FIELD,
            f"Field '{field_name}' is required",
            [ErrorDetail(field=field_name, message="Required", value=None)],
        )
    if isinstance(value, str) and not value.strip():
        return error_response(
            ErrorCode.INVALID_INPUT,
            f"Field '{field_name}' cannot be empty",
            [ErrorDetail(field=field_name, message="Cannot be empty", value="")],
        )
    if isinstance(value, list) and len(value) == 0:
        return error_response(
            ErrorCode.INVALID_INPUT,
            f"Field '{field_name}' cannot be an empty array",
            [ErrorDetail(field=field_name, message="Cannot be empty array", value=[])],
        )
    return None


def validate_string_length(
    value: str, field_name: str, min_len: int = 1, max_len: int = 1000,
) -> Optional[ErrorResponse]:
    """Validate string length is within bounds."""
    if len(value) < min_len:
        return error_response(
            ErrorCode.INVALID_FORMAT,
            f"Field '{field_name}' must be at least {min_len} characters",
            [ErrorDetail(field=field_name, message=f"Min {min_len} chars", value=value[:50])],
        )
    if len(value) > max_len:
        return error_response(
            ErrorCode.INVALID_FORMAT,
            f"Field '{field_name}' must be at most {max_len} characters",
            [ErrorDetail(field=field_name, message=f"Max {max_len} chars", value=value[:50])],
        )
    return None


def validate_url(value: str, field_name: str) -> Optional[ErrorResponse]:
    """Validate URL format (must start with http:// or https://)."""
    if not value.startswith(("http://", "https://")):
        return error_response(
            ErrorCode.INVALID_FORMAT,
            f"Field '{field_name}' must be a valid URL (http:// or https://)",
            [ErrorDetail(field=field_name, message="Invalid URL format", value=value)],
        )
    return None


def validate_enum_value(
    value: str, field_name: str, allowed_values: list[str], error_message: str = None,
) -> Optional[ErrorResponse]:
    """Validate value is one of the allowed enum values."""
    if value not in allowed_values:
        return error_response(
            ErrorCode.INVALID_INPUT,
            error_message or f"Field '{field_name}' must be one of: {', '.join(allowed_values)}",
            [ErrorDetail(field=field_name, message=f"Must be one of: {allowed_values}", value=value)],
        )
    return None


__all__ = [
    "validate_required",
    "validate_string_length",
    "validate_url",
    "validate_enum_value",
    "sanitize_string",
    "strip_control_chars",
    "reject_null_bytes",
    "limit_string_length",
]
