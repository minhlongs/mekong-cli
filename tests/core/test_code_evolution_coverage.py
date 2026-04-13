"""
Coverage-focused tests for CodeEvolutionEngine.

Targets uncovered paths in src/core/code_evolution.py:
- _validate_code: syntax errors, dangerous patterns, dangerous imports
- analyze_source: long lines, bare except, TODO/FIXME detection
- _load_journal / _save_journal: YAML round-trip, bad status values
- get_stats: with populated journal
- rollback: happy path + wrong status
- apply_evolution: passed vs not-passed
- propose_evolution: file not found, LLM returns same content
- _find_attempt: hit vs miss
- get_journal: limit slicing
"""

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from src.core.code_evolution import (
    DANGEROUS_PATTERNS,
    CodeChange,
    CodeEvolutionEngine,
    EvolutionAttempt,
    EvolutionStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_engine(tmpdir: str, llm_client=None) -> CodeEvolutionEngine:
    src_core = os.path.join(tmpdir, "src", "core")
    src_agents = os.path.join(tmpdir, "src", "agents")
    os.makedirs(src_core, exist_ok=True)
    os.makedirs(src_agents, exist_ok=True)

    with open(os.path.join(src_core, "sample.py"), "w") as f:
        f.write("def hello():\n    return 'world'\n")

    journal = os.path.join(tmpdir, ".mekong", "journal.yaml")
    return CodeEvolutionEngine(
        project_root=tmpdir,
        llm_client=llm_client,
        journal_path=journal,
    )


def _attempt(status=EvolutionStatus.PROPOSED, attempt_id="evo-1") -> EvolutionAttempt:
    return EvolutionAttempt(
        id=attempt_id,
        description="test",
        status=status,
        branch_name=f"evolution/{attempt_id}",
    )


# ---------------------------------------------------------------------------
# _validate_code
# ---------------------------------------------------------------------------

class TestValidateCode(unittest.TestCase):
    """Tests for CodeEvolutionEngine._validate_code."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.engine = _make_engine(self.tmpdir)
        self.dummy_path = Path(self.tmpdir) / "src" / "core" / "sample.py"

    def test_valid_code_returns_none(self):
        code = "def foo():\n    return 42\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNone(result)

    def test_syntax_error_detected(self):
        code = "def foo(\n    return 42\n"  # missing closing paren
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)
        self.assertIn("Syntax error", result)

    def test_eval_pattern_blocked(self):
        code = "x = eval('1+1')\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)
        self.assertIn("Dangerous pattern", result)

    def test_exec_pattern_blocked(self):
        code = "exec('print(1)')\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)
        self.assertIn("Dangerous pattern", result)

    def test_os_system_blocked(self):
        code = "import os\nos.system('rm -rf /')\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)
        self.assertIn("Dangerous pattern", result)

    def test_subprocess_run_blocked(self):
        code = "import subprocess\nsubprocess.run(['ls'])\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)
        self.assertIn("Dangerous pattern", result)

    def test_dangerous_pattern_in_comment_is_allowed(self):
        # A line that is a comment should not trigger the block
        code = "# eval( is dangerous\ndef safe():\n    return 1\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNone(result)

    def test_ctypes_import_blocked(self):
        code = "import ctypes\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)
        self.assertIn("Dangerous import", result)

    def test_pickle_import_blocked(self):
        code = "import pickle\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)
        self.assertIn("Dangerous import", result)

    def test_marshal_import_blocked(self):
        code = "import marshal\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)
        self.assertIn("Dangerous import", result)

    def test_from_ctypes_blocked(self):
        code = "from ctypes import cdll\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)

    def test_from_pickle_blocked(self):
        code = "from pickle import loads\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)

    def test_compile_pattern_blocked(self):
        code = "compile('print(1)', '<string>', 'exec')\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)
        self.assertIn("Dangerous pattern", result)

    def test_dunder_import_blocked(self):
        code = "mod = __import__('os')\n"
        result = self.engine._validate_code(code, self.dummy_path)
        self.assertIsNotNone(result)


# ---------------------------------------------------------------------------
# analyze_source
# ---------------------------------------------------------------------------

class TestAnalyzeSource(unittest.TestCase):
    """Tests for analyze_source covering branch paths not in existing tests."""

    def _make_engine_with_file(self, content: str) -> tuple:
        tmpdir = tempfile.mkdtemp()
        src_core = os.path.join(tmpdir, "src", "core")
        os.makedirs(src_core, exist_ok=True)
        fname = os.path.join(src_core, "module.py")
        with open(fname, "w") as f:
            f.write(content)
        engine = _make_engine(tmpdir)
        engine.project_root = Path(tmpdir)
        return engine, tmpdir

    def test_long_line_detected(self):
        # Line exceeds 120 chars
        long_line = "x = " + "a" * 130
        engine, _ = self._make_engine_with_file(long_line + "\n")
        report = engine.analyze_source("src/core")
        # At least one file should have long_lines recorded
        has_long = any(f.get("long_lines", 0) > 0 for f in report["files"])
        self.assertTrue(has_long)

    def test_bare_except_detected(self):
        code = "try:\n    pass\nexcept:\n    pass\n"
        engine, _ = self._make_engine_with_file(code)
        report = engine.analyze_source("src/core")
        issues_text = " ".join(report["issues"])
        self.assertIn("broad exception", issues_text)

    def test_exception_class_detected(self):
        code = "try:\n    pass\nexcept Exception:\n    pass\n"
        engine, _ = self._make_engine_with_file(code)
        report = engine.analyze_source("src/core")
        issues_text = " ".join(report["issues"])
        self.assertIn("broad exception", issues_text)

    def test_todo_fixme_detected(self):
        code = "# TODO: fix this\n# FIXME: also this\ndef foo(): pass\n"
        engine, _ = self._make_engine_with_file(code)
        report = engine.analyze_source("src/core")
        issues_text = " ".join(report["issues"])
        self.assertIn("TODO/FIXME", issues_text)

    def test_hack_marker_detected(self):
        code = "# HACK: temporary workaround\ndef foo(): pass\n"
        engine, _ = self._make_engine_with_file(code)
        report = engine.analyze_source("src/core")
        issues_text = " ".join(report["issues"])
        self.assertIn("TODO/FIXME", issues_text)

    def test_large_file_issue_reported(self):
        # Create file with 501 lines
        code = "\n".join(["x = 1"] * 501)
        engine, _ = self._make_engine_with_file(code)
        report = engine.analyze_source("src/core")
        issues_text = " ".join(report["issues"])
        self.assertIn("Too large", issues_text)

    def test_totals_accumulate_across_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            src_core = os.path.join(tmpdir, "src", "core")
            os.makedirs(src_core)
            for i in range(3):
                with open(os.path.join(src_core, f"mod{i}.py"), "w") as f:
                    f.write(f"def func{i}():\n    return {i}\n")
            engine = CodeEvolutionEngine(
                project_root=tmpdir,
                journal_path=os.path.join(tmpdir, ".mekong", "journal.yaml"),
            )
            report = engine.analyze_source("src/core")
            self.assertEqual(len(report["files"]), 3)
            self.assertGreaterEqual(report["total_functions"], 3)


# ---------------------------------------------------------------------------
# Journal persistence
# ---------------------------------------------------------------------------

class TestJournalPersistence(unittest.TestCase):
    """Tests for _load_journal / _save_journal."""

    def test_save_and_reload_journal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            attempt = EvolutionAttempt(
                id="evo-42",
                description="Add typing",
                status=EvolutionStatus.APPLIED,
                branch_name="evolution/evo-42",
                test_results="ok",
                reasoning="improve types",
                timestamp=1234567890.0,
            )
            engine._journal.append(attempt)
            engine._save_journal()

            # Reload
            engine2 = _make_engine(tmpdir)
            engine2._journal_path = engine._journal_path
            engine2._load_journal()

            self.assertEqual(len(engine2._journal), 1)
            loaded = engine2._journal[0]
            self.assertEqual(loaded.id, "evo-42")
            self.assertEqual(loaded.status, EvolutionStatus.APPLIED)
            self.assertEqual(loaded.description, "Add typing")

    def test_load_journal_with_invalid_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            journal_path = Path(tmpdir) / ".mekong" / "journal.yaml"
            journal_path.parent.mkdir(parents=True)
            data = [{"id": "evo-bad", "status": "nonexistent_status", "description": "x"}]
            journal_path.write_text(yaml.dump(data))

            engine = CodeEvolutionEngine(
                project_root=tmpdir,
                journal_path=str(journal_path),
            )
            # Should fall back to PROPOSED instead of crashing
            self.assertEqual(len(engine._journal), 1)
            self.assertEqual(engine._journal[0].status, EvolutionStatus.PROPOSED)

    def test_load_journal_empty_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            journal_path = Path(tmpdir) / ".mekong" / "journal.yaml"
            journal_path.parent.mkdir(parents=True)
            journal_path.write_text("")  # empty YAML → None

            engine = CodeEvolutionEngine(
                project_root=tmpdir,
                journal_path=str(journal_path),
            )
            self.assertEqual(len(engine._journal), 0)

    def test_load_journal_corrupted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            journal_path = Path(tmpdir) / ".mekong" / "journal.yaml"
            journal_path.parent.mkdir(parents=True)
            journal_path.write_text(":::invalid yaml:::")

            engine = CodeEvolutionEngine(
                project_root=tmpdir,
                journal_path=str(journal_path),
            )
            self.assertEqual(engine._journal, [])

    def test_journal_capped_at_max(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            # Add MAX_JOURNAL + 10 entries
            for i in range(CodeEvolutionEngine.MAX_JOURNAL + 10):
                engine._journal.append(EvolutionAttempt(
                    id=f"evo-{i}",
                    description=f"attempt {i}",
                    status=EvolutionStatus.PROPOSED,
                ))
            engine._save_journal()

            # Reload and check it's capped
            engine2 = _make_engine(tmpdir)
            engine2._journal_path = engine._journal_path
            engine2._load_journal()
            self.assertLessEqual(len(engine2._journal), CodeEvolutionEngine.MAX_JOURNAL)


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------

class TestGetStats(unittest.TestCase):
    def test_stats_with_mixed_statuses(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            statuses = [
                EvolutionStatus.APPLIED,
                EvolutionStatus.PASSED,
                EvolutionStatus.FAILED,
                EvolutionStatus.ROLLED_BACK,
                EvolutionStatus.PROPOSED,
            ]
            for i, st in enumerate(statuses):
                engine._journal.append(EvolutionAttempt(
                    id=f"evo-{i}", description="x", status=st,
                ))

            stats = engine.get_stats()
            self.assertEqual(stats["total_attempts"], 5)
            self.assertEqual(stats["applied"], 1)
            self.assertEqual(stats["failed"], 1)
            self.assertEqual(stats["rolled_back"], 1)
            # passed = PASSED + APPLIED = 2
            self.assertEqual(stats["passed"], 2)
            self.assertAlmostEqual(stats["success_rate"], 2 / 5)

    def test_stats_all_applied(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            for i in range(3):
                engine._journal.append(EvolutionAttempt(
                    id=f"evo-{i}", description="x", status=EvolutionStatus.APPLIED,
                ))
            stats = engine.get_stats()
            self.assertAlmostEqual(stats["success_rate"], 1.0)


# ---------------------------------------------------------------------------
# get_journal limit
# ---------------------------------------------------------------------------

class TestGetJournal(unittest.TestCase):
    def test_get_journal_respects_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            for i in range(50):
                engine._journal.append(EvolutionAttempt(
                    id=f"evo-{i}", description=f"attempt {i}",
                ))
            result = engine.get_journal(limit=10)
            self.assertEqual(len(result), 10)
            # Should be the last 10
            self.assertEqual(result[-1].id, "evo-49")

    def test_get_journal_all_when_small(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            for i in range(5):
                engine._journal.append(EvolutionAttempt(id=f"evo-{i}", description="x"))
            result = engine.get_journal(limit=20)
            self.assertEqual(len(result), 5)


# ---------------------------------------------------------------------------
# rollback
# ---------------------------------------------------------------------------

class TestRollback(unittest.TestCase):
    def test_rollback_applied_attempt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            file_path = "src/core/sample.py"
            original_content = "def hello():\n    return 'world'\n"

            attempt = EvolutionAttempt(
                id="evo-rb",
                description="test",
                status=EvolutionStatus.APPLIED,
                rollback_data={file_path: original_content},
            )
            engine._journal.append(attempt)

            result = engine.rollback("evo-rb")
            self.assertTrue(result)
            self.assertEqual(attempt.status, EvolutionStatus.ROLLED_BACK)

            # File should be restored
            full_path = Path(tmpdir) / file_path
            self.assertEqual(full_path.read_text(), original_content)

    def test_rollback_wrong_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            attempt = _attempt(status=EvolutionStatus.FAILED, attempt_id="evo-fail")
            engine._journal.append(attempt)

            result = engine.rollback("evo-fail")
            self.assertFalse(result)

    def test_rollback_missing_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            result = engine.rollback("no-such-id")
            self.assertFalse(result)


# ---------------------------------------------------------------------------
# apply_evolution
# ---------------------------------------------------------------------------

class TestApplyEvolution(unittest.TestCase):
    def test_apply_wrong_status_returns_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            for st in [
                EvolutionStatus.PROPOSED,
                EvolutionStatus.TESTING,
                EvolutionStatus.FAILED,
                EvolutionStatus.ROLLED_BACK,
            ]:
                attempt = _attempt(status=st)
                self.assertFalse(engine.apply_evolution(attempt))

    @patch("src.core.code_evolution.CodeEvolutionEngine._git_cmd")
    @patch("src.core.code_evolution.get_event_bus")
    def test_apply_passed_succeeds(self, mock_get_bus, mock_git_cmd):
        mock_bus = MagicMock()
        mock_get_bus.return_value = mock_bus
        mock_git_cmd.return_value = ""

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            attempt = _attempt(status=EvolutionStatus.PASSED, attempt_id="evo-ok")
            engine._journal.append(attempt)

            result = engine.apply_evolution(attempt)
            self.assertTrue(result)
            self.assertEqual(attempt.status, EvolutionStatus.APPLIED)
            mock_bus.emit.assert_called_once()

    @patch("src.core.code_evolution.CodeEvolutionEngine._git_cmd", side_effect=Exception("merge conflict"))
    def test_apply_git_failure_returns_false(self, _mock):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            attempt = _attempt(status=EvolutionStatus.PASSED, attempt_id="evo-conflict")
            engine._journal.append(attempt)

            result = engine.apply_evolution(attempt)
            self.assertFalse(result)
            self.assertEqual(attempt.status, EvolutionStatus.FAILED)


# ---------------------------------------------------------------------------
# propose_evolution edge cases
# ---------------------------------------------------------------------------

class TestProposeEvolution(unittest.TestCase):
    def test_propose_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            result = engine.propose_evolution("src/core/nonexistent.py", "add types")
            self.assertIsNone(result)

    def test_propose_forbidden_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            # governance.py is in FORBIDDEN_FILES
            result = engine.propose_evolution("src/core/governance.py", "add types")
            self.assertIsNone(result)

    def test_propose_with_llm_returning_same_content(self):
        """If LLM returns same code, proposal is None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            original = (Path(tmpdir) / "src" / "core" / "sample.py").read_text()

            mock_llm = MagicMock()
            mock_llm.generate.return_value = original  # unchanged
            engine.llm_client = mock_llm

            result = engine.propose_evolution("src/core/sample.py", "improve something")
            self.assertIsNone(result)

    def test_propose_with_llm_returning_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)

            mock_llm = MagicMock()
            mock_llm.generate.return_value = ""
            engine.llm_client = mock_llm

            result = engine.propose_evolution("src/core/sample.py", "improve")
            self.assertIsNone(result)

    @patch("src.core.code_evolution.get_event_bus")
    def test_propose_with_llm_success_appends_journal(self, mock_get_bus):
        mock_bus = MagicMock()
        mock_get_bus.return_value = mock_bus

        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)

            mock_llm = MagicMock()
            mock_llm.generate.return_value = "def hello():\n    return 'improved'\n"
            engine.llm_client = mock_llm

            result = engine.propose_evolution("src/core/sample.py", "improve return")
            self.assertIsNotNone(result)
            self.assertEqual(len(engine._journal), 1)
            self.assertEqual(result.status, EvolutionStatus.PROPOSED)
            mock_bus.emit.assert_called_once()

    def test_propose_llm_raises_exception(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)

            mock_llm = MagicMock()
            mock_llm.generate.side_effect = RuntimeError("LLM unavailable")
            engine.llm_client = mock_llm

            result = engine.propose_evolution("src/core/sample.py", "improve")
            self.assertIsNone(result)


# ---------------------------------------------------------------------------
# _find_attempt
# ---------------------------------------------------------------------------

class TestFindAttempt(unittest.TestCase):
    def test_find_existing_attempt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            attempt = _attempt(attempt_id="evo-xyz")
            engine._journal.append(attempt)

            found = engine._find_attempt("evo-xyz")
            self.assertIs(found, attempt)

    def test_find_missing_attempt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            found = engine._find_attempt("no-such-id")
            self.assertIsNone(found)


# ---------------------------------------------------------------------------
# _is_safe_to_modify edge cases
# ---------------------------------------------------------------------------

class TestIsSafeEdgeCases(unittest.TestCase):
    def test_code_evolution_itself_forbidden(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            self.assertFalse(engine._is_safe_to_modify("src/core/code_evolution.py"))

    def test_path_not_in_safe_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = _make_engine(tmpdir)
            self.assertFalse(engine._is_safe_to_modify("src/auth/secure_storage.py"))
            self.assertFalse(engine._is_safe_to_modify("tests/test_foo.py"))


if __name__ == "__main__":
    unittest.main()
