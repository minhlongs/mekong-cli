"""Tests for Mekong Tool Registry (AGI v2)."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.tool_registry import (
    MCPTool,
    Tool,
    ToolParameter,
    ToolRegistry,
    ToolType,
)


class TestTool(unittest.TestCase):
    def test_default_values(self):
        t = Tool(name="test", description="desc")
        self.assertEqual(t.tool_type, ToolType.BUILTIN)
        self.assertEqual(t.success_count, 0)
        self.assertEqual(t.success_rate, 0.0)
        self.assertEqual(t.reliability, "low")

    def test_success_rate(self):
        t = Tool(name="t", description="d", success_count=9, failure_count=1)
        self.assertAlmostEqual(t.success_rate, 0.9)
        self.assertEqual(t.reliability, "high")

    def test_medium_reliability(self):
        t = Tool(name="t", description="d", success_count=7, failure_count=3)
        self.assertEqual(t.reliability, "medium")


class TestMCPTool(unittest.TestCase):
    def test_from_tool_with_parameters_and_defaults(self):
        tool = Tool(
            name="fetch_url",
            description="Fetch a URL",
            tool_type=ToolType.MCP,
            parameters=[
                ToolParameter(name="url", description="Target URL", type="string", required=True),
                ToolParameter(name="timeout", description="Timeout in sec", type="integer", default=30, required=False),
            ],
        )
        mcp = MCPTool.from_tool(tool)
        self.assertEqual(mcp.name, "fetch_url")
        self.assertEqual(mcp.description, "Fetch a URL")
        self.assertEqual(mcp.inputSchema["type"], "object")
        self.assertIn("url", mcp.inputSchema["properties"])
        self.assertIn("timeout", mcp.inputSchema["properties"])
        self.assertEqual(mcp.inputSchema["properties"]["timeout"]["default"], 30)
        self.assertEqual(mcp.inputSchema["required"], ["url"])

    def test_from_tool_without_required_parameters(self):
        tool = Tool(
            name="ping",
            description="Ping service",
            tool_type=ToolType.MCP,
            parameters=[
                ToolParameter(name="verbose", description="Verbose output", type="boolean", required=False),
            ],
        )
        mcp = MCPTool.from_tool(tool)
        self.assertNotIn("required", mcp.inputSchema)


class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._path = str(Path(self._tmpdir) / "tool_registry.yaml")
        self.registry = ToolRegistry(persist_path=self._path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_register_and_get(self):
        tool = self.registry.register("my-tool", "A test tool", ToolType.CUSTOM)
        self.assertIsNotNone(self.registry.get("my-tool"))
        self.assertEqual(tool.name, "my-tool")

    def test_unregister(self):
        self.registry.register("temp", "temp tool")
        self.assertTrue(self.registry.unregister("temp"))
        self.assertIsNone(self.registry.get("temp"))
        self.assertFalse(self.registry.unregister("nonexistent"))

    def test_search(self):
        self.registry.register("git-push", "Push to remote", tags=["git", "deploy"])
        self.registry.register("npm-build", "Build project", tags=["npm", "build"])
        results = self.registry.search("git")
        self.assertTrue(any(t.name == "git-push" for t in results))

    def test_search_by_type_and_tag_filter(self):
        self.registry.register("api-tool", "API tool", tool_type=ToolType.API, tags=["web", "cloud"])
        self.registry.register("cli-tool", "CLI tool", tool_type=ToolType.CLI, tags=["local"])

        # Match type and tag
        results = self.registry.search("tool", tool_type=ToolType.API, tags=["web"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "api-tool")

        # Mismatch tag
        results_no_tag = self.registry.search("tool", tool_type=ToolType.API, tags=["nonexistent"])
        self.assertEqual(len(results_no_tag), 0)

        # Search by tag query string
        results_tag_query = self.registry.search("cloud")
        self.assertEqual(len(results_tag_query), 1)
        self.assertEqual(results_tag_query[0].name, "api-tool")

    def test_execute_with_handler(self):
        self.registry.register(
            "add", "Add numbers",
            handler=lambda a=1, b=2: a + b,
        )
        result = self.registry.execute("add", {"a": 3, "b": 4})
        self.assertTrue(result["success"])
        self.assertEqual(result["output"], "7")
        self.assertGreater(result["duration_ms"], 0.0)

    def test_execute_not_found(self):
        result = self.registry.execute("nonexistent")
        self.assertFalse(result["success"])
        self.assertIn("not found", result["output"])

    def test_execute_no_handler_or_template(self):
        self.registry.register("empty_tool", "Tool with nothing")
        result = self.registry.execute("empty_tool")
        self.assertFalse(result["success"])
        self.assertIn("has no handler or command template", result["output"])

    def test_execute_command_template_success_and_rolling_duration(self):
        self.registry.register(
            "echo_test",
            "Echo message",
            command_template="echo {msg}",
        )
        res1 = self.registry.execute("echo_test", {"msg": "hello"})
        self.assertTrue(res1["success"])
        self.assertEqual(res1["output"], "hello")

        # Second run to test rolling average duration branch (total > 1)
        res2 = self.registry.execute("echo_test", {"msg": "world"})
        self.assertTrue(res2["success"])
        tool = self.registry.get("echo_test")
        self.assertEqual(tool.success_count, 2)
        self.assertGreater(tool.avg_duration_ms, 0.0)

    def test_execute_command_template_failure_exit_code(self):
        self.registry.register(
            "fail_cmd",
            "Failing command",
            command_template="false",
        )
        res = self.registry.execute("fail_cmd")
        self.assertFalse(res["success"])
        self.assertIn("Exit code", res["output"])
        tool = self.registry.get("fail_cmd")
        self.assertEqual(tool.failure_count, 1)

    def test_execute_shell_run_safe_and_unsafe(self):
        # 1. Safe command execution
        mock_proc = MagicMock(returncode=0, stdout="safe command output\n", stderr="")
        with patch("subprocess.run", return_value=mock_proc):
            res = self.registry.execute("shell:run", {"command": "echo 'safe command'"})
            self.assertTrue(res["success"])
            self.assertIn("safe command output", res["output"])

        # 2. Unsafe command blocked
        mock_san = MagicMock()
        mock_res = MagicMock(is_safe=False, blocked_reason="Dangerous token", blocked_patterns=["rm -rf"])
        mock_san.sanitize.return_value = mock_res
        with patch("src.core.command_sanitizer.CommandSanitizer", return_value=mock_san):
            res_unsafe = self.registry.execute("shell:run", {"command": "rm -rf /"})
            self.assertFalse(res_unsafe["success"])
            self.assertIn("blocked by CommandSanitizer", res_unsafe["output"])

        # 3. Unsafe command with no blocked_reason
        mock_res2 = MagicMock(is_safe=False, blocked_reason=None, blocked_patterns=["pattern1", "pattern2"])
        mock_san.sanitize.return_value = mock_res2
        with patch("src.core.command_sanitizer.CommandSanitizer", return_value=mock_san):
            res_unsafe2 = self.registry.execute("shell:run", {"command": "dangerous"})
            self.assertFalse(res_unsafe2["success"])
            self.assertIn("pattern1; pattern2", res_unsafe2["output"])

        # 4. CommandSanitizer ImportError fallback
        with patch.dict(sys.modules, {"src.core.command_sanitizer": None}):
            res_no_san = self.registry.execute("shell:run", {"command": "ls"})
            self.assertFalse(res_no_san["success"])
            self.assertIn("CommandSanitizer module missing", res_no_san["output"])

    def test_list_tools(self):
        all_tools = self.registry.list_tools()
        self.assertGreater(len(all_tools), 0)

    def test_list_tools_by_type(self):
        builtins = self.registry.list_tools(ToolType.BUILTIN)
        self.assertGreater(len(builtins), 0)

    def test_list_mcp_tools(self):
        self.registry.register(
            "mcp_calc", "Calculate",
            tool_type=ToolType.MCP,
            parameters=[ToolParameter(name="x", description="number", type="integer")],
        )
        mcp_tools = self.registry.list_mcp_tools()
        self.assertEqual(len(mcp_tools), 1)
        self.assertEqual(mcp_tools[0].name, "mcp_calc")

    def test_list_for_agent(self):
        agent_empty = MagicMock(allowed_tools=[])
        agent_wildcard = MagicMock(allowed_tools=["*"])
        agent_specific = MagicMock(allowed_tools=["git:status", "git_diff"])

        # Empty -> all tools
        self.assertEqual(len(self.registry.list_for_agent(agent_empty)), len(self.registry.list_tools()))
        # Wildcard -> all tools
        self.assertEqual(len(self.registry.list_for_agent(agent_wildcard)), len(self.registry.list_tools()))

        # Specific
        filtered = self.registry.list_for_agent(agent_specific)
        names = {t.name for t in filtered}
        self.assertIn("git:status", names)
        self.assertIn("git:diff", names)

    def test_validate_call(self):
        agent_empty = MagicMock(allowed_tools=[])
        agent_wildcard = MagicMock(allowed_tools=["*"])
        agent_specific = MagicMock(allowed_tools=["git:status", "git:diff"])

        self.assertTrue(self.registry.validate_call(agent_empty, "anything"))
        self.assertTrue(self.registry.validate_call(agent_wildcard, "anything"))

        self.assertTrue(self.registry.validate_call(agent_specific, "git:status"))
        self.assertTrue(self.registry.validate_call(agent_specific, "git_diff"))
        self.assertFalse(self.registry.validate_call(agent_specific, "file:read"))

    def test_get_stats(self):
        self.registry.register("tool1", "desc1")
        self.registry.register("tool2", "desc2")
        stats = self.registry.get_stats()
        self.assertIn("total_tools", stats)
        self.assertIn("type_counts", stats)
        self.assertIn("total_executions", stats)
        self.assertIn("overall_success_rate", stats)

    def test_suggest_tool_found_and_none(self):
        tool = self.registry.suggest_tool("git")
        self.assertIsNotNone(tool)

        no_tool = self.registry.suggest_tool("xyznonexistentunmatchedquery123")
        self.assertIsNone(no_tool)

    def test_discover_from_cli_success(self):
        mock_proc = MagicMock()
        mock_proc.stdout = """
  Usage: mycli [COMMAND]

  Commands:
    init       Initialize project
    deploy     Deploy application
    options    Ignore this
    usage      Ignore this
    examples   Ignore this
    see        Ignore this
"""
        mock_proc.stderr = ""
        with patch("subprocess.run", return_value=mock_proc):
            discovered = self.registry.discover_from_cli("mycli")
            self.assertEqual(len(discovered), 2)
            names = [d.name for d in discovered]
            self.assertIn("mycli:init", names)
            self.assertIn("mycli:deploy", names)
            self.assertNotIn("mycli:options", names)

    def test_discover_from_cli_empty_or_error(self):
        # 1. Exception in subprocess
        with patch("subprocess.run", side_effect=RuntimeError("exec error")):
            self.assertEqual(self.registry.discover_from_cli("broken"), [])

        # 2. Empty help text
        mock_proc = MagicMock(stdout="", stderr="")
        with patch("subprocess.run", return_value=mock_proc):
            self.assertEqual(self.registry.discover_from_cli("empty"), [])

    def test_discover_from_openapi(self):
        spec = {
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "listUsers",
                        "summary": "List all users",
                        "parameters": [
                            {"name": "limit", "in": "query", "schema": {"type": "integer"}, "required": True},
                        ],
                    },
                    "head": {  # Non-supported HTTP method ignored
                        "summary": "Head check",
                    },
                },
            },
        }
        discovered = self.registry.discover_from_openapi(spec)
        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0].name, "api:listUsers")
        self.assertEqual(discovered[0].endpoint, "GET https://api.example.com/users")
        self.assertEqual(discovered[0].parameters[0].name, "limit")
        self.assertTrue(discovered[0].parameters[0].required)

    def test_discover_from_openapi_no_servers_and_default_operation_id(self):
        spec = {
            "paths": {
                "/items": {
                    "post": {
                        "description": "Create item",
                    },
                },
            },
        }
        discovered = self.registry.discover_from_openapi(spec)
        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0].name, "api:post__items")
        self.assertEqual(discovered[0].endpoint, "POST /items")

    def test_builtins_registered(self):
        self.assertIsNotNone(self.registry.get("shell:run"))
        self.assertIsNotNone(self.registry.get("git:status"))
        self.assertIsNotNone(self.registry.get("file:read"))

    def test_persistence_save_and_load_roundtrip(self):
        self.registry.register(
            "custom_tool",
            "Custom description",
            tool_type=ToolType.CUSTOM,
            parameters=[ToolParameter(name="p1", description="param 1", type="string", required=True)],
            tags=["tag1", "tag2"],
        )
        # Load in a new registry instance
        new_reg = ToolRegistry(persist_path=self._path)
        tool = new_reg.get("custom_tool")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.description, "Custom description")
        self.assertEqual(tool.tool_type, ToolType.CUSTOM)
        self.assertEqual(len(tool.parameters), 1)
        self.assertEqual(tool.parameters[0].name, "p1")
        self.assertTrue(tool.parameters[0].required)

    def test_load_nonexistent_or_corrupted(self):
        # 1. Nonexistent path
        reg = ToolRegistry(persist_path=str(Path(self._tmpdir) / "nonexistent.yaml"))
        self.assertGreater(len(reg._tools), 0)  # Has builtins

        # 2. Corrupted YAML file
        corrupt_path = Path(self._tmpdir) / "corrupt.yaml"
        corrupt_path.write_text("invalid : [ yaml : content")
        reg_corrupt = ToolRegistry(persist_path=str(corrupt_path))
        self.assertGreater(len(reg_corrupt._tools), 0)

    def test_load_unknown_tool_type_falls_back_to_custom(self):
        yaml_content = """
unknown_tool:
  description: "Unknown tool"
  tool_type: "completely_invalid_type"
  command_template: ""
  tags: []
"""
        type_test_path = Path(self._tmpdir) / "type_test.yaml"
        type_test_path.write_text(yaml_content)
        reg = ToolRegistry(persist_path=str(type_test_path))
        tool = reg.get("unknown_tool")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.tool_type, ToolType.CUSTOM)


if __name__ == "__main__":
    unittest.main()
