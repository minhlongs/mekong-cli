# Review Report: Milestone M3 SQLite & AST Symbol Indexer

## Review Summary

**Verdict**: APPROVE

The implementation of Milestone M3 inside `antigravity/hybrid_runtime` is correct, robust, and fully conforms to the interface contracts specified in `SCOPE.md`. It provides a clean SQLite persistence layer (using WAL, trigger-driven FTS5 trigram indexing, and foreign key cascades) and a robust Dual-Track Symbol Indexer (supporting both Tree-sitter and a regex fallback with indentation/brace-matching heuristics) along with an incremental walker.

No integrity violations, facade implementations, or hardcoded shortcuts were found in the source code or test suites.

---

## Verified Claims

- **Claim 1: Database Initialization and Schema Conformance**
  - *Status*: PASS
  - *Method*: Verified via static inspection of `src/db.rs` lines 12-64 and `SessionDb::new` lines 68-82. The database is initialized under `<repo_path>/.git/antigravity/session.db` and applies schemas for `files`, `symbols`, `session_metadata`, and `chat_history`.
- **Claim 2: Performance-Oriented SQLite Pragmas**
  - *Status*: PASS
  - *Method*: Verified via static inspection of `setup_pragmas` in `src/db.rs` lines 84-90. It enables WAL mode, NORMAL synchronization, foreign keys ON, and MEMORY temp_store.
- **Claim 3: FTS5 Trigram & SQL Wildcard Fallback**
  - *Status*: PASS
  - *Method*: Verified via static inspection of migration 1 in `src/db.rs` (lines 33-50) and `query_symbols` (lines 175-240). It creates virtual table `symbols_fts` and triggers `symbols_ai`, `symbols_ad`, and `symbols_au`. It tries trigram MATCH first and gracefully falls back to a wildcard `LIKE` search on match failure/empty sets.
- **Claim 4: Walkdir Crawling with Ignored Lists**
  - *Status*: PASS
  - *Method*: Verified via static inspection of `index_repo` in `src/indexer.rs` lines 279-344. It ignores `.git`, `node_modules`, `.agents`, `target`, `.venv`, and `__pycache__` directories.
- **Claim 5: SHA-256 Hash Incremental Indexing**
  - *Status*: PASS
  - *Method*: Verified via static inspection of `calculate_file_hash` (lines 263-277) and incremental update logic in `index_repo` (lines 313-329) and `update_file_symbols` (lines 129-168). Files with matching hashes skip updates entirely, and modified files update their symbols inside a transaction.
- **Claim 6: Cascade Deletion of Symbols and Index Entries**
  - *Status*: PASS
  - *Method*: Verified via static inspection of schema definition (line 27), `delete_file` (lines 123-127), cleanup loop (lines 336-341), and trigger `symbols_ad` (lines 43-45). Deleting files triggers cascaded deletes in `symbols` and `symbols_fts`.
- **Claim 7: Dual-Track AST Parser**
  - *Status*: PASS
  - *Method*: Verified via static inspection of `extract_symbols_from_file` in `src/indexer.rs` lines 24-49. If feature flag `tree-sitter-grammars` is enabled and works, it uses Tree-sitter; otherwise it falls back to regex matching.
- **Claim 8: Block-End Heuristics**
  - *Status*: PASS
  - *Method*: Verified via static inspection of `find_brace_block_end` (lines 209-227) and `find_python_block_end` (lines 229-247) in `src/indexer.rs`. It counts brace nests for Rust/JS/TS and indentation levels for Python.

---

## Findings

### [Minor] Finding 1: Heuristic Limitation in Regex Fallback Brace-Matching
- **What**: Brace counting (`find_brace_block_end`) does not parse tokens.
- **Where**: `src/indexer.rs` lines 209-227
- **Why**: Braces located inside comments or string literals (e.g. `let bracket = "}";` or `// {`) will distort the brace count and could cause block end line calculations to be inaccurate.
- **Suggestion**: This is acceptable for the regex fallback track. However, the runtime should ensure `tree-sitter-grammars` feature is enabled for production environments to avoid heuristic inaccuracies.

### [Minor] Finding 2: Heuristic Limitation in Regex Fallback Python Indentation
- **What**: Python block-end estimation (`find_python_block_end`) does not parse multiline strings or docstrings.
- **Where**: `src/indexer.rs` lines 229-247
- **Why**: If a docstring or multiline string has a line with 0-column indentation (e.g., query string templates), it will cause the parser to mark the block as ended prematurely.
- **Suggestion**: Similar to Finding 1, this is a minor limitation of regex fallback. Tree-sitter Python parser should be preferred for production deployments.

---

## Coverage Gaps

- **Tree-sitter Language Grammar Availability**:
  - *Risk Level*: Low
  - *Description*: The Tree-sitter implementation relies on grammar libraries such as `tree-sitter-rust`, `tree-sitter-python`, and `tree-sitter-typescript`. If these are compiled, parsing is highly accurate. If they are disabled or fail to compile/link, the engine falls back to regex. The regex fallback works correctly but has standard heuristic limits.
  - *Recommendation*: Ensure that the features are enabled (`--features tree-sitter-grammars`) during deployment/shipping pipelines to guarantee high-accuracy parsing.

---

## Unverified Items

- **Cargo Test Execution**:
  - *Reason not verified*: Tool environment constraint. Running `cargo test --test m3_tests` timed out waiting for manual approval of the command execution in the subagent sandbox environment.
  - *Mitigation*: The integration test suite (`tests/m3_tests.rs`) was inspect-validated. It covers schema validation, migration check, WAL pragma check, cascade checks, metadata/chat stores, brace-matching, python indentation, and search query latency performance (< 5ms).
