"""Tests for compression module."""

from __future__ import annotations

from src.core.compression import compress


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _msg(role: str, content: str, **extra: str) -> dict[str, object]:
    return {"role": role, "content": content, **extra}


def _tool_msg(content: str) -> dict[str, object]:
    return {"role": "tool", "content": content, "tool_call_id": "tc-1"}


# ------------------------------------------------------------------
# Session dedup
# ------------------------------------------------------------------


class TestDedupSystemMessages:
    def test_removes_duplicate_system(self) -> None:
        msgs = [
            _msg("system", "You are helpful"),
            _msg("user", "Hi"),
            _msg("assistant", "Hello"),
            _msg("system", "You are helpful"),
            _msg("user", "Bye"),
        ]
        result = compress(msgs, target_savings=0.0)
        assert len(result) == 4
        assert result[0]["content"] == "You are helpful"

    def test_keeps_distinct_system_messages(self) -> None:
        msgs = [
            _msg("system", "Rules A"),
            _msg("user", "Hi"),
            _msg("system", "Rules B"),
        ]
        result = compress(msgs, target_savings=0.0)
        assert len(result) == 3

    def test_non_system_messages_not_deduped(self) -> None:
        msgs = [_msg("user", "same"), _msg("user", "same")]
        result = compress(msgs, target_savings=0.0)
        assert len(result) == 2


# ------------------------------------------------------------------
# Truncate tool results
# ------------------------------------------------------------------


class TestTruncateToolResults:
    def test_short_content_not_truncated(self) -> None:
        content = "short"
        msgs = [_tool_msg(content)]
        result = compress(msgs, target_savings=0.0, max_token_chars=1000)
        assert result[0]["content"] == content

    def test_long_content_truncated(self) -> None:
        content = "x" * 100_000
        msgs = [_tool_msg(content)]
        result = compress(msgs, target_savings=0.0, max_token_chars=500)
        output = str(result[0]["content"])
        assert len(output) < len(content)
        assert "[TRUNCATED" in output
        assert "100000 chars" in output

    def test_non_tool_messages_untouched(self) -> None:
        content = "x" * 100_000
        msgs = [_msg("user", content)]
        result = compress(msgs, target_savings=0.0, max_token_chars=500)
        assert result[0]["content"] == content


# ------------------------------------------------------------------
# Prose collapse
# ------------------------------------------------------------------


class TestCollapseProse:
    def test_excessive_newlines_collapsed(self) -> None:
        content = "hello\n\n\n\n\n\nworld"
        msgs = [_msg("user", content)]
        result = compress(msgs, target_savings=0.5)
        assert "\n\n\n" not in str(result[0]["content"])

    def test_multiple_spaces_collapsed(self) -> None:
        content = "hello    world   foo"
        msgs = [_msg("user", content)]
        result = compress(msgs, target_savings=0.5)
        assert "    " not in str(result[0]["content"])


# ------------------------------------------------------------------
# Compression ratio
# ------------------------------------------------------------------


class TestCompressionRatio:
    def test_returns_messages_list(self) -> None:
        msgs = [_msg("user", "hello")]
        result = compress(msgs)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_empty_input(self) -> None:
        result = compress([])
        assert result == []

    def test_prose_only_when_needed(self) -> None:
        # Messages with lots of whitespace should be collapsed
        content = "a" + " " * 500 + "b" + "\n\n\n\n\n" + "c"
        msgs = [_msg("user", content)]
        result = compress(msgs, target_savings=0.99)
        # Should have collapsed to save tokens
        orig_len = len(content)
        new_len = len(str(result[0]["content"]))
        assert new_len < orig_len

    def test_input_not_mutated(self) -> None:
        msgs = [_msg("system", "dup"), _msg("user", "hi"), _msg("system", "dup")]
        original_first = msgs[0]["content"]
        compress(msgs, target_savings=0.0)
        assert msgs[0]["content"] == original_first
        assert len(msgs) == 3
