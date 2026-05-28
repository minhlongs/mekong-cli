---
name: pev-verify
description: Verify that PEV pipeline output is correct. Trigger after any mekong cook, mekong run, or agent execution. Contains verification scripts and the verification protocol that catches the documented pattern of Opus falsely claiming task completion (verified 7+ times in production).
---

# PEV Verification

## Overview
Opus has been verified AT LEAST 7 TIMES falsely claiming task completion. Never trust "done" reports. This skill enforces programmatic verification after every PEV run.

## Verification Protocol

After ANY agent claim of completion, run these checks:

### File creation claims
```bash
# Agent says "created src/foo.ts"
cat src/foo.ts | head -20  # Verify file exists AND has content
wc -l src/foo.ts           # Verify non-trivial length
```

### Test claims
```bash
# Agent says "all tests pass"
npm test 2>&1 | tail -20   # Actually run tests, check output
echo "Exit code: $?"       # Verify exit code 0
```

### Git claims
```bash
# Agent says "committed and pushed"
git log --oneline -3       # Verify commit exists
git diff --stat HEAD~1     # Verify files actually changed
git remote -v              # Verify correct remote
```

### Deploy claims
```bash
# Agent says "deployed to Cloudflare"
curl -sf https://your-worker.workers.dev/health | jq .
```

## Scripts
- `scripts/verify-files.sh <file1> <file2>` — Check files exist and have content
- `scripts/verify-tests.sh` — Run test suite and assert exit code 0
- `scripts/verify-git.sh` — Check last commit matches expected description

## Gotchas
- Opus claims "fixed the bug" without actually running the failing test. ALWAYS re-run.
- Opus claims "pushed to remote" but only committed locally. Check `git log --remotes` vs `git log`.
- Opus claims "19 files changed" but only touched 3. Check `git diff --stat`.
- The number one failure mode: agent modifies the right file but introduces a syntax error. Always verify with the language's native parser/compiler.
