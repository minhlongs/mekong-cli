"""Tests for src/core/error_responses.py — standardized API error schema."""

from __future__ import annotations

import uuid
from datetime import datetime

from src.core.error_responses import (
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    error_response,
)


class TestErrorCode:
    def test_client_error_codes(self):
        assert ErrorCode.INVALID_INPUT.value == "INVALID_INPUT"
        assert ErrorCode.MISSING_FIELD.value == "MISSING_FIELD"
        assert ErrorCode.INVALID_FORMAT.value == "INVALID_FORMAT"
        assert ErrorCode.UNAUTHORIZED.value == "UNAUTHORIZED"
        assert ErrorCode.FORBIDDEN.value == "FORBIDDEN"
        assert ErrorCode.NOT_FOUND.value == "NOT_FOUND"
        assert ErrorCode.CONFLICT.value == "CONFLICT"
        assert ErrorCode.RATE_LIMIT_EXCEEDED.value == "RATE_LIMIT_EXCEEDED"
        assert ErrorCode.INSUFFICIENT_CREDITS.value == "INSUFFICIENT_CREDITS"

    def test_server_error_codes(self):
        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"
        assert ErrorCode.SERVICE_UNAVAILABLE.value == "SERVICE_UNAVAILABLE"
        assert ErrorCode.EXTERNAL_SERVICE_ERROR.value == "EXTERNAL_SERVICE_ERROR"


class TestErrorDetail:
    def test_error_detail_creation(self):
        detail = ErrorDetail(field="goal", message="Required", value=None)
        assert detail.field == "goal"
        assert detail.message == "Required"
        assert detail.value is None

    def test_error_detail_with_value(self):
        detail = ErrorDetail(field="count", message="Must be positive", value=-5)
        assert detail.value == -5


class TestErrorResponse:
    def test_to_dict_with_details(self):
        detail = ErrorDetail(field="tenant_id", message="Invalid UUID", value="abc")
        resp = ErrorResponse(
            error_code=ErrorCode.INVALID_INPUT,
            message="Validation failed",
            details=[detail],
            request_id="req-123",
            timestamp="2026-09-10T00:00:00Z",
        )
        d = resp.to_dict()
        assert d == {
            "error": {
                "code": "INVALID_INPUT",
                "message": "Validation failed",
                "details": [
                    {"field": "tenant_id", "message": "Invalid UUID", "value": "abc"}
                ],
                "request_id": "req-123",
                "timestamp": "2026-09-10T00:00:00Z",
            }
        }

    def test_to_dict_without_details(self):
        resp = ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Server crashed",
            details=None,
            request_id="req-456",
            timestamp="2026-09-10T00:00:00Z",
        )
        d = resp.to_dict()
        assert d["error"]["details"] == []
        assert d["error"]["code"] == "INTERNAL_ERROR"


class TestErrorResponseFactory:
    def test_error_response_factory_defaults(self):
        resp = error_response(ErrorCode.NOT_FOUND, "Resource not found")
        assert resp.error_code == ErrorCode.NOT_FOUND
        assert resp.message == "Resource not found"
        assert resp.details == []
        # Valid UUIDv4
        parsed_uuid = uuid.UUID(resp.request_id)
        assert parsed_uuid.version == 4
        # Valid ISO timestamp
        parsed_dt = datetime.fromisoformat(resp.timestamp)
        assert parsed_dt is not None

    def test_error_response_factory_with_details(self):
        details = [ErrorDetail(field="name", message="Too long", value="xyz" * 50)]
        resp = error_response(ErrorCode.INVALID_INPUT, "Bad payload", details)
        assert resp.error_code == ErrorCode.INVALID_INPUT
        assert len(resp.details) == 1
        assert resp.details[0].field == "name"
        d = resp.to_dict()
        assert len(d["error"]["details"]) == 1
