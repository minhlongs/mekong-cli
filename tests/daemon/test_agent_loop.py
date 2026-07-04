"""Unit tests for src/daemon/agent_loop.py."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open


# ---------------------------------------------------------------------------
# _safe_path
# ---------------------------------------------------------------------------

class TestSafePath:
    def test_valid_relative_path(self):
        from src.daemon.agent_loop import _safe_path, SANDBOX_DIR
        result = _safe_path("logs/test.log")
        assert str(result).startswith(str(SANDBOX_DIR.resolve()))

    def test_traversal_blocked(self):
        from src.daemon.agent_loop import _safe_path
        with pytest.raises(ValueError, match="traversal"):
            _safe_path("../../etc/passwd")

    def test_nested_valid_path(self):
        from src.daemon.agent_loop import _safe_path, SANDBOX_DIR
        result = _safe_path("sub/dir/file.txt")
        assert str(result).startswith(str(SANDBOX_DIR.resolve()))


# ---------------------------------------------------------------------------
# execute_tool — read_file
# ---------------------------------------------------------------------------

class TestExecuteToolReadFile:
    def test_file_not_found(self):
        from src.daemon.agent_loop import execute_tool
        with patch("src.daemon.agent_loop._safe_path") as mock_sp:
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = False
            mock_sp.return_value = mock_path
            result = execute_tool("read_file", {"path": "missing.txt"})
        assert "not found" in result

    def test_file_exists_returns_content(self):
        from src.daemon.agent_loop import execute_tool
        with patch("src.daemon.agent_loop._safe_path") as mock_sp:
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = "hello world"
            mock_sp.return_value = mock_path
            result = execute_tool("read_file", {"path": "hello.txt"})
        assert result == "hello world"

    def test_large_file_truncated(self):
        from src.daemon.agent_loop import execute_tool
        big_content = "x" * 5000
        with patch("src.daemon.agent_loop._safe_path") as mock_sp:
            mock_path = MagicMock(spec=Path)
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = big_content
            mock_sp.return_value = mock_path
            result = execute_tool("read_file", {"path": "big.txt"})
        assert len(result) <= 4000


# ---------------------------------------------------------------------------
# execute_tool — write_file
# ---------------------------------------------------------------------------

class TestExecuteToolWriteFile:
    def test_write_file_returns_byte_count(self):
        from src.daemon.agent_loop import execute_tool
        content = "some content"
        with patch("src.daemon.agent_loop._safe_path") as mock_sp:
            mock_path = MagicMock(spec=Path)
            mock_path.parent = MagicMock()
            mock_sp.return_value = mock_path
            result = execute_tool("write_file", {"path": "out.txt", "content": content})
        assert str(len(content)) in result
        mock_path.write_text.assert_called_once_with(content)

    def test_write_creates_parent_dirs(self):
        from src.daemon.agent_loop import execute_tool
        with patch("src.daemon.agent_loop._safe_path") as mock_sp:
            mock_path = MagicMock(spec=Path)
            mock_parent = MagicMock()
            mock_path.parent = mock_parent
            mock_sp.return_value = mock_path
            execute_tool("write_file", {"path": "sub/out.txt", "content": "data"})
        mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# execute_tool — http_get
# ---------------------------------------------------------------------------

class TestExecuteToolHttpGet:
    def test_non_http_url_rejected(self):
        from src.daemon.agent_loop import execute_tool
        result = execute_tool("http_get", {"url": "ftp://example.com"})
        assert "Error" in result

    def test_localhost_blocked(self):
        from src.daemon.agent_loop import execute_tool
        result = execute_tool("http_get", {"url": "http://localhost/secret"})
        assert "blocked" in result.lower()

    def test_127_0_0_1_blocked(self):
        from src.daemon.agent_loop import execute_tool
        result = execute_tool("http_get", {"url": "http://127.0.0.1/secret"})
        assert "blocked" in result.lower()

    def test_private_ip_10_blocked(self):
        from src.daemon.agent_loop import execute_tool
        result = execute_tool("http_get", {"url": "http://10.0.0.1/secret"})
        assert "blocked" in result.lower()

    def test_private_ip_192_168_blocked(self):
        from src.daemon.agent_loop import execute_tool
        result = execute_tool("http_get", {"url": "http://192.168.1.1/secret"})
        assert "blocked" in result.lower()

    def test_valid_url_fetches_content(self):
        from src.daemon.agent_loop import execute_tool
        mock_response = MagicMock()
        mock_response.read.return_value = b"page content"
        mock_response.__enter__ = lambda s: mock_response
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("src.daemon.agent_loop.urlopen", return_value=mock_response):
            result = execute_tool("http_get", {"url": "https://example.com"})
        assert "page content" in result

    def test_valid_url_truncated_at_4000(self):
        from src.daemon.agent_loop import execute_tool
        mock_response = MagicMock()
        mock_response.read.return_value = b"A" * 5000
        mock_response.__enter__ = lambda s: mock_response
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("src.daemon.agent_loop.urlopen", return_value=mock_response):
            result = execute_tool("http_get", {"url": "https://example.com"})
        assert len(result) <= 4000


# ---------------------------------------------------------------------------
# execute_tool — list_dir
# ---------------------------------------------------------------------------

class TestExecuteToolListDir:
    def test_not_a_directory(self):
        from src.daemon.agent_loop import execute_tool
        with patch("src.daemon.agent_loop._safe_path") as mock_sp:
            mock_path = MagicMock(spec=Path)
            mock_path.is_dir.return_value = False
            mock_sp.return_value = mock_path
            result = execute_tool("list_dir", {"path": "file.txt"})
        assert "Not a directory" in result

    def test_lists_files(self, tmp_path):
        from src.daemon.agent_loop import execute_tool, SANDBOX_DIR
        # Use real paths inside sandbox so _safe_path resolves correctly
        test_dir = SANDBOX_DIR / "test_list_tmp"
        test_dir.mkdir(parents=True, exist_ok=True)
        (test_dir / "beta.txt").write_text("b")
        (test_dir / "alpha.txt").write_text("a")
        try:
            result = execute_tool("list_dir", {"path": "test_list_tmp"})
            assert result.index("alpha.txt") < result.index("beta.txt")
        finally:
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# execute_tool — append_log
# ---------------------------------------------------------------------------

class TestExecuteToolAppendLog:
    def test_appends_timestamped_message(self):
        from src.daemon.agent_loop import execute_tool
        with patch("builtins.open", mock_open()) as m:
            with patch.object(Path, "mkdir"):
                result = execute_tool("append_log", {"filename": "agent.log", "message": "hello"})
        assert "Logged" in result
        handle = m()
        written = handle.write.call_args[0][0]
        assert "hello" in written

    def test_sanitizes_filename(self):
        from src.daemon.agent_loop import execute_tool
        with patch("builtins.open", mock_open()):
            with patch.object(Path, "mkdir"):
                result = execute_tool("append_log", {"filename": "../../evil", "message": "x"})
        # The traversal chars replaced — should not raise
        assert "Logged" in result


# ---------------------------------------------------------------------------
# execute_tool — unknown tool
# ---------------------------------------------------------------------------

class TestExecuteToolUnknown:
    def test_unknown_tool_returns_message(self):
        from src.daemon.agent_loop import execute_tool
        result = execute_tool("nonexistent_tool", {})
        assert "Unknown tool" in result

    def test_exception_returns_error_string(self):
        from src.daemon.agent_loop import execute_tool
        # Force an exception by passing bad args
        with patch("src.daemon.agent_loop._safe_path", side_effect=RuntimeError("boom")):
            result = execute_tool("read_file", {"path": "x"})
        assert "Tool error" in result


# ---------------------------------------------------------------------------
# run_agent_sync
# ---------------------------------------------------------------------------

class TestRunAgentSync:
    def _msg(self, content=None, tool_calls=None):
        return {"content": content, "tool_calls": tool_calls}

    def test_returns_final_content_when_no_tool_calls(self):
        from src.daemon.agent_loop import run_agent_sync
        final_msg = self._msg(content="All done!")
        with patch("src.daemon.agent_loop._llm_call", return_value=final_msg):
            result = run_agent_sync("do something", model_tier="fast")
        assert result == "All done!"

    def test_llm_failure_returns_error(self):
        from src.daemon.agent_loop import run_agent_sync
        from urllib.error import URLError
        with patch("src.daemon.agent_loop._llm_call", side_effect=URLError("timeout")):
            result = run_agent_sync("task", model_tier="fast")
        assert "Error" in result

    def test_tool_call_executed_and_result_appended(self):
        from src.daemon.agent_loop import run_agent_sync

        tool_msg = self._msg(tool_calls=[{
            "id": "tc1",
            "function": {"name": "read_file", "arguments": json.dumps({"path": "x.txt"})},
        }])
        final_msg = self._msg(content="Done after tool")

        call_count = [0]

        def fake_llm(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return tool_msg
            return final_msg

        with patch("src.daemon.agent_loop._llm_call", side_effect=fake_llm):
            with patch("src.daemon.agent_loop.execute_tool", return_value="file_content") as mock_exec:
                result = run_agent_sync("task", model_tier="fast")

        mock_exec.assert_called_once_with("read_file", {"path": "x.txt"})
        assert result == "Done after tool"

    def test_invalid_json_args_handled_gracefully(self):
        from src.daemon.agent_loop import run_agent_sync

        tool_msg = self._msg(tool_calls=[{
            "id": "tc2",
            "function": {"name": "read_file", "arguments": "NOT_JSON"},
        }])
        final_msg = self._msg(content="OK")

        call_seq = [tool_msg, final_msg]
        with patch("src.daemon.agent_loop._llm_call", side_effect=call_seq):
            with patch("src.daemon.agent_loop.execute_tool", return_value="result") as mock_exec:
                result = run_agent_sync("task", model_tier="fast")

        # Should have called execute_tool with empty dict on bad JSON
        mock_exec.assert_called_once_with("read_file", {})
        assert result == "OK"

    def test_tool_call_without_id_handled_gracefully(self):
        from src.daemon.agent_loop import run_agent_sync

        tool_msg = self._msg(tool_calls=[{
            # NO "id" field in this tool call dictionary
            "function": {"name": "read_file", "arguments": json.dumps({"path": "x.txt"})},
        }])
        final_msg = self._msg(content="Done without id")

        call_seq = [tool_msg, final_msg]
        with patch("src.daemon.agent_loop._llm_call", side_effect=call_seq):
            with patch("src.daemon.agent_loop.execute_tool", return_value="file_content"):
                result = run_agent_sync("task", model_tier="fast")

        assert result == "Done without id"

    def test_max_steps_reached_returns_last_content(self):
        from src.daemon.agent_loop import run_agent_sync

        # Always return tool calls — never terminates naturally
        tool_msg = {"content": "step", "tool_calls": [{
            "id": "tc",
            "function": {"name": "append_log", "arguments": json.dumps({"filename": "f.log", "message": "m"})},
        }]}
        with patch("src.daemon.agent_loop._llm_call", return_value=tool_msg):
            with patch("src.daemon.agent_loop.execute_tool", return_value="ok"):
                result = run_agent_sync("task", model_tier="fast", max_steps=2)
        # max steps exhausted — falls through to last message content
        assert result is not None

    def test_system_prompt_prepended(self):
        from src.daemon.agent_loop import run_agent_sync
        captured_messages = []

        def fake_llm(messages, *args, **kwargs):
            captured_messages.extend(messages)
            return {"content": "done", "tool_calls": None}

        with patch("src.daemon.agent_loop._llm_call", side_effect=fake_llm):
            run_agent_sync("user task", system_prompt="Be helpful")

        roles = [m["role"] for m in captured_messages]
        assert roles[0] == "system"
        assert roles[1] == "user"

    def test_fast_vs_deep_tier_config(self):
        from src.daemon.agent_loop import run_agent_sync, TIER_CONFIG
        calls = []

        def fake_llm(messages, base_url, model, *args, **kwargs):
            calls.append((base_url, model))
            return {"content": "done", "tool_calls": None}

        with patch("src.daemon.agent_loop._llm_call", side_effect=fake_llm):
            run_agent_sync("task", model_tier="deep")

        assert calls[0][1] == TIER_CONFIG["deep"]["model"]

    def test_unknown_tier_falls_back_to_fast(self):
        from src.daemon.agent_loop import run_agent_sync, TIER_CONFIG
        calls = []

        def fake_llm(messages, base_url, model, *args, **kwargs):
            calls.append(model)
            return {"content": "done", "tool_calls": None}

        with patch("src.daemon.agent_loop._llm_call", side_effect=fake_llm):
            run_agent_sync("task", model_tier="nonexistent")

        assert calls[0] == TIER_CONFIG["fast"]["model"]


# ---------------------------------------------------------------------------
# run_agent (async wrapper)
# ---------------------------------------------------------------------------

class TestRunAgent:
    @pytest.mark.asyncio
    async def test_async_wrapper_returns_sync_result(self):
        from src.daemon.agent_loop import run_agent
        with patch("src.daemon.agent_loop.run_agent_sync", return_value="async_result"):
            result = await run_agent("task")
        assert result == "async_result"
