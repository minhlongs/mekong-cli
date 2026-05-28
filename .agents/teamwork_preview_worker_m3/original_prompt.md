## 2026-05-26T16:35:03Z

You are a versatile worker (teamwork_preview_worker_m3).
Your working directory is /Users/macbook/mekong-cli/.agents/teamwork_preview_worker_m3.
Your parent is 43e9a79e-50e7-4530-9e79-62ba7076968a (the implementation orchestrator).

Your task:
Implement Milestone M3: SQLite & AST for the Anti-Gravity 2.0 Hybrid Runtime inside `/Users/macbook/mekong-cli/antigravity/hybrid_runtime`.

Please read the design reports:
- `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_m3_1/analysis.md` (SQLite and DB schema design)
- `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_m3_2/analysis.md` (AST symbol parsing and Regex fallback)
- `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_m3_3/analysis.md` (Repo walker, hashing, and integration)

Key implementation items:
1. **SQLite persistence layer (`src/db.rs`)**:
   - Implement `SessionDb` with SQLite connection.
   - Configure optimizations via PRAGMA (WAL mode, normal sync, memory temp_store, enable foreign keys).
   - Set up automatic schema migrations using `PRAGMA user_version`. Create tables: `files`, `symbols`, `session_metadata`, and `chat_history`.
   - Setup FTS5 trigram virtual table `symbols_fts` and database triggers to keep it synchronized.
   - Implement `update_file_symbols(path: &str, hash: &str, symbols: &[Symbol])` using transactions.
   - Implement query methods for symbols.
2. **AST symbol indexer (`src/indexer.rs`)**:
   - Implement `Symbol` struct (with path, hash, name, kind, start_line, end_line).
   - Implement `extract_symbols_from_file(file_path: &Path, content: &str, hash: &str) -> Result<Vec<Symbol>>` using a Dual-Track Parser: try tree-sitter if grammar crates are compiled, and fall back to the robust Regex-based pattern matching parser with curly-brace matching (for Rust/JS/TS) and indentation matching (for Python) to find block end lines.
   - Implement `index_repo(repo_path: &Path) -> Result<()>` traversing the repository using `walkdir`. Automatically ignore `.git`, `node_modules`, `.agents`, `target`, etc. Use hashes (e.g. SHA-256) of files to skip unchanged files (incremental index), insert new/modified files and cascade delete old records for modified or deleted files.
   - Implement `query_symbols(query: &str) -> Result<Vec<Symbol>>` searching the SQLite DB (with trigram `MATCH` or falling back to `LIKE` wildcard). Implement automatic discovery of `session.db` by traversing up parent directories starting from the current directory.
3. **Dependencies (`Cargo.toml`)**:
   - Add standard library dependencies such as `walkdir = "2"`, `sha2 = "0.10"`, etc. if needed to support walking and hashing. Do NOT add heavy grammars unless you configure them with features or fallback elegantly.
4. **Verification**:
   - Write unit tests in `src/db.rs` and `src/indexer.rs` (or a dedicated integration test file under `tests/`) to verify:
     - Table initialization and migrations.
     - Database operations (inserting, deleting, cascading, and WAL mode).
     - Symbol extraction correctness (including regex fallback and brace/indentation heuristics).
     - Sub-5ms query response time on symbols.
   - Run `cargo check`, `cargo build`, and `cargo test` in `/Users/macbook/mekong-cli/antigravity/hybrid_runtime` to verify.

Verify compilation and tests, and document the results in `/Users/macbook/mekong-cli/.agents/teamwork_preview_worker_m3/handoff.md`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
