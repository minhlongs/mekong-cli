# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Multi-Platform Packaging, Distribution & Sandbox Execution (Phase 14).

Covers:
1. PackagingBridge: pyproject parsing, metadata validation, asset bundling, Homebrew formula, Docker assets, manifest.
2. SandboxHarness: runtime probing, fallback subprocess execution, environment scrubbing, timeout enforcement, metrics.
3. CLI Commands: mekong package (--verify, --target, --output-dir, --json) & mekong sandbox (run, status, --json).
4. Native MCP Tools: mekong_package_build and mekong_sandbox_exec dual-engine parity.
5. AST Core Boundary Compliance: strict standard library only, zero vendor SDKs in packaging_bridge & sandbox_bridge.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.packaging_bridge import (
    DistributionArtifact,
    PackagingBridge,
    PackagingReport,
    PackageMetadata,
    _sha256_of_file,
)
from src.core.sandbox_bridge import (
    SandboxConfig,
    SandboxHarness,
    SandboxResult,
    SandboxStatus,
    get_sandbox_harness,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for packaging and sandboxing tests."""
    tmp = Path(tempfile.mkdtemp(prefix="mekong_pkg_sb_test_"))
    yield tmp
    shutil.rmtree(str(tmp), ignore_errors=True)


class TestPackagingBridge:
    """Tests for metadata parsing, validation, and asset bundling."""

    def test_read_metadata_from_actual_repo(self):
        bridge = PackagingBridge()
        meta = bridge.read_metadata()
        assert meta.name == "mekong-cli"
        assert meta.version
        assert "mekong" in meta.entry_point

    def test_read_metadata_empty_dir(self, temp_dir: Path):
        bridge = PackagingBridge(project_root=temp_dir)
        meta = bridge.read_metadata()
        assert meta.name == "mekong-cli"  # Default fallback
        assert meta.version == "6.0.0"

    def test_validate_metadata_success(self):
        bridge = PackagingBridge()
        is_valid, errors = bridge.validate_metadata()
        assert is_valid, f"Validation failed with: {errors}"
        assert len(errors) == 0

    def test_validate_metadata_missing_files(self, temp_dir: Path):
        bridge = PackagingBridge(project_root=temp_dir)
        is_valid, errors = bridge.validate_metadata()
        assert not is_valid
        assert any("README.md" in e for e in errors)
        assert any("LICENSE" in e for e in errors)

    def test_bundle_antigravity_assets(self, temp_dir: Path):
        bridge = PackagingBridge()
        stats = bridge.bundle_antigravity_assets(temp_dir)
        assert stats["skills_bundled"] > 200
        assert stats["subagents_bundled"] > 0
        assert (temp_dir / ".agents" / "skills").exists()
        assert (temp_dir / ".agents" / "subagents").exists()

    def test_generate_homebrew_formula(self, temp_dir: Path):
        bridge = PackagingBridge()
        formula_file = temp_dir / "Formula" / "mekong.rb"
        artifact = bridge.generate_homebrew_formula(
            formula_file,
            tarball_url="https://example.com/mekong.tar.gz",
            sha256_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        )
        assert artifact.artifact_type == "homebrew_formula"
        assert formula_file.exists()
        assert artifact.size_bytes > 0
        assert len(artifact.sha256) == 64

        content = formula_file.read_text(encoding="utf-8")
        assert "class Mekong < Formula" in content
        assert "https://example.com/mekong.tar.gz" in content
        assert "depends_on \"python@3.11\"" in content

    def test_generate_docker_assets(self, temp_dir: Path):
        bridge = PackagingBridge()
        artifacts = bridge.generate_docker_assets(temp_dir)
        assert len(artifacts) == 2
        types = {a.artifact_type for a in artifacts}
        assert types == {"dockerfile", "docker_compose"}

        dockerfile = temp_dir / "Dockerfile"
        compose = temp_dir / "docker-compose.yml"
        assert dockerfile.exists()
        assert compose.exists()

        df_content = dockerfile.read_text(encoding="utf-8")
        assert "FROM python:3.11-slim AS builder" in df_content
        assert "ENTRYPOINT [\"mekong\"]" in df_content
        assert "CMD [\"gateway\"" in df_content

        compose_content = compose.read_text(encoding="utf-8")
        assert "mekong-gateway:" in compose_content
        assert "8080:8080" in compose_content

    def test_build_distribution_package_all(self, temp_dir: Path):
        bridge = PackagingBridge()
        out_dir = temp_dir / "dist"
        report = bridge.build_distribution_package(target="all", output_dir=out_dir)

        assert report.is_valid
        assert report.skills_bundled > 200
        assert report.subagents_bundled > 0
        assert len(report.artifacts) >= 4  # formula, dockerfile, compose, manifest

        manifest_file = out_dir / "manifest.json"
        assert manifest_file.exists()
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        assert manifest_data["name"] == "mekong-cli"
        assert len(manifest_data["artifacts"]) >= 3


class TestSandboxHarness:
    """Tests for sandbox execution, resource constraints, fallback, and scrubbing."""

    def test_runtime_probing(self):
        harness = SandboxHarness()
        is_avail, runtime = harness.check_container_runtime()
        assert isinstance(is_avail, bool)
        assert isinstance(runtime, str)

    def test_fallback_execution_echo(self, temp_dir: Path):
        harness = SandboxHarness()
        cfg = SandboxConfig(workspace_dir=str(temp_dir), timeout_seconds=5)
        res = harness.execute("echo 'Hello Sandbox'", config=cfg, prefer_fallback=True)

        assert res.exit_code == 0
        assert "Hello Sandbox" in res.stdout
        assert res.isolation_backend == "process_fallback"
        assert not res.timed_out
        assert res.duration_ms > 0

    def test_environment_scrubbing(self, temp_dir: Path):
        harness = SandboxHarness()
        # Set sensitive env vars in current process
        with patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "sk-ant-secret123",
            "OPENAI_API_KEY": "sk-secret456",
            "GITHUB_TOKEN": "ghp_secret789",
            "STRIPE_SECRET_KEY": "sk_test_secret",
            "SAFE_CUSTOM_VAR": "visible_ok",
        }):
            cfg = SandboxConfig(
                workspace_dir=str(temp_dir),
                env_vars={"USER_INJECTED": "custom_val"},
            )
            # Inspect env in the sandbox
            cmd = 'python3 -c "import os; print(os.environ.get(\'ANTHROPIC_API_KEY\', \'NONE\'), os.environ.get(\'SAFE_CUSTOM_VAR\', \'NONE\'), os.environ.get(\'USER_INJECTED\', \'NONE\'))"'
            res = harness.execute(cmd, config=cfg, prefer_fallback=True)

            assert res.exit_code == 0
            parts = res.stdout.strip().split()
            assert parts[0] == "NONE"  # ANTHROPIC_API_KEY scrubbed
            assert parts[1] == "visible_ok"  # Safe var preserved
            assert parts[2] == "custom_val"  # Injected var passed

    def test_timeout_enforcement(self, temp_dir: Path):
        harness = SandboxHarness()
        cfg = SandboxConfig(workspace_dir=str(temp_dir), timeout_seconds=1)
        res = harness.execute("sleep 3", config=cfg, prefer_fallback=True)

        assert res.timed_out
        assert res.exit_code == 124
        assert "timed out" in res.stderr

    def test_container_execution_arguments_mocked(self, temp_dir: Path):
        harness = SandboxHarness()
        cfg = SandboxConfig(
            image="python:3.11-alpine",
            timeout_seconds=10,
            memory_limit_mb=256,
            cpu_quota=0.5,
            workspace_dir=str(temp_dir),
            read_only_root=True,
            allow_network=False,
            env_vars={"FOO": "BAR"},
        )

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "container output"
        mock_proc.stderr = ""

        with patch.object(harness, "check_container_runtime", return_value=(True, "docker")):
            with patch("subprocess.run", return_value=mock_proc) as mock_sub:
                res = harness.execute("echo hi", config=cfg, prefer_fallback=False)

                assert res.exit_code == 0
                assert res.isolation_backend == "container"
                assert mock_sub.called
                cmd_args = mock_sub.call_args[0][0]
                assert "docker" in cmd_args
                assert "run" in cmd_args
                assert "--memory=256m" in cmd_args
                assert "--cpus=0.5" in cmd_args
                assert "--network=none" in cmd_args
                assert "--read-only" in cmd_args
                assert "-e" in cmd_args
                assert "FOO=BAR" in cmd_args
                assert "python:3.11-alpine" in cmd_args

    def test_status_metrics_and_history(self, temp_dir: Path):
        harness = SandboxHarness()
        cfg = SandboxConfig(workspace_dir=str(temp_dir))

        status_before = harness.get_status()
        initial_execs = status_before.total_executions

        res1 = harness.execute("echo test1", config=cfg, prefer_fallback=True)
        res2 = harness.execute("sh -c 'exit 42'", config=cfg, prefer_fallback=True)

        status_after = harness.get_status()
        assert status_after.total_executions == initial_execs + 2
        assert status_after.total_failures >= 1
        assert len(status_after.recent_executions) >= 2
        assert any(r.command == "echo test1" for r in status_after.recent_executions)


class TestCliCommands:
    """Tests for Typer CLI package and sandbox commands."""

    def test_cli_package_verify(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["package", "--verify"])
        assert result.exit_code == 0
        assert "Package metadata" in result.output

    def test_cli_package_verify_json(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["package", "--verify", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["metadata"]["name"] == "mekong-cli"

    def test_cli_package_build_homebrew(self, temp_dir: Path):
        app = build_app()
        runner = CliRunner()
        out_dir = str(temp_dir / "dist_brew")
        result = runner.invoke(app, ["package", "--target", "homebrew", "--output-dir", out_dir, "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_valid"] is True
        assert any(a["artifact_type"] == "homebrew_formula" for a in data["artifacts"])

    def test_cli_sandbox_status_json(self):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["sandbox", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "is_docker_available" in data
        assert "total_executions" in data

    def test_cli_sandbox_run_json(self, temp_dir: Path):
        app = build_app()
        runner = CliRunner()
        result = runner.invoke(app, ["sandbox", "run", "echo 'cli_sandbox_ok'", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["exit_code"] == 0
        assert "cli_sandbox_ok" in data["stdout"]


class TestMcpToolsParity:
    """Tests for native MCP tools packaging and sandbox parity."""

    def test_mcp_package_build_fallback(self, temp_dir: Path):
        from scripts.mcp_server import handle_package_build
        res = handle_package_build({"target": "homebrew", "output_dir": str(temp_dir / "mcp_dist")})
        data = json.loads(res)
        assert data["ok"] is True
        assert data["data"]["is_valid"] is True
        assert any(a["artifact_type"] == "homebrew_formula" for a in data["data"]["artifacts"])

    def test_mcp_sandbox_exec_fallback(self):
        from scripts.mcp_server import handle_sandbox_exec
        res = handle_sandbox_exec({"command": "echo 'mcp_sandbox_hello'", "timeout": 5})
        data = json.loads(res)
        assert data["ok"] is True
        assert data["data"]["exit_code"] == 0
        assert "mcp_sandbox_hello" in data["data"]["stdout"]

    def test_core_mcp_server_package_and_sandbox(self, temp_dir: Path):
        from src.core.mcp_server import MekongMcpServer
        server = MekongMcpServer()
        pkg_raw = server._handle_package_build({"target": "docker", "output_dir": str(temp_dir / "core_mcp_dist")})
        pkg_data = json.loads(pkg_raw)
        assert pkg_data["ok"] is True
        assert pkg_data["data"]["is_valid"] is True

        sb_raw = server._handle_sandbox_exec({"command": "echo 'core_mcp_sb_hello'"})
        sb_data = json.loads(sb_raw)
        assert sb_data["ok"] is True
        assert sb_data["data"]["exit_code"] == 0


class TestAstCoreBoundary:
    """Verify standard-library-only rule for packaging_bridge.py and sandbox_bridge.py."""

    FORBIDDEN_MODULES = {"anthropic", "openai", "requests", "httpx", "fastapi", "pydantic", "aiohttp"}

    @pytest.mark.parametrize("rel_path", [
        "src/core/packaging_bridge.py",
        "src/core/sandbox_bridge.py",
    ])
    def test_pure_standard_library_imports(self, rel_path: str):
        full_path = Path(__file__).resolve().parents[1] / rel_path
        assert full_path.exists(), f"File {rel_path} does not exist"

        tree = ast.parse(full_path.read_text(encoding="utf-8"), filename=rel_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    assert root_pkg not in self.FORBIDDEN_MODULES, (
                        f"Forbidden import '{alias.name}' found in {rel_path} (line {node.lineno})"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    assert root_pkg not in self.FORBIDDEN_MODULES, (
                        f"Forbidden from-import '{node.module}' found in {rel_path} (line {node.lineno})"
                    )
