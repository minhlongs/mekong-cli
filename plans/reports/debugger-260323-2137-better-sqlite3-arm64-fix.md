---
title: better-sqlite3 native binding fix — darwin-arm64
date: 2026-03-23T21:37
type: debugger
---

## Executive Summary

- **Problem**: better-sqlite3 native binding not found for `node-v141-darwin-arm64`
- **Root cause**: Node v25.2.1 (ABI 141) — prebuilt binary not distributed for this version; binding needed recompilation from source
- **Fix**: `pnpm rebuild better-sqlite3` — compiled from source on the machine
- **Result**: 2398/2398 tests passing (0 failures), up from 2199/2388

---

## Technical Analysis

### Environment

| Item | Value |
|------|-------|
| Platform | darwin arm64 (M1 Max) |
| Node.js | v25.2.1 |
| Node ABI | 141 |
| better-sqlite3 | 11.6.0 |
| Package manager | pnpm 10.32.1 |

### Root Cause

better-sqlite3 11.6.0 ships prebuilt binaries for common Node LTS versions. Node v25.x is a current release (not LTS), so `node-v141-darwin-arm64` prebuilt does not exist. When pnpm installed the package, it downloaded sources only — and the native `.node` file was absent.

The fix: `pnpm rebuild better-sqlite3` triggers `node-gyp` to compile the C++ extension locally using the machine's installed Xcode toolchain. M1 Max has all required build tools, so compilation succeeds cleanly.

### Affected Test Groups (before fix)

- `DecisionStore` tests (SQLite persistence layer)
- `DecisionLogger` tests (audit log writes)
- OpenClaw wiring tests (agent state persistence)
- All tests that instantiate a real SQLite db (189 reported failing)

### Fix Applied

```bash
cd /Users/macbookprom1/projects/algo-trade
pnpm rebuild better-sqlite3
# => Compiled successfully for node-v141-darwin-arm64
```

### Verification

```
node -e "require('better-sqlite3')"
# => better-sqlite3 loaded OK

npx vitest run
# => Test Files  158 passed (158)
# => Tests       2398 passed (2398)
# => Duration    9.94s
```

---

## Results

| Metric | Before | After |
|--------|--------|-------|
| Test files | ~149 pass | 158 pass |
| Tests passing | ~2199 | 2398 |
| Tests failing | ~189 | 0 |
| SQLite binding | missing | compiled ok |

---

## Recommendations

1. **Pin to Node LTS**: Node v25.x is current/bleeding-edge. Switch to v22 LTS to get prebuilt binaries and avoid recompile on every fresh install. `.nvmrc` or `.node-version` file with `22` is sufficient.
2. **postinstall script**: Add `"postinstall": "pnpm rebuild better-sqlite3"` to package.json as a safety net for non-LTS environments.
3. **CI matrix**: If CI uses Node v22 but dev uses v25, the binary issue may resurface on new clones. Standardize via `.nvmrc`.

---

## Unresolved Questions

- None. Issue fully resolved.
