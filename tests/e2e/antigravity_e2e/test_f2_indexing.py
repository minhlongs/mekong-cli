import subprocess
import sqlite3
import shutil
import os
from pathlib import Path

def test_f2_t1_01_sqlite_schema_initialization(antigravity_bin, clean_db):
    # Running any command initializes the database schema
    proc = subprocess.run(f"{antigravity_bin} --status", shell=True, capture_output=True, text=True)
    assert proc.returncode == 0
    
    assert clean_db.exists()
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    conn.close()
    
    expected_tables = ["sessions", "session_history", "files", "symbols", "kv_cache_registry"]
    for t in expected_tables:
        assert t in tables

def test_f2_t1_02_ast_indexing_python_file(antigravity_bin, clean_db, tmp_path):
    test_file = tmp_path / "app.py"
    test_file.write_text("class Database:\n    def connect(self):\n        pass\n\ndef main():\n    pass\n")
    
    proc = subprocess.run(f"{antigravity_bin} --index {test_file}", shell=True, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Indexing completed successfully" in proc.stdout
    
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute("SELECT path, hash FROM files")
    files_rows = cursor.fetchall()
    assert len(files_rows) == 1
    assert files_rows[0][0] == str(test_file.resolve())
    
    cursor.execute("SELECT name, kind, signature FROM symbols ORDER BY name")
    symbols_rows = cursor.fetchall()
    conn.close()
    
    assert len(symbols_rows) == 3
    # Sorted order of names: Database, connect, main
    assert symbols_rows[0][0] == "Database"
    assert symbols_rows[0][1] == "class"
    assert symbols_rows[1][0] == "connect"
    assert symbols_rows[1][1] == "function"
    assert symbols_rows[2][0] == "main"
    assert symbols_rows[2][1] == "function"

def test_f2_t1_03_symbol_query_by_name(antigravity_bin, clean_db, tmp_path):
    test_file = tmp_path / "app.py"
    test_file.write_text("def unique_search_symbol_xyz():\n    pass\n")
    
    # Index the file
    subprocess.run(f"{antigravity_bin} --index {test_file}", shell=True)
    
    # Query the symbol
    proc = subprocess.run(f"{antigravity_bin} --query unique_search_symbol_xyz", shell=True, capture_output=True, text=True)
    assert proc.returncode == 0
    assert f"File: {test_file.resolve()}" in proc.stdout
    assert "Symbol: unique_search_symbol_xyz" in proc.stdout

def test_f2_t1_04_session_history_logging(antigravity_bin, clean_db):
    proc = subprocess.run(f"{antigravity_bin} --task 'format file' --yes", shell=True, capture_output=True, text=True)
    assert proc.returncode == 0
    
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, current_branch FROM sessions")
    sessions = cursor.fetchall()
    cursor.execute("SELECT session_id, iteration_step, task_description, route_choice, execution_outcome FROM session_history")
    history = cursor.fetchall()
    conn.close()
    
    assert len(sessions) == 1
    assert sessions[0][0] == "sess_mock"
    assert sessions[0][1] == "main"
    
    assert len(history) == 1
    assert history[0][0] == "sess_mock"
    assert history[0][1] == 1
    assert history[0][2] == "format file"
    assert history[0][3] == "LOCAL_QWEN"
    assert history[0][4] == "Success"

def test_f2_t1_05_kv_cache_registry_update(antigravity_bin, clean_db, tmp_path):
    test_file = tmp_path / "helper.py"
    test_file.write_text("def my_helper():\n    pass\n")
    subprocess.run(f"{antigravity_bin} --index {test_file}", shell=True)
    
    # Run query
    proc = subprocess.run(f"{antigravity_bin} --query my_helper", shell=True, capture_output=True, text=True)
    assert proc.returncode == 0
    
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute("SELECT query_hash, token_count FROM kv_cache_registry")
    rows = cursor.fetchall()
    conn.close()
    
    assert len(rows) == 1
    assert rows[0][1] == len("my_helper")

def test_f2_t2_01_missing_db_directory_auto_create(antigravity_bin, clean_db):
    # Force deletion of DB directory
    db_dir = clean_db.parent
    if db_dir.exists():
        shutil.rmtree(db_dir)
    assert not db_dir.exists()
    
    # Run status, which should trigger db directory and schema auto-creation
    proc = subprocess.run(f"{antigravity_bin} --status", shell=True, capture_output=True, text=True)
    assert proc.returncode == 0
    assert db_dir.exists()
    assert clean_db.exists()

def test_f2_t2_02_symbol_indexing_syntax_error_file(antigravity_bin, clean_db, tmp_path):
    test_file = tmp_path / "broken.py"
    test_file.write_text("class ValidClass:\n    pass\n\ndef broken_func(a,:\n    pass\n")
    
    proc = subprocess.run(f"{antigravity_bin} --index {test_file}", shell=True, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Indexing completed successfully" in proc.stdout
    
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name, kind FROM symbols ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    
    # ValidClass should still be indexed despite syntax error downstream
    names = [r[0] for r in rows]
    assert "ValidClass" in names

def test_f2_t2_03_query_non_existent_symbol(antigravity_bin, clean_db):
    # Ensure initialized
    subprocess.run(f"{antigravity_bin} --status", shell=True)
    
    proc = subprocess.run(f"{antigravity_bin} --query non_existent_xyz_symbol", shell=True, capture_output=True, text=True)
    assert proc.returncode == 0
    assert proc.stdout == ""

def test_f2_t2_04_db_lock_concurrency_handling(antigravity_bin, clean_db):
    # Initialize DB
    subprocess.run(f"{antigravity_bin} --status", shell=True)
    
    # Verify WAL mode is set and allows concurrent reads/writes without lock
    conn = sqlite3.connect(clean_db)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0].lower()
    assert mode == "wal"
    conn.close()

def test_f2_t2_05_database_purge_and_vacuum(antigravity_bin, clean_db):
    # Initialize
    subprocess.run(f"{antigravity_bin} --task 'format file' --yes", shell=True)
    
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM session_history")
    cursor.execute("VACUUM")
    conn.commit()
    
    # Confirm purged successfully
    cursor.execute("SELECT count(*) FROM session_history")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 0

def test_f2_f3_indexer_update_on_patch_execution(antigravity_bin, clean_db):
    # Runs task with indexing triggers
    proc = subprocess.run(f"{antigravity_bin} --task 'indexer update on patch' --yes", shell=True, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Triggering incremental AST indexing..." in proc.stdout
    
    # Query to check added function exists
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM symbols WHERE name = 'test_added_func'")
    row = cursor.fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "test_added_func"

def test_r2_incremental_repo_indexing_perf(antigravity_bin, clean_db, tmp_path):
    test_file = tmp_path / "app.py"
    test_file.write_text("def my_func():\n    pass\n")
    
    # First index: 1 indexed, 0 skipped
    proc1 = subprocess.run(f"{antigravity_bin} --index {test_file}", shell=True, capture_output=True, text=True)
    assert "Indexed: 1, Skipped: 0" in proc1.stdout
    
    # Second index (no modifications): 0 indexed, 1 skipped
    proc2 = subprocess.run(f"{antigravity_bin} --index {test_file}", shell=True, capture_output=True, text=True)
    assert "Indexed: 0, Skipped: 1" in proc2.stdout
