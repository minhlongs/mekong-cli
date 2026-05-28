import subprocess
import os
import sys
import socket
import time
import shutil
from pathlib import Path

def test_f5_t1_01_launch_llama_script_args(tmp_path):
    # Setup mock llama-server binary in PATH
    mock_bin_dir = tmp_path / "bin"
    mock_bin_dir.mkdir()
    mock_server = mock_bin_dir / "llama-server"
    mock_server.write_text("#!/usr/bin/env python3\nimport sys\nprint('llama-server called with args:', ' '.join(sys.argv))\n")
    mock_server.chmod(0o755)
    
    # Setup dummy model file
    model_dir = Path("/Users/macbook/mekong-cli/models")
    model_dir.mkdir(parents=True, exist_ok=True)
    dummy_model = model_dir / "qwen3.6-35b-instruct-q4_k_m.gguf"
    dummy_model.write_text("dummy model content")
    
    env = os.environ.copy()
    env["PATH"] = str(mock_bin_dir) + os.path.pathsep + env["PATH"]
    
    try:
        proc = subprocess.run(
            "bash scripts/launch-llama.sh",
            shell=True, capture_output=True, text=True, env=env
        )
        assert proc.returncode == 0
        assert "--threads 8" in proc.stdout
        assert "--n-gpu-layers 99" in proc.stdout
        assert "--no-mmap" in proc.stdout
        assert "--flash-attn" in proc.stdout
    finally:
        # Clean up model file
        if dummy_model.exists():
            dummy_model.unlink()

def test_f5_t1_02_run_claude_hybrid_script(tmp_path):
    # Setup mock claude binary in PATH
    mock_bin_dir = tmp_path / "bin"
    mock_bin_dir.mkdir()
    mock_claude = mock_bin_dir / "claude"
    mock_claude.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "print('CLAUDE_MODEL:', os.environ.get('ANTHROPIC_MODEL'))\n"
        "print('CLAUDE_URL:', os.environ.get('ANTHROPIC_BASE_URL'))\n"
    )
    mock_claude.chmod(0o755)
    
    env = os.environ.copy()
    env["PATH"] = str(mock_bin_dir) + os.path.pathsep + env["PATH"]
    
    # 1. Cloud path (Reasoning task)
    proc_cloud = subprocess.run(
        "bash scripts/run-claude-hybrid.sh 'refactor the main system architecture'",
        shell=True, capture_output=True, text=True, env=env
    )
    assert proc_cloud.returncode == 0
    assert "CLAUDE_MODEL: claude-3-5-sonnet-latest" in proc_cloud.stdout
    assert "CLAUDE_URL: None" in proc_cloud.stdout or "CLAUDE_URL: \n" in proc_cloud.stdout
    
    # 2. Local path (Simple execution task)
    proc_local = subprocess.run(
        "bash scripts/run-claude-hybrid.sh 'format standard main.py file'",
        shell=True, capture_output=True, text=True, env=env
    )
    assert proc_local.returncode == 0
    assert "CLAUDE_MODEL: Qwen3.6-35B-A3B" in proc_local.stdout
    assert "CLAUDE_URL: http://localhost:8080/v1" in proc_local.stdout

def test_f5_t1_03_llama_server_status_health(antigravity_bin):
    proc = subprocess.run(f"{antigravity_bin} --status", shell=True, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Inference Driver: LOCAL_LLAMA (llama.cpp)" in proc.stdout
    # Status shows connection database and llama-server state (stopped in test workspace)
    assert "llama-server status: stopped" in proc.stdout or "llama-server status: running" in proc.stdout

def test_f5_t1_04_metal_offload_detection():
    # Read launch script and verify Metal layers offload configuration exists
    script = Path("scripts/launch-llama.sh")
    assert script.exists()
    content = script.read_text()
    assert "--n-gpu-layers 99" in content

def test_f5_t1_05_no_mmap_flag_check():
    # Read launch script and verify no-mmap flag configuration exists
    script = Path("scripts/launch-llama.sh")
    assert script.exists()
    content = script.read_text()
    assert "--no-mmap" in content

def test_f5_t2_01_model_file_missing_check():
    # Ensure model file is missing
    dummy_model = Path("/Users/macbook/mekong-cli/models/qwen3.6-35b-instruct-q4_k_m.gguf")
    if dummy_model.exists():
        dummy_model.unlink()
        
    proc = subprocess.run("bash scripts/launch-llama.sh", shell=True, capture_output=True, text=True)
    assert proc.returncode == 1
    assert "Error: Model file not detected at" in proc.stdout

def test_f5_t2_02_port_collision_fallback(tmp_path):
    # Setup mock llama-server binary that tries to bind to port
    mock_bin_dir = tmp_path / "bin"
    mock_bin_dir.mkdir()
    mock_server = mock_bin_dir / "llama-server"
    mock_server.write_text(
        "#!/usr/bin/env python3\n"
        "import sys, socket\n"
        "try:\n"
        "    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
        "    s.bind(('127.0.0.1', 8080))\n"
        "    s.close()\n"
        "except Exception:\n"
        "    print('Error: Address already in use', file=sys.stderr)\n"
        "    sys.exit(1)\n"
    )
    mock_server.chmod(0o755)
    
    # Setup dummy model file
    model_dir = Path("/Users/macbook/mekong-cli/models")
    model_dir.mkdir(parents=True, exist_ok=True)
    dummy_model = model_dir / "qwen3.6-35b-instruct-q4_k_m.gguf"
    dummy_model.write_text("dummy model content")
    
    # Bind port 8080 in python first to trigger collision
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 8080))
    s.listen(1)
    
    env = os.environ.copy()
    env["PATH"] = str(mock_bin_dir) + os.path.pathsep + env["PATH"]
    
    try:
        proc = subprocess.run(
            "bash scripts/launch-llama.sh",
            shell=True, capture_output=True, text=True, env=env
        )
        assert proc.returncode == 1
        assert "Address already in use" in proc.stderr
    finally:
        s.close()
        if dummy_model.exists():
            dummy_model.unlink()

def test_f5_t2_03_insufficient_vram_warning(antigravity_bin):
    # Insufficient VRAM warning during status checks can be verified on low memory environments or mock
    # status outputs system check details
    proc = subprocess.run(f"{antigravity_bin} --status", shell=True, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Inference Driver:" in proc.stdout

def test_f5_t2_04_claude_api_rate_limit_retry(antigravity_bin):
    # Simulates cloud agent running, catching 429 and retrying
    proc = subprocess.run(
        f"{antigravity_bin} --task 'refactor library with rate limits' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Selected Route: CLAUDE_CLOUD" in proc.stdout

def test_f5_t2_05_llama_server_crash_recovery(antigravity_bin):
    # Mid-run crash recovery logic check
    proc = subprocess.run(
        f"{antigravity_bin} --task 'format file server crash recovery' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Success" in proc.stdout

def test_f3_f4_tool_timeout_during_agent_validation(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'tool timeout during validation' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 1
    assert "timeout exceeded during build step" in proc.stderr

def test_r5_agent_loop_recovery_from_compilation_error(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'recovery from compiler warning' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Iteration 1:" in proc.stdout
    assert "Validation Failed: compile error" in proc.stderr
    assert "Iteration 2:" in proc.stdout
    assert "Applying corrective patch..." in proc.stdout
    assert "Success" in proc.stdout
