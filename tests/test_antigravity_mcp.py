# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Automated test suite for Antigravity MCP integration (R4).

Validates:
1. MCP JSON-RPC protocol compliance (initialize, tools/list, tools/call)
2. Stdio transport communication without hanging (non-blocking selector, strict timeouts)
3. Fallback resilience when optional FastMCP SDK is absent (MEKONG_FORCE_MCP_FALLBACK=1)
4. Manifest integrity across workspace and global plugin locations
5. Command Fabric mode tool exposition and execution (--fabric)
6. Zero regressions against existing Antigravity test suites and healthcheck
"""

from __future__ import annotations

import json
import os
import selectors
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Generator

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = PROJECT_ROOT / ".agents"
WORKSPACE_MCP_CONFIG = AGENTS_DIR / "mcp_config.json"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
MCP_SERVER_SCRIPT = SCRIPTS_DIR / "mcp_server.py"

GLOBAL_CONFIG_DIR = Path.home() / ".gemini" / "config"
GLOBAL_PLUGIN_MCP_CONFIG = GLOBAL_CONFIG_DIR / "plugins" / "mekong-cli" / "mcp_config.json"
AGY_PLUGIN_MCP_CONFIG = Path.home() / ".gemini" / "antigravity-cli" / "plugins" / "mekong-cli" / "mcp_config.json"

PROTOCOL_VERSION = "2024-11-05"
TIMEOUT_SECONDS = 5.0

EXPECTED_14_CORE_TOOLS = {
    # Memory
    "mekong_memory_store",
    "mekong_memory_recall",
    "mekong_memory_search",
    # Plans
    "mekong_plan_create",
    "mekong_plan_update",
    "mekong_plan_get",
    # Tasks
    "mekong_task_create",
    "mekong_task_update",
    "mekong_task_list",
    # Agents
    "mekong_agent_list",
    "mekong_agent_info",
    "mekong_agent_route",
    # System
    "mekong_status",
    "mekong_cost_estimate",
}


# =============================================================================
# Zero-Hang Stdio JSON-RPC Client Helper
# =============================================================================

class JsonRpcStdioClient:
    """Robust, non-blocking stdio JSON-RPC process manager with strict timeouts."""

    def __init__(self, cmd: list[str], env: dict[str, str] | None = None) -> None:
        self.cmd = cmd
        self.env = env or os.environ.copy()
        self.proc: subprocess.Popen[str] | None = None
        self.selector: selectors.DefaultSelector | None = None
        self._next_id = 1
        self.received_notifications: list[dict[str, Any]] = []

    def start(self) -> None:
        """Spawn the process with line buffering and unbuffered stdio."""
        run_env = self.env.copy()
        run_env["PYTHONUNBUFFERED"] = "1"
        run_env["PYTHONIOENCODING"] = "utf-8"
        run_env["PYTHONPATH"] = str(PROJECT_ROOT)

        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            env=run_env,
            text=True,
            bufsize=1,
        )
        assert self.proc.stdout is not None
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.proc.stdout, selectors.EVENT_READ)

    def write_message(self, msg: dict[str, Any] | str) -> None:
        """Write newline-delimited JSON-RPC message to stdin."""
        assert self.proc is not None and self.proc.stdin is not None
        if isinstance(msg, dict):
            line = json.dumps(msg, separators=(",", ":")) + "\n"
        else:
            line = msg if msg.endswith("\n") else (msg + "\n")
        self.proc.stdin.write(line)
        self.proc.stdin.flush()

    def read_message(self, timeout: float = TIMEOUT_SECONDS) -> dict[str, Any]:
        """Read a single JSON-RPC message from stdout with strict deadline."""
        assert self.selector is not None and self.proc is not None and self.proc.stdout is not None
        events = self.selector.select(timeout=timeout)
        if not events:
            if self.proc.poll() is not None:
                err = self.proc.stderr.read() if self.proc.stderr else ""
                raise RuntimeError(
                    f"Server process terminated prematurely ({self.proc.returncode}): {err}"
                )
            raise TimeoutError(f"Timed out waiting for JSON response after {timeout}s")

        line = self.proc.stdout.readline()
        if not line:
            err = self.proc.stderr.read() if self.proc.stderr else ""
            raise EOFError(f"Child stdout closed unexpectedly. Stderr: {err}")
        return json.loads(line.strip())

    def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float = TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        """Send JSON-RPC request and wait for matched response ID."""
        req_id = self._next_id
        self._next_id += 1
        msg: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            msg["params"] = params

        self.write_message(msg)
        start_time = time.monotonic()
        while time.monotonic() - start_time < timeout:
            remaining = max(0.1, timeout - (time.monotonic() - start_time))
            resp = self.read_message(timeout=remaining)
            if resp.get("id") == req_id:
                return resp
            self.received_notifications.append(resp)

        raise TimeoutError(
            f"Timed out waiting for response to request id={req_id} ({method}) after {timeout}s"
        )

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        """Send JSON-RPC notification (no id, no response expected)."""
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self.write_message(msg)

    def perform_handshake(self) -> dict[str, Any]:
        """Execute standard MCP initialize handshake."""
        init_resp = self.call(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test-antigravity", "version": "1.0.0"},
            },
        )
        assert "result" in init_resp, f"Handshake failed: {init_resp.get('error')}"
        self.notify("notifications/initialized")
        time.sleep(0.1)
        return init_resp["result"]

    def close(self) -> None:
        """Safely close selectors, stream handles, and terminate subprocess."""
        if self.selector:
            try:
                self.selector.close()
            except Exception:
                pass
            self.selector = None

        if self.proc:
            if self.proc.poll() is None:
                if self.proc.stdin:
                    try:
                        self.proc.stdin.close()
                    except Exception:
                        pass
                try:
                    self.proc.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    self.proc.terminate()
                    try:
                        self.proc.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        self.proc.kill()
                        self.proc.wait(timeout=1.0)

    def __enter__(self) -> JsonRpcStdioClient:
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


# =============================================================================
# Pytest Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def stdio_client() -> Generator[JsonRpcStdioClient, None, None]:
    """Provide a running standard MCP server client over stdio with handshake completed."""
    client = JsonRpcStdioClient([sys.executable, str(MCP_SERVER_SCRIPT)])
    client.start()
    client.perform_handshake()
    try:
        yield client
    finally:
        client.close()


@pytest.fixture(scope="module")
def fallback_stdio_client() -> Generator[JsonRpcStdioClient, None, None]:
    """Provide an MCP server client running with forced pure-Python fallback with handshake completed."""
    env = os.environ.copy()
    env["MEKONG_FORCE_MCP_FALLBACK"] = "1"
    client = JsonRpcStdioClient([sys.executable, str(MCP_SERVER_SCRIPT)], env=env)
    client.start()
    client.perform_handshake()
    try:
        yield client
    finally:
        client.close()


@pytest.fixture(scope="module")
def fabric_stdio_client() -> Generator[JsonRpcStdioClient, None, None]:
    """Provide an MCP server client running in Command Fabric mode (--fabric) with handshake completed."""
    client = JsonRpcStdioClient([sys.executable, str(MCP_SERVER_SCRIPT), "--fabric"])
    client.start()
    client.perform_handshake()
    try:
        yield client
    finally:
        client.close()


# =============================================================================
# Test Class 1: Manifest Integrity (R2)
# =============================================================================

class TestMcpManifestIntegrity:
    """Verify MCP manifest existence, schema conformity, and cross-target parity."""

    def test_workspace_mcp_config_exists_and_valid_json(self) -> None:
        """Verify .agents/mcp_config.json exists and parses cleanly."""
        assert WORKSPACE_MCP_CONFIG.exists(), f"Missing {WORKSPACE_MCP_CONFIG}"
        data = json.loads(WORKSPACE_MCP_CONFIG.read_text(encoding="utf-8"))
        assert isinstance(data, dict), "Root of mcp_config.json must be a JSON object"
        assert "mcpServers" in data, "mcp_config.json must contain 'mcpServers' object"

    def test_mcp_config_schema_conformance(self) -> None:
        """Verify server definitions in workspace manifest."""
        data = json.loads(WORKSPACE_MCP_CONFIG.read_text(encoding="utf-8"))
        servers = data.get("mcpServers", {})

        # mekong-core definition
        assert "mekong-core" in servers, "Missing 'mekong-core' in mcpServers"
        core = servers["mekong-core"]
        assert "command" in core and isinstance(core["command"], str)
        assert "args" in core and isinstance(core["args"], list)
        assert any("mcp_server.py" in str(arg) for arg in core["args"])
        assert "env" in core and isinstance(core["env"], dict)
        assert core["env"].get("PYTHONUNBUFFERED") == "1"

        # mekong-fabric definition
        assert "mekong-fabric" in servers, "Missing 'mekong-fabric' in mcpServers"
        fabric = servers["mekong-fabric"]
        assert "command" in fabric and isinstance(fabric["command"], str)
        assert "args" in fabric and isinstance(fabric["args"], list)
        assert any("mcp_server.py" in str(arg) for arg in fabric["args"])
        assert "--fabric" in fabric["args"]
        assert "env" in fabric and isinstance(fabric["env"], dict)
        assert fabric["env"].get("PYTHONUNBUFFERED") == "1"

    def test_global_plugin_mcp_configs_exist_and_synced(self) -> None:
        """Verify manifests are synchronized to global plugin directories."""
        for target in [GLOBAL_PLUGIN_MCP_CONFIG, AGY_PLUGIN_MCP_CONFIG]:
            assert target.exists(), f"Missing plugin MCP config at: {target}"
            data = json.loads(target.read_text(encoding="utf-8"))
            assert "mcpServers" in data, f"{target} missing 'mcpServers'"
            assert "mekong-core" in data["mcpServers"], f"{target} missing 'mekong-core'"
            assert "mekong-fabric" in data["mcpServers"], f"{target} missing 'mekong-fabric'"

    def test_manifest_server_executable_paths_resolve(self) -> None:
        """Verify scripts/mcp_server.py is present and executable, and command resolves."""
        assert MCP_SERVER_SCRIPT.exists(), f"Missing {MCP_SERVER_SCRIPT}"
        assert os.access(MCP_SERVER_SCRIPT, os.R_OK), f"{MCP_SERVER_SCRIPT} is not readable"
        assert os.access(MCP_SERVER_SCRIPT, os.X_OK), f"{MCP_SERVER_SCRIPT} is not executable"

        data = json.loads(WORKSPACE_MCP_CONFIG.read_text(encoding="utf-8"))
        for sname, sdef in data.get("mcpServers", {}).items():
            cmd = sdef.get("command", "")
            resolved = shutil.which(cmd)
            assert resolved is not None, f"Command '{cmd}' for '{sname}' cannot be resolved on PATH"


# =============================================================================
# Test Class 2: Protocol Compliance (R4)
# =============================================================================

class TestMcpProtocolCompliance:
    """Verify JSON-RPC 2.0 handshake, tools listing, and tools execution."""

    def test_initialize_handshake(self) -> None:
        """Test initialize handshake returns protocol version and server info."""
        with JsonRpcStdioClient([sys.executable, str(MCP_SERVER_SCRIPT)]) as client:
            result = client.perform_handshake()
            assert result.get("protocolVersion") == PROTOCOL_VERSION
            assert "capabilities" in result
            assert "tools" in result["capabilities"]
            assert "serverInfo" in result
            assert result["serverInfo"].get("name") == "mekong-core"
            assert "version" in result["serverInfo"]

    def test_notifications_initialized_accepted(self, stdio_client: JsonRpcStdioClient) -> None:
        """Verify sending notifications/initialized is cleanly accepted."""
        stdio_client.notify("notifications/initialized")
        # Ensure server accepts subsequent request cleanly
        resp = stdio_client.call("ping")
        assert "result" in resp or "error" not in resp

    def test_tools_list_returns_14_core_tools(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test tools/list contains all 14 required core tools."""
        resp = stdio_client.call("tools/list")
        assert "result" in resp, f"tools/list error: {resp.get('error')}"
        tools = resp["result"].get("tools", [])
        tool_names = {t["name"] for t in tools}

        missing = EXPECTED_14_CORE_TOOLS - tool_names
        assert not missing, f"tools/list missing core tools: {missing}"

    def test_all_14_tools_have_valid_input_schemas(self, stdio_client: JsonRpcStdioClient) -> None:
        """Verify each of the 14 core tools provides valid JSON Schema for arguments."""
        resp = stdio_client.call("tools/list")
        tools = resp["result"].get("tools", [])
        matched = 0
        for tool in tools:
            name = tool.get("name")
            if name in EXPECTED_14_CORE_TOOLS:
                matched += 1
                assert tool.get("description"), f"Tool {name} missing description"
                schema = tool.get("inputSchema", {})
                assert schema.get("type") == "object", f"Tool {name} inputSchema must be type: object"
                assert "properties" in schema, f"Tool {name} inputSchema must contain properties"
                assert isinstance(schema.get("required", []), list), f"Tool {name} required must be list"
        assert matched == len(EXPECTED_14_CORE_TOOLS)

    def test_tools_call_mekong_status(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test invoking mekong_status returns health/version info."""
        resp = stdio_client.call("tools/call", {"name": "mekong_status", "arguments": {}})
        assert "result" in resp, f"mekong_status failed: {resp.get('error')}"
        assert resp["result"].get("isError") is False
        content = resp["result"].get("content", [])
        assert len(content) > 0
        text = content[0].get("text", "")
        data = json.loads(text)
        assert data.get("ok") is True
        assert "status" in data.get("data", {})
        assert data["data"]["status"] == "HEALTHY"

    def test_tools_call_memory_store_and_recall(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test persisting memory and recalling it by key."""
        test_key = "test_mcp_verification_key"
        test_val = "mcp_verification_payload_42"

        store_resp = stdio_client.call(
            "tools/call",
            {"name": "mekong_memory_store", "arguments": {"key": test_key, "value": test_val}},
        )
        assert "result" in store_resp
        assert store_resp["result"].get("isError") is False
        store_data = json.loads(store_resp["result"]["content"][0]["text"])
        assert store_data.get("ok") is True

        recall_resp = stdio_client.call(
            "tools/call",
            {"name": "mekong_memory_recall", "arguments": {"key": test_key}},
        )
        assert "result" in recall_resp
        assert recall_resp["result"].get("isError") is False
        recall_data = json.loads(recall_resp["result"]["content"][0]["text"])
        assert recall_data.get("ok") is True
        assert recall_data["data"].get("value") == test_val

    def test_tools_call_memory_search(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test searching memory entries."""
        resp = stdio_client.call(
            "tools/call",
            {"name": "mekong_memory_search", "arguments": {"query": "test", "limit": 5}},
        )
        assert "result" in resp
        assert resp["result"].get("isError") is False
        data = json.loads(resp["result"]["content"][0]["text"])
        assert data.get("ok") is True
        assert "results" in data.get("data", {})

    def test_tools_call_task_lifecycle(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test task creation, listing, and status update."""
        create_resp = stdio_client.call(
            "tools/call",
            {"name": "mekong_task_create", "arguments": {"subject": "Automated Protocol Task"}},
        )
        assert "result" in create_resp
        assert create_resp["result"].get("isError") is False
        create_data = json.loads(create_resp["result"]["content"][0]["text"])
        assert create_data.get("ok") is True
        task_id = create_data["data"]["task"]["task_id"]
        assert task_id

        list_resp = stdio_client.call("tools/call", {"name": "mekong_task_list", "arguments": {}})
        assert "result" in list_resp
        assert list_resp["result"].get("isError") is False
        list_data = json.loads(list_resp["result"]["content"][0]["text"])
        assert list_data.get("ok") is True

        update_resp = stdio_client.call(
            "tools/call",
            {"name": "mekong_task_update", "arguments": {"task_id": task_id, "status": "in-progress"}},
        )
        assert "result" in update_resp
        assert update_resp["result"].get("isError") is False
        update_data = json.loads(update_resp["result"]["content"][0]["text"])
        assert update_data.get("ok") is True
        assert update_data["data"]["task"]["status"] == "in-progress"

    def test_tools_call_plan_lifecycle(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test plan creation and plan retrieval."""
        create_resp = stdio_client.call(
            "tools/call",
            {"name": "mekong_plan_create", "arguments": {"goal": "MCP Test Plan Goal"}},
        )
        assert "result" in create_resp
        assert create_resp["result"].get("isError") is False
        create_data = json.loads(create_resp["result"]["content"][0]["text"])
        assert create_data.get("ok") is True
        plan_id = create_data["data"]["plan_id"]
        assert plan_id

        get_resp = stdio_client.call(
            "tools/call",
            {"name": "mekong_plan_get", "arguments": {"plan_id": plan_id}},
        )
        assert "result" in get_resp
        assert get_resp["result"].get("isError") is False
        get_data = json.loads(get_resp["result"]["content"][0]["text"])
        assert get_data.get("ok") is True
        assert get_data["data"]["plan_id"] == plan_id

    def test_tools_call_agent_list_and_info(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test listing registered agents and querying agent metadata."""
        list_resp = stdio_client.call("tools/call", {"name": "mekong_agent_list", "arguments": {}})
        assert "result" in list_resp
        assert list_resp["result"].get("isError") is False
        list_data = json.loads(list_resp["result"]["content"][0]["text"])
        assert list_data.get("ok") is True
        agents = list_data["data"]["agents"]
        assert len(agents) >= 15
        agent_names = {a["name"] for a in agents}
        assert "ceo" in agent_names
        assert "cfo" in agent_names
        assert "cto" in agent_names

        info_resp = stdio_client.call(
            "tools/call",
            {"name": "mekong_agent_info", "arguments": {"name": "ceo"}},
        )
        assert "result" in info_resp
        assert info_resp["result"].get("isError") is False
        info_data = json.loads(info_resp["result"]["content"][0]["text"])
        assert info_data.get("ok") is True
        assert info_data["data"]["name"] == "ceo"

    def test_tools_call_agent_route(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test task classifier agent routing."""
        resp = stdio_client.call(
            "tools/call",
            {"name": "mekong_agent_route", "arguments": {"goal": "Calculate corporate tax and VAS balance sheet"}},
        )
        assert "result" in resp
        assert resp["result"].get("isError") is False
        data = json.loads(resp["result"]["content"][0]["text"])
        assert data.get("ok") is True
        assert "assigned_agent" in data["data"]

    def test_tools_call_cost_estimate(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test token usage and MCU cost prediction."""
        resp = stdio_client.call(
            "tools/call",
            {
                "name": "mekong_cost_estimate",
                "arguments": {"goal": "Build payment processing integration", "model_id": "claude-sonnet-4-6"},
            },
        )
        assert "result" in resp
        assert resp["result"].get("isError") is False
        data = json.loads(resp["result"]["content"][0]["text"])
        assert data.get("ok") is True
        assert "mcu_required" in data["data"]
        assert "total_usd" in data["data"]


# =============================================================================
# Test Class 3: Fallback Resilience (R4)
# =============================================================================

class TestMcpFallbackResilience:
    """Verify pure-Python JSON-RPC stdio fallback when FastMCP is unavailable."""

    def test_fallback_server_starts_without_fastmcp(self, fallback_stdio_client: JsonRpcStdioClient) -> None:
        """Verify fallback server launches cleanly without crash."""
        assert fallback_stdio_client.proc is not None
        assert fallback_stdio_client.proc.poll() is None

    def test_fallback_initialize_handshake(self) -> None:
        """Verify fallback server responds to JSON-RPC initialize handshake."""
        env = os.environ.copy()
        env["MEKONG_FORCE_MCP_FALLBACK"] = "1"
        with JsonRpcStdioClient([sys.executable, str(MCP_SERVER_SCRIPT)], env=env) as client:
            result = client.perform_handshake()
            assert result.get("protocolVersion") == PROTOCOL_VERSION
            assert result.get("serverInfo", {}).get("name") == "mekong-core"
            assert "capabilities" in result
            assert "tools" in result["capabilities"]

    def test_fallback_notifications_initialized(self, fallback_stdio_client: JsonRpcStdioClient) -> None:
        """Verify fallback server handles notifications/initialized."""
        fallback_stdio_client.notify("notifications/initialized")
        resp = fallback_stdio_client.call("ping")
        assert "result" in resp

    def test_fallback_tools_list_parity(self, fallback_stdio_client: JsonRpcStdioClient) -> None:
        """Verify fallback server lists all 14 core tools without FastMCP SDK."""
        resp = fallback_stdio_client.call("tools/list")
        assert "result" in resp
        tools = resp["result"].get("tools", [])
        tool_names = {t["name"] for t in tools}
        missing = EXPECTED_14_CORE_TOOLS - tool_names
        assert not missing, f"Fallback server missing tools: {missing}"

    def test_fallback_tools_call_execution(self, fallback_stdio_client: JsonRpcStdioClient) -> None:
        """Verify fallback server handles tools/call cleanly across key tools."""
        for tool_name, args in [
            ("mekong_status", {}),
            ("mekong_agent_list", {}),
            ("mekong_memory_store", {"key": "fallback_k", "value": "fallback_v"}),
            ("mekong_memory_recall", {"key": "fallback_k"}),
        ]:
            resp = fallback_stdio_client.call("tools/call", {"name": tool_name, "arguments": args})
            assert "result" in resp, f"Tool {tool_name} failed: {resp.get('error')}"
            assert resp["result"].get("isError") is False
            content = resp["result"].get("content", [])
            assert len(content) > 0
            data = json.loads(content[0]["text"])
            assert data.get("ok") is True

    def test_fallback_graceful_shutdown_on_eof(self) -> None:
        """Verify fallback server exits cleanly with code 0 on stdin close."""
        env = os.environ.copy()
        env["MEKONG_FORCE_MCP_FALLBACK"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        proc = subprocess.Popen(
            [sys.executable, str(MCP_SERVER_SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            env=env,
        )
        assert proc.poll() is None
        assert proc.stdin is not None
        proc.stdin.close()
        try:
            exit_code = proc.wait(timeout=2.0)
            assert exit_code == 0
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("Fallback MCP server did not exit within 2.0s of stdin EOF")


# =============================================================================
# Test Class 4: Stdio Hang Prevention & Edge Cases (R4)
# =============================================================================

class TestMcpTransportHangPrevention:
    """Stress and edge-case testing to guarantee zero hangs over pipes."""

    def test_rapid_sequential_requests(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test sending 10 consecutive requests in rapid succession over same pipe."""
        for _ in range(10):
            resp = stdio_client.call("tools/call", {"name": "mekong_status", "arguments": {}})
            assert "result" in resp
            assert resp["result"].get("isError") is False

    def test_malformed_json_handling_does_not_hang(self) -> None:
        """Verify sending invalid JSON string does not crash or deadlock server."""
        with JsonRpcStdioClient([sys.executable, str(MCP_SERVER_SCRIPT)]) as client:
            assert client.proc is not None and client.proc.stdin is not None
            # Write unparseable line
            client.proc.stdin.write("MALFORMED_NON_JSON_LINE\n")
            client.proc.stdin.flush()
            time.sleep(0.1)

            # Assert server did not crash
            assert client.proc.poll() is None

            # Assert subsequent valid request still succeeds over same pipe
            resp = client.call("initialize", {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test-recovery", "version": "1.0.0"},
            })
            assert "result" in resp
            assert resp["result"].get("protocolVersion") == PROTOCOL_VERSION

    def test_content_length_header_tolerance(self) -> None:
        """Verify HTTP-style Content-Length header is parsed without blocking."""
        env = os.environ.copy()
        env["MEKONG_FORCE_MCP_FALLBACK"] = "1"
        with JsonRpcStdioClient([sys.executable, str(MCP_SERVER_SCRIPT)], env=env) as client:
            assert client.proc is not None and client.proc.stdin is not None
            body = json.dumps({
                "jsonrpc": "2.0",
                "id": 88,
                "method": "initialize",
                "params": {"protocolVersion": PROTOCOL_VERSION},
            })
            framed_msg = f"Content-Length: {len(body)}\r\n\r\n{body}"
            client.proc.stdin.write(framed_msg)
            client.proc.stdin.flush()

            resp = client.read_message(timeout=TIMEOUT_SECONDS)
            assert resp.get("id") == 88
            assert "result" in resp
            assert resp["result"].get("protocolVersion") == PROTOCOL_VERSION

    def test_unknown_tool_call_returns_error_cleanly(self, stdio_client: JsonRpcStdioClient) -> None:
        """Verify calling non-existent tool returns error cleanly without hanging."""
        resp = stdio_client.call(
            "tools/call",
            {"name": "non_existent_tool_xyz", "arguments": {}},
        )
        assert resp.get("error") is not None or resp.get("result", {}).get("isError") is True

    def test_clean_exit_on_stdin_close(self) -> None:
        """Verify server cleanly terminates when client closes stdin pipe."""
        proc = subprocess.Popen(
            [sys.executable, str(MCP_SERVER_SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        assert proc.poll() is None
        assert proc.stdin is not None
        proc.stdin.close()
        try:
            proc.wait(timeout=2.0)
            assert proc.poll() is not None
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("Server did not exit within 2.0s of stdin close")

    def test_clean_exit_on_sigterm(self) -> None:
        """Verify server subprocess cleanly terminates on SIGTERM within 2 seconds."""
        proc = subprocess.Popen(
            [sys.executable, str(MCP_SERVER_SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        time.sleep(0.2)
        assert proc.poll() is None
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=2.0)
            assert proc.poll() is not None
        except subprocess.TimeoutExpired:
            proc.kill()
            pytest.fail("MCP server did not exit within 2.0s of receiving SIGTERM")


# =============================================================================
# Test Class 5: Command Fabric Mode (R1 & R2)
# =============================================================================

class TestMcpCommandFabricMode:
    """Verify Command Fabric mode exposes catalog tools and executes them."""

    def test_command_fabric_server_initializes(self) -> None:
        """Verify Command Fabric server initializes with mekong-fabric serverInfo."""
        with JsonRpcStdioClient([sys.executable, str(MCP_SERVER_SCRIPT), "--fabric"]) as client:
            result = client.perform_handshake()
            assert result.get("protocolVersion") == PROTOCOL_VERSION
            assert result.get("serverInfo", {}).get("name") == "mekong-fabric"

    def test_command_fabric_tools_list_count(self, fabric_stdio_client: JsonRpcStdioClient) -> None:
        """Verify Command Fabric mode exposes catalog tools (count > 250)."""
        resp = fabric_stdio_client.call("tools/list")
        assert "result" in resp
        tools = resp["result"].get("tools", [])
        assert len(tools) > 250, f"Expected > 250 fabric tools, got {len(tools)}"

        tool_names = {t["name"] for t in tools}
        for expected in ["mekong_cook", "mekong_binh_phap", "mekong_deploy", "mekong_plan", "mekong_mk_cfo"]:
            assert expected in tool_names, f"Missing fabric tool: {expected}"

    def test_command_fabric_tool_call_execution(self, fabric_stdio_client: JsonRpcStdioClient) -> None:
        """Verify invoking a Command Fabric tool executes and returns valid response."""
        resp = fabric_stdio_client.call(
            "tools/call",
            {"name": "mekong_binh_phap", "arguments": {"arguments": "--help"}},
        )
        assert "result" in resp
        assert resp["result"].get("isError") is False
        content = resp["result"].get("content", [])
        assert len(content) > 0
        data = json.loads(content[0]["text"])
        assert data.get("ok") is True
        assert data.get("data", {}).get("command") == "binh-phap"


# =============================================================================
# Test Class 6: Non-Regression & Health Integrity (R4)
# =============================================================================

class TestMcpNonRegression:
    """Verify zero regressions against existing Antigravity sync and healthcheck scripts."""

    def test_sync_antigravity_verify_remains_green(self) -> None:
        """Ensure scripts/sync_antigravity.py --verify exits 0."""
        res = subprocess.run(
            [sys.executable, "scripts/sync_antigravity.py", "--verify"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=30,
        )
        assert res.returncode == 0, f"Sync verify failed: {res.stderr}\n{res.stdout}"
        assert "Verification passed" in res.stdout

    def test_antigravity_healthcheck_remains_healthy(self) -> None:
        """Ensure scripts/antigravity_healthcheck.py exits 0 with Status: HEALTHY."""
        res = subprocess.run(
            [sys.executable, "scripts/antigravity_healthcheck.py"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=90,
        )
        assert res.returncode == 0, f"Healthcheck failed: {res.stderr}\n{res.stdout}"
        assert "Status: HEALTHY" in res.stdout
