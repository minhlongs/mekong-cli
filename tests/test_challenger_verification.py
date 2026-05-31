import json
import threading
import time
from unittest.mock import MagicMock, patch

from src.core.file_lock import locked_read, locked_read_write
from src.daemon.worker_pool import WorkerPool
from src.daemon.agent_loop import run_agent_sync
from src.core.planner import RecipePlanner
from src.core.parser import Recipe, RecipeStep

# 1. Concurrency Testing
def test_intense_missions_json_concurrency(tmp_path):
    """
    Run highly concurrent read/write operations against missions.json
    using locked_read and locked_read_write to verify no JSONDecodeError or corruption occurs.
    """
    file_path = tmp_path / "missions.json"
    file_path.write_text(json.dumps({"missions": []}))

    errors = []
    
    def writer_thread(tid):
        for i in range(50):
            try:
                with locked_read_write(file_path) as f:
                    content = f.read()
                    data = json.loads(content) if content else {}
                    missions = data.get("missions", [])
                    missions.append({
                        "task_id": f"task_{tid}_{i}",
                        "status": "success",
                        "completed_at": "2026-05-31T12:00:00",
                        "duration_ms": 150
                    })
                    f.seek(0)
                    f.write(json.dumps({"missions": missions}, indent=2))
                    f.truncate()
            except Exception as e:
                errors.append(f"Writer {tid} error: {e}")
            time.sleep(0.001)

    def reader_thread(tid):
        for i in range(50):
            try:
                with locked_read(file_path) as f:
                    content = f.read()
                    if content:
                        data = json.loads(content)
                        _ = data.get("missions", [])
            except Exception as e:
                errors.append(f"Reader {tid} error: {e}")
            time.sleep(0.001)

    threads = []
    for t in range(10):  # 10 writers, 10 readers
        threads.append(threading.Thread(target=writer_thread, args=(t,)))
        threads.append(threading.Thread(target=reader_thread, args=(t,)))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"JSON errors during concurrent operations: {errors}"
    
    with open(file_path, "r") as f:
        data = json.loads(f.read())
        assert len(data.get("missions", [])) == 10 * 50

# 2. Stress Testing
def test_worker_status_cache_stress():
    """
    Verify the cache mechanism in WorkerPool.refresh_status functions under high-frequency polling.
    """
    pool = WorkerPool()
    
    # Mock PM2 available and jlist output
    pool._pm2_available = lambda: True
    
    call_count = 0
    def mock_run_pm2(args):
        nonlocal call_count
        call_count += 1
        return MagicMock(
            returncode=0,
            stdout=json.dumps([
                {
                    "pid": 123,
                    "pm2_env": {"name": "test-worker", "status": "online"},
                    "monit": {"cpu": 0.0, "memory": 1000000}
                }
            ]),
            stderr=""
        )
    
    pool._run_pm2 = mock_run_pm2
    
    # Run high frequency calls
    for _ in range(50):
        pool.refresh_status()
        
    # Since refresh_cache_ttl is 5.0 seconds, only 1 call to _run_pm2 should have happened
    assert call_count == 1, f"Expected 1 call to PM2, got {call_count}"
    
    # Force call
    pool.refresh_status(force=True)
    assert call_count == 2
    
    # Concurrent polling
    call_count = 0
    errors = []
    def poll_thread():
        try:
            for _ in range(20):
                pool.refresh_status()
                time.sleep(0.001)
        except Exception as e:
            errors.append(e)
            
    threads = [threading.Thread(target=poll_thread) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    assert not errors, f"Errors in concurrent status retrieval: {errors}"
    assert call_count <= 5, f"PM2 calls were not cached correctly under concurrency: {call_count}"

# 3. Edge Cases
def test_tool_call_missing_id_parallel():
    """
    Test tool call payloads with missing ID and verify fallback behavior under multiple parallel iterations.
    """
    # Mock LLM to return a tool call without "id"
    tool_msg = {
        "content": "Running tool...",
        "tool_calls": [{
            # No ID
            "function": {"name": "read_file", "arguments": json.dumps({"path": "test.txt"})},
        }]
    }
    final_msg = {"content": "Final output"}
    
    call_counts = {}
    
    def mock_llm_call(messages, *args, **kwargs):
        msg_key = id(messages)
        count = call_counts.get(msg_key, 0)
        call_counts[msg_key] = count + 1
        if count == 0:
            return tool_msg
        else:
            tool_response = messages[-1]
            assert tool_response["role"] == "tool"
            assert "tool_call_id" in tool_response
            assert tool_response["tool_call_id"].startswith("call_")
            return final_msg

    errors = []
    def run_agent_thread():
        try:
            res = run_agent_sync("help", model_tier="fast")
            assert res == "Final output"
        except Exception as e:
            errors.append(e)

    # Patch globally before spawning threads to avoid context manager races
    with patch("src.daemon.agent_loop._llm_call", side_effect=mock_llm_call):
        with patch("src.daemon.agent_loop.execute_tool", return_value="some_file_content"):
            threads = [threading.Thread(target=run_agent_thread) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

    assert not errors, f"Errors during parallel tool execution with missing ID: {errors}"

# 4. DAG Planning
def test_dag_replanning_preserves_upstream_dependencies():
    """
    Run replanning test cases under edge dependency structures (parallel branches, complex dependencies)
    and assert that original upstream dependencies are fully preserved.
    """
    planner = RecipePlanner()
    
    # Case 1: Parallel branches
    original_recipe = Recipe(
        name="Parallel Branches Recipe",
        description="Verify replanning on parallel branches",
        steps=[
            RecipeStep(order=1, title="Step 1", description="Root step", params={"dependencies": []}, dependencies=[]),
            RecipeStep(order=2, title="Step 2", description="implement step 2", params={"dependencies": [1]}, dependencies=[1]),
            RecipeStep(order=3, title="Step 3", description="Task C", params={"dependencies": [1]}, dependencies=[1]),
            RecipeStep(order=4, title="Step 4", description="Task D", params={"dependencies": [2, 3]}, dependencies=[2, 3]),
        ]
    )
    
    new_recipe = planner.replan_failed_branch(original_recipe, failed_step_order=2)
    
    kept_titles = {s.title for s in new_recipe.steps}
    assert "Step 1" in kept_titles
    assert "Step 3" in kept_titles
    assert "Step 4" not in kept_titles
    
    new_steps = [s for s in new_recipe.steps if s.title not in ["Step 1", "Step 3"]]
    assert len(new_steps) > 0, "No new steps generated for the failed branch replan"
    
    first_new_step = new_steps[0]
    assert 1 in first_new_step.dependencies, f"First new step dependencies {first_new_step.dependencies} do not preserve original upstream dependency 1"
    assert 1 in first_new_step.params.get("dependencies", [])

    # Case 2: Complex dependencies
    original_recipe_2 = Recipe(
        name="Complex Deps Recipe",
        description="Verify replanning with multiple upstreams",
        steps=[
            RecipeStep(order=1, title="Step 1", description="Root A", params={"dependencies": []}, dependencies=[]),
            RecipeStep(order=2, title="Step 2", description="Root B", params={"dependencies": []}, dependencies=[]),
            RecipeStep(order=3, title="Step 3", description="implement step 3", params={"dependencies": [1, 2]}, dependencies=[1, 2]),
            RecipeStep(order=4, title="Step 4", description="Task D", params={"dependencies": [3]}, dependencies=[3]),
        ]
    )
    
    new_recipe_2 = planner.replan_failed_branch(original_recipe_2, failed_step_order=3)
    
    kept_titles_2 = {s.title for s in new_recipe_2.steps}
    assert "Step 1" in kept_titles_2
    assert "Step 2" in kept_titles_2
    assert "Step 4" not in kept_titles_2
    
    new_steps_2 = [s for s in new_recipe_2.steps if s.title not in ["Step 1", "Step 2"]]
    assert len(new_steps_2) > 0
    
    first_new_step_2 = new_steps_2[0]
    assert 1 in first_new_step_2.dependencies
    assert 2 in first_new_step_2.dependencies
    assert 1 in first_new_step_2.params.get("dependencies", [])
    assert 2 in first_new_step_2.params.get("dependencies", [])
