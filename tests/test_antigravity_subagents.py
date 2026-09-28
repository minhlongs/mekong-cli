# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Automated test suite for Antigravity dynamic subagents integration (R4).

Validates:
1. Subagent payload generation across all 25 domain agents (src.core.subagent_dispatch)
2. Schema conformance for define_subagent, invoke_subagent, and context_engineering
3. Role validation, error handling, and fuzzy suggestions on invalid agent roles
4. CLI agent spawn command (mekong agent spawn) in live, dry-run, and JSON modes
5. MCP dynamic subagent dispatch bridge (mekong_subagent_dispatch) over stdio JSON-RPC
6. Pure-Python fallback stdio server compatibility (MEKONG_FORCE_MCP_FALLBACK=1)
7. Global plugin subagent replication and byte-for-byte SHA-256 parity
8. Non-regression of scripts/sync_antigravity.py --verify and scripts/antigravity_healthcheck.py
"""

from __future__ import annotations

import hashlib
import json
import os
import selectors
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Generator

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = PROJECT_ROOT / ".agents"
LOCAL_SUBAGENTS_DIR = AGENTS_DIR / "subagents"
LOCAL_DEFINITIONS_DIR = LOCAL_SUBAGENTS_DIR / "definitions"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
MCP_SERVER_SCRIPT = SCRIPTS_DIR / "mcp_server.py"

GLOBAL_CONFIG_DIR = Path.home() / ".gemini" / "config"
GLOBAL_PLUGIN_DIR = GLOBAL_CONFIG_DIR / "plugins" / "mekong-cli" / "subagents"
AGY_PLUGIN_DIR = Path.home() / ".gemini" / "antigravity-cli" / "plugins" / "mekong-cli" / "subagents"

PROTOCOL_VERSION = "2024-11-05"
TIMEOUT_SECONDS = 5.0

ALL_25_SUBAGENT_IDS: tuple[str, ...] = (
    "sun-tzu",
    "ceo",
    "cto",
    "cmo",
    "coo",
    "cfo",
    "cso",
    "ae",
    "pm",
    "eng",
    "ops",
    "tester",
    "planner",
    "brainstormer",
    "code-reviewer",
    "code-simplifier",
    "debugger",
    "docs-manager",
    "fullstack-developer",
    "git-manager",
    "journal-writer",
    "kongming",
    "project-manager",
    "researcher",
    "ui-ux-designer",
)


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
                "clientInfo": {"name": "test-antigravity-subagents", "version": "1.0.0"},
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


def run_cli_agent_spawn(
    *args: str,
    use_mekong_bin: bool = False,
    timeout: float = 30.0,
) -> subprocess.CompletedProcess[str]:
    """Execute mekong agent spawn via sys.executable module or direct mekong binary."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    if use_mekong_bin and shutil.which("mekong"):
        cmd = ["mekong", "agent", "spawn", *args]
    else:
        cmd = [sys.executable, "-m", "src.main", "agent", "spawn", *args]

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=timeout,
    )


def compute_sha256(path: Path) -> str:
    """Compute hex SHA-256 digest of file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


# =============================================================================
# Test Class 1: Subagent Payload Generation & Schema Conformance (R1 & R2)
# =============================================================================

class TestSubagentPayloadGeneration:
    """Verify subagent dispatch engine generates compliant payloads for all 25 agents."""

    @pytest.mark.parametrize("agent_id", ALL_25_SUBAGENT_IDS)
    def test_all_25_domain_subagents_generate_valid_payloads(self, agent_id: str) -> None:
        """Test each registered agent generates a complete, valid dispatch payload."""
        from src.core.subagent_dispatch import build_subagent_dispatch_payload

        res = build_subagent_dispatch_payload(
            role=agent_id,
            task="Perform operational review and propose execution plan.",
            project_root=PROJECT_ROOT,
        )
        assert res.get("ok") is True, f"Failed payload generation for {agent_id}: {res.get('error')}"
        data = res.get("data", {})
        assert data.get("role") == agent_id
        assert data.get("name")
        assert data.get("model_tier") in ("pro", "flash", "inherit")
        assert "define_subagent_payload" in data
        assert "invoke_subagent_payload" in data
        assert "context_engineering" in data

    @pytest.mark.parametrize("agent_id", ALL_25_SUBAGENT_IDS)
    def test_define_subagent_payload_schema_conformance(self, agent_id: str) -> None:
        """Test define_subagent payload matches Antigravity dynamic subagent tool schema."""
        from src.core.subagent_dispatch import build_subagent_dispatch_payload

        res = build_subagent_dispatch_payload(role=agent_id, task="Architecture audit")
        assert res.get("ok") is True
        def_payload = res["data"]["define_subagent_payload"]

        # Validate name is non-empty and valid identifier
        name = def_payload.get("name")
        assert isinstance(name, str) and len(name) > 0
        assert name.isidentifier(), f"Subagent name '{name}' must be a valid identifier"

        # Validate description
        desc = def_payload.get("description")
        assert isinstance(desc, str) and len(desc) > 0

        # Validate system prompt completeness
        prompt = def_payload.get("system_prompt")
        assert isinstance(prompt, str) and len(prompt) >= 50
        assert (
            agent_id.lower() in prompt.lower()
            or name.lower() in prompt.lower()
            or agent_id.replace("-", " ").lower() in prompt.lower()
        )

        # Validate boolean capability flags
        assert isinstance(def_payload.get("enable_write_tools"), bool)
        assert isinstance(def_payload.get("enable_subagent_tools"), bool)
        assert def_payload.get("enable_mcp_tools") is True

    @pytest.mark.parametrize("agent_id", ALL_25_SUBAGENT_IDS)
    def test_invoke_subagent_payload_schema_conformance(self, agent_id: str) -> None:
        """Test invoke_subagent payload matches Antigravity invocation schema."""
        from src.core.subagent_dispatch import build_subagent_dispatch_payload

        sample_task = "Analyze market expansion opportunities for Q4"
        res = build_subagent_dispatch_payload(role=agent_id, task=sample_task)
        assert res.get("ok") is True
        inv_payload = res["data"]["invoke_subagent_payload"]

        expected_var_name = agent_id.replace("-", "_")
        assert inv_payload.get("subagent_name") == expected_var_name
        assert inv_payload.get("task") == sample_task
        assert inv_payload.get("goal") == sample_task

    @pytest.mark.parametrize("agent_id", ALL_25_SUBAGENT_IDS)
    def test_context_engineering_schema_conformance(self, agent_id: str) -> None:
        """Test HARNESS.md context engineering constraints and guardrails."""
        from src.core.subagent_dispatch import (
            CONTEXT_CEILING,
            HIGH_RISK_GATES,
            build_subagent_dispatch_payload,
        )

        res = build_subagent_dispatch_payload(role=agent_id, task="Validate constraints")
        assert res.get("ok") is True
        ctx = res["data"]["context_engineering"]

        assert ctx.get("role") == agent_id
        assert isinstance(ctx.get("context_budget"), int)
        assert 0 < ctx["context_budget"] <= CONTEXT_CEILING
        assert ctx.get("total_context_ceiling") == CONTEXT_CEILING
        assert ctx.get("model_tier") in ("pro", "flash", "inherit")

        # Allowed tools
        tools = ctx.get("tool_allowlist")
        assert isinstance(tools, list) and len(tools) > 0
        assert ctx.get("allowed_tools") == tools

        # High-risk gates and escalation
        assert isinstance(ctx.get("ceo_override"), bool)
        assert ctx.get("can_override") == ctx.get("ceo_override")
        assert ctx.get("high_risk_gates") == HIGH_RISK_GATES
        assert isinstance(ctx.get("escalation_path"), dict)
        assert len(ctx["escalation_path"]) >= 5
        assert "sop_reference" in ctx and len(ctx["sop_reference"]) > 0

    def test_rejection_of_unknown_roles_with_suggestions_and_list(self) -> None:
        """Test rejection of unknown roles returns fuzzy suggestions and full role list."""
        from src.core.subagent_dispatch import VALID_SUBAGENTS, build_subagent_dispatch_payload

        # Case 1: Fuzzy match for sun-tzu
        res1 = build_subagent_dispatch_payload(role="suntzu", task="Strategic plan")
        assert res1.get("ok") is False
        err1 = res1.get("error", "")
        assert "Unknown agent role 'suntzu'" in err1
        assert "Did you mean:" in err1
        assert "'sun-tzu'" in err1
        assert f"Available roles ({len(VALID_SUBAGENTS)}):" in err1
        assert len(res1.get("available_roles", [])) == 25

        # Case 2: Unknown arbitrary role
        res2 = build_subagent_dispatch_payload(role="quantum-wizard", task="Compute")
        assert res2.get("ok") is False
        err2 = res2.get("error", "")
        assert "Unknown agent role 'quantum-wizard'" in err2
        assert f"Available roles ({len(VALID_SUBAGENTS)}):" in err2
        assert set(res2.get("available_roles", [])) == set(VALID_SUBAGENTS)

    def test_empty_arguments_validation(self) -> None:
        """Test missing role or missing task returns clear validation error."""
        from src.core.subagent_dispatch import build_subagent_dispatch_payload

        res_no_role = build_subagent_dispatch_payload(role="", task="Valid task")
        assert res_no_role.get("ok") is False
        assert "Missing required argument: role" in res_no_role.get("error", "")

        res_no_task = build_subagent_dispatch_payload(role="cto", task="")
        assert res_no_task.get("ok") is False
        assert "Missing required argument: task" in res_no_task.get("error", "")

    def test_role_name_normalization(self) -> None:
        """Test role IDs with hyphens or underscores normalize to canonical agent ID."""
        from src.core.subagent_dispatch import build_subagent_dispatch_payload

        res_hyphen = build_subagent_dispatch_payload(role="sun-tzu", task="Advice")
        res_underscore = build_subagent_dispatch_payload(role="sun_tzu", task="Advice")

        assert res_hyphen.get("ok") is True
        assert res_underscore.get("ok") is True
        assert res_hyphen["data"]["role"] == "sun-tzu"
        assert res_underscore["data"]["role"] == "sun-tzu"
        assert res_hyphen["data"]["define_subagent_payload"]["name"] == "sun_tzu"
        assert res_underscore["data"]["define_subagent_payload"]["name"] == "sun_tzu"

    def test_model_tier_override_behavior(self) -> None:
        """Test overriding model tier reflects in dispatch payload and context engineering."""
        from src.core.subagent_dispatch import build_subagent_dispatch_payload

        # Inherit preserves default
        res_inherit = build_subagent_dispatch_payload(role="cto", task="Review", model_tier="inherit")
        assert res_inherit["data"]["model_tier"] == "pro"

        # Explicit flash override
        res_flash = build_subagent_dispatch_payload(role="cto", task="Review", model_tier="flash")
        assert res_flash["data"]["model_tier"] == "flash"
        assert res_flash["data"]["context_engineering"]["model_tier"] == "flash"

        # Explicit pro override
        res_pro = build_subagent_dispatch_payload(role="tester", task="Review", model_tier="pro")
        assert res_pro["data"]["model_tier"] == "pro"
        assert res_pro["data"]["context_engineering"]["model_tier"] == "pro"

    def test_dispatch_alias_matches_build_subagent_dispatch_payload(self) -> None:
        """Test dispatch() alias produces identical payload to build_subagent_dispatch_payload()."""
        from src.core.subagent_dispatch import build_subagent_dispatch_payload, dispatch

        res1 = build_subagent_dispatch_payload("cto", "Architecture review", model_tier="flash")
        res2 = dispatch("cto", "Architecture review", model_tier="flash")
        assert res1 == res2


# =============================================================================
# Test Class 2: CLI Agent Spawn Command (R1)
# =============================================================================

class TestAgentSpawnCli:
    """Verify CLI command `mekong agent spawn` across dry-run, json, and live modes."""

    def test_spawn_cto_dry_run_exits_0_and_prints_metadata(self) -> None:
        """Test CLI `mekong agent spawn cto --task 'Architecture review' --dry-run` exits 0 with preview."""
        res = run_cli_agent_spawn("cto", "--task", "Architecture review", "--dry-run")
        assert res.returncode == 0, f"Command failed: {res.stderr}\n{res.stdout}"
        stdout = res.stdout

        assert "Agent Spawn Preview (Dry Run)" in stdout
        assert "CTO — Chief Technology Officer" in stdout
        assert "cto" in stdout
        assert "Role ID" in stdout
        assert "Context Budget" in stdout
        assert "24,000 tokens" in stdout
        assert "Architecture review" in stdout
        assert "Injected System Prompt (cto)" in stdout
        assert "Dry-run complete. No agent processes were spawned." in stdout

    def test_spawn_cto_dry_run_json_produces_valid_json(self) -> None:
        """Test CLI `mekong agent spawn cto --task 'Architecture review' --dry-run --json` outputs valid JSON."""
        res = run_cli_agent_spawn("cto", "--task", "Architecture review", "--dry-run", "--json")
        assert res.returncode == 0, f"Command failed: {res.stderr}\n{res.stdout}"

        data = json.loads(res.stdout)
        assert data.get("ok") is True
        assert data.get("status") == "dry_run"
        assert data.get("role") == "cto"
        assert data.get("task") == "Architecture review"
        assert data.get("context_budget") == 24000
        assert data.get("total_context_ceiling") == 40000

        # Sub-payloads
        assert "define_subagent_payload" in data
        assert data["define_subagent_payload"]["name"] == "cto"
        assert "invoke_subagent_payload" in data
        assert data["invoke_subagent_payload"]["subagent_name"] == "cto"
        assert "context_engineering" in data
        assert data["context_engineering"]["context_budget"] == 24000

    def test_spawn_sun_tzu_model_tier_override_reflected_in_json(self) -> None:
        """Test CLI `mekong agent spawn sun-tzu --task 'Strategic review' --model-tier flash --dry-run --json`."""
        res = run_cli_agent_spawn(
            "sun-tzu",
            "--task",
            "Strategic review",
            "--model-tier",
            "flash",
            "--dry-run",
            "--json",
        )
        assert res.returncode == 0, f"Command failed: {res.stderr}\n{res.stdout}"

        data = json.loads(res.stdout)
        assert data.get("ok") is True
        assert data.get("role") == "sun-tzu"
        assert data.get("model_tier") == "flash"
        assert data["context_engineering"]["model_tier"] == "flash"

    def test_spawn_unknown_agent_rejected_with_suggestions_and_nonzero_exit(self) -> None:
        """Test CLI `mekong agent spawn unknown_agent --task 'foo'` exits non-zero and suggests roles."""
        res = run_cli_agent_spawn("unknown_agent", "--task", "foo")
        assert res.returncode != 0
        output = res.stdout + res.stderr

        assert "Unknown agent role: 'unknown_agent'" in output
        assert "Available roles (25):" in output
        assert "sun-tzu" in output
        assert "cto" in output

    def test_spawn_unknown_agent_json_output(self) -> None:
        """Test CLI `mekong agent spawn unknown_agent --task 'foo' --json` emits structured error JSON."""
        res = run_cli_agent_spawn("unknown_agent", "--task", "foo", "--json")
        assert res.returncode != 0

        data = json.loads(res.stdout)
        assert data.get("ok") is False
        assert data.get("status") == "failed"
        assert "unknown_agent" in data.get("error", "")
        assert len(data.get("available_roles", [])) == 25

    def test_spawn_cto_live_mode_outputs_execution_summary_and_exits_0(self) -> None:
        """Test CLI `mekong agent spawn cto --task 'Smoke test'` in live mode outputs execution summary panel."""
        res = run_cli_agent_spawn("cto", "--task", "Smoke test")
        assert res.returncode == 0, f"Command failed: {res.stderr}\n{res.stdout}"
        stdout = res.stdout

        assert "Agent Execution Summary" in stdout
        assert "Status: SUCCESS" in stdout
        assert "Role: cto" in stdout
        assert "Model: pro" in stdout
        assert "Output" in stdout

    def test_spawn_live_mode_json_output(self) -> None:
        """Test CLI `mekong agent spawn tester --task 'Verify system' --json` outputs structured success JSON."""
        res = run_cli_agent_spawn("tester", "--task", "Verify system", "--json")
        assert res.returncode == 0, f"Command failed: {res.stderr}\n{res.stdout}"

        data = json.loads(res.stdout)
        assert data.get("ok") is True
        assert data.get("status") == "success"
        assert data.get("role") == "tester"
        assert isinstance(data.get("elapsed_time"), (int, float))
        assert "output" in data and len(data["output"]) > 0

    @pytest.mark.skipif(shutil.which("mekong") is None, reason="'mekong' binary not found on PATH")
    def test_mekong_binary_direct_spawn_dry_run(self) -> None:
        """Test direct `mekong` binary execution matches Python module behavior."""
        res = run_cli_agent_spawn("cto", "--task", "Direct binary test", "--dry-run", use_mekong_bin=True)
        assert res.returncode == 0, f"Direct mekong invocation failed: {res.stderr}\n{res.stdout}"
        assert "Agent Spawn Preview (Dry Run)" in res.stdout
        assert "cto" in res.stdout


# =============================================================================
# Test Class 3: MCP Dynamic Subagent Bridge Dispatch (R2)
# =============================================================================

class TestMcpSubagentDispatch:
    """Verify MCP stdio JSON-RPC handshake, mekong_subagent_dispatch tool, and fallback."""

    def test_stdio_jsonrpc_handshake(self) -> None:
        """Test standard MCP server initialize handshake."""
        with JsonRpcStdioClient([sys.executable, str(MCP_SERVER_SCRIPT)]) as client:
            result = client.perform_handshake()
            assert result.get("protocolVersion") == PROTOCOL_VERSION
            assert "capabilities" in result
            assert "tools" in result["capabilities"]
            assert result.get("serverInfo", {}).get("name") == "mekong-core"

    def test_tools_list_exposes_mekong_subagent_dispatch(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test tools/list exposes mekong_subagent_dispatch with complete input schema."""
        resp = stdio_client.call("tools/list")
        assert "result" in resp, f"tools/list error: {resp.get('error')}"
        tools = {t["name"]: t for t in resp["result"].get("tools", [])}

        assert "mekong_subagent_dispatch" in tools, "Missing 'mekong_subagent_dispatch' in tools/list"
        disp = tools["mekong_subagent_dispatch"]
        assert disp.get("description"), "Missing description for mekong_subagent_dispatch"

        schema = disp.get("inputSchema", {})
        assert schema.get("type") == "object"
        props = schema.get("properties", {})
        assert "role" in props, "Schema must include 'role'"
        assert "task" in props, "Schema must include 'task'"
        assert "model_tier" in props, "Schema must include 'model_tier'"
        assert set(schema.get("required", [])) >= {"role", "task"}

    def test_tools_call_subagent_dispatch_valid_cto(self, stdio_client: JsonRpcStdioClient) -> None:
        """Test tools/call mekong_subagent_dispatch returns valid define and invoke payloads for CTO."""
        resp = stdio_client.call(
            "tools/call",
            {
                "name": "mekong_subagent_dispatch",
                "arguments": {
                    "role": "cto",
                    "task": "Review system architecture",
                },
            },
        )
        assert "result" in resp, f"tools/call error: {resp.get('error')}"
        assert resp["result"].get("isError") is False
        content = resp["result"].get("content", [])
        assert len(content) > 0

        data = json.loads(content[0]["text"])
        assert data.get("ok") is True
        payload_data = data.get("data", {})
        assert payload_data.get("role") == "cto"
        assert payload_data.get("model_tier") == "pro"

        # Check define payload
        def_payload = payload_data.get("define_subagent_payload", {})
        assert def_payload.get("name") == "cto"
        assert "system_prompt" in def_payload and len(def_payload["system_prompt"]) >= 50
        assert def_payload.get("enable_mcp_tools") is True

        # Check invoke payload
        inv_payload = payload_data.get("invoke_subagent_payload", {})
        assert inv_payload.get("subagent_name") == "cto"
        assert inv_payload.get("task") == "Review system architecture"

        # Check context constraints
        ctx = payload_data.get("context_engineering", {})
        assert ctx.get("context_budget") == 24000
        assert ctx.get("total_context_ceiling") == 40000

    @pytest.mark.parametrize(
        "role_name,expected_budget",
        [
            ("sun-tzu", 30000),
            ("ceo", 30000),
            ("cto", 24000),
            ("pm", 20000),
            ("eng", 24000),
            ("ops", 16000),
            ("debugger", 16000),
            ("kongming", 16000),
        ],
    )
    def test_tools_call_subagent_dispatch_key_agents(
        self,
        stdio_client: JsonRpcStdioClient,
        role_name: str,
        expected_budget: int,
    ) -> None:
        """Test tools/call mekong_subagent_dispatch across representative domain subagents."""
        resp = stdio_client.call(
            "tools/call",
            {
                "name": "mekong_subagent_dispatch",
                "arguments": {
                    "role": role_name,
                    "task": "Perform strategic domain evaluation",
                },
            },
        )
        assert "result" in resp
        content = resp["result"].get("content", [])
        assert len(content) > 0
        data = json.loads(content[0]["text"])
        assert data.get("ok") is True
        payload_data = data.get("data", {})
        assert payload_data.get("role") == role_name
        assert payload_data.get("context_engineering", {}).get("context_budget") == expected_budget

    def test_tools_call_subagent_dispatch_unknown_role_returns_error(
        self,
        stdio_client: JsonRpcStdioClient,
    ) -> None:
        """Test tools/call with unknown agent role returns error with suggestions."""
        resp = stdio_client.call(
            "tools/call",
            {
                "name": "mekong_subagent_dispatch",
                "arguments": {
                    "role": "unknown_ninja",
                    "task": "Infiltrate codebase",
                },
            },
        )
        assert "result" in resp
        content = resp["result"].get("content", [])
        assert len(content) > 0
        data = json.loads(content[0]["text"])

        assert data.get("ok") is False
        error_msg = data.get("error", "")
        assert "Unknown agent role 'unknown_ninja'" in error_msg
        assert "Available roles (25):" in error_msg
        assert len(data.get("available_roles", [])) == 25

    def test_fallback_stdio_server_subagent_dispatch(
        self,
        fallback_stdio_client: JsonRpcStdioClient,
    ) -> None:
        """Test pure-Python fallback stdio server (MEKONG_FORCE_MCP_FALLBACK=1) handles subagent dispatch."""
        resp = fallback_stdio_client.call(
            "tools/call",
            {
                "name": "mekong_subagent_dispatch",
                "arguments": {
                    "role": "sun-tzu",
                    "task": "Strategic counsel on resource allocation",
                },
            },
        )
        assert "result" in resp, f"Fallback call failed: {resp.get('error')}"
        content = resp["result"].get("content", [])
        assert len(content) > 0
        data = json.loads(content[0]["text"])

        assert data.get("ok") is True
        payload_data = data.get("data", {})
        assert payload_data.get("role") == "sun-tzu"
        assert payload_data.get("define_subagent_payload", {}).get("name") == "sun_tzu"
        assert payload_data.get("context_engineering", {}).get("context_budget") == 30000

        # Also verify fallback unknown role error handling
        err_resp = fallback_stdio_client.call(
            "tools/call",
            {
                "name": "mekong_subagent_dispatch",
                "arguments": {"role": "invalid_ninja", "task": "test"},
            },
        )
        err_content = json.loads(err_resp["result"]["content"][0]["text"])
        assert err_content.get("ok") is False
        assert "Unknown agent role" in err_content.get("error", "")


# =============================================================================
# Test Class 4: Global Plugin Subagent Replication & SHA-256 Parity (R3)
# =============================================================================

class TestGlobalPluginSubagentReplication:
    """Verify replication presence, schema validity, and byte-for-byte SHA-256 integrity."""

    def test_workspace_and_global_plugin_directories_exist(self) -> None:
        """Verify .agents/subagents exists locally and in both global plugin destinations."""
        assert LOCAL_SUBAGENTS_DIR.is_dir(), f"Missing local {LOCAL_SUBAGENTS_DIR}"
        assert LOCAL_DEFINITIONS_DIR.is_dir(), f"Missing local {LOCAL_DEFINITIONS_DIR}"
        assert GLOBAL_PLUGIN_DIR.is_dir(), f"Missing global plugin {GLOBAL_PLUGIN_DIR}"
        assert AGY_PLUGIN_DIR.is_dir(), f"Missing antigravity-cli plugin {AGY_PLUGIN_DIR}"

    def test_global_plugin_registries_schema_and_counts(self) -> None:
        """Verify registry.json exists and conforms across all three locations."""
        for label, sdir in [
            ("local", LOCAL_SUBAGENTS_DIR),
            ("global_plugin", GLOBAL_PLUGIN_DIR),
            ("agy_plugin", AGY_PLUGIN_DIR),
        ]:
            reg_path = sdir / "registry.json"
            assert reg_path.is_file(), f"Missing registry.json in {label}: {reg_path}"

            data = json.loads(reg_path.read_text(encoding="utf-8"))
            assert data.get("schema") == "antigravity.subagents.registry.v1", f"Bad schema in {label}"
            assert data.get("total_agents") == 25, f"Expected 25 agents in {label}, got {data.get('total_agents')}"
            agents = data.get("agents", [])
            assert len(agents) == 25, f"Expected 25 agent records in {label}, got {len(agents)}"

            agent_ids = {a["id"] for a in agents}
            assert agent_ids == set(ALL_25_SUBAGENT_IDS), f"Mismatched agent IDs in {label}"

    def test_all_25_definition_files_present_in_all_locations(self) -> None:
        """Verify all 25 definition markdown files exist and are non-empty in all three locations."""
        for label, def_dir in [
            ("local", LOCAL_DEFINITIONS_DIR),
            ("global_plugin", GLOBAL_PLUGIN_DIR / "definitions"),
            ("agy_plugin", AGY_PLUGIN_DIR / "definitions"),
        ]:
            assert def_dir.is_dir(), f"Missing definitions dir in {label}: {def_dir}"
            md_files = list(def_dir.glob("*.md"))
            assert len(md_files) == 25, f"Expected 25 definition markdown files in {label}, found {len(md_files)}"

            for aid in ALL_25_SUBAGENT_IDS:
                def_file = def_dir / f"{aid}.md"
                assert def_file.is_file(), f"Missing {aid}.md in {label}"
                content = def_file.read_text(encoding="utf-8").strip()
                assert len(content) >= 50, f"Definition {aid}.md in {label} is too short ({len(content)} bytes)"

    def test_byte_for_byte_sha256_integrity_across_targets(self) -> None:
        """Verify exact SHA-256 byte-for-byte parity across local workspace and both global plugins."""
        local_reg = LOCAL_SUBAGENTS_DIR / "registry.json"
        g1_reg = GLOBAL_PLUGIN_DIR / "registry.json"
        g2_reg = AGY_PLUGIN_DIR / "registry.json"

        local_reg_hash = compute_sha256(local_reg)
        assert compute_sha256(g1_reg) == local_reg_hash, f"SHA mismatch on {g1_reg}"
        assert compute_sha256(g2_reg) == local_reg_hash, f"SHA mismatch on {g2_reg}"

        for aid in ALL_25_SUBAGENT_IDS:
            local_md = LOCAL_DEFINITIONS_DIR / f"{aid}.md"
            g1_md = GLOBAL_PLUGIN_DIR / "definitions" / f"{aid}.md"
            g2_md = AGY_PLUGIN_DIR / "definitions" / f"{aid}.md"

            local_hash = compute_sha256(local_md)
            assert compute_sha256(g1_md) == local_hash, f"SHA mismatch on {g1_md} for {aid}"
            assert compute_sha256(g2_md) == local_hash, f"SHA mismatch on {g2_md} for {aid}"


# =============================================================================
# Test Class 5: Subagent Health & Regression Integrity (R4)
# =============================================================================

class TestSubagentHealthAndRegression:
    """Verify zero regressions across sync verification and antigravity healthcheck."""

    def test_sync_antigravity_verify_exits_0(self) -> None:
        """Ensure `python3 scripts/sync_antigravity.py --verify` validates subagents and exits 0."""
        res = subprocess.run(
            [sys.executable, "scripts/sync_antigravity.py", "--verify"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=30,
        )
        assert res.returncode == 0, f"Sync verify failed: {res.stderr}\n{res.stdout}"
        assert "Auditing domain subagents..." in res.stdout
        assert "Verification passed" in res.stdout

    def test_antigravity_healthcheck_exits_0_and_healthy(self) -> None:
        """Ensure `python3 scripts/antigravity_healthcheck.py` passes all checks with Status: HEALTHY."""
        res = subprocess.run(
            [sys.executable, "scripts/antigravity_healthcheck.py"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=90,
        )
        assert res.returncode == 0, f"Healthcheck failed: {res.stderr}\n{res.stdout}"
        assert "Status: HEALTHY" in res.stdout
        assert "Failures: 0" in res.stdout
