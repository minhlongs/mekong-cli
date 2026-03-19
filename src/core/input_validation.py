"""Reusable input validation helpers for Mekong CLI API."""

from typing import Any, Optional
from src.core.error_responses import (
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    error_response,
)


def validate_required(
    value: Any,
    field_name: str
) -> Optional[ErrorResponse]:
    """
    Check that a required field is not null, empty string, or empty list.

    Args:
        value: The field value to validate
        field_name: Human-readable field name for error messages

    Returns:
        ErrorResponse if validation fails, None if passes
    """
    if value is None:
        return error_response(
            ErrorCode.MISSING_FIELD,
            f"Field '{field_name}' is required",
            [ErrorDetail(field=field_name, message="Required", value=None)]
        )

    if isinstance(value, str) and not value.strip():
        return error_response(
            ErrorCode.INVALID_INPUT,
            f"Field '{field_name}' cannot be empty",
            [ErrorDetail(field=field_name, message="Cannot be empty", value="")]
        )

    if isinstance(value, list) and len(value) == 0:
        return error_response(
            ErrorCode.INVALID_INPUT,
            f"Field '{field_name}' cannot be an empty array",
            [ErrorDetail(field=field_name, message="Cannot be empty array", value=[])]
        )

    return None


def validate_string_length(
    value: str,
    field_name: str,
    min_len: int = 1,
    max_len: int = 1000
) -> Optional[ErrorResponse]:
    """
    Validate string length is within bounds.

    Args:
        value: The string to validate
        field_name: Field name for error messages
        min_len: Minimum allowed length (default 1)
        max_len: Maximum allowed length (default 1000)

    Returns:
        ErrorResponse if validation fails, None if passes
    """
    if len(value) < min_len:
        return error_response(
            ErrorCode.INVALID_FORMAT,
            f"Field '{field_name}' must be at least {min_len} characters",
            [ErrorDetail(field=field_name, message=f"Min {min_len} chars", value=value[:50])]
        )

    if len(value) > max_len:
        return error_response(
            ErrorCode.INVALID_FORMAT,
            f"Field '{field_name}' must be at most {max_len} characters",
            [ErrorDetail(field=field_name, message=f"Max {max_len} chars", value=value[:50])]
        )

    return None


def validate_url(
    value: str,
    field_name: str
) -> Optional[ErrorResponse]:
    """
    Validate URL format (must start with http:// or https://).

    Args:
        value: The URL string to validate
        field_name: Field name for error messages

    Returns:
        ErrorResponse if validation fails, None if passes
    """
    if not value.startswith(("http://", "https://")):
        return error_response(
            ErrorCode.INVALID_FORMAT,
            f"Field '{field_name}' must be a valid URL (http:// or https://)",
            [ErrorDetail(field=field_name, message="Invalid URL format", value=value)]
        )
    return None


def validate_enum_value(
    value: str,
    field_name: str,
    allowed_values: list[str],
    error_message: str = None
) -> Optional[ErrorResponse]:
    """
    Validate value is one of the allowed enum values.

    Args:
        value: The value to validate
        field_name: Field name for error messages
        allowed_values: List of allowed values
        error_message: Custom error message (optional)

    Returns:
        ErrorResponse if validation fails, None if passes
    """
    if value not in allowed_values:
        return error_response(
            ErrorCode.INVALID_INPUT,
            error_message or f"Field '{field_name}' must be one of: {', '.join(allowed_values)}",
            [ErrorDetail(field=field_name, message=f"Must be one of: {allowed_values}", value=value)]
        )
    return None


__all__ = [
    "validate_required",
    "validate_string_length",
    "validate_url",
    "validate_enum_value",
]
