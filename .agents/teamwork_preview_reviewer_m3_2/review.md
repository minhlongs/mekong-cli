# Review & Adversarial Challenge Report: Milestone M3

## Review Summary

**Verdict**: APPROVE

The SQLite and AST symbol indexing implementation meets requirements. Schema design, WAL configuration, FTS5 trigrams, Walkdir walking, hash comparison, and dual-track parsing with fallback heuristics are implemented and function correctly.

---

## Quality Findings

### Minor Finding 1: Hardcoded Folder Ignore List
- **What**: The folder ignore list is hardcoded in the walk dir traversal.
- **Where**: `src/indexer.rs:300`
- **Why**: Large non-code directories not covered in the hardcoded list will still be scanned, increasing resource overhead.
- **Suggestion**: Load directories to ignore from `.gitignore` or custom configs.

### Minor Finding 2: Robustness of FTS5 MATCH Query
- **What**: The FTS5 string formatting only replaces double-quotes.
- **Where**: `src/db.rs:177`
- **Why**: Special FTS5 query syntax chars (e.g. `AND`, `OR`, `*`, `:`) can cause syntax errors, although handled gracefully via a `LIKE` fallback.
- **Suggestion**: Escape all special characters before formatting the match string.

---

## Verified Claims

- Normalized schema with cascade deletes -> Verified via inspection of schema triggers and tests -> PASS
- SQLite WAL configuration -> Verified via database setup settings -> PASS
- Dual-Track Parser & Heuristics -> Verified via test cases checking block ends -> PASS
- Incremental indexing via SHA-256 hashes -> Verified via hash update database tests -> PASS

---

## Coverage Gaps
- Custom ignore rules -> Risk: Medium -> Recommend accepting risk for M3 and addressing in future milestones.

---

## Adversarial Challenge Summary

**Overall risk assessment**: MEDIUM

---

## Challenges

### Medium Challenge 1: Brace Counting Heuristic Failures
- **Assumption challenged**: Curly brace count represents block scope.
- **Attack scenario**: Mismatched curly braces inside comments or string literals throw off the parser block boundaries.
- **Blast radius**: Out-of-bounds start/end line numbers for symbols.
- **Mitigation**: Filter out comment blocks and string tokens prior to brace counting.

### Medium Challenge 2: Python Indentation Trailing Docstring
- **Assumption challenged**: Docstring indentations track with code.
- **Attack scenario**: Code containing multi-line strings or docstrings with zero-indent lines terminates block detection prematurely.
- **Blast radius**: Symbols get cropped before their true ending line.
- **Mitigation**: Skip empty or string-only lines when evaluating indentation levels.
