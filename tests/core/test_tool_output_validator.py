"""Tests for src/core/tool_output_validator.py."""


from src.core.tool_output_validator import (
    ToolOutputSchema,
    format_retry_feedback,
    validate_tool_output,
)

SCHEMA = ToolOutputSchema(
    name="test_tool",
    required_fields=["status", "count"],
    field_types={"status": str, "count": int},
    max_output_size=100,
)


def test_valid_json_passes():
    raw = '{"status": "ok", "count": 5}'
    result = validate_tool_output(raw, SCHEMA)
    assert result.success is True
    assert result.data == {"status": "ok", "count": 5}
    assert result.error is None


def test_malformed_json_retryable():
    raw = '{"status": "ok", "count":}'
    result = validate_tool_output(raw, SCHEMA)
    assert result.success is False
    assert result.retryable is True
    assert "Malformed JSON" in result.error
    assert result.raw_output == raw


def test_empty_string_is_malformed():
    result = validate_tool_output("", SCHEMA)
    assert result.success is False
    assert result.retryable is True
    assert "Malformed JSON" in result.error


def test_missing_required_field_retryable():
    raw = '{"status": "ok"}'  # missing "count"
    result = validate_tool_output(raw, SCHEMA)
    assert result.success is False
    assert result.retryable is True
    assert "Missing fields" in result.error
    assert "count" in result.error


def test_type_mismatch_retryable():
    raw = '{"status": "ok", "count": "not-an-int"}'
    result = validate_tool_output(raw, SCHEMA)
    assert result.success is False
    assert result.retryable is True
    assert "Type mismatch" in result.error
    assert "count" in result.error
    assert "int" in result.error


def test_oversized_output_non_retryable():
    raw = '{"status": "ok", "count": 1}' + " " * 200  # exceeds max_output_size=100
    result = validate_tool_output(raw, SCHEMA)
    assert result.success is False
    assert result.retryable is False
    assert "exceeds" in result.error


def test_format_retry_feedback_contains_expected_info():
    raw = '{"status": "ok"}'  # missing "count"
    result = validate_tool_output(raw, SCHEMA)
    assert not result.success

    feedback = format_retry_feedback(result, SCHEMA)
    assert "test_tool" in feedback
    assert "Missing fields" in feedback
    assert "status" in feedback
    assert "count" in feedback
    assert "valid JSON" in feedback.lower() or "retry" in feedback.lower()


def test_no_required_fields_schema_accepts_any_object():
    loose = ToolOutputSchema(name="loose", required_fields=[], field_types={})
    result = validate_tool_output('{"anything": true}', loose)
    assert result.success is True


def test_non_dict_json_with_required_fields():
    raw = '[1, 2, 3]'
    result = validate_tool_output(raw, SCHEMA)
    assert result.success is False
    assert result.retryable is True
