# Scope: E2E Testing Track for Anti-Gravity 2.0

## Feature Inventory
We identify $N = 5$ distinct user-facing features from the requirements:
1. **F1: Hybrid Routing & Context Compaction**: Heuristic classification (regex keywords), token budget check (local vs cloud), and context compaction (AST head extraction keeping source code under 16k tokens).
2. **F2: AST Symbol Indexing & SQLite DB**: tree-sitter or ast-grep symbol extraction (path, hash, name, kind, line numbers), lightweight SQLite schema at `.git/antigravity/session.db`, query symbol latency under 5ms.
3. **F3: Agent Loop & Execution Control**: Observe-Retrieve-Reason-Patch-Execute-Verify loop, interactive TTY approval blocks for file-writing/deleting/execution.
4. **F4: Tool Runner & Streaming**: Command execution with timeouts, stdout streaming, and process cancellation.
5. **F5: Inference Driver & Launcher Scripts**: `launch-llama.sh` (Metal GPU, 8 threads, flash attention, no-mmap) and `run-claude-hybrid.sh` execution.

## E2E Testing Methodology
We will use a 4-tier approach for testing:
- **Tier 1: Feature Coverage (25 tests)**: 5 happy-path test cases per feature.
- **Tier 2: Boundary & Corner Cases (25 tests)**: 5 edge-case/error-handling test cases per feature.
- **Tier 3: Cross-Feature Combinations (5 tests)**: Testing interactions between features (e.g. routing + indexing, agent loop + tool execution under timeout).
- **Tier 4: Real-World Workloads (5 tests)**: Realistic application scenarios exercising the entire stack.

## Milestones
| # | Milestone Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| E1 | Test Design & Specs | Write SCOPE.md and TEST_INFRA.md | None | DONE |
| E2 | Test Harness & Mocks | Build the test runner, validation utilities, and mock interfaces for early milestones | E1 | DONE |
| E3 | Implement Tier 1-2 Tests | Write 50 test cases for feature coverage and boundaries | E2 | DONE |
| E4 | Implement Tier 3-4 Tests | Write 10 test cases for combinations and real workloads | E3 | DONE |
| E5 | Verification & Test Ready | Run the test suite against the target and publish TEST_READY.md | E4 | DONE |

## E2E Test Suite Architecture
- **Language**: Python (utilizing pytest)
- **Test Entrypoints**: We will execute the compiled Rust binary `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/target/debug/antigravity` if present, or fall back to a mock CLI shim if the implementation track hasn't compiled it yet.
- **Test Runner Location**: `tests/e2e/antigravity_e2e` or `tests/e2e/test_antigravity.py`
- **Output Artifact**: `TEST_READY.md` containing features and test coverage check.
