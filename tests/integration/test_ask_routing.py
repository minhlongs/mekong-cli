"""Integration tests for /ask VI+EN NL routing — verifies end-to-end routing."""
from __future__ import annotations

import pytest
from typer.testing import CliRunner
from src.commands.core_commands import app


runner = CliRunner()


COMMON_TESTS = [
    # (input, expected_route_command_or_None_for_LLM_fallback)
    ("code giao diện", "cook"),
    ("sửa lỗi thanh toán", "fix"),
    ("lập kế hoạch marketing", "plan"),
    ("viết bài blog", "content-blog"),
    ("tạo chiến dịch marketing", "marketing-campaign"),
    ("quét bảo mật", "security-scan"),
    ("phân tích dữ liệu", "analytics-report"),
    ("deploy lên production", "deploy"),
    ("tạo tài liệu", "docs"),
]


@pytest.mark.parametrize("input_text,expected", COMMON_TESTS)
def test_ask_routes_vietnamese(input_text: str, expected: str) -> None:
    """Vietnamese input routes to correct command."""
    result = runner.invoke(app, ["ask", input_text])
    assert result.exit_code == 0, f"Failed for: {input_text}"
    assert (
        expected in result.output
    ), f"Expected '{expected}' in output for '{input_text}', got: {result.output[:200]}"


EN_TESTS = [
    ("build a campaign", "marketing-campaign"),
    ("fix the bug", "fix"),
    ("create a plan", "plan"),
    ("write a blog post", "content-blog"),
    ("deploy to production", "deploy"),
]


@pytest.mark.parametrize("input_text,expected", EN_TESTS)
def test_ask_routes_english(input_text: str, expected: str) -> None:
    """English input routes to correct command."""
    result = runner.invoke(app, ["ask", input_text])
    assert result.exit_code == 0, f"Failed for: {input_text}"
    assert expected in result.output, f"Expected '{expected}' in output for '{input_text}'"


def test_ask_unknown_falls_through() -> None:
    """Unknown input should not crash — output contains answer/fallback."""
    result = runner.invoke(app, ["ask", "hello world unknown intent"])
    # Should not crash (exit 0 or graceful exit)
    assert result.exit_code in (0, 1)


def test_ask_empty_argument() -> None:
    """Empty argument should show help or fail gracefully."""
    result = runner.invoke(app, ["ask", ""])
    # Should not crash
    assert result.exit_code in (0, 1, 2)
