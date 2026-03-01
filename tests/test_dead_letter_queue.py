"""Tests for Dead Letter Queue — QStash DLQ pattern."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.dead_letter_queue import DeadLetterQueue


class TestDeadLetterQueue:
    def test_push_and_list(self, tmp_path):
        """Push a failed mission and list it."""
        dlq = DeadLetterQueue(dlq_dir=tmp_path / "dlq")
        letter = dlq.push(
            recipe_id="recipe-1",
            goal="Deploy app",
            error="Build failed",
            attempts=3,
            last_step_index=2,
        )

        assert letter.recipe_id == "recipe-1"
        assert letter.attempts == 3

        entries = dlq.list_all()
        assert len(entries) == 1
        assert entries[0].goal == "Deploy app"

    def test_get_by_id(self, tmp_path):
        """Get a specific DLQ entry by ID."""
        dlq = DeadLetterQueue(dlq_dir=tmp_path / "dlq")
        letter = dlq.push("r1", "Goal", "Error", 1)

        fetched = dlq.get(letter.id)
        assert fetched is not None
        assert fetched.recipe_id == "r1"

    def test_get_nonexistent(self, tmp_path):
        """Get returns None for nonexistent ID."""
        dlq = DeadLetterQueue(dlq_dir=tmp_path / "dlq")
        assert dlq.get("nonexistent") is None

    def test_mark_retried(self, tmp_path):
        """Mark a DLQ entry as retried."""
        dlq = DeadLetterQueue(dlq_dir=tmp_path / "dlq")
        letter = dlq.push("r1", "Goal", "Error", 2)

        assert dlq.mark_retried(letter.id) is True
        fetched = dlq.get(letter.id)
        assert fetched.retried is True

    def test_remove(self, tmp_path):
        """Remove a DLQ entry permanently."""
        dlq = DeadLetterQueue(dlq_dir=tmp_path / "dlq")
        letter = dlq.push("r1", "Goal", "Error", 1)

        assert dlq.remove(letter.id) is True
        assert dlq.get(letter.id) is None
        assert dlq.count() == 0

    def test_count(self, tmp_path):
        """Count entries in DLQ."""
        dlq = DeadLetterQueue(dlq_dir=tmp_path / "dlq")
        assert dlq.count() == 0

        dlq.push("r1", "G1", "E1", 1)
        dlq.push("r2", "G2", "E2", 2)
        assert dlq.count() == 2

    def test_clear(self, tmp_path):
        """Clear all DLQ entries."""
        dlq = DeadLetterQueue(dlq_dir=tmp_path / "dlq")
        dlq.push("r1", "G1", "E1", 1)
        dlq.push("r2", "G2", "E2", 2)

        removed = dlq.clear()
        assert removed == 2
        assert dlq.count() == 0

    def test_empty_dlq_dir(self, tmp_path):
        """Operations on empty DLQ dir are safe."""
        dlq = DeadLetterQueue(dlq_dir=tmp_path / "nonexistent")
        assert dlq.list_all() == []
        assert dlq.count() == 0
        assert dlq.clear() == 0
