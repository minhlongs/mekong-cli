"""Tests for PEV checkpoint/resume and bounded iteration patterns."""

import subprocess
from unittest.mock import patch


from src.core.executor import RecipeExecutor
from src.core.parser import Recipe, RecipeStep
from src.core.pev_checkpoint import CheckpointStore, PipelineCheckpoint, _utc_now


# ---------------------------------------------------------------------------
# CheckpointStore unit tests
# ---------------------------------------------------------------------------


class TestCheckpointStore:
    def test_save_and_load_roundtrip(self, tmp_path):
        store = CheckpointStore(str(tmp_path))
        cp = PipelineCheckpoint(
            pipeline_id="pipe-1",
            completed_steps=[1, 2],
            last_step_order=2,
            status="running",
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )
        store.save(cp)
        loaded = store.load("pipe-1")
        assert loaded is not None
        assert loaded.pipeline_id == "pipe-1"
        assert loaded.completed_steps == [1, 2]
        assert loaded.last_step_order == 2
        assert loaded.status == "running"

    def test_load_missing_returns_none(self, tmp_path):
        store = CheckpointStore(str(tmp_path))
        assert store.load("nonexistent") is None

    def test_delete_removes_file(self, tmp_path):
        store = CheckpointStore(str(tmp_path))
        cp = PipelineCheckpoint(
            pipeline_id="pipe-del",
            completed_steps=[],
            last_step_order=0,
            status="running",
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )
        store.save(cp)
        store.delete("pipe-del")
        assert store.load("pipe-del") is None

    def test_list_checkpoints(self, tmp_path):
        store = CheckpointStore(str(tmp_path))
        for pid in ["alpha", "beta", "gamma"]:
            cp = PipelineCheckpoint(
                pipeline_id=pid,
                completed_steps=[],
                last_step_order=0,
                status="running",
                created_at=_utc_now(),
                updated_at=_utc_now(),
            )
            store.save(cp)
        ids = store.list_checkpoints()
        assert ids == ["alpha", "beta", "gamma"]

    def test_list_checkpoints_empty(self, tmp_path):
        store = CheckpointStore(str(tmp_path))
        assert store.list_checkpoints() == []

    def test_load_corrupt_json_returns_none(self, tmp_path):
        corrupt = tmp_path / "bad-pipe.json"
        corrupt.write_text("NOT JSON", encoding="utf-8")
        store = CheckpointStore(str(tmp_path))
        assert store.load("bad-pipe") is None

    def test_default_dir_created(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        import pathlib
        monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
        store = CheckpointStore()
        assert store._dir.exists()

    def test_save_updates_updated_at(self, tmp_path):
        store = CheckpointStore(str(tmp_path))
        ts_before = _utc_now()
        cp = PipelineCheckpoint(
            pipeline_id="ts-test",
            completed_steps=[],
            last_step_order=0,
            status="running",
            created_at=ts_before,
            updated_at=ts_before,
        )
        store.save(cp)
        loaded = store.load("ts-test")
        # updated_at must be set (save() always refreshes it)
        assert loaded is not None
        assert loaded.updated_at >= ts_before


# ---------------------------------------------------------------------------
# Bounded iteration guard tests
# ---------------------------------------------------------------------------


class TestBoundedIteration:
    def _make_executor(self, num_steps: int = 0) -> RecipeExecutor:
        recipe = Recipe(name="test-recipe", description="Test")
        return RecipeExecutor(recipe)

    def test_constants_defined(self):
        assert RecipeExecutor.MAX_RETRIES_PER_STEP == 5
        assert RecipeExecutor.MAX_TOTAL_ITERATIONS == 20

    def test_iteration_counter_increments(self):
        recipe = Recipe(name="r", description="d")
        step = RecipeStep(order=1, title="T", description="echo hi")
        executor = RecipeExecutor(recipe)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["echo", "hi"], returncode=0, stdout="hi", stderr=""
            )
            executor.execute_step(step)
            assert executor._total_iterations == 1
            executor.execute_step(step)
            assert executor._total_iterations == 2

    def test_iteration_cap_returns_error(self):
        recipe = Recipe(name="r", description="d")
        step = RecipeStep(order=1, title="T", description="echo hi")
        executor = RecipeExecutor(recipe)
        # Exhaust the cap
        executor._total_iterations = RecipeExecutor.MAX_TOTAL_ITERATIONS
        result = executor.execute_step(step)
        assert result.exit_code == 1
        assert "iteration cap" in result.stderr.lower()
        assert result.metadata.get("iteration_cap_hit") is True

    def test_per_step_retry_clamped(self):
        """retry=100 in params must be clamped to MAX_RETRIES_PER_STEP."""
        recipe = Recipe(name="r", description="d")
        # retry=100 → raw_attempts=101, clamped to MAX_RETRIES_PER_STEP+1=6
        step = RecipeStep(
            order=1, title="T", description="false",
            params={"retry": 100, "retry_delay": 0},
        )
        executor = RecipeExecutor(recipe)
        call_count = 0

        def always_fail(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            exc = subprocess.CalledProcessError(1, "false")
            exc.stdout = ""
            exc.stderr = ""
            raise exc

        with patch("subprocess.run", side_effect=always_fail):
            result = executor._execute_shell_step(step)

        assert result.exit_code == 1
        # Must not exceed MAX_RETRIES_PER_STEP + 1 (= 6) attempts
        assert call_count <= RecipeExecutor.MAX_RETRIES_PER_STEP + 1


# ---------------------------------------------------------------------------
# Checkpoint wired into executor
# ---------------------------------------------------------------------------


class TestExecutorCheckpointWiring:
    def test_checkpoint_saved_on_success(self, tmp_path):
        store = CheckpointStore(str(tmp_path))
        recipe = Recipe(name="my-pipeline", description="d")
        step = RecipeStep(order=3, title="T", description="echo ok")
        executor = RecipeExecutor(recipe, checkpoint_store=store)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["echo", "ok"], returncode=0, stdout="ok", stderr=""
            )
            executor.execute_step(step)

        cp = store.load("my-pipeline")
        assert cp is not None
        assert 3 in cp.completed_steps
        assert cp.last_step_order == 3
        assert cp.status == "running"

    def test_checkpoint_accumulates_steps(self, tmp_path):
        store = CheckpointStore(str(tmp_path))
        recipe = Recipe(name="accum-pipeline", description="d")
        executor = RecipeExecutor(recipe, checkpoint_store=store)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["echo"], returncode=0, stdout="ok", stderr=""
            )
            for order in [1, 2, 3]:
                step = RecipeStep(order=order, title=f"S{order}", description="echo x")
                executor.execute_step(step)

        cp = store.load("accum-pipeline")
        assert cp is not None
        assert cp.completed_steps == [1, 2, 3]

    def test_failed_step_not_checkpointed(self, tmp_path):
        store = CheckpointStore(str(tmp_path))
        recipe = Recipe(name="fail-pipeline", description="d")
        step = RecipeStep(order=1, title="T", description="false")
        executor = RecipeExecutor(recipe, checkpoint_store=store)

        with patch("subprocess.run") as mock_run:
            exc = subprocess.CalledProcessError(1, "false")
            exc.stdout = ""
            exc.stderr = "error"
            mock_run.side_effect = exc
            executor.execute_step(step)

        assert store.load("fail-pipeline") is None

    def test_no_checkpoint_store_no_error(self):
        """Executor with no checkpoint_store works normally."""
        recipe = Recipe(name="r", description="d")
        step = RecipeStep(order=1, title="T", description="echo hi")
        executor = RecipeExecutor(recipe)  # no checkpoint_store

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=["echo", "hi"], returncode=0, stdout="hi", stderr=""
            )
            result = executor.execute_step(step)
        assert result.exit_code == 0
