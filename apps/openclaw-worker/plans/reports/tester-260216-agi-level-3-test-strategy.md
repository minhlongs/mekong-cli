# AGI Level 3 Testing Strategy: Post-Mission Gate & Mission Journal

## Executive Summary
This document outlines the testing strategy for the AGI Level 3 components responsible for automated verification, deployment, and learning. The focus is on ensuring the "Bất khả bại" (Undefeatable) principle of Binh Pháp through rigorous validation of the build gate and persistent journaling.

## 1. Component Overview

### 1.1 `post-mission-gate.js` (Implemented)
- **Role**: CI/CD Gate. Runs builds/lints after missions and pushes changes only if GREEN.
- **Key Functions**: `runBuildGate`, `pushIfGreen`, `runFullGate`.
- **Binh Pháp Strategy**: 第四篇 軍形 (First make yourself undefeatable).

### 1.2 `mission-journal.js` (Planned/AGI Level 5)
- **Role**: Self-Learning Journal. Records mission data and analyzes patterns.
- **Target File**: `data/mission-history.json` / `wins.jsonl`.
- **Binh Pháp Strategy**: 第十三篇 用間 (Know enemy, know self).

---

## 2. Test Scenarios & Edge Cases

### 2.1 Build Verification Gate (`runBuildGate`)
| Scenario | Impact | Test Case |
|----------|--------|-----------|
| **Missing `package.json`** | Skip build | Verify it returns `{ pass: true }` (allow non-npm projects). |
| **Missing `scripts.build`** | Skip build | Verify it returns `{ pass: true }` if build script is absent. |
| **Build Timeout** | Block push | Mock a build that takes >120s; verify process is killed. |
| **OOM / Crash** | Block push | Simulate process exit code 137; verify RED gate. |
| **Partial Success** | Block push | `build` passes but `typecheck` fails; verify RED gate. |

### 2.2 Git Operations & Push Safety (`pushIfGreen`)
| Scenario | Impact | Test Case |
|----------|--------|-----------|
| **No Changes** | Skip commit | Verify it returns `pushed: false, reason: 'no-changes'`. |
| **Forbidden File Violation** | Rollback | Modify `config.js`; verify `git checkout` is triggered before commit. |
| **Network Error** | Log failure | Mock `git push` failure (403/timeout); verify results saved locally. |
| **Diverged Branch** | Log failure | Simulate "Updates were rejected"; verify no crash, graceful failure. |
| **Large Diff** | Performance | Simulate 100+ file changes; verify memory/timeout handling. |

### 2.3 Concurrent Journal Writes (`mission-journal.js`)
| Scenario | Impact | Test Case |
|----------|--------|-----------|
| **Simultaneous Missions** | Data corruption | 5 concurrent processes writing to `mission-history.json`; verify no JSON syntax errors. |
| **Disk Full** | Data loss | Simulate `ENOSPC`; verify error handling (don't crash the worker). |
| **Lock Contentions** | Hang | Verify use of flock/atomic rename (`temp` -> `final`) to prevent partial writes. |
| **Malformed JSON** | Recovery | Corruption in journal file; verify agent can auto-recover or rotate log. |

---

## 3. Proposed Testing Tools

- **Vitest**: Core unit testing for logic mocking `execSync` and `fs`.
- **Test-Double / Mocking**: Replace `child_process` to avoid actual git pushes during testing.
- **Docker/Tmpfs**: Run integration tests in isolated directories to verify real `git add/commit` without polluting the main repo.

## 4. Binh Pháp Quality Gates (Enforcement)

- **始計 (Initial Calculations)**: All tests must run in < 30s.
- **作戰 (Waging War)**: 100% Type safety for new AGI components.
- **軍形 (Security)**: `FORBIDDEN_FILES` list must be strictly enforced.

## 5. Next Steps
1. [ ] Implement unit tests for `post-mission-gate.js` using Vitest.
2. [ ] Prototype `mission-journal.js` with atomic write capability.
3. [ ] Integrate concurrency stress tests into CI pipeline.

---
**Reported by**: Claude QA Engineer (Haiku 4.5)
**Date**: 2026-02-16
**Status**: 🟢 PLANNING READY
