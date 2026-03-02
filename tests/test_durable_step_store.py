"""Tests for Durable Step Store — QStash context.run() pattern."""

import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.durable_step_store import DurableStepStore


class FakeResult:
    """Minimal fake to simulate ExecutionResult."""

    def __init__(self, exit_code=0, stdout="ok", stderr="", metadata=None):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.metadata = metadata or {}


class TestDurableStepStore:
    def test_save_and_load(self, tmp_path):
        """Save step result then load it back."""
        store = DurableStepStore(store_dir=tmp_path / "steps")
        result = FakeResult(exit_code=0, stdout="done")
        store.save("recipe-1", 0, result)

        loaded = store.load("recipe-1")
        assert len(loaded) == 1
        assert loaded[0].step_index == 0
        assert loaded[0].exit_code == 0
        assert loaded[0].stdout == "done"

    def test_resume_index_empty(self, tmp_path):
        """Resume index is 0 when no steps completed."""
        store = DurableStepStore(store_dir=tmp_path / "steps")
        assert store.get_resume_index("nonexistent") == 0

    def test_resume_index_after_steps(self, tmp_path):
        """Resume index is next step after last completed."""
        store = DurableStepStore(store_dir=tmp_path / "steps")
        store.save("r1", 0, FakeResult())
        store.save("r1", 1, FakeResult())
        store.save("r1", 2, FakeResult())
        assert store.get_resume_index("r1") == 3

    def test_is_step_completed(self, tmp_path):
        """Check individual step completion status."""
        store = DurableStepStore(store_dir=tmp_path / "steps")
        store.save("r1", 0, FakeResult(exit_code=0))
        store.save("r1", 1, FakeResult(exit_code=1))

        assert store.is_step_completed("r1", 0) is True
        assert store.is_step_completed("r1", 1) is False  # exit_code=1
        assert store.is_step_completed("r1", 5) is False  # not saved

    def test_clear(self, tmp_path):
        """Clear removes all step results for a recipe."""
        store = DurableStepStore(store_dir=tmp_path / "steps")
        store.save("r1", 0, FakeResult())
        store.save("r1", 1, FakeResult())
        store.clear("r1")

        assert store.load("r1") == []
        assert store.get_resume_index("r1") == 0

    def test_list_incomplete(self, tmp_path):
        """List recipes with incomplete step results."""
        store = DurableStepStore(store_dir=tmp_path / "steps")
        store.save("recipe-a", 0, FakeResult())
        store.save("recipe-b", 0, FakeResult())

        incomplete = store.list_incomplete()
        assert "recipe-a" in incomplete
        assert "recipe-b" in incomplete

    def test_corrupt_file_skipped(self, tmp_path):
        """Corrupt JSON files are skipped gracefully."""
        store = DurableStepStore(store_dir=tmp_path / "steps")
        recipe_dir = tmp_path / "steps" / "bad-recipe"
        recipe_dir.mkdir(parents=True)
        (recipe_dir / "0.json").write_text("NOT JSON")

        loaded = store.load("bad-recipe")
        assert loaded == []
