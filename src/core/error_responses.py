"""Standardized error response schema for Mekong CLI API."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any
import uuid
from datetime import datetime, timezone


class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""

    # Client errors (4xx)
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INSUFFICIENT_CREDITS = "INSUFFICIENT_CREDITS"

    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


@dataclass
class ErrorDetail:
    """Granular field-level error information."""

    field: str  # e.g., "goal", "tenant_id"
    message: str  # e.g., "Required", "Must be 1-5000 chars"
    value: Optional[Any] = None  # The actual invalid value (truncated)


@dataclass
class ErrorResponse:
    """Standardized API error response."""

    error_code: ErrorCode
    message: str
    details: list[ErrorDetail] = None
    request_id: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "details": [
                    {"field": d.field, "message": d.message, "value": d.value}
                    for d in (self.details or [])
                ],
                "request_id": self.request_id,
                "timestamp": self.timestamp,
            }
        }


def error_response(
    code: ErrorCode,
    message: str,
    details: list[ErrorDetail] = None
) -> ErrorResponse:
    """Factory function to create ErrorResponse with auto-generated metadata."""
    return ErrorResponse(
        error_code=code,
        message=message,
        details=details or [],
        request_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


__all__ = ["ErrorCode", "ErrorDetail", "ErrorResponse", "error_response"]
