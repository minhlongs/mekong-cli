# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Comprehensive test suite for Antigravity Lifecycle Hooks system.

Tests:
1. TestDestructiveGitBlocking: blocks git force pushes, hard resets, force clean, branch deletion.
2. TestProductionDeployBlocking: blocks mekong ship --prod, ci deploy --prod, deploy --env prod, etc.
3. TestVASLedgerBlocking: blocks destructive SQL queries, accounting folder deletions, company reset.
4. TestQuanDoanhProtection: blocks modifications to Command HQ protected boundary paths.
5. TestCEOOverride: permits gated operations when --ceo-override or MEKONG_CEO_OVERRIDE=1 is present.
6. TestSafeCommandsPass: ensures non-destructive development commands execute cleanly.
7. TestInputParsingCascade: validates command resolution across CLI args, env vars, and JSON stdin.
8. TestPostToolAuditLogger: verifies telemetry persistence, schema conformance, and ISO timestamps.
9. TestFailOpenResilience: verifies post_tool_audit.py never crashes under unwritable disks or corrupt input.
10. TestMultiTargetSyncIntegration: verifies hooks.json deployment across local and global plugin targets.
"""

from __future__ import annotations

import datetime
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRE_TOOL_GUARDRAIL = PROJECT_ROOT / "scripts" / "hooks" / "pre_tool_guardrail.py"
POST_TOOL_AUDIT = PROJECT_ROOT / "scripts" / "hooks" / "post_tool_audit.py"
SYNC_ANTIGRAVITY = PROJECT_ROOT / "scripts" / "sync_antigravity.py"
LOCAL_HOOKS_JSON = PROJECT_ROOT / ".agents" / "hooks.json"
GLOBAL_PLUGIN_DIR = Path.home() / ".gemini" / "config" / "plugins" / "mekong-cli"
AGY_PLUGIN_DIR = Path.home() / ".gemini" / "antigravity-cli" / "plugins" / "mekong-cli"


# =============================================================================
# Helper Utilities
# =============================================================================

def run_guardrail(
    cmd: str | None = None,
    *,
    argv: list[str] | None = None,
    env: dict[str, str] | None = None,
    stdin: str | None = None,
    stdin_json: dict[str, Any] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Execute pre_tool_guardrail.py in an isolated subprocess."""
    base_env = os.environ.copy()
    # Ensure MEKONG_CEO_OVERRIDE is not unintentionally inherited from ambient shell
    base_env.pop("MEKONG_CEO_OVERRIDE", None)
    base_env.pop("TOOL_COMMAND", None)
    base_env.pop("ANTIGRAVITY_COMMAND", None)
    base_env.pop("COMMAND_LINE", None)
    if env:
        base_env.update(env)

    args = [sys.executable, str(PRE_TOOL_GUARDRAIL)]
    if argv is not None:
        args.extend(argv)
    elif cmd is not None:
        args.append(cmd)

    input_text: str | None = None
    if stdin_json is not None:
        input_text = json.dumps(stdin_json)
    elif stdin is not None:
        input_text = stdin

    return subprocess.run(
        args,
        input=input_text,
        capture_output=True,
        text=True,
        env=base_env,
        cwd=PROJECT_ROOT,
    )


def run_audit(
    *,
    argv: list[str] | None = None,
    env: dict[str, str] | None = None,
    stdin: str | None = None,
    stdin_json: dict[str, Any] | None = None,
    log_file: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Execute post_tool_audit.py in an isolated subprocess."""
    base_env = os.environ.copy()
    base_env.pop("ANTIGRAVITY_COMMAND", None)
    base_env.pop("TOOL_COMMAND", None)
    base_env.pop("COMMAND_LINE", None)
    base_env.pop("TOOL_NAME", None)
    base_env.pop("TOOL_EXIT_CODE", None)
    if log_file is not None:
        base_env["MEKONG_AUDIT_LOG"] = str(log_file)
    if env:
        base_env.update(env)

    args = [sys.executable, str(POST_TOOL_AUDIT)]
    if argv is not None:
        args.extend(argv)

    input_text: str | None = None
    if stdin_json is not None:
        input_text = json.dumps(stdin_json)
    elif stdin is not None:
        input_text = stdin

    return subprocess.run(
        args,
        input=input_text,
        capture_output=True,
        text=True,
        env=base_env,
        cwd=PROJECT_ROOT,
    )


# =============================================================================
# 1. TestDestructiveGitBlocking
# =============================================================================

class TestDestructiveGitBlocking:
    """Validate interception of destructive and history-rewriting git commands."""

    @pytest.mark.parametrize(
        "cmd",
        [
            "git push --force",
            "git push -f",
            "git push origin main",
            "git push origin \"main\"",
            "git push origin 'main'",
            "git push origin \"master\"",
            "git push \\\n--force",
            "git push \n --force",
            "git reset --hard",
            "git clean -fdx",
            "git branch -D",
            "git push origin main --force",
            "git push origin -f feature/security",
            "git reset --hard HEAD~2",
            "git clean -f -d",
            "git push origin --delete temp-branch",
            "git checkout -f",
        ],
    )
    def test_destructive_git_commands_are_denied(self, cmd: str) -> None:
        proc = run_guardrail(cmd)
        assert proc.returncode == 1, f"Expected returncode 1 for '{cmd}', got {proc.returncode}"

        # Decision output must be valid JSON with decision="deny"
        try:
            payload = json.loads(proc.stdout.strip())
        except json.JSONDecodeError as exc:
            pytest.fail(f"Stdout did not contain valid JSON for '{cmd}': {proc.stdout} ({exc})")

        assert payload.get("decision") == "deny", f"Expected decision 'deny' for '{cmd}', got {payload}"
        assert "reason" in payload, f"Missing 'reason' field in deny response for '{cmd}'"

        # Stderr must contain explanatory warning and bypass guidance
        assert "MEKONG HARNESS GUARDRAIL TRIGGERED" in proc.stderr
        assert "--ceo-override" in proc.stderr or "MEKONG_CEO_OVERRIDE" in proc.stderr


# =============================================================================
# 2. TestProductionDeployBlocking
# =============================================================================

class TestProductionDeployBlocking:
    """Validate interception of unverified live production deployment operations."""

    @pytest.mark.parametrize(
        "cmd",
        [
            "mekong ship --prod",
            "ci deploy --prod",
            "deploy --env prod",
            "wrangler deploy --env prod",
            "npm publish",
            "mekong ship --production",
            "ci deploy --env production",
            "deploy --target prod",
            "pnpm publish",
            "poetry publish",
            "kubectl -n prod delete pod gateway-0",
        ],
    )
    def test_production_deploy_commands_are_denied(self, cmd: str) -> None:
        proc = run_guardrail(cmd)
        assert proc.returncode == 1, f"Expected returncode 1 for '{cmd}', got {proc.returncode}"

        payload = json.loads(proc.stdout.strip())
        assert payload.get("decision") == "deny"
        assert "reason" in payload
        assert "MEKONG HARNESS GUARDRAIL TRIGGERED" in proc.stderr


# =============================================================================
# 3. TestVASLedgerBlocking
# =============================================================================

class TestVASLedgerBlocking:
    """Validate interception of irreversible VAS accounting and tax mutations."""

    @pytest.mark.parametrize(
        "cmd",
        [
            'sqlite3 data/accounting.db "DROP TABLE ledger"',
            'psql -c "DELETE FROM invoices WHERE 1=1"',
            'mysql -e "TRUNCATE TABLE transactions"',
            "rm -rf .mekong/treasury",
            "rm -rf .mekong/raas",
            "rm -rf data/accounting",
            "mekong company reset",
            "company reset",
            "mekong billing purge",
            "mekong ke-toan post",
            "ke-toan close",
            "mekong thue submit",
            "thue pay",
        ],
    )
    def test_vas_ledger_mutations_are_denied(self, cmd: str) -> None:
        proc = run_guardrail(cmd)
        assert proc.returncode == 1, f"Expected returncode 1 for '{cmd}', got {proc.returncode}"

        payload = json.loads(proc.stdout.strip())
        assert payload.get("decision") == "deny"
        assert "reason" in payload
        assert "MEKONG HARNESS GUARDRAIL TRIGGERED" in proc.stderr


# =============================================================================
# 4. TestQuanDoanhProtection
# =============================================================================

class TestQuanDoanhProtection:
    """Validate strict read-only boundary enforcement for Command HQ (QUAN DOANH) paths."""

    @pytest.mark.parametrize(
        "cmd",
        [
            "rm -rf mekong/bootstrap",
            "rm mekong//bootstrap",
            "rm mekong/./bootstrap",
            "rm -rf mekong//bootstrap",
            "rm -rf mekong/./bootstrap",
            "touch mekong/bootstrap/exploit.sh",
            "rm -rf mekong/constitution",
            "sed -i '' 's/forbidden/allowed/' mekong/constitution/rules/hooks.md",
            "rm -rf mekong/hooks",
            "rm -rf mekong/init",
            "rm -rf mekong/audit",
            "echo 'hacked' > mekong/constitution/hack.txt",
            "echo 'hacked' >> mekong/bootstrap/init.sh",
            "echo 'evil' > ./mekong//bootstrap",
            "> ./mekong//bootstrap",
            "git rm mekong/constitution/ARCHITECTURE.md",
        ],
    )
    def test_quan_doanh_shell_modifications_are_denied(self, cmd: str) -> None:
        proc = run_guardrail(cmd)
        assert proc.returncode == 1, f"Expected returncode 1 for '{cmd}', got {proc.returncode}"

        payload = json.loads(proc.stdout.strip())
        assert payload.get("decision") == "deny"
        assert "reason" in payload
        assert "MEKONG HARNESS GUARDRAIL TRIGGERED" in proc.stderr

    @pytest.mark.parametrize(
        "target_file",
        [
            "/Users/macbook/mekong-cli/mekong/bootstrap/init.sh",
            "/Users/macbook/mekong-cli/mekong/constitution/rules.md",
            "/Users/macbook/mekong-cli/mekong/hooks/hook.cjs",
            "/Users/macbook/mekong-cli/mekong/init/config.json",
            "/Users/macbook/mekong-cli/mekong/audit/audit.log",
            "mekong/constitution/SOPS.md",
        ],
    )
    def test_quan_doanh_file_tool_modifications_are_denied(self, target_file: str) -> None:
        payload_input = {
            "toolCall": {
                "name": "write_to_file",
                "args": {"TargetFile": target_file, "CodeContent": "malicious content"},
            }
        }
        proc = run_guardrail(stdin_json=payload_input)
        assert proc.returncode == 1

        payload = json.loads(proc.stdout.strip())
        assert payload.get("decision") == "deny"
        assert "reason" in payload
        assert "MEKONG HARNESS GUARDRAIL TRIGGERED" in proc.stderr


# =============================================================================
# 5. TestCEOOverride
# =============================================================================

class TestCEOOverride:
    """Validate CEO override authority bypass via command flag and environment variable."""

    @pytest.mark.parametrize(
        "cmd",
        [
            "git push --force --ceo-override",
            "git reset --hard --ceo-override",
            "mekong ship --prod --ceo-override",
            "rm -rf mekong/constitution --ceo-override",
            "mekong company reset --ceo-override",
        ],
    )
    def test_ceo_override_via_command_flag(self, cmd: str) -> None:
        proc = run_guardrail(cmd)
        assert proc.returncode == 0, f"Expected returncode 0 with flag override for '{cmd}': {proc.stderr}"

        payload = json.loads(proc.stdout.strip())
        assert payload.get("decision") == "allow"
        assert "reason" in payload or "ceo_override" in payload or payload == {"decision": "allow"}

    @pytest.mark.parametrize(
        "env_value",
        ["1", "true", "yes", "TRUE"],
    )
    @pytest.mark.parametrize(
        "cmd",
        [
            "git push --force",
            "git reset --hard",
            "mekong ship --prod",
            "rm -rf mekong/constitution",
            "mekong company reset",
        ],
    )
    def test_ceo_override_via_environment_variable(self, env_value: str, cmd: str) -> None:
        proc = run_guardrail(cmd, env={"MEKONG_CEO_OVERRIDE": env_value})
        assert proc.returncode == 0, f"Expected returncode 0 with env override for '{cmd}': {proc.stderr}"

    @pytest.mark.parametrize(
        "cmd",
        [
            "git push --force --ceo-override=true",
            "git push --force --ceo-override=1",
            "git push --force --ceo-override=yes",
            "git push --force --ceo-override=TRUE",
        ],
    )
    def test_ceo_override_with_truthy_values(self, cmd: str) -> None:
        proc = run_guardrail(cmd)
        assert proc.returncode == 0, f"Expected returncode 0 with truthy override for '{cmd}': {proc.stderr}"
        payload = json.loads(proc.stdout.strip())
        assert payload.get("decision") == "allow"

    @pytest.mark.parametrize(
        "cmd",
        [
            "git push --force --ceo-override=false",
            "git push --force --ceo-override=0",
            "git push --force --ceo-override-fake",
            "git push --force --no-ceo-override",
            "git push --force -m \"fix --ceo-override\"",
            "git push --force -m \"fixed --ceo-override bug\"",
            "echo \"--ceo-override\" && git push --force",
        ],
    )
    def test_ceo_override_false_positives_blocked(self, cmd: str) -> None:
        proc = run_guardrail(cmd)
        assert proc.returncode == 1, f"Expected returncode 1 for false override attempt '{cmd}', got {proc.returncode}"
        payload = json.loads(proc.stdout.strip())
        assert payload.get("decision") == "deny"
        assert "MEKONG HARNESS GUARDRAIL TRIGGERED" in proc.stderr



# =============================================================================
# 6. TestSafeCommandsPass
# =============================================================================

class TestSafeCommandsPass:
    """Validate that standard non-destructive development commands execute without interference."""

    @pytest.mark.parametrize(
        "cmd",
        [
            "git status",
            "git diff",
            "pytest",
            "mekong test",
            'mekong cook "build feature"',
            "git log -n 5",
            "git branch -a",
            "mekong doctor",
            "mekong version",
            "ls -la",
            "cat README.md",
            "python3 -m pytest tests/",
        ],
    )
    def test_safe_commands_pass_cleanly(self, cmd: str) -> None:
        proc = run_guardrail(cmd)
        assert proc.returncode == 0, f"Safe command '{cmd}' was unexpectedly blocked: {proc.stderr}"

        payload = json.loads(proc.stdout.strip())
        assert payload.get("decision") == "allow"


# =============================================================================
# 7. TestInputParsingCascade
# =============================================================================

class TestInputParsingCascade:
    """Validate command ingestion across CLI args, env vars, and multi-format JSON stdin."""

    def test_cli_positional_args(self) -> None:
        proc = run_guardrail(argv=["git", "push", "--force"])
        assert proc.returncode == 1
        assert json.loads(proc.stdout.strip()).get("decision") == "deny"

    def test_cli_command_flag(self) -> None:
        proc = run_guardrail(argv=["--command", "git push --force"])
        assert proc.returncode == 1
        assert json.loads(proc.stdout.strip()).get("decision") == "deny"

    def test_environment_variable_tool_command(self) -> None:
        proc = run_guardrail(env={"TOOL_COMMAND": "git push --force"})
        assert proc.returncode == 1
        assert json.loads(proc.stdout.strip()).get("decision") == "deny"

    def test_environment_variable_antigravity_command(self) -> None:
        proc = run_guardrail(env={"ANTIGRAVITY_COMMAND": "git push --force"})
        assert proc.returncode == 1
        assert json.loads(proc.stdout.strip()).get("decision") == "deny"

    def test_antigravity_camelcase_json_stdin(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "run_command",
            "toolCall": {
                "args": {
                    "CommandLine": "git push --force",
                    "Cwd": str(PROJECT_ROOT),
                }
            },
        }
        proc = run_guardrail(stdin_json=payload)
        assert proc.returncode == 1
        assert json.loads(proc.stdout.strip()).get("decision") == "deny"

    def test_claude_code_snake_case_json_stdin(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "run_command",
            "tool_input": {
                "command": "git push --force",
            },
        }
        proc = run_guardrail(stdin_json=payload)
        assert proc.returncode == 1
        assert json.loads(proc.stdout.strip()).get("decision") == "deny"

    def test_claude_code_camelcase_in_tool_input(self) -> None:
        payload = {
            "tool_input": {
                "CommandLine": "git push --force",
            }
        }
        proc = run_guardrail(stdin_json=payload)
        assert proc.returncode == 1
        assert json.loads(proc.stdout.strip()).get("decision") == "deny"

    def test_raw_stdin_fallback(self) -> None:
        proc = run_guardrail(stdin="git push --force")
        assert proc.returncode == 1
        assert json.loads(proc.stdout.strip()).get("decision") == "deny"

    def test_empty_input_defaults_to_allow(self) -> None:
        proc = run_guardrail(stdin="")
        assert proc.returncode == 0
        assert json.loads(proc.stdout.strip()).get("decision") == "allow"


# =============================================================================
# 8. TestPostToolAuditLogger
# =============================================================================

class TestPostToolAuditLogger:
    """Validate execution telemetry recording, structured JSONL schema, and ISO timestamps."""

    def test_audit_log_written_via_cli_flags(self, tmp_path: Path) -> None:
        log_file = tmp_path / "telemetry.log"
        proc = run_audit(
            argv=[
                "--command", "pytest tests/test_antigravity_hooks.py",
                "--exit-code", "0",
                "--tool", "run_command",
                "--duration", "150.25",
                "--status", "success",
            ],
            log_file=log_file,
        )
        assert proc.returncode == 0
        assert log_file.exists()

        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1

        record = json.loads(lines[0])
        assert record["command"] == "pytest tests/test_antigravity_hooks.py"
        assert record["exit_code"] == 0
        assert record["tool"] == "run_command"
        assert record["status"] == "success"
        assert record["duration_ms"] == 150.25
        assert record["hook_event"] == "PostToolUse"
        assert "timestamp" in record
        assert "cwd" in record

        # Assert timestamp is valid ISO 8601 UTC
        ts = record["timestamp"]
        parsed_dt = datetime.datetime.fromisoformat(ts)
        assert parsed_dt.tzinfo is not None

    def test_audit_log_written_via_json_stdin(self, tmp_path: Path) -> None:
        log_file = tmp_path / "telemetry.log"
        payload = {
            "hook_event_name": "PostToolUse",
            "tool_name": "run_command",
            "tool_input": {"CommandLine": "git push origin main"},
            "tool_response": {"exit_code": 1},
            "duration_ms": 42.0,
        }
        proc = run_audit(stdin_json=payload, log_file=log_file)
        assert proc.returncode == 0

        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1

        record = json.loads(lines[0])
        assert record["command"] == "git push origin main"
        assert record["exit_code"] == 1
        assert record["status"] == "failed"
        assert record["duration_ms"] == 42.0

    def test_audit_log_sequential_appends(self, tmp_path: Path) -> None:
        log_file = tmp_path / "audit_chain.log"

        run_audit(argv=["--command", "cmd 1", "--exit-code", "0"], log_file=log_file)
        run_audit(argv=["--command", "cmd 2", "--exit-code", "1"], log_file=log_file)
        run_audit(argv=["--command", "cmd 3", "--exit-code", "0"], log_file=log_file)

        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3

        cmds = [json.loads(line)["command"] for line in lines]
        assert cmds == ["cmd 1", "cmd 2", "cmd 3"]


# =============================================================================
# 9. TestFailOpenResilience
# =============================================================================

class TestFailOpenResilience:
    """Validate that post_tool_audit.py unconditionally succeeds and never disrupts tools."""

    def test_unwritable_directory_fails_open(self, tmp_path: Path) -> None:
        read_only_dir = tmp_path / "ro_dir"
        read_only_dir.mkdir(parents=True, exist_ok=True)
        read_only_dir.chmod(stat.S_IREAD | stat.S_IEXEC)  # 0o555 (no write)

        forbidden_log = read_only_dir / "audit.log"
        try:
            proc = run_audit(
                argv=["--command", "git status"],
                log_file=forbidden_log,
            )
            assert proc.returncode == 0
            assert proc.stderr == ""
        finally:
            read_only_dir.chmod(stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)

    def test_unwritable_file_path_fails_open(self) -> None:
        proc = run_audit(
            argv=["--command", "git status"],
            log_file=Path("/dev/null/forbidden/nonexistent/audit.log"),
        )
        assert proc.returncode == 0
        assert proc.stderr == ""

    def test_corrupted_json_stdin_fails_open(self, tmp_path: Path) -> None:
        proc = run_audit(stdin="{ malformed json [syntax error", log_file=tmp_path / "audit.log")
        assert proc.returncode == 0

    def test_empty_stdin_fails_open(self, tmp_path: Path) -> None:
        proc = run_audit(stdin="", log_file=tmp_path / "audit.log")
        assert proc.returncode == 0

    def test_non_numeric_values_do_not_crash(self, tmp_path: Path) -> None:
        payload = {
            "tool_input": {"command": "echo test"},
            "tool_response": {"exit_code": "not-an-int"},
            "duration_ms": "not-a-float",
        }
        proc = run_audit(stdin_json=payload, log_file=tmp_path / "audit.log")
        assert proc.returncode == 0


# =============================================================================
# 10. TestMultiTargetSyncIntegration
# =============================================================================

class TestMultiTargetSyncIntegration:
    """Validate hooks synchronization and integrity across workspace and global plugin targets."""

    def test_sync_verify_cli_passes(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SYNC_ANTIGRAVITY), "--verify"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
        assert proc.returncode == 0, f"sync_antigravity.py --verify failed:\n{proc.stdout}\n{proc.stderr}"
        assert "Verification passed!" in proc.stdout

    def test_workspace_hooks_manifest_exists_and_valid(self) -> None:
        assert LOCAL_HOOKS_JSON.exists(), f"Missing {LOCAL_HOOKS_JSON}"
        data = json.loads(LOCAL_HOOKS_JSON.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

        hook_cfg = data.get("mekong-harness") or data
        assert hook_cfg.get("enabled") is True
        assert "PreToolUse" in hook_cfg
        assert "PostToolUse" in hook_cfg

        pre_matchers = [entry.get("matcher") for entry in hook_cfg["PreToolUse"]]
        post_matchers = [entry.get("matcher") for entry in hook_cfg["PostToolUse"]]
        assert "run_command" in pre_matchers
        assert "run_command" in post_matchers

    def test_global_plugin_manifests_exist_and_match(self) -> None:
        for p_dir in [GLOBAL_PLUGIN_DIR, AGY_PLUGIN_DIR]:
            p_hooks = p_dir / "hooks.json"
            assert p_hooks.exists(), f"Missing global plugin hooks at {p_hooks}"
            data = json.loads(p_hooks.read_text(encoding="utf-8"))
            hook_cfg = data.get("mekong-harness") or data
            assert "enabled" in hook_cfg
            assert isinstance(hook_cfg["enabled"], bool)
            assert "PreToolUse" in hook_cfg
            assert "PostToolUse" in hook_cfg

    def test_hook_scripts_exist_and_are_executable(self) -> None:
        for script_path in [PRE_TOOL_GUARDRAIL, POST_TOOL_AUDIT]:
            assert script_path.exists(), f"Missing hook script {script_path}"
            assert os.access(script_path, os.R_OK), f"Not readable: {script_path}"
            assert os.access(script_path, os.X_OK), f"Not executable: {script_path}"
