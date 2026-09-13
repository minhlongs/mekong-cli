# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for CodeEvolutionEngine and associated data structures (src/core/code_evolution.py).

All tests are hermetic and deterministic: git commands and LLM clients are mocked
to prevent filesystem/git mutations and ensure 100% statement and branch coverage.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.core.code_evolution import (
    CodeChange,
    CodeEvolutionEngine,
    EvolutionAttempt,
    EvolutionStatus,
)


# ===========================================================================
# Dataclass & Enum Tests
# ===========================================================================


class TestEvolutionAttempt:
    def test_default_values(self):
        a = EvolutionAttempt()
        assert a.id == ""
        assert a.description == ""
        assert a.changes == []
        assert a.status == EvolutionStatus.PROPOSED
        assert a.test_results == ""
        assert a.branch_name == ""
        assert a.reasoning == ""
        assert a.rollback_data == {}
        assert isinstance(a.timestamp, float)

    def test_fields_settable(self):
        change = CodeChange(file_path="src/core/test.py", change_type="modify")
        a = EvolutionAttempt(
            id="evo-123",
            description="Fix bug",
            changes=[change],
            status=EvolutionStatus.APPLIED,
            test_results="all passed",
            branch_name="evolution/evo-123",
            reasoning="Performance fix",
            rollback_data={"src/core/test.py": "old code"},
        )
        assert a.id == "evo-123"
        assert a.description == "Fix bug"
        assert len(a.changes) == 1
        assert a.status == EvolutionStatus.APPLIED
        assert a.rollback_data["src/core/test.py"] == "old code"


class TestCodeChange:
    def test_default_values(self):
        c = CodeChange(file_path="src/core/test.py")
        assert c.file_path == "src/core/test.py"
        assert c.original_content == ""
        assert c.modified_content == ""
        assert c.description == ""
        assert c.change_type == "modify"

    def test_fields_settable(self):
        c = CodeChange(
            file_path="src/core/new.py",
            original_content="a = 1",
            modified_content="a = 2",
            description="update a",
            change_type="create",
        )
        assert c.change_type == "create"
        assert c.modified_content == "a = 2"


class TestEvolutionStatus:
    def test_all_statuses(self):
        assert len(EvolutionStatus) == 6
        assert EvolutionStatus.PROPOSED.value == "proposed"
        assert EvolutionStatus.TESTING.value == "testing"
        assert EvolutionStatus.PASSED.value == "passed"
        assert EvolutionStatus.FAILED.value == "failed"
        assert EvolutionStatus.APPLIED.value == "applied"
        assert EvolutionStatus.ROLLED_BACK.value == "rolled_back"


# ===========================================================================
# CodeEvolutionEngine Initialization & Journal Loading
# ===========================================================================


class TestCodeEvolutionEngineInit:
    def test_init_defaults(self, tmp_path):
        engine = CodeEvolutionEngine(project_root=str(tmp_path))
        assert engine.project_root == tmp_path
        assert engine.llm_client is None
        assert engine._journal_path == Path(".mekong/evolution_journal.yaml")
        assert engine._journal == []

    def test_load_journal_nonexistent(self, tmp_path):
        journal = tmp_path / "nonexistent.yaml"
        engine = CodeEvolutionEngine(project_root=str(tmp_path), journal_path=str(journal))
        assert engine._journal == []

    def test_load_journal_valid_and_invalid_statuses(self, tmp_path):
        journal = tmp_path / "journal.yaml"
        data = [
            {
                "id": "evo-1",
                "description": "first",
                "status": "applied",
                "test_results": "ok",
                "branch_name": "b1",
                "timestamp": 123.0,
                "reasoning": "r1",
            },
            {
                "id": "evo-2",
                "description": "second",
                "status": "invalid_status_string",  # Fallback to PROPOSED
                "test_results": "",
                "branch_name": "b2",
                "timestamp": 124.0,
                "reasoning": "r2",
            },
        ]
        journal.write_text(yaml.dump(data))
        engine = CodeEvolutionEngine(project_root=str(tmp_path), journal_path=str(journal))
        assert len(engine._journal) == 2
        assert engine._journal[0].status == EvolutionStatus.APPLIED
        assert engine._journal[1].status == EvolutionStatus.PROPOSED

    def test_load_journal_corrupted_yaml(self, tmp_path):
        journal = tmp_path / "corrupt.yaml"
        journal.write_text("invalid: [yaml: broken")
        engine = CodeEvolutionEngine(project_root=str(tmp_path), journal_path=str(journal))
        assert engine._journal == []


# ===========================================================================
# Source Analysis (analyze_source)
# ===========================================================================


class TestAnalyzeSource:
    def test_analyze_nonexistent_directory(self, tmp_path):
        engine = CodeEvolutionEngine(project_root=str(tmp_path))
        res = engine.analyze_source("nonexistent_dir")
        assert "error" in res

    def test_analyze_source_detects_all_patterns(self, tmp_path):
        src_core = tmp_path / "src" / "core"
        src_core.mkdir(parents=True)

        # File with > 500 lines, long lines > 120, bare except, and TODO marker
        long_line = "x = '" + "a" * 130 + "'"
        lines = ["def func1():\n    pass\n"]
        lines.append(long_line + "\n")
        lines.append("try:\n    pass\nexcept:\n    pass\n")
        lines.append("# TODO: refactor this\n")
        # Pad to over 500 lines
        lines.extend(["# comment line\n"] * 520)

        sample_file = src_core / "complex_module.py"
        sample_file.write_text("".join(lines))

        # Unreadable file to trigger read_text exception handler
        bad_file = src_core / "bad.py"
        bad_file.write_text("def ok(): pass")

        engine = CodeEvolutionEngine(project_root=str(tmp_path))

        with patch.object(Path, "read_text", side_effect=[
            "".join(lines),
            OSError("Permission denied"),
        ]):
            report = engine.analyze_source("src/core")

        assert report["target"] == "src/core"
        assert report["total_lines"] > 500
        assert report["total_functions"] >= 1
        assert any("Too large" in issue for issue in report["issues"])
        assert any("broad exception handling" in issue for issue in report["issues"])
        assert any("TODO/FIXME" in issue for issue in report["issues"])
        assert report["files"][0]["long_lines"] >= 1


# ===========================================================================
# Propose Evolution & Safety Checks
# ===========================================================================


class TestProposeEvolution:
    def test_safety_checks(self, tmp_path):
        engine = CodeEvolutionEngine(project_root=str(tmp_path))
        # Forbidden files
        assert engine._is_safe_to_modify("src/core/governance.py") is False
        assert engine._is_safe_to_modify("src/core/code_evolution.py") is False
        # Allowed directories
        assert engine._is_safe_to_modify("src/core/nlu.py") is True
        assert engine._is_safe_to_modify("src/agents/worker.py") is True
        # Disallowed directories
        assert engine._is_safe_to_modify("src/config.py") is False
        assert engine._is_safe_to_modify("main.py") is False

    def test_propose_unsafe_file_returns_none(self, tmp_path):
        engine = CodeEvolutionEngine(project_root=str(tmp_path))
        res = engine.propose_evolution("src/core/governance.py", "modify safety")
        assert res is None

    def test_propose_nonexistent_file_returns_none(self, tmp_path):
        engine = CodeEvolutionEngine(project_root=str(tmp_path))
        res = engine.propose_evolution("src/core/not_there.py", "improve")
        assert res is None

    def test_propose_without_llm_returns_none(self, tmp_path):
        file_path = tmp_path / "src" / "core" / "sample.py"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("def hello(): return 1")

        engine = CodeEvolutionEngine(project_root=str(tmp_path), llm_client=None)
        res = engine.propose_evolution("src/core/sample.py", "improve")
        assert res is None

    def test_propose_with_llm_identical_code_returns_none(self, tmp_path):
        file_path = tmp_path / "src" / "core" / "sample.py"
        file_path.parent.mkdir(parents=True)
        content = "def hello(): return 1"
        file_path.write_text(content)

        fake_llm = MagicMock()
        fake_llm.generate.return_value = content  # No change

        engine = CodeEvolutionEngine(project_root=str(tmp_path), llm_client=fake_llm)
        res = engine.propose_evolution("src/core/sample.py", "improve")
        assert res is None

    def test_propose_with_llm_empty_response_returns_none(self, tmp_path):
        file_path = tmp_path / "src" / "core" / "sample.py"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("def hello(): return 1")

        fake_llm = MagicMock()
        fake_llm.generate.return_value = ""

        engine = CodeEvolutionEngine(project_root=str(tmp_path), llm_client=fake_llm)
        res = engine.propose_evolution("src/core/sample.py", "improve")
        assert res is None

    def test_propose_with_llm_exception_returns_none(self, tmp_path):
        file_path = tmp_path / "src" / "core" / "sample.py"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("def hello(): return 1")

        fake_llm = MagicMock()
        fake_llm.generate.side_effect = RuntimeError("API down")

        engine = CodeEvolutionEngine(project_root=str(tmp_path), llm_client=fake_llm)
        res = engine.propose_evolution("src/core/sample.py", "improve")
        assert res is None

    def test_propose_success_records_journal_and_emits_event(self, tmp_path):
        file_path = tmp_path / "src" / "core" / "sample.py"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("def hello(): return 1")
        journal_file = tmp_path / ".mekong" / "journal.yaml"

        fake_llm = MagicMock()
        fake_llm.generate.return_value = "def hello(): return 2"

        engine = CodeEvolutionEngine(
            project_root=str(tmp_path),
            llm_client=fake_llm,
            journal_path=str(journal_file),
        )

        with patch("src.core.code_evolution.get_event_bus") as mock_bus:
            attempt = engine.propose_evolution("src/core/sample.py", "return 2 instead")
            assert attempt is not None
            assert attempt.status == EvolutionStatus.PROPOSED
            assert attempt.changes[0].modified_content == "def hello(): return 2"
            assert len(engine._journal) == 1
            assert journal_file.exists()
            mock_bus.return_value.emit.assert_called_once()


# ===========================================================================
# Test Evolution (test_evolution)
# ===========================================================================


class TestEvolutionTesting:
    @pytest.fixture(autouse=True)
    def setup_engine(self, tmp_path):
        self.tmp_path = tmp_path
        self.file_path = tmp_path / "src" / "core" / "module.py"
        self.file_path.parent.mkdir(parents=True)
        self.file_path.write_text("original code")
        self.journal_file = tmp_path / ".mekong" / "journal.yaml"

        self.engine = CodeEvolutionEngine(
            project_root=str(tmp_path),
            journal_path=str(self.journal_file),
        )

    def test_test_evolution_passes(self):
        attempt = EvolutionAttempt(
            id="evo-pass",
            description="pass test",
            changes=[CodeChange(
                file_path="src/core/module.py",
                original_content="original code",
                modified_content="modified code",
            )],
            branch_name="evolution/evo-pass",
        )

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "PASSED"
        mock_proc.stderr = ""

        with patch.object(self.engine, "_git_cmd", return_value="main") as mock_git:
            with patch("subprocess.run", return_value=mock_proc):
                passed = self.engine.test_evolution(attempt)
                assert passed is True
                assert attempt.status == EvolutionStatus.PASSED
                assert "PASSED" in attempt.test_results
                assert mock_git.call_count >= 5  # rev-parse, checkout -b, add -A, commit, checkout main

    def test_test_evolution_fails_restores_original_and_deletes_branch(self):
        attempt = EvolutionAttempt(
            id="evo-fail",
            description="fail test",
            changes=[CodeChange(
                file_path="src/core/module.py",
                original_content="original code",
                modified_content="modified code",
            )],
            branch_name="evolution/evo-fail",
        )

        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = "FAILED"
        mock_proc.stderr = "AssertionError"

        with patch.object(self.engine, "_git_cmd", return_value="main") as mock_git:
            with patch("subprocess.run", return_value=mock_proc):
                passed = self.engine.test_evolution(attempt)
                assert passed is False
                assert attempt.status == EvolutionStatus.FAILED
                assert self.file_path.read_text() == "original code"
                mock_git.assert_any_call("branch -D evolution/evo-fail")

    def test_test_evolution_exception_restores_original_and_cleans_up(self):
        attempt = EvolutionAttempt(
            id="evo-err",
            description="error test",
            changes=[CodeChange(
                file_path="src/core/module.py",
                original_content="original code",
                modified_content="modified code",
            )],
            branch_name="evolution/evo-err",
        )

        with patch.object(self.engine, "_git_cmd") as mock_git:
            mock_git.side_effect = ["main", RuntimeError("git checkout failed"), "main", ""]
            passed = self.engine.test_evolution(attempt)
            assert passed is False
            assert attempt.status == EvolutionStatus.FAILED
            assert "git checkout failed" in attempt.test_results

    def test_test_evolution_exception_with_restore_error_handled(self):
        attempt = EvolutionAttempt(
            id="evo-err2",
            description="error test 2",
            changes=[CodeChange(
                file_path="src/core/module.py",
                original_content="original code",
                modified_content="modified code",
            )],
            branch_name="evolution/evo-err2",
        )

        orig_write_text = Path.write_text

        def write_side_effect(path_self, *args, **kwargs):
            if "module.py" in str(path_self):
                raise OSError("module write failed")
            return orig_write_text(path_self, *args, **kwargs)

        with patch.object(self.engine, "_git_cmd", return_value="main"):
            with patch.object(Path, "write_text", side_effect=write_side_effect, autospec=True):
                passed = self.engine.test_evolution(attempt)
                assert passed is False
                assert attempt.status == EvolutionStatus.FAILED


# ===========================================================================
# Apply Evolution & Rollback
# ===========================================================================


class TestApplyAndRollback:
    @pytest.fixture(autouse=True)
    def setup_engine(self, tmp_path):
        self.tmp_path = tmp_path
        self.file_path = tmp_path / "src" / "core" / "module.py"
        self.file_path.parent.mkdir(parents=True)
        self.file_path.write_text("original code")
        self.journal_file = tmp_path / ".mekong" / "journal.yaml"

        self.engine = CodeEvolutionEngine(
            project_root=str(tmp_path),
            journal_path=str(self.journal_file),
        )

    def test_apply_evolution_not_passed_returns_false(self):
        attempt = EvolutionAttempt(id="evo-1", status=EvolutionStatus.PROPOSED)
        assert self.engine.apply_evolution(attempt) is False

    def test_apply_evolution_success(self):
        attempt = EvolutionAttempt(
            id="evo-apply",
            description="apply success",
            status=EvolutionStatus.PASSED,
            branch_name="evolution/evo-apply",
        )

        with patch.object(self.engine, "_git_cmd", return_value="merged"):
            with patch("src.core.code_evolution.get_event_bus") as mock_bus:
                applied = self.engine.apply_evolution(attempt)
                assert applied is True
                assert attempt.status == EvolutionStatus.APPLIED
                mock_bus.return_value.emit.assert_called_once()

    def test_apply_evolution_git_merge_fails(self):
        attempt = EvolutionAttempt(
            id="evo-merge-fail",
            status=EvolutionStatus.PASSED,
            branch_name="evolution/evo-merge-fail",
        )

        with patch.object(self.engine, "_git_cmd", side_effect=RuntimeError("conflict")):
            applied = self.engine.apply_evolution(attempt)
            assert applied is False
            assert attempt.status == EvolutionStatus.FAILED

    def test_rollback_nonexistent_or_not_applied(self):
        assert self.engine.rollback("nonexistent") is False

        attempt = EvolutionAttempt(id="evo-passed-only", status=EvolutionStatus.PASSED)
        self.engine._journal.append(attempt)
        assert self.engine.rollback("evo-passed-only") is False

    def test_rollback_success(self):
        self.file_path.write_text("modified code")
        attempt = EvolutionAttempt(
            id="evo-roll",
            status=EvolutionStatus.APPLIED,
            rollback_data={"src/core/module.py": "original code"},
        )
        self.engine._journal.append(attempt)

        rolled = self.engine.rollback("evo-roll")
        assert rolled is True
        assert attempt.status == EvolutionStatus.ROLLED_BACK
        assert self.file_path.read_text() == "original code"

    def test_rollback_write_exception_handled(self):
        attempt = EvolutionAttempt(
            id="evo-roll-err",
            status=EvolutionStatus.APPLIED,
            rollback_data={"src/core/module.py": "original code"},
        )
        self.engine._journal.append(attempt)

        with patch.object(Path, "write_text", side_effect=OSError("disk full")):
            assert self.engine.rollback("evo-roll-err") is False


# ===========================================================================
# Journal, Stats, and Helper Utilities
# ===========================================================================


class TestJournalStatsAndHelpers:
    @pytest.fixture(autouse=True)
    def setup_engine(self, tmp_path):
        self.tmp_path = tmp_path
        self.engine = CodeEvolutionEngine(project_root=str(tmp_path))

    def test_get_journal_limit(self):
        for i in range(30):
            self.engine._journal.append(EvolutionAttempt(id=f"evo-{i}"))
        journal = self.engine.get_journal(limit=10)
        assert len(journal) == 10
        assert journal[-1].id == "evo-29"

    def test_get_stats_empty(self):
        stats = self.engine.get_stats()
        assert stats["total_attempts"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["applied"] == 0

    def test_get_stats_populated(self):
        self.engine._journal.extend([
            EvolutionAttempt(id="1", status=EvolutionStatus.APPLIED),
            EvolutionAttempt(id="2", status=EvolutionStatus.PASSED),
            EvolutionAttempt(id="3", status=EvolutionStatus.FAILED),
            EvolutionAttempt(id="4", status=EvolutionStatus.ROLLED_BACK),
        ])
        stats = self.engine.get_stats()
        assert stats["total_attempts"] == 4
        assert stats["applied"] == 1
        assert stats["passed"] == 2  # APPLIED + PASSED
        assert stats["failed"] == 1
        assert stats["rolled_back"] == 1
        assert stats["success_rate"] == 0.5

    def test_git_cmd_real_subprocess_mocked(self):
        mock_proc = MagicMock()
        mock_proc.stdout = "main\n"
        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            out = self.engine._git_cmd("branch --show-current")
            assert out == "main"
            mock_run.assert_called_once_with(
                "git branch --show-current",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.tmp_path),
            )

    def test_llm_generate_improvement_without_llm(self):
        assert self.engine._llm_generate_improvement("file.py", "orig", "desc") == ""

    def test_llm_generate_improvement_with_llm(self):
        fake_llm = MagicMock()
        fake_llm.generate.return_value = "new code"
        self.engine.llm_client = fake_llm
        out = self.engine._llm_generate_improvement("file.py", "orig", "desc")
        assert out == "new code"
        assert fake_llm.generate.call_count == 1
