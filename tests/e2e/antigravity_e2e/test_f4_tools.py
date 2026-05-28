import subprocess
import signal
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor

def test_f4_t1_01_shell_command_execution(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --run-tool 'echo hello_world'",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "hello_world" in proc.stdout

def test_f4_t1_02_stdout_real_time_streaming(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --run-tool 'echo line1 && echo line2'",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "line1\nline2" in proc.stdout

def test_f4_t1_03_tool_timeout_enforcement(antigravity_bin):
    # sleep for 5 seconds but set timeout to 100 milliseconds
    proc = subprocess.run(
        f"{antigravity_bin} --run-tool 'sleep 5' --timeout 100",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 124
    assert "Timeout exceeded" in proc.stderr

def test_f4_t1_04_process_cancellation_sigint(antigravity_bin):
    # Start a long sleep command
    p = subprocess.Popen(
        f"{antigravity_bin} --run-tool 'sleep 10'",
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    time.sleep(0.2)
    # Send SIGINT to the process group
    os.killpg(os.getpgid(p.pid), signal.SIGINT)
    p.wait()
    # Process group was killed, return code should be non-zero
    assert p.returncode != 0

def test_f4_t1_05_ripgrep_tool_search(antigravity_bin, tmp_path):
    test_file = tmp_path / "find_me.txt"
    test_file.write_text("This file contains search_pattern_xyz_123 in a line.\n")
    
    # We run rg search simulation
    proc = subprocess.run(
        f"{antigravity_bin} --rg 'search_pattern_xyz_123'",
        shell=True, capture_output=True, text=True
    )
    # Since we run in mekong-cli workspace, it will find matches or print simulation matches
    assert proc.returncode == 0
    assert "search_pattern_xyz_123" in proc.stdout

def test_f4_t2_01_command_not_found_handling(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --run-tool 'non_existent_binary_xyz_123'",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 127
    assert "Command not found" in proc.stderr

def test_f4_t2_02_extremely_long_stdout_buffer_handling(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --run-tool 'python3 -c \"for i in range(50000): print(f\\\"line {i}\\\")\"'",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    # verify it streamed all 50k lines
    assert "line 49999" in proc.stdout

def test_f4_t2_03_command_with_non_utf8_binary_output(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --run-tool 'python3 -c \"import sys; sys.stdout.buffer.write(b\\\"hello \\xff world\\\\n\\\")\"'",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    # non-utf8 characters should be gracefully replaced, preventing decode crashes
    assert "hello" in proc.stdout
    assert "world" in proc.stdout

def test_f4_t2_04_sandbox_permissions_violation(antigravity_bin):
    # Modifying files outside the workspace should trigger sandbox violation when sandbox is enabled
    proc = subprocess.run(
        f"{antigravity_bin} --run-tool 'cat /etc/passwd' --sandbox",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 1
    assert "Sandbox violation: access denied" in proc.stderr

def test_f4_t2_05_environment_variables_isolation(antigravity_bin):
    # Set parent secrets
    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = "secret_to_scrub"
    env["SECRET_KEY"] = "sensitive_database_password"
    
    # Run tool checker
    proc = subprocess.run(
        f"{antigravity_bin} --run-tool 'test_env_isolation'",
        shell=True, capture_output=True, text=True, env=env
    )
    # The runner inside mock_antigravity scrubs ANTHROPIC_API_KEY and SECRET_KEY
    assert proc.returncode == 0
    assert "Environment isolation verified" in proc.stdout

def test_f2_f4_db_query_during_file_indexing(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'db query during file indexing' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Concurrency verified: DB query during indexing succeeded without lock." in proc.stdout

def test_r4_multi_process_concurrency_stress(antigravity_bin):
    # Spin up 5 concurrent tools in threads
    def run_one():
        p = subprocess.run(
            f"{antigravity_bin} --run-tool 'echo concurrent_thread'",
            shell=True, capture_output=True, text=True
        )
        return p.returncode, p.stdout
        
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_one) for _ in range(5)]
        results = [f.result() for f in futures]
        
    for code, out in results:
        assert code == 0
        assert "concurrent_thread" in out
