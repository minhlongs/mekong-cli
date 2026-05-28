# Anti-Gravity 2.0 E2E Testing Framework Analysis

## 1. Investigation Details

* **Target Directory**: `/Users/macbook/mekong-cli/antigravity/hybrid_runtime`
* **Observation**: The directory `/Users/macbook/mekong-cli/antigravity/hybrid_runtime` does not exist. There are no files relating to the Rust workspace, launcher scripts (`launch-llama.sh`, `run-claude-hybrid.sh`), or implementation files (`main.rs`, `router.rs`, `loop.rs`, `db.rs`, `indexer.rs`, `tools.rs`, `inference.rs`) under the `antigravity` path.
* **Current State**: The path `antigravity/` exists, but contains only Python modules (`__init__.py`, `mcp_server.py`, `vibe_kanban_bridge.py`) and subdirectories (`core`, `infrastructure`, `vibe_kanban`), which are part of the mekong-cli Python runtime.
* **Conclusion**: The Rust hybrid runtime is in a pre-implementation phase. The E2E test suite must be designed to run against either the compiled Rust binary (when implemented) or a mock CLI shim to support dual-track parallel progress.

---

## 2. Feature Inventory to be Tested

Derived from `PROJECT.md` and `/Users/macbook/mekong-cli/.agents/sub_orch_e2e_testing/SCOPE.md`:

| Feature ID | Feature Name | Key Capabilities |
|------------|--------------|------------------|
| **F1** | Hybrid Routing & Context Compaction | Heuristic regex keywords, token budget calculation, context signature compaction (< 16,384 tokens) |
| **F2** | AST Symbol Indexing & SQLite DB | tree-sitter/ast-grep symbol extraction, SQLite persistence at `.git/antigravity/session.db`, query latency < 5ms |
| **F3** | Agent Loop & Execution Control | Observe-Retrieve-Reason-Patch-Execute-Verify loop, interactive TTY approval blocks for file modifications |
| **F4** | Tool Runner & Streaming | Shell, git, ripgrep commands, process timeouts, stdout streaming, SIGINT cancellation |
| **F5** | Inference Driver & Launch Scripts | `launch-llama.sh` (Metal GPU, 8 threads, no-mmap, flash-attn), `run-claude-hybrid.sh` execution |

---

## 3. E2E Test Runner Architecture

The test runner will be built in **Python** using the **pytest** framework. This aligns with the existing test environment on the system.

### Test Runner Structure
```
tests/e2e/antigravity_e2e/
├── __init__.py
├── conftest.py              # Pytest fixtures for setup/teardown (db path, env overrides)
├── test_f1_routing.py       # F1 E2E tests (12 tests)
├── test_f2_indexing.py      # F2 E2E tests (12 tests)
├── test_f3_agent_loop.py    # F3 E2E tests (12 tests)
├── test_f4_tools.py         # F4 E2E tests (12 tests)
└── test_f5_inference.py     # F5 E2E tests (12 tests)
```

### Execution Strategy (Dual-Track Mode)
The test runner will execute the binary path defined by `ANTIGRAVITY_BIN`.
* **Track A (Compiled Binary)**: `ANTIGRAVITY_BIN=/Users/macbook/mekong-cli/antigravity/hybrid_runtime/target/debug/antigravity`
* **Track B (Mock CLI Shim)**: `ANTIGRAVITY_BIN=python3 /Users/macbook/mekong-cli/tests/e2e/mock_antigravity.py`

---

## 4. 4-Tier Test Cases Specification (60 Tests)

Below are the 60 test cases structured across 4 tiers.

### Tier 1: Feature Coverage (25 tests, 5 per feature)

#### Feature F1: Hybrid Routing & Context Compaction
1. `test_f1_t1_01_heuristic_local_routing`: Verifies that basic tasks (e.g. containing "format", "ripgrep") return `LOCAL_QWEN` route.
2. `test_f1_t1_02_heuristic_cloud_routing`: Verifies that architectural tasks (e.g. containing "refactor architecture") return `CLAUDE_CLOUD` route.
3. `test_f1_t1_03_token_budget_routing`: Verifies that tasks with large contexts (exceeding 16,384 tokens) route to `CLAUDE_CLOUD`.
4. `test_f1_t1_04_context_compaction_basic`: Verifies source code compaction extracts signatures and removes body blocks.
5. `test_f1_t1_05_compact_with_comments_retained`: Verifies context compactor retains key docstrings and class comments while removing details.

#### Feature F2: AST Symbol Indexing & SQLite DB
6. `test_f2_t1_01_sqlite_schema_initialization`: Verifies that database is initialized with `files`, `symbols`, `session_history`, and `kv_cache_registry` tables.
7. `test_f2_t1_02_ast_indexing_python_file`: Verifies indexing extracts correct symbols (class/function names, kind, lines) from Python files.
8. `test_f2_t1_03_symbol_query_by_name`: Verifies querying symbols runs under 5ms and returns correct lines and signatures.
9. `test_f2_t1_04_session_history_logging`: Verifies step-by-step history logs are recorded to `session_history`.
10. `test_f2_t1_05_kv_cache_registry_update`: Verifies KV cache details (hashes, tokens) are successfully updated.

#### Feature F3: Agent Loop & Execution Control
11. `test_f3_t1_01_observe_state_change`: Verifies the agent loop gathers changes from git status/diffs.
12. `test_f3_t1_02_retrieve_relevant_symbols`: Verifies retrieval gathers required symbol context.
13. `test_f3_t1_03_patch_generation_application`: Verifies loop parses structured patch outputs and applies them.
14. `test_f3_t1_04_interactive_approval_confirm`: Verifies execution halts and prompts user for approval, proceeding on positive TTY input.
15. `test_f3_t1_05_validation_success_terminates_loop`: Verifies that when tests compile and pass, the loop halts with success.

#### Feature F4: Tool Runner & Streaming
16. `test_f4_t1_01_shell_command_execution`: Verifies shell command executes and returns code, stdout, and stderr.
17. `test_f4_t1_02_stdout_real_time_streaming`: Verifies output streams in real time as generated by running processes.
18. `test_f4_t1_03_tool_timeout_enforcement`: Verifies commands running past timeout are terminated and return timeout errors.
19. `test_f4_t1_04_process_cancellation_sigint`: Verifies tool runner traps Ctrl+C and kills child processes.
20. `test_f4_t1_05_ripgrep_tool_search`: Verifies ripgrep executes searches and returns matching symbols/lines.

#### Feature F5: Inference Driver & Launch Scripts
21. `test_f5_t1_01_launch_llama_script_args`: Verifies `launch-llama.sh` executes llama.cpp server with Metal and thread configuration.
22. `test_f5_t1_02_run_claude_hybrid_script`: Verifies `run-claude-hybrid.sh` executes correct model route.
23. `test_f5_t1_03_llama_server_status_health`: Verifies status command returns healthy if server is listening on 8080.
24. `test_f5_t1_04_metal_offload_detection`: Verifies launcher config contains `--n-gpu-layers 99` and `--flash-attn`.
25. `test_f5_t1_05_no_mmap_flag_check`: Verifies launcher uses `--no-mmap` flag.

---

### Tier 2: Boundary & Corner Cases (25 tests, 5 per feature)

#### Feature F1: Hybrid Routing & Context Compaction
26. `test_f1_t2_01_empty_task_routing`: Verifies behavior on empty task input (falls back to local/default routing).
27. `test_f1_t2_02_conflicting_keywords_routing`: Verifies priority of Cloud keywords over Local keywords (e.g. "format refactored architecture").
28. `test_f1_t2_03_malformed_source_compaction`: Verifies compactor does not crash on syntax errors and falls back to text compaction.
29. `test_f1_t2_04_extreme_large_file_compaction`: Verifies compactor handles 1MB+ files and truncates correctly under token ceiling.
30. `test_f1_t2_05_api_key_absence_fallback`: Verifies fallback to local model if cloud model lacks key.

#### Feature F2: AST Symbol Indexing & SQLite DB
31. `test_f2_t2_01_missing_db_directory_auto_create`: Verifies database directories are created automatically if `.git/antigravity/` does not exist.
32. `test_f2_t2_02_symbol_indexing_syntax_error_file`: Verifies indexer handles syntax errors gracefully, indexing remaining valid nodes.
33. `test_f2_t2_03_query_non_existent_symbol`: Verifies querying a missing symbol returns empty list under 1ms.
34. `test_f2_t2_04_db_lock_concurrency_handling`: Verifies SQLite concurrent read/write handles transaction blocks gracefully.
35. `test_f2_t2_05_database_purge_and_vacuum`: Verifies purging/vacuuming does not corrupt database, and successfully frees space.

#### Feature F3: Agent Loop & Execution Control
36. `test_f3_t2_01_interactive_approval_reject`: Verifies loop aborts/replans when user rejects tool execution.
37. `test_f3_t2_02_validation_failed_initiates_rollback`: Verifies failed validation triggers automatic git checkout/rollback of patches.
38. `test_f3_t2_03_maximum_iteration_limit_exhausted`: Verifies loop exits with failure when max iterations (e.g., 15) is hit.
39. `test_f3_t2_04_malformed_patch_syntax_handling`: Verifies parsing handles malformed unified diff output.
40. `test_f3_t2_05_non_interactive_approval_bypass`: Verifies `--yes` bypasses approvals.

#### Feature F4: Tool Runner & Streaming
41. `test_f4_t2_01_command_not_found_handling`: Verifies command execution failure returns error code cleanly.
42. `test_f4_t2_02_extremely_long_stdout_buffer_handling`: Verifies tool runner streams 50,000+ output lines without memory leaks.
43. `test_f4_t2_03_command_with_non_utf8_binary_output`: Verifies streaming does not choke on binary/non-UTF8 characters.
44. `test_f4_t2_04_sandbox_permissions_violation`: Verifies sandbox prevents file writes outside workspace root.
45. `test_f4_t2_05_environment_variables_isolation`: Verifies target environment isolates credentials/secrets.

#### Feature F5: Inference Driver & Launch Scripts
46. `test_f5_t2_01_model_file_missing_check`: Verifies `launch-llama.sh` fails with code 1 when model file is missing.
47. `test_f5_t2_02_port_collision_fallback`: Verifies launcher handles port collision on 8080.
48. `test_f5_t2_03_insufficient_vram_warning`: Verifies script warning if system memory is insufficient for local model weights.
49. `test_f5_t2_04_claude_api_rate_limit_retry`: Verifies cloud API client handles HTTP 429 using exponential backoff retries.
50. `test_f5_t2_05_llama_server_crash_recovery`: Verifies agent auto-restarts llama-server on crash mid-session.

---

### Tier 3: Cross-Feature Combinations (5 tests)

51. `test_f1_f5_routing_to_failed_local_inference_escalation`: Verifies routing decides `LOCAL_QWEN`, but detects server is offline and escalates to `CLAUDE_CLOUD`.
52. `test_f2_f3_indexer_update_on_patch_execution`: Verifies that a successful patch execution by the agent loop automatically triggers re-indexing of that file and updates the SQLite DB.
53. `test_f3_f4_tool_timeout_during_agent_validation`: Verifies agent loop handles slow build command by timing it out, recording failure, and continuing rollback.
54. `test_f1_f3_loop_context_compactor_integration`: Verifies that as iterations progress, the context compactor compresses older execution history logs in the session DB.
55. `test_f2_f4_db_query_during_file_indexing`: Verifies concurrent queries work seamlessly while the AST indexer is updating the database.

---

### Tier 4: Real-World Workloads (5 tests)

56. `test_r1_full_hybrid_routing_compaction_pipeline`: Tests a complex task sequence verifying routing, context compaction, and prompt assembly.
57. `test_r2_incremental_repo_indexing_perf`: Tests indexing a codebase with 100+ files, validating that unmodified files are skipped and processing finishes under 500ms.
58. `test_r3_end_to_end_bug_fix_cycle`: Runs a full loop task to fix a syntax bug in a script, verifying compilation, tests passing, and success exit.
59. `test_r4_multi_process_concurrency_stress`: Runs multiple background tool executions under load to check for resource exhaustion.
60. `test_r5_agent_loop_recovery_from_compilation_error`: Verifies agent loop recovers from compilation errors by reading stderr and generating secondary patches.

---

## 5. Proposed Mock CLI Binary (`mock_antigravity.py`)

This Python script mocks the interface contracts of the Anti-Gravity 2.0 Rust CLI binary. It reads/writes to SQLite and parses arguments, enabling E2E tests to execute.

```python
#!/usr/bin/env python3
import sys
import os
import argparse
import sqlite3
import re
import json
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
        CREATE TABLE IF NOT EXISTS kv_cache_registry (
            key TEXT PRIMARY KEY,
            last_accessed INTEGER NOT NULL,
            token_count INTEGER NOT NULL,
            content_hash TEXT NOT NULL
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
    # Simulated routing heuristics
    cloud_keywords = ["refactor", "architecture", "design", "rewrite", "security"]
    local_keywords = ["format", "ripgrep", "ast-grep", "syntax", "tests", "status"]
    
    for kw in cloud_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', task, re.IGNORECASE):
            return "CLAUDE_CLOUD"
    for kw in local_keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', task, re.IGNORECASE):
            return "LOCAL_QWEN"
            
    # Default route based on token approximation
    if len(task.split()) > 100:
        return "CLAUDE_CLOUD"
    return "LOCAL_QWEN"

def main():
    parser = argparse.ArgumentParser(description="Mock Anti-Gravity 2.0 CLI Runtime")
    parser.add_argument("--task", type=str, help="Execute a specific task")
    parser.add_argument("--interactive", action="store_true", help="Start interactive TTY loop")
    parser.add_argument("--route-only", type=str, help="Determine route decision for task")
    parser.add_argument("--compact-only", type=str, help="Compact a file signature")
    parser.add_argument("--index", type=str, help="Index repository at directory path")
    parser.add_argument("--query", type=str, help="Query symbol from database")
    parser.add_argument("--status", action="store_true", help="Print runtime status")
    parser.add_argument("--yes", action="store_true", help="Bypass interactive approvals")
    
    args = parser.parse_args()
    init_db()
    
    if args.route_only:
        route = route_task(args.route_only)
        print(f"Decision: {route}")
        sys.exit(0)
        
    elif args.compact_only:
        file_path = Path(args.compact_only)
        if not file_path.exists():
            print(f"Error: File {file_path} not found", file=sys.stderr)
            sys.exit(1)
        # Mock compaction: extract function/class lines
        content = file_path.read_text()
        compacted = []
        for line in content.splitlines():
            if line.strip().startswith(("def ", "class ", "fn ", "pub fn ", "struct ", "impl ")):
                compacted.append(line)
        print("\n".join(compacted))
        sys.exit(0)
        
    elif args.index:
        dir_path = Path(args.index)
        if not dir_path.exists() or not dir_path.is_dir():
            print(f"Error: Directory {dir_path} not found", file=sys.stderr)
            sys.exit(1)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Mock index Python files
        for py_file in dir_path.glob("**/*.py"):
            cursor.execute("INSERT OR REPLACE INTO files (path, last_modified, hash) VALUES (?, ?, ?)",
                           (str(py_file), int(py_file.stat().st_mtime), "mock_hash"))
            file_id = cursor.lastrowid
            
            # Simple AST parser
            content = py_file.read_text()
            for i, line in enumerate(content.splitlines(), start=1):
                if line.strip().startswith("def "):
                    name = line.split("def ")[1].split("(")[0].strip()
                    cursor.execute("INSERT INTO symbols (file_id, name, kind, start_line, end_line, signature) VALUES (?, ?, ?, ?, ?, ?)",
                                   (file_id, name, "function", i, i+5, line.strip()))
                elif line.strip().startswith("class "):
                    name = line.split("class ")[1].split(":")[0].split("(")[0].strip()
                    cursor.execute("INSERT INTO symbols (file_id, name, kind, start_line, end_line, signature) VALUES (?, ?, ?, ?, ?, ?)",
                                   (file_id, name, "class", i, i+20, line.strip()))
        conn.commit()
        conn.close()
        print("Indexing completed successfully")
        sys.exit(0)
        
    elif args.query:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT files.path, symbols.name, symbols.kind, symbols.start_line, symbols.end_line FROM symbols JOIN files ON symbols.file_id = files.id WHERE symbols.name LIKE ?", (f"%{args.query}%",))
        results = cursor.fetchall()
        conn.close()
        for r in results:
            print(f"File: {r[0]} | Symbol: {r[1]} | Kind: {r[2]} | Range: L{r[3]}-L{r[4]}")
        sys.exit(0)
        
    elif args.status:
        print("Inference Driver: LOCAL_LLAMA (llama.cpp)")
        print("Llama Server Port: 8080 (Listening)")
        print("GPU Offloading: 99 Layers (Metal Accelerated)")
        print("KV Cache Size: 32768 tokens")
        print("SQLite Database: Connected (.git/antigravity/session.db)")
        sys.exit(0)
        
    elif args.task:
        route = route_task(args.task)
        print(f"Starting agent loop...")
        print(f"Selected Route: {route}")
        print("Step 1/3 - Analyzing state...")
        print("Found active file: src/api/auth.rs")
        
        # Approval Block simulation
        if not args.yes:
            print("Execute command: 'git diff'? [y/N]", end=" ", flush=True)
            choice = sys.stdin.readline().strip().lower()
            if choice not in ["y", "yes"]:
                print("Rejected by user.")
                sys.exit(1)
        
        print("Running: git diff")
        print("Step 2/3 - Patching file...")
        print("Step 3/3 - Validation (compiling & running tests)...")
        print("Success: 12 tests passed.")
        
        # Log session history
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", ("sess_mock", 1234567, "main", 1234567))
        cursor.execute("INSERT INTO session_history (session_id, iteration_step, task_description, route_choice, execution_outcome, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                       ("sess_mock", 1, args.task, route, "Success", 1234567))
        conn.commit()
        conn.close()
        sys.exit(0)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```
