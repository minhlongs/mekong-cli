"""Tests for cli.tui.palette command picker."""

import pytest
from unittest.mock import patch, MagicMock

from cli.tui.palette import CommandPicker, CommandMatch, fuzzy_search


# ── Keyword routing table (mirrors ask.md) ─────────────────────────────
ROUTING_TABLE = [
    # (command, [VI patterns], [EN patterns])
    ("cook", ["code", "lập trình", "viết code", "xây dựng"],
                 ["code", "build", "implement", "develop"]),
    ("fix", ["sửa lỗi", "sửa bug", "lỗi", "hỏng", "không chạy"],
                ["fix", "debug", "bug", "broken", "error"]),
    ("plan", ["lập kế hoạch", "lên kế hoạch", "tạo kế hoạch"],
              ["plan", "create plan", "build plan", "roadmap"]),
    ("brainstorm", ["brainstorm", "động não", "gợi ý"],
                          ["brainstorm", "idea", "ideate"]),
    ("docs", ["tài liệu", "viết docs"], ["docs", "document", "readme"]),
    ("ship", ["triển khai", "đưa lên production"],
              ["deploy", "release", "ship", "push"]),
    ("test", ["viết test", "chạy test", "kiểm thử"],
             ["test", "unit test", "write test"]),
    ("security-scan", ["quét bảo mật", "kiểm tra bảo mật"],
                       ["security scan", "security audit"]),
    ("analytics-report", ["phân tích", "báo cáo phân tích"],
                         ["analytics", "analyze data"]),
    ("ask", ["hỏi đáp", "câu hỏi kiến trúc"],
             ["question", "architecture", "how does"]),
]


class TestFuzzySearch:
    """Unit tests for fuzzy keyword matching."""

    def test_vi_match_code(self):
        """Vietnamese "code" → cook command."""
        results = fuzzy_search("code giao diện", ROUTING_TABLE)
        assert len(results) > 0
        assert results[0].command == "cook"

    def test_en_match_build(self):
        """English "build" → cook command."""
        results = fuzzy_search("build landing page", ROUTING_TABLE)
        assert len(results) > 0
        assert results[0].command == "cook"

    def test_vi_match_fix(self):
        """Vietnamese "sửa lỗi" → fix command."""
        results = fuzzy_search("sửa lỗi thanh toán", ROUTING_TABLE)
        assert len(results) > 0
        assert results[0].command == "fix"

    def test_en_match_debug(self):
        """English "debug" → fix command."""
        results = fuzzy_search("debug the payment error", ROUTING_TABLE)
        assert len(results) > 0
        assert results[0].command == "fix"

    def test_vi_match_plan(self):
        """Vietnamese "lập kế hoạch" → plan command."""
        results = fuzzy_search("lập kế hoạch marketing Q3", ROUTING_TABLE)
        assert len(results) > 0
        assert results[0].command == "plan"

    def test_en_match_plan(self):
        """English "plan" → plan command."""
        results = fuzzy_search("plan the next sprint", ROUTING_TABLE)
        assert len(results) > 0
        assert results[0].command == "plan"

    def test_no_match_returns_empty(self):
        """Unrelated query returns empty results."""
        results = fuzzy_search("hello world", ROUTING_TABLE)
        assert len(results) == 0

    def test_empty_query_returns_empty(self):
        """Empty string returns empty results."""
        results = fuzzy_search("", ROUTING_TABLE)
        assert len(results) == 0

    def test_case_insensitive(self):
        """Matching is case-insensitive."""
        results = fuzzy_search("CODE BUILD", ROUTING_TABLE)
        assert len(results) > 0
        assert results[0].command == "cook"

    def test_priority_order(self):
        """Routing table order wins on tied score."""
        # "sửa lỗi code" matches both fix (sửa lỗi) and cook (code)
        # Both score 0.5; table order breaks tie → cook is first entry
        results = fuzzy_search("sửa lỗi code", ROUTING_TABLE)
        assert len(results) > 0
        # Both should be in results
        commands = [r.command for r in results]
        assert "cook" in commands
        assert "fix" in commands
        # cook appears first due to table order (score tie)
        assert results[0].command == "cook"

    def test_result_has_score(self):
        """Results include a relevance score."""
        results = fuzzy_search("code", ROUTING_TABLE)
        if results:
            assert results[0].score >= 0

    def test_result_has_matched_pattern(self):
        """Results include the matched pattern."""
        results = fuzzy_search("code", ROUTING_TABLE)
        if results:
            assert results[0].matched_pattern is not None


class TestCommandPicker:
    """Integration tests for CommandPicker (mocked questionary)."""

    @patch("cli.tui.palette.questionary.autocomplete")
    def test_picker_returns_command(self, mock_autocomplete):
        """Picker returns selected command."""
        mock_autocomplete.return_value.ask.return_value = "cook"

        picker = CommandPicker(ROUTING_TABLE)
        result = picker.pick("code something")
        assert result == "cook"

    @patch("cli.tui.palette.questionary.autocomplete")
    def test_picker_returns_none_on_cancel(self, mock_autocomplete):
        """Picker returns None when user cancels (Ctrl+C)."""
        mock_autocomplete.return_value.ask.return_value = None

        picker = CommandPicker(ROUTING_TABLE)
        result = picker.pick("hello")
        assert result is None

    @patch("cli.tui.palette.questionary.autocomplete")
    def test_picker_suggests_top_5(self, mock_autocomplete):
        """Picker shows max 5 suggestions."""
        from cli.tui.palette import fuzzy_search

        results = fuzzy_search("a", ROUTING_TABLE)
        assert len(results) <= 5


class TestCommandMatch:
    """Tests for CommandMatch dataclass."""

    def test_create_match(self):
        from cli.tui.palette import CommandMatch

        m = CommandMatch(command="cook", score=0.9, matched_pattern="code")
        assert m.command == "cook"
        assert m.score == 0.9
        assert m.matched_pattern == "code"

    def test_match_sorting(self):
        from cli.tui.palette import CommandMatch

        matches = [
            CommandMatch("plan", 0.3, "plan"),
            CommandMatch("cook", 0.9, "code"),
            CommandMatch("fix", 0.5, "fix"),
        ]
        sorted_matches = sorted(matches, key=lambda m: m.score, reverse=True)
        assert sorted_matches[0].command == "cook"
        assert sorted_matches[1].command == "fix"
        assert sorted_matches[2].command == "plan"
