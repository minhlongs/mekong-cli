# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Automated test suite for Antigravity Project Scaffolding Engine (R4).

Validates:
1. TestScaffoldCoreEngine: Python API unit tests for scaffolding, dry-run,
   force overwrite, profiles (full, minimal, antigravity, unknown).
2. TestScaffoldCliCommands: End-to-end CLI execution with --dry-run, --json,
   --force, and default target resolution.
3. TestScaffoldArtifactIntegrity: Deep verification of YAML frontmatter,
   subagents registry and definitions, hooks.json, mcp_config.json,
   executable bits, and rules.
4. TestScaffoldEdgeCasesAndSecurity: Path traversal protection, non-directory
   targets, deeply nested paths, and git vs non-git parity.
5. TestScaffoldNonRegressionAndHealth: Static analysis boundary adherence
   (10/10) and Antigravity system healthcheck (36/36 HEALTHY).
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from src.core.scaffold import (
    MINIMAL_SKILLS,
    MINIMAL_SUBAGENTS,
    PROTECTED_SYSTEM_DIRS,
    ScaffoldResult,
    scaffold_antigravity_project,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_init_cli(
    args: list[str],
    cwd: Path | str | None = None,
    timeout: float = 30.0,
) -> subprocess.CompletedProcess[str]:
    """Execute `python3 -m src.main init <args>` in subprocess."""
    work_dir = str(cwd) if cwd is not None else str(PROJECT_ROOT)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    cmd = [sys.executable, "-m", "src.main", "init", *args]
    return subprocess.run(
        cmd,
        cwd=work_dir,
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
    )


# =============================================================================
# 1. TestScaffoldCoreEngine (Python API)
# =============================================================================


class TestScaffoldCoreEngine:
    """Core scaffolding engine API unit tests."""

    def test_scaffold_fresh_directory_full_profile(self, tmp_path: Path) -> None:
        """Scaffolds a fresh directory, asserting skills, subagents, hooks, MCP, rules."""
        target = tmp_path / "fresh_workspace"
        assert not target.exists()

        result = scaffold_antigravity_project(
            target_path=target,
            profile="full",
            dry_run=False,
            force=False,
        )

        assert result.success is True
        assert result.ok is True
        assert result.error is None
        assert result.profile == "full"
        assert result.target_path == target.resolve()

        # Counts / stats check
        assert result.counts["skills"] == 234
        assert result.counts["subagents"] == 25
        assert result.stats["skills"] == 234
        assert result.stats["subagents"] == 25
        assert result.stats["rules"] >= 2
        assert len(result.created_files) >= 265
        assert len(result.skipped_files) == 0
        assert len(result.modified_files) == 0

        # Filesystem verification
        skills_dir = target / ".agents" / "skills"
        assert skills_dir.is_dir()
        skill_dirs = [p for p in skills_dir.iterdir() if p.is_dir()]
        assert len(skill_dirs) == 234

        subagents_dir = target / ".agents" / "subagents"
        assert (subagents_dir / "registry.json").is_file()
        defs_dir = subagents_dir / "definitions"
        assert defs_dir.is_dir()
        def_files = list(defs_dir.glob("*.md"))
        assert len(def_files) == 25

        assert (target / ".agents" / "hooks.json").is_file()
        assert (target / ".agents" / "mcp_config.json").is_file()
        assert (target / "scripts" / "mcp_server.py").is_file()
        assert (target / "scripts" / "hooks" / "pre_tool_guardrail.py").is_file()
        assert (target / "scripts" / "hooks" / "post_tool_audit.py").is_file()
        assert (target / "GEMINI.md").is_file()
        assert (target / "HARNESS.md").is_file()
        assert (target / ".mekong").is_dir()

    def test_scaffold_dry_run_zero_mutation_fresh_target(self, tmp_path: Path) -> None:
        """Dry-run on a fresh target must create 0 files and leave disk untouched."""
        target = tmp_path / "dry_run_new_workspace"
        assert not target.exists()

        result = scaffold_antigravity_project(
            target_path=target,
            profile="full",
            dry_run=True,
            force=False,
        )

        assert result.success is True
        assert result.ok is True
        assert not target.exists(), "Target directory must not be created during dry-run"
        assert len(result.created_files) >= 265
        assert len(result.skipped_files) == 0
        assert len(result.modified_files) == 0

    def test_scaffold_dry_run_zero_mutation_existing_target(self, tmp_path: Path) -> None:
        """Dry-run on an existing directory leaves pre-existing files completely untouched."""
        target = tmp_path / "existing_dir"
        target.mkdir(parents=True)
        canary = target / "canary.txt"
        canary.write_text("CANARY_DATA_DO_NOT_TOUCH", encoding="utf-8")
        orig_mtime = canary.stat().st_mtime_ns

        result = scaffold_antigravity_project(
            target_path=target,
            profile="full",
            dry_run=True,
            force=False,
        )

        assert result.success is True
        assert result.ok is True

        # Existing files untouched and zero new files created
        files_after = list(target.rglob("*"))
        assert files_after == [canary]
        assert canary.read_text(encoding="utf-8") == "CANARY_DATA_DO_NOT_TOUCH"
        assert canary.stat().st_mtime_ns == orig_mtime

    def test_scaffold_force_overwrite_behavior(self, tmp_path: Path) -> None:
        """Existing files are preserved without force, and overwritten when force=True."""
        target = tmp_path / "overwrite_test"
        target.mkdir(parents=True)
        custom_gemini = target / "GEMINI.md"
        custom_gemini.write_text("CUSTOM_USER_RULE_SENTINEL", encoding="utf-8")

        # Step 1: Run without force -> GEMINI.md should be skipped
        res1 = scaffold_antigravity_project(target, force=False)
        assert res1.success is True
        assert custom_gemini.read_text(encoding="utf-8") == "CUSTOM_USER_RULE_SENTINEL"
        assert "GEMINI.md" in res1.skipped_files
        assert "GEMINI.md" not in res1.modified_files

        # Step 2: Run with force -> GEMINI.md should be overwritten and recorded in modified_files
        res2 = scaffold_antigravity_project(target, force=True)
        assert res2.success is True
        assert "GEMINI.md" in res2.modified_files
        assert custom_gemini.read_text(encoding="utf-8") != "CUSTOM_USER_RULE_SENTINEL"

    def test_scaffold_profiles_selection(self, tmp_path: Path) -> None:
        """Validates minimal, antigravity, and invalid profile error handling."""
        # Minimal profile
        min_target = tmp_path / "min_proj"
        res_min = scaffold_antigravity_project(min_target, profile="minimal")
        assert res_min.success is True
        assert 20 <= res_min.counts["skills"] < 50
        assert res_min.counts["subagents"] == len(MINIMAL_SUBAGENTS)

        # Core minimal skills exist
        for skill_name in ("cook", "plan", "ship", "doctor", "binh-phap", "status"):
            assert (min_target / ".agents" / "skills" / skill_name / "SKILL.md").is_file()

        # Antigravity profile (full compatibility stack)
        ag_target = tmp_path / "ag_proj"
        res_ag = scaffold_antigravity_project(ag_target, profile="antigravity")
        assert res_ag.success is True
        assert res_ag.counts["skills"] == 234
        assert res_ag.counts["subagents"] == 25

        # Unknown profile raises ValueError
        with pytest.raises(ValueError, match="Unknown profile 'unknown'"):
            scaffold_antigravity_project(tmp_path / "err_proj", profile="unknown")


# =============================================================================
# 2. TestScaffoldCliCommands (CLI Subprocess)
# =============================================================================


class TestScaffoldCliCommands:
    """CLI end-to-end command invocations."""

    def test_cli_init_fresh_target_console(self, tmp_path: Path) -> None:
        """Invoke `python3 -m src.main init <path>` in standard console mode."""
        target = tmp_path / "cli_workspace"
        res = run_init_cli([str(target)])
        assert res.returncode == 0, f"CLI init failed with stderr: {res.stderr}"

        # Terminal output validations
        output = res.stdout
        assert "Genesis Complete" in output or "Initialized Antigravity Project" in output
        assert "234" in output
        assert "25" in output
        assert (target / ".agents" / "skills").is_dir()
        assert (target / "GEMINI.md").is_file()

    def test_cli_init_dry_run_console(self, tmp_path: Path) -> None:
        """Invoke `python3 -m src.main init <path> --dry-run` and verify zero disk mutation."""
        target = tmp_path / "cli_dry"
        res = run_init_cli([str(target), "--dry-run"])
        assert res.returncode == 0, f"Dry-run failed: {res.stderr}"

        output = res.stdout
        assert "Dry Run" in output or "Preview" in output
        assert not target.exists(), "Dry-run CLI must not create target directory"

    def test_cli_init_json_output(self, tmp_path: Path) -> None:
        """Invoke `python3 -m src.main init <path> --json` and assert structured JSON payload."""
        target = tmp_path / "cli_json"
        res = run_init_cli([str(target), "--json"])
        assert res.returncode == 0, f"JSON init failed: {res.stderr}"

        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["status"] == "scaffolded"
        assert data["target"] == str(target.resolve())
        assert data["profile"] == "full"
        assert data["dry_run"] is False
        assert data["force"] is False
        assert data["counts"]["skills"] == 234
        assert data["counts"]["subagents"] == 25
        assert len(data["created_files"]) >= 265
        assert data["skipped_files"] == []
        assert data["modified_files"] == []
        assert data["error"] is None

    def test_cli_init_dry_run_json(self, tmp_path: Path) -> None:
        """Invoke `init <path> --dry-run --json` and assert dry_run status in JSON."""
        target = tmp_path / "cli_dry_json"
        res = run_init_cli([str(target), "--dry-run", "--json"])
        assert res.returncode == 0, f"Dry-run JSON failed: {res.stderr}"

        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["status"] == "dry_run"
        assert data["dry_run"] is True
        assert not target.exists()
        assert len(data["created_files"]) >= 265

    def test_cli_init_force_flag_cli(self, tmp_path: Path) -> None:
        """Verify `--force` and `-f` flags via CLI execution."""
        target = tmp_path / "cli_force"
        target.mkdir(parents=True)
        gemini = target / "GEMINI.md"
        gemini.write_text("SENTINEL_CLI_CONTENT", encoding="utf-8")

        # Live run without force -> skipped
        res1 = run_init_cli([str(target), "--json"])
        assert res1.returncode == 0
        data1 = json.loads(res1.stdout)
        assert "GEMINI.md" in data1["skipped_files"]
        assert gemini.read_text(encoding="utf-8") == "SENTINEL_CLI_CONTENT"

        # Live run with --force -> modified
        res2 = run_init_cli([str(target), "--force", "--json"])
        assert res2.returncode == 0
        data2 = json.loads(res2.stdout)
        assert "GEMINI.md" in data2["modified_files"]
        assert gemini.read_text(encoding="utf-8") != "SENTINEL_CLI_CONTENT"

    def test_cli_init_default_to_current_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify running `init` with no path argument defaults to current working directory."""
        cwd_project = tmp_path / "cwd_project"
        cwd_project.mkdir(parents=True)

        res = run_init_cli(["--json"], cwd=cwd_project)
        assert res.returncode == 0, f"Default cwd init failed: {res.stderr}"

        data = json.loads(res.stdout)
        assert data["ok"] is True
        assert data["target"] == str(cwd_project.resolve())
        assert (cwd_project / ".agents" / "skills").is_dir()
        assert (cwd_project / "GEMINI.md").is_file()


# =============================================================================
# 3. TestScaffoldArtifactIntegrity (Schemas & Permissions)
# =============================================================================


class TestScaffoldArtifactIntegrity:
    """Artifact schema, frontmatter, and file permission integrity."""

    def test_scaffolded_skills_yaml_frontmatter(self, tmp_path: Path) -> None:
        """Validate all 234 skills have valid YAML frontmatter per healthcheck rules."""
        target = tmp_path / "integrity_skills"
        result = scaffold_antigravity_project(target)
        assert result.success is True

        skills_dir = target / ".agents" / "skills"
        skills = sorted([p for p in skills_dir.iterdir() if p.is_dir()])
        assert len(skills) == 234

        for skill_path in skills:
            skill_md = skill_path / "SKILL.md"
            assert skill_md.is_file(), f"Missing SKILL.md in {skill_path}"

            lines = skill_md.read_text(encoding="utf-8").splitlines()
            assert len(lines) >= 3, f"SKILL.md too short: {skill_md}"
            assert lines[0].strip() == "---", f"First line must be '---' in {skill_md}"

            # Check closing frontmatter delimiter within lines 1-20
            closing_idx = -1
            for idx, line in enumerate(lines[1:20], start=1):
                if line.strip() == "---":
                    closing_idx = idx
                    break
            assert closing_idx != -1, f"Missing closing '---' delimiter in {skill_md}"

            frontmatter_lines = lines[1:closing_idx]
            has_name = any(line.strip().startswith("name:") for line in frontmatter_lines)
            has_desc = any(line.strip().startswith("description:") for line in frontmatter_lines)

            assert has_name, f"Missing 'name:' in frontmatter of {skill_md}"
            assert has_desc, f"Missing 'description:' in frontmatter of {skill_md}"

    def test_scaffolded_subagent_registry_and_definitions(self, tmp_path: Path) -> None:
        """Validate `registry.json` structure and corresponding 25 definition markdowns."""
        target = tmp_path / "integrity_subagents"
        result = scaffold_antigravity_project(target)
        assert result.success is True

        reg_file = target / ".agents" / "subagents" / "registry.json"
        assert reg_file.is_file()
        registry = json.loads(reg_file.read_text(encoding="utf-8"))

        agents = registry.get("agents", [])
        assert len(agents) == 25

        defs_dir = target / ".agents" / "subagents" / "definitions"
        assert defs_dir.is_dir()

        for agent in agents:
            agent_id = agent["id"]
            def_path = defs_dir / f"{agent_id}.md"
            assert def_path.is_file(), f"Missing definition file for agent '{agent_id}'"
            content = def_path.read_text(encoding="utf-8")
            assert len(content) > 50, f"Definition file too small for agent '{agent_id}'"
            assert ("Role" in content or "Mission" in content or "You are" in content)

    def test_scaffolded_mcp_config_schema(self, tmp_path: Path) -> None:
        """Validate `mcp_config.json` schema and command definitions."""
        target = tmp_path / "integrity_mcp"
        result = scaffold_antigravity_project(target)
        assert result.success is True

        mcp_file = target / ".agents" / "mcp_config.json"
        assert mcp_file.is_file()
        mcp_data = json.loads(mcp_file.read_text(encoding="utf-8"))

        servers = mcp_data.get("mcpServers", {})
        assert "mekong-core" in servers
        assert "mekong-fabric" in servers

        core_server = servers["mekong-core"]
        assert core_server["command"] == "python3"
        assert "scripts/mcp_server.py" in core_server["args"]

        fabric_server = servers["mekong-fabric"]
        assert fabric_server["command"] == "python3"
        assert "--fabric" in fabric_server["args"]

    def test_scaffolded_hooks_schema(self, tmp_path: Path) -> None:
        """Validate `hooks.json` lifecycle hook schema."""
        target = tmp_path / "integrity_hooks"
        result = scaffold_antigravity_project(target)
        assert result.success is True

        hooks_file = target / ".agents" / "hooks.json"
        assert hooks_file.is_file()
        hooks_data = json.loads(hooks_file.read_text(encoding="utf-8"))

        assert "mekong-harness" in hooks_data
        harness_cfg = hooks_data["mekong-harness"]
        assert harness_cfg.get("enabled") is True
        assert "PreToolUse" in harness_cfg
        assert "PostToolUse" in harness_cfg

    def test_scaffolded_scripts_executable_bits(self, tmp_path: Path) -> None:
        """Verify executable permission bits on scripts under POSIX."""
        if os.name == "nt":
            pytest.skip("Executable bits check is POSIX-specific")

        target = tmp_path / "integrity_exec"
        result = scaffold_antigravity_project(target)
        assert result.success is True

        mcp_script = target / "scripts" / "mcp_server.py"
        pre_guard = target / "scripts" / "hooks" / "pre_tool_guardrail.py"
        post_audit = target / "scripts" / "hooks" / "post_tool_audit.py"

        assert os.access(mcp_script, os.X_OK), f"mcp_server.py is not executable: {mcp_script}"
        assert os.access(pre_guard, os.X_OK), f"pre_tool_guardrail.py is not executable: {pre_guard}"
        assert os.access(post_audit, os.X_OK), f"post_tool_audit.py is not executable: {post_audit}"

    def test_scaffolded_rules_content(self, tmp_path: Path) -> None:
        """Validate generated GEMINI.md and HARNESS.md content."""
        target = tmp_path / "integrity_rules"
        result = scaffold_antigravity_project(target)
        assert result.success is True

        gemini_content = (target / "GEMINI.md").read_text(encoding="utf-8")
        assert "Mekong CLI: CEO Solo Agentic Harness Engineering Platform" in gemini_content
        assert "/cook" in gemini_content

        harness_content = (target / "HARNESS.md").read_text(encoding="utf-8")
        assert "## 1. Context Budget" in harness_content
        assert "## 3. CEO Override Clauses" in harness_content


# =============================================================================
# 4. TestScaffoldEdgeCasesAndSecurity (Security & Edge Cases)
# =============================================================================


class TestScaffoldEdgeCasesAndSecurity:
    """Security boundaries, path traversal guards, and filesystem edge cases."""

    def test_path_traversal_protection(self, tmp_path: Path) -> None:
        """Refuses to scaffold into protected system root directories."""
        for protected_dir in ("/", "/etc", "/usr", "/bin", "/var"):
            with pytest.raises(ValueError, match="protected system directory"):
                scaffold_antigravity_project(protected_dir)

    def test_target_is_existing_file_fails(self, tmp_path: Path) -> None:
        """Targeting an existing regular file fails cleanly in Python API and CLI."""
        target_file = tmp_path / "not_a_dir.txt"
        target_file.write_text("THIS_IS_A_FILE", encoding="utf-8")

        # Python API raises ValueError
        with pytest.raises(ValueError, match="exists and is not a directory"):
            scaffold_antigravity_project(target_file)

        # CLI invocation returns non-zero with error in JSON
        res = run_init_cli([str(target_file), "--json"])
        assert res.returncode != 0
        data = json.loads(res.stdout)
        assert data["ok"] is False
        assert "not a directory" in data["error"]

    def test_deeply_nested_target_auto_creates_parents(self, tmp_path: Path) -> None:
        """Scaffolding deeply nested path creates all intermediate parents."""
        target = tmp_path / "level1" / "level2" / "level3" / "target_proj"
        assert not target.exists()

        result = scaffold_antigravity_project(target)
        assert result.success is True
        assert target.is_dir()
        assert (target / ".agents" / "skills").is_dir()
        assert result.counts["skills"] == 234

    def test_git_and_nongit_directory_parity(self, tmp_path: Path) -> None:
        """Ensures identical scaffolding behavior between git repos and non-git dirs."""
        git_target = tmp_path / "git_workspace"
        git_target.mkdir(parents=True)
        subprocess.run(["git", "init"], cwd=str(git_target), check=True, capture_output=True)

        plain_target = tmp_path / "plain_workspace"
        plain_target.mkdir(parents=True)

        res_git = scaffold_antigravity_project(git_target)
        res_plain = scaffold_antigravity_project(plain_target)

        assert res_git.success is True
        assert res_plain.success is True
        assert res_git.counts["skills"] == res_plain.counts["skills"] == 234
        assert res_git.counts["subagents"] == res_plain.counts["subagents"] == 25
        assert len(res_git.created_files) == len(res_plain.created_files)


# =============================================================================
# 5. TestScaffoldNonRegressionAndHealth (Non-Regression)
# =============================================================================


class TestScaffoldNonRegressionAndHealth:
    """Non-regression checks against AST boundary tests and healthcheck suite."""

    def test_core_boundary_static_analysis_passes(self) -> None:
        """Confirms `tests/test_core_boundary.py` passes 10/10 with zero vendor SDK imports."""
        env = dict(os.environ)
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        cmd = [sys.executable, "-m", "pytest", "tests/test_core_boundary.py"]
        res = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            env=env,
            timeout=30.0,
        )
        assert res.returncode == 0, f"Boundary test failed: {res.stderr}\n{res.stdout}"
        assert "10 passed" in res.stdout

    def test_antigravity_healthcheck_remains_healthy(self) -> None:
        """Confirms `scripts/antigravity_healthcheck.py` returns HEALTHY (exit 0)."""
        env = dict(os.environ)
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        cmd = [sys.executable, "scripts/antigravity_healthcheck.py"]
        res = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            env=env,
            timeout=90.0,
        )
        assert res.returncode == 0, f"Healthcheck failed: {res.stderr}\n{res.stdout}"
        assert "Status: HEALTHY" in res.stdout
