import subprocess
import os

def test_f1_t1_01_heuristic_local_routing(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --route-only 'format python file tests'",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Decision: LOCAL_QWEN" in proc.stdout

def test_f1_t1_02_heuristic_cloud_routing(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --route-only 'refactor the main architecture'",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Decision: CLAUDE_CLOUD" in proc.stdout

def test_f1_t1_03_token_budget_routing(antigravity_bin):
    # Massive context simulation (>100 words)
    long_task = " ".join(["word"] * 105)
    proc = subprocess.run(
        f"{antigravity_bin} --route-only '{long_task}'",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Decision: CLAUDE_CLOUD" in proc.stdout

def test_f1_t1_04_context_compaction_basic(antigravity_bin, tmp_path):
    test_file = tmp_path / "test_func.py"
    test_file.write_text("def my_sum(a, b):\n    x = a + b\n    return x\n")
    proc = subprocess.run(
        f"{antigravity_bin} --compact-only {test_file}",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "def my_sum(a, b):" in proc.stdout
    assert "pass" in proc.stdout
    assert "return x" not in proc.stdout

def test_f1_t1_05_compact_with_comments_retained(antigravity_bin, tmp_path):
    test_file = tmp_path / "test_func.py"
    test_file.write_text("def my_sum(a, b):\n    # This sums two numbers\n    \"\"\"Docstring goes here\"\"\"\n    return a + b\n")
    proc = subprocess.run(
        f"{antigravity_bin} --compact-only {test_file}",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "def my_sum(a, b):" in proc.stdout
    assert "# This sums two numbers" in proc.stdout
    assert "Docstring goes here" in proc.stdout

def test_f1_t2_01_empty_task_routing(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --route-only '   '",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Decision: LOCAL_QWEN" in proc.stdout

def test_f1_t2_02_conflicting_keywords_routing(antigravity_bin):
    # Cloud keyword "security" should take precedence over local keyword "format"
    proc = subprocess.run(
        f"{antigravity_bin} --route-only 'format structure for security refactoring'",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Decision: CLAUDE_CLOUD" in proc.stdout

def test_f1_t2_03_malformed_source_compaction(antigravity_bin, tmp_path):
    # Syntactically invalid Python
    test_file = tmp_path / "test_malformed.py"
    test_file.write_text("def my_sum(a, b:\n    # This is a comment\n    return x\n")
    proc = subprocess.run(
        f"{antigravity_bin} --compact-only {test_file}",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    # Fallback to line matching still outputs the comment and definition line
    assert "def my_sum(a, b:" in proc.stdout
    assert "# This is a comment" in proc.stdout

def test_f1_t2_04_extreme_large_file_compaction(antigravity_bin, tmp_path):
    test_file = tmp_path / "test_huge.py"
    with open(test_file, "w") as f:
        f.write("def dummy():\n" + "    pass\n" * 100000) # file size over 1MB
    proc = subprocess.run(
        f"{antigravity_bin} --compact-only {test_file}",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "# File too large, context truncated" in proc.stdout

def test_f1_t2_05_api_key_absence_fallback(antigravity_bin):
    # Unset ANTHROPIC_API_KEY and verify fallback behavior for cloud-routed tasks
    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = ""
    proc = subprocess.run(
        f"{antigravity_bin} --route-only 'refactor standard routing library'",
        shell=True, capture_output=True, text=True, env=env
    )
    assert proc.returncode == 0
    assert "Decision: LOCAL_QWEN" in proc.stdout
    assert "Warning: ANTHROPIC_API_KEY is missing" in proc.stderr

def test_f1_f5_routing_to_failed_local_inference_escalation(antigravity_bin):
    # Local server is unresponsive, routing should escalate to cloud
    env = os.environ.copy()
    env["MOCK_LLAMA_SERVER_UNRESPONSIVE"] = "1"
    env["ANTHROPIC_API_KEY"] = "mock_key"
    proc = subprocess.run(
        f"{antigravity_bin} --route-only 'format file'",
        shell=True, capture_output=True, text=True, env=env
    )
    assert proc.returncode == 0
    assert "Decision: CLAUDE_CLOUD" in proc.stdout
    assert "Warning: local llama-server is unresponsive" in proc.stderr

def test_r1_full_hybrid_routing_compaction_pipeline(antigravity_bin, tmp_path):
    # Full pipeline: route a task, check decision, compact a python file
    proc_route = subprocess.run(
        f"{antigravity_bin} --route-only 'format source file syntax'",
        shell=True, capture_output=True, text=True
    )
    assert "Decision: LOCAL_QWEN" in proc_route.stdout
    
    test_file = tmp_path / "pipeline.py"
    test_file.write_text("class Pipeline:\n    \"\"\"Handles data flow\"\"\"\n    def run(self):\n        pass\n")
    proc_compact = subprocess.run(
        f"{antigravity_bin} --compact-only {test_file}",
        shell=True, capture_output=True, text=True
    )
    assert "class Pipeline:" in proc_compact.stdout
    assert "Handles data flow" in proc_compact.stdout
    assert "def run(self):" in proc_compact.stdout
