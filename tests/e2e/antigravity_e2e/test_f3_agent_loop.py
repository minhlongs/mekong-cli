import subprocess
import sqlite3
import os
import sys

def test_f3_t1_01_observe_state_change(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'observe change' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Phase: Observe" in proc.stdout

def test_f3_t1_02_retrieve_relevant_symbols(antigravity_bin, clean_db):
    # Seed symbols
    subprocess.run(f"{antigravity_bin} --status", shell=True)
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO files (id, path, last_modified, hash) VALUES (1, 'mock.py', 123, 'hash')")
    cursor.execute("INSERT INTO symbols (file_id, name, kind, start_line, end_line, signature) VALUES (1, 'test_func', 'function', 1, 2, 'def test_func()')")
    conn.commit()
    conn.close()
    
    proc = subprocess.run(
        f"{antigravity_bin} --task 'retrieve relevant symbols' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Phase: Retrieve" in proc.stdout
    assert "Retrieved Symbol: test_func" in proc.stdout

def test_f3_t1_03_patch_generation_application(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'apply patch' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Phase: Reason & Patch" in proc.stdout
    assert "Success" in proc.stdout

def test_f3_t1_04_interactive_approval_confirm(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'format file'",
        shell=True, input="y\n", capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "git diff'? [y/N]" in proc.stdout
    assert "Success" in proc.stdout

def test_f3_t1_05_validation_success_terminates_loop(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'simple task' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Success" in proc.stdout

def test_f3_t2_01_interactive_approval_reject(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'format file'",
        shell=True, input="n\n", capture_output=True, text=True
    )
    assert proc.returncode == 1
    assert "Rejected" in proc.stdout

def test_f3_t2_02_validation_failed_initiates_rollback(antigravity_bin, clean_db):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'fail validation' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 1
    assert "Validation Failed: compilation error" in proc.stderr
    assert "Initiating rollback..." in proc.stdout
    
    # Check execution outcome logged to DB as Failed
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute("SELECT execution_outcome FROM session_history")
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "Failed"

def test_f3_t2_03_maximum_iteration_limit_exhausted(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'maximum iteration exhausted' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 1
    assert "Iteration 15: Running step..." in proc.stdout
    assert "Error: Maximum iteration limit reached" in proc.stderr

def test_f3_t2_04_malformed_patch_syntax_handling(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'malformed patch' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Warning: Malformed patch syntax ignored" in proc.stderr
    assert "Success" in proc.stdout

def test_f3_t2_05_non_interactive_approval_bypass(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'format file' --yes",
        shell=True, capture_output=True, text=True
    )
    # With --yes, it shouldn't print the git diff prompt and should complete successfully
    assert "git diff'? [y/N]" not in proc.stdout
    assert proc.returncode == 0

def test_f1_f3_loop_context_compactor_integration(antigravity_bin):
    proc = subprocess.run(
        f"{antigravity_bin} --task 'loop context compactor' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Compacting session history logs..." in proc.stdout

def test_r3_end_to_end_bug_fix_cycle(antigravity_bin):
    # Simulates a bug fix cycle where step 1 fails, and step 2 corrects and succeeds
    proc = subprocess.run(
        f"{antigravity_bin} --task 'corrective patch bugfix' --yes",
        shell=True, capture_output=True, text=True
    )
    assert proc.returncode == 0
    assert "Iteration 1:" in proc.stdout
    assert "Validation Failed: compile error" in proc.stderr
    assert "Iteration 2:" in proc.stdout
    assert "Applying corrective patch..." in proc.stdout
    assert "Success: 12 tests passed." in proc.stdout
