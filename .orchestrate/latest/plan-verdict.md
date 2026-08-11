AMEND — ROUND: 3

SCOPE: Re-verification of the 3 remaining ROUND-2 conditions only (C2, C3, C4).
New findings go to "Out-of-scope observations" and do NOT block.

## Condition status (ROUND-2 remaining list)

| # | Condition | Status |
|---|-----------|--------|
| 1 | Identify/create canonical active plan dir; confirm exactly one active plan + list dirs to archive | SATISFIED (unchanged) |
| 2 | Specify how `bin/mekong` is produced so Gate 6 is verifiable | **NOT SATISFIED (HIGH)** |
| 3 | Define clean-tree target branch + commit/stash/discard strategy | **PARTIAL (MED)** |
| 4 | Add concrete smoke report paths / test commands for Step 5 | **NOT SATISFIED (HIGH)** |

## Evidence

Commands run from `/Users/macbook/mekong-cli`:

```
ls -la bin/mekong 2>/dev/null && bin/mekong --version 2>/dev/null || echo "bin/mekong not found or not executable"
# → bin/mekong not found or not executable

git branch --show-current && git status --short | wc -l
# → kongming-kill-list-5.0.0
# → 615

ls plans/ | grep -c "260811-"  && ls plans/ | grep -c "260809-mekong-bootstrap-parallel"
# → 4
# → 1

ls -la harness/bin/
# → mk.ts, mk.js, ak.ts, ak.js (no mekong binary here either)

npx tsx harness/bin/mk.ts
# → returns "mekong 1.0.0 (harness-core)" — not 6.0.0

python3 -m pytest tests/ -v --co -q
# → collected 7982 items / 2 skipped (Python pytest; no @mekong/zalo scoped packages)
```

## Findings

**C2 HIGH:** `bin/mekong` does not exist in the workspace. The plan asserts `bin/mekong --version` returns `6.0.0` (plan.md line 18) but the artifact must first be built by bootstrap—there is no fallback if bootstrap fails to produce it. The plan does not harden Gate 6 for the missing-artifact case (e.g., "if `bin/mekong` absent after bootstrap, halt ship; if present, assert version matches package.json").

**C3 MED:** Branch cleanup strategy is still incomplete. Plan says "Target branch: main" (plan.md line 16) but HEAD is `kongming-kill-list-5.0.0` with 615 dirty files. No explicit branch transition step (checkout → stash → merge → run bootstrap → re-apply stash) is written into the execution sequence.

**C4 HIGH:** `pnpm turbo run test --filter=@mekong/zalo --filter=@mekong/tax --filter=@mekong/sophia` (plan.md line 17) references scoped workspace packages that do not exist in this repo. The Python test target `python3 -m pytest tests/ -v` is the only verified path (7982 items collected). Gate 5 command must be replaced with real invocable commands, and Step 5 owner/acceptance criteria updated accordingly.

## Conditions to flip AMEND → PASS / CONDITIONAL PASS

- **C2:** Hard-code a fallback in Step 6 / Gate 6: if `bin/mekong` is absent after bootstrap, ship is BLOCKED. If present, assert version equals `package.json` `6.0.0`. Do not assume bootstrap always produces the artifact.
- **C3:** Append a branch transition step before Step 4: "Check out `main` (or confirm current branch is acceptable ship target), stash dirty tree, run bootstrap, then re-apply or drop stash." Gate 4 must name the exact branch it asserts clean.
- **C4:** Replace the turbo filter command with `python3 -m pytest tests/ -v` (or with actual test targets for any JS sub-packages that exist). Update the Step 5 Acceptance Criteria to match the executable command and its expected output (pass/fail count).

## Out-of-scope observations (NON-BLOCKING)

- `mekong/` is doc-only; plan.md line 54 notes this but still references a binary that could live there—clarify that `mekong/` carries no build artifact.
- `harness/bin/mk.ts` returns version `1.0.0 (harness-core)` — far below the `6.0.0` target. This may indicate the bootstrap path needs to update the version string in the harness source, not just copy a binary. Investigate version source before hardening C2.
- `plans/` still holds ~34 other legacy dirs; Gate 1's "exactly one active plan" wording was rephrased in ROUND 2 but not yet reflected in the plan.md Gate 1 cell.
- Python workspace support is disabled in turbo config (per ROUND 2 observation); if a unified JS+Python smoke command is desired, enable `futureFlags.experimentalPythonWorkspaces` first or run Python tests standalone.

## Scope check

No files modified. Read-only inspection only. Verdict written to `.orchestrate/latest/plan-verdict.md`.
