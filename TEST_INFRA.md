# Anti-Gravity 2.0 Test Infrastructure Specification

This document defines the End-to-End (E2E) testing framework, test suite tiers, and runner configurations for the Anti-Gravity 2.0 Hybrid Runtime.

---

## 1. Goals & Principles

1. **Dual-Track Testing**: The test suite can run in two modes:
   - **Production Track**: Running against the compiled Rust binary at `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/target/debug/antigravity`.
   - **Mock/Simulation Track**: Running against a Python mock CLI shim (`tests/e2e/mock_antigravity.py`) to verify the E2E runner, assertion logic, and tests before the Rust code is fully compiled.
2. **Zero Network Calls**: No actual calls to external APIs (like Anthropic Claude API) during test execution. Network requests must be mocked or captured via environment variables.
3. **Comprehensive Coverage**: Minimum threshold of 60 tests (12 per feature across 5 features) distributed across 4 tiers of complexity.
4. **Visual & Behavioral Verification**: Enforces interactive TTY approval checks, stderr logs, process termination, and SQLite persistence verification.

---

## 2. Feature Inventory under Test

The E2E test suite targets 5 core user-facing features:

| Feature ID | Feature Name | Core Capabilities |
|------------|--------------|-------------------|
| **F1** | Hybrid Routing & Context Compaction | Classification heuristics, token budget limits, and tree-sitter context signature compaction (< 16,384 tokens). |
| **F2** | AST Symbol Indexing & SQLite DB | AST Symbol extraction, SQLite session tracking at `.git/antigravity/session.db`, symbol query latency < 5ms. |
| **F3** | Agent Loop & Execution Control | Observe-Retrieve-Reason-Patch-Execute-Verify (ORRPEV) iteration loop, interactive TTY approval gates. |
| **F4** | Tool Runner & Streaming | Subprocess launcher (shell, git, rg, ast-grep), streaming stdout, timeout limits, SIGINT process group cleanup. |
| **F5** | Inference Driver & Launch Scripts | llama.cpp server configuration (`launch-llama.sh` - Metal GPU, 8 threads, no-mmap, flash-attn) and `run-claude-hybrid.sh` CLI wrapper. |

---

## 3. E2E Test Suite Specification (60 Tests)

### Tier 1: Feature Coverage (25 Tests)

#### Feature F1: Hybrid Routing & Context Compaction
1. `test_f1_t1_01_heuristic_local_routing`: Validates that tasks containing local keywords (e.g. "format", "ripgrep", "syntax check") route to `LOCAL_QWEN`.
2. `test_f1_t1_02_heuristic_cloud_routing`: Validates that complex tasks containing cloud keywords (e.g. "refactor architecture", "migrate framework") route to `CLAUDE_CLOUD`.
3. `test_f1_t1_03_token_budget_routing`: Validates that task inputs with massive context (> 16k tokens) automatically route to `CLAUDE_CLOUD` due to local context overflow.
4. `test_f1_t1_04_context_compaction_basic`: Validates that the AST context compactor successfully replaces function bodies with function signatures.
5. `test_f1_t1_05_compact_with_comments_retained`: Validates that signature comments and docstrings are preserved during AST compaction.

#### Feature F2: AST Symbol Indexing & SQLite DB
6. `test_f2_t1_01_sqlite_schema_initialization`: Validates that database files are created and tables (`sessions`, `session_history`, `kv_cache_registry`, `files`, `symbols`) are initialized correctly.
7. `test_f2_t1_02_ast_indexing_python_file`: Validates tree-sitter or ast-grep parse python files and insert classes and functions into SQLite.
8. `test_f2_t1_03_symbol_query_by_name`: Validates symbol queries execute under 5ms and return valid file paths and lines.
9. `test_f2_t1_04_session_history_logging`: Validates iteration history details are logged to `session_history` after every loop cycle.
10. `test_f2_t1_05_kv_cache_registry_update`: Validates KV cache hashes and token counts are correctly updated on query lookup.

#### Feature F3: Agent Loop & Execution Control
11. `test_f3_t1_01_observe_state_change`: Validates loop detects git changes or workspace modifications.
12. `test_f3_t1_02_retrieve_relevant_symbols`: Validates loop pulls correct signature definitions from SQLite during retrieve phase.
13. `test_f3_t1_03_patch_generation_application`: Validates loop parses unified diff patches and applies them successfully to target files.
14. `test_f3_t1_04_interactive_approval_confirm`: Validates loop prompts for approval before executing destructive actions, continuing on positive input.
15. `test_f3_t1_05_validation_success_terminates_loop`: Validates that when a compilation test returns success, the loop halts and reports success.

#### Feature F4: Tool Runner & Streaming
16. `test_f4_t1_01_shell_command_execution`: Validates shell tool runs commands and outputs clean status, stdout, and stderr.
17. `test_f4_t1_02_stdout_real_time_streaming`: Validates console output streams in real time as the underlying command produces it.
18. `test_f4_t1_03_tool_timeout_enforcement`: Validates commands running beyond `timeout_ms` are terminated, returning a timeout status.
19. `test_f4_t1_04_process_cancellation_sigint`: Validates tool runner captures SIGINT and terminates child process groups.
20. `test_f4_t1_05_ripgrep_tool_search`: Validates the ripgrep search tool returns matches with line number indicators.

#### Feature F5: Inference Driver & Launch Scripts
21. `test_f5_t1_01_launch_llama_script_args`: Validates `launch-llama.sh` invokes the server with 8 performance threads, Metal GPU offloading, and no-mmap.
22. `test_f5_t1_02_run_claude_hybrid_script`: Validates `run-claude-hybrid.sh` selects correct environment variables and CLI model endpoint.
23. `test_f5_t1_03_llama_server_status_health`: Validates the agent status command detects llama-server status.
24. `test_f5_t1_04_metal_offload_detection`: Validates system logs contain Metal acceleration offload indicators (`--n-gpu-layers 99`).
25. `test_f5_t1_05_no_mmap_flag_check`: Validates that server is running with `--no-mmap` configuration.

---

### Tier 2: Boundary & Corner Cases (25 Tests)

#### Feature F1: Hybrid Routing & Context Compaction
26. `test_f1_t2_01_empty_task_routing`: Validates routing falls back gracefully to default route on empty or whitespace-only inputs.
27. `test_f1_t2_02_conflicting_keywords_routing`: Validates that cloud force keywords take precedence over local keywords (e.g. "format structure for security refactoring").
28. `test_f1_t2_03_malformed_source_compaction`: Validates that AST compaction falls back to signature text line matches on syntax errors.
29. `test_f1_t2_04_extreme_large_file_compaction`: Validates compaction doesn't crash on huge files (> 1MB) and enforces a strict token count limit.
30. `test_f1_t2_05_api_key_absence_fallback`: Validates that if cloud route is chosen but ANTHROPIC_API_KEY is missing, it alerts the user and falls back.

#### Feature F2: AST Symbol Indexing & SQLite DB
31. `test_f2_t2_01_missing_db_directory_auto_create`: Validates the DB client automatically initializes the `.git/antigravity/` folder if it doesn't exist.
32. `test_f2_t2_02_symbol_indexing_syntax_error_file`: Validates indexer handles syntax errors gracefully, indexing other valid blocks in the file.
33. `test_f2_t2_03_query_non_existent_symbol`: Validates symbol query for unknown names returns an empty list under 1ms.
34. `test_f2_t2_04_db_lock_concurrency_handling`: Validates concurrent SQLite queries and writes function without locking using WAL journal mode.
35. `test_f2_t2_05_database_purge_and_vacuum`: Validates database purging clears session history records and vacuums correctly without corruption.

#### Feature F3: Agent Loop & Execution Control
36. `test_f3_t2_01_interactive_approval_reject`: Validates that when a user enters "n" or rejects tool execution, the loop does not run the tool.
37. `test_f3_t2_02_validation_failed_initiates_rollback`: Validates that if compilation/validation checks fail, the loop rolls back the patch using git checkout.
38. `test_f3_t2_03_maximum_iteration_limit_exhausted`: Validates the loop halts and reports failure when the step count exceeds the maximum limit (15).
39. `test_f3_t2_04_malformed_patch_syntax_handling`: Validates parsing of malformed unified diff patch outputs does not crash the loop.
40. `test_f3_t2_05_non_interactive_approval_bypass`: Validates that running the CLI with `--yes` flag bypasses all interactive confirmation gates.

#### Feature F4: Tool Runner & Streaming
41. `test_f4_t2_01_command_not_found_handling`: Validates command executor returns exit code 127 and descriptive stderr when binary is missing.
42. `test_f4_t2_02_extremely_long_stdout_buffer_handling`: Validates streaming output works under load (50k+ stdout lines) without memory bloat.
43. `test_f4_t2_03_command_with_non_utf8_binary_output`: Validates process output parsing extracts raw bytes to avoid decoding crashes on binary sequences.
44. `test_f4_t2_04_sandbox_permissions_violation`: Validates the sandbox execution prevents actions modifying system directories outside workspace root.
45. `test_f4_t2_05_environment_variables_isolation`: Validates the execution environment is scrubbed of parent environment secrets.

#### Feature F5: Inference Driver & Launch Scripts
46. `test_f5_t2_01_model_file_missing_check`: Validates `launch-llama.sh` exits with code 1 and outputs errors when the model GGUF path doesn't exist.
47. `test_f5_t2_02_port_collision_fallback`: Validates that launcher script aborts cleanly and reports when port 8080 is already in use.
48. `test_f5_t2_03_insufficient_vram_warning`: Validates warning output when RAM/VRAM checks show insufficient memory allocations for the 35B model.
49. `test_f5_t2_04_claude_api_rate_limit_retry`: Validates the Anthropic client catches HTTP 429 rate limit statuses and applies retry logic.
50. `test_f5_t2_05_llama_server_crash_recovery`: Validates client detects connection dropouts mid-run and initiates server recovery/restarts.

---

### Tier 3: Cross-Feature Combinations (5 Tests)

51. `test_f1_f5_routing_to_failed_local_inference_escalation`: Validates local routing fallback to cloud when llama-server is unresponsive.
52. `test_f2_f3_indexer_update_on_patch_execution`: Validates patch application automatically triggers incremental AST indexing and updates the SQLite DB.
53. `test_f3_f4_tool_timeout_during_agent_validation`: Validates agent loop halts build step when it exceeds timeout, recording validation failure.
54. `test_f1_f3_loop_context_compactor_integration`: Validates session db compactor compresses history logs as iterations progress.
55. `test_f2_f4_db_query_during_file_indexing`: Validates database concurrency by querying symbols while background indexing runs.

---

### Tier 4: Real-World Workloads (5 Tests)

56. `test_r1_full_hybrid_routing_compaction_pipeline`: Traces a full task pipeline involving regex routing, context compaction, and template rendering.
57. `test_r2_incremental_repo_indexing_perf`: Validates file parsing optimization: files with identical hashes are skipped, completing scans in < 500ms.
58. `test_r3_end_to_end_bug_fix_cycle`: Runs a full bugfix loop solving a compiler warning in a target script, testing execution and successful resolution.
59. `test_r4_multi_process_concurrency_stress`: Invokes concurrent commands in parallel to verify thread safety and file handles.
60. `test_r5_agent_loop_recovery_from_compilation_error`: Validates the agent reads error reports, writes a corrective patch, and runs tests to successfully verify.

---

## 4. E2E Test Runner Implementation Plan

The test runner is written in Python, utilizing pytest. It controls process pipelines using `subprocess.Popen` and validates databases via `sqlite3`.

### Directory Layout
```
tests/e2e/antigravity_e2e/
├── conftest.py
├── test_f1_routing.py
├── test_f2_indexing.py
├── test_f3_agent_loop.py
├── test_f4_tools.py
└── test_f5_inference.py
```

### Pytest Configuration (`tests/e2e/antigravity_e2e/conftest.py`)
```python
import pytest
import os
import sqlite3
import subprocess
from pathlib import Path

@pytest.fixture(scope="session")
def antigravity_bin():
    # Use environment variable or fallback to python mock CLI shim
    default_shim = str(Path(__file__).parents[2] / "e2e" / "mock_antigravity.py")
    bin_path = os.getenv("ANTIGRAVITY_BIN", f"python3 {default_shim}")
    return bin_path

@pytest.fixture(scope="function")
def clean_db():
    db_path = Path(".git/antigravity/session.db")
    if db_path.exists():
        db_path.unlink()
    yield db_path
    if db_path.exists():
        db_path.unlink()
```

---

## 5. Mock CLI Shim (`tests/e2e/mock_antigravity.py`)

A mock Python CLI that simulates the CLI interface of the compiled Rust binary, enabling test runner validation:

```python
#!/usr/bin/env python3
import sys
import os
import argparse
import sqlite3
import re
from pathlib import Path

DB_PATH = Path(".git/antigravity/session.db")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at INTEGER NOT NULL,
            current_branch TEXT NOT NULL,
            last_active_at INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            iteration_step INTEGER NOT NULL,
            task_description TEXT NOT NULL,
            route_choice TEXT NOT NULL,
            execution_outcome TEXT NOT NULL,
            patch_applied TEXT,
            timestamp INTEGER NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(session_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            last_modified INTEGER NOT NULL,
            hash TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS symbols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER,
            name TEXT NOT NULL,
            kind TEXT NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            signature TEXT NOT NULL,
            FOREIGN KEY(file_id) REFERENCES files(id)
        )
    """)
    conn.commit()
    conn.close()

def route_task(task: str):
    cloud_keywords = ["refactor", "architecture", "design", "rewrite", "security"]
    local_keywords = ["format", "ripgrep", "ast-grep", "syntax", "tests", "status"]
    for kw in cloud_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', task, re.IGNORECASE):
            return "CLAUDE_CLOUD"
    for kw in local_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', task, re.IGNORECASE):
            return "LOCAL_QWEN"
    return "CLAUDE_CLOUD" if len(task.split()) > 100 else "LOCAL_QWEN"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str)
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--route-only", type=str)
    parser.add_argument("--compact-only", type=str)
    parser.add_argument("--index", type=str)
    parser.add_argument("--query", type=str)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    init_db()
    
    if args.route_only:
        print(f"Decision: {route_task(args.route_only)}")
    elif args.compact_only:
        file_path = Path(args.compact_only)
        if not file_path.exists():
            sys.exit(1)
        content = file_path.read_text()
        for line in content.splitlines():
            if line.strip().startswith(("def ", "class ", "fn ", "struct ")):
                print(line)
    elif args.index:
        dir_path = Path(args.index)
        if not dir_path.exists():
            sys.exit(1)
        print("Indexing completed successfully")
    elif args.query:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT files.path, symbols.name FROM symbols JOIN files ON symbols.file_id = files.id WHERE symbols.name LIKE ?", (f"%{args.query}%",))
        results = cursor.fetchall()
        for r in results:
            print(f"File: {r[0]} | Symbol: {r[1]}")
        conn.close()
    elif args.status:
        print("Inference Driver: LOCAL_LLAMA (llama.cpp)")
        print("SQLite Database: Connected (.git/antigravity/session.db)")
    elif args.task:
        route = route_task(args.task)
        print(f"Selected Route: {route}")
        if not args.yes:
            print("Execute command: 'git diff'? [y/N]", end=" ", flush=True)
            choice = sys.stdin.readline().strip().lower()
            if choice not in ["y", "yes"]:
                print("Rejected")
                sys.exit(1)
        print("Success: 12 tests passed.")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO sessions VALUES ('sess_mock', 12345, 'main', 12345)")
        cursor.execute("INSERT INTO session_history (session_id, iteration_step, task_description, route_choice, execution_outcome, timestamp) VALUES ('sess_mock', 1, ?, ?, 'Success', 12345)", (args.task, route))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    main()
```

---

## 6. How to Run E2E Tests

Verify the infrastructure and runner by specifying the `ANTIGRAVITY_BIN` environment variable:

```bash
# Verify using the mock CLI shim
ANTIGRAVITY_BIN="python3 tests/e2e/mock_antigravity.py" python3 -m pytest tests/e2e/antigravity_e2e/

# Verify using the compiled Rust binary
ANTIGRAVITY_BIN="/Users/macbook/mekong-cli/antigravity/hybrid_runtime/target/debug/antigravity" python3 -m pytest tests/e2e/antigravity_e2e/
```
