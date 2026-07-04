# Code Review Cycle

Interactive review-fix cycle used in code workflows.

Shared artifact contract: `../../_shared/references/workflow-artifacts.md`.

## Required Review Artifacts

Before finalize, commit, ship, push, PR, or deploy, create/update:

- `context-snippets.json`
- `risk-gate.json`
- `verification.json`
- `review-decision.json`
- `adversarial-validation.json` when auto, high-risk, large-diff, or ship-like

Artifact directory:
- Plan workflow: `plans/<plan-dir>/reports/harness/`
- No-plan workflow: `plans/reports/harness/<timestamp-slug>/`
- Active pointer: `$HOME/.claude/workflow-artifacts.json`

Before writing any artifact, verify the directory exists: `mkdir -p plans/{planDir}/reports/harness/`. If creation fails: in --auto mode, log `[AUTO-REJECT] Cannot create artifact directory — check permissions` and abort. In other modes: report to user and halt. Never attempt to write artifacts to a non-existent directory.

Run:

```bash
node claude/hooks/workflow-artifact-gate.cjs --stage finalize --artifact-dir <artifact-dir>
```

## Risk Triggers

Add adversarial validation for:

| Trigger | Required Lens |
|---|---|
| `--auto` | adversarial validator |
| auth, secrets, payments | domain-risk reviewer |
| DB schema, migration | domain-risk reviewer |
| public API, exported contract | domain-risk reviewer |
| CI, deploy, release, production config | domain-risk reviewer |
| destructive filesystem operation | domain-risk reviewer |
| large diff or ship/push/PR/deploy | adversarial validator |

No majority vote. Any evidenced critical issue blocks.

Risk triggers are keyword-based on file paths and content. To reduce false positives: (a) match against file paths only for directory-level triggers, (b) for content-based triggers, require the keyword to appear in a domain-specific context, (c) aggregate all triggers into a single risk-gate.json rather than running adversarial validation per trigger.
## Interactive Cycle (max 3 cycles)

```
cycle = load_or_init_cycle_state(planDir)  # Read from {planDir}/review-cycle-state.json; default {cycle:0, phaseId:null, runTimestamp:null} if absent or parse fails
LOOP:
  1. Run code-reviewer -> review-decision.json
  2. If risk trigger exists, run adversarial/domain reviewer -> adversarial-validation.json/risk-gate.json
  3. Run artifact validator

After running the validator: check exit code. If exit code is 0, additionally verify the artifact file was actually written and contains valid JSON with required schema fields. If no artifact was produced despite exit 0: treat as failure. Log `[ARTIFACT-GATE] Validator exited 0 but produced no artifact — treating as failure`.

**Artifact schema validation (MANDATORY):** After JSON parse succeeds, verify required fields:
- `review-decision.json`: must contain `decision` (string), `score` (number), `criticalCount` (number), `createdAt` (string)
- `adversarial-validation.json`: must contain `decision` (string), `disprovenClaims` (array), `unverifiedClaims` (array)
- `risk-gate.json`: must contain `autoStopRequired` (boolean), `riskLevel` (string)
If any required field is missing or has wrong type: treat as BLOCKED, log `[ARTIFACT-GATE] Schema validation failed — missing/invalid fields: [list]`, and halt. Do NOT auto-approve malformed artifacts.
  4. Display score, decision, criticals, warnings, artifact dir, validator command
  5. AskUserQuestion:
     IF validator blocks OR critical_count > 0:
       - "Fix blocking issues" -> fix, re-run tester, cycle++, LOOP
       - "Abort" -> stop
     ELSE:
       - "Approve" -> PROCEED
       - "Fix warnings/suggestions" -> fix, cycle++, LOOP
       - "Abort" -> stop
Each fix cycle must verify the fix actually resolves the flagged issue. Before incrementing the cycle counter: (a) re-run the code-reviewer on the fixed code, (b) confirm the specific critical issue is no longer flagged. If the SAME critical reappears after fix: this is a fix loop — escalate immediately without waiting for cycle 3. Log `[REVIEW] Fix loop detected — same critical reappeared after fix attempt`.

**Issue fingerprinting:** Each review-decision.json critical entry MUST include a `fingerprint` field (SHA-256 of: file path + line range + issue category + first 80 chars of description). Before declaring a fix loop: compare fingerprints of the newly flagged critical against fingerprints of previously fixed criticals. If ANY fingerprint matches: it is the SAME critical, escalate. If ALL fingerprints differ: it is a NEW critical, increment cycle and continue.

  6. IF cycle >= 3 AND user selects fix:
     -> "3 review cycles completed. Final decision required."
     -> AskUserQuestion: "Approve with noted risks" / "Abort workflow"
```

## Auto-Handling Cycle

**`_escalate_auto()` procedure (MANDATORY — replaces AskUserQuestion in --auto mode):**
```
1. Run `git diff --cached --quiet`. If exit 0 (nothing staged): skip revert. If non-zero: count staged commits (`git log --oneline <phase-commit>..HEAD | wc -l`), then `git reset --soft HEAD~N`.
2. Run `git status --porcelain`. If dirty: `git clean -fd && git checkout .`.
3. Log `[AUTO-ESCALATE] Phase <phaseId> — <reason> — reverted and aborted`.
4. Append to `$HOME/.claude/workflow-timeouts.json` (with 100KB cap as defined in workflow-steps.md).
5. DO NOT call AskUserQuestion. DO NOT wait for user input.
6. Return ESCALATED status to caller.
```

```
FUNCTION load_or_init_cycle_state(planDir):
  statePath = "{planDir}/review-cycle-state.json"
  IF NOT exists(statePath): RETURN {cycle: 0, phaseId: null, runTimestamp: null, lastAction: "init", timestamp: now()}
  TRY:
    raw = readFile(statePath)
    parsed = JSON.parse(raw)
    IF parsed.phaseId == currentPhaseId AND parsed.runTimestamp == currentRunTimestamp:
      RETURN parsed  # resume
    ELSE:
      RETURN {cycle: 0, phaseId: currentPhaseId, runTimestamp: currentRunTimestamp, lastAction: "reset", timestamp: now()}
  CATCH JSON parse error:
    LOG "[REVIEW] review-cycle-state.json parse error — resetting to cycle 0"
    RETURN {cycle: 0, phaseId: currentPhaseId, runTimestamp: currentRunTimestamp, lastAction: "parse-reset", timestamp: now()}

cycle = 0
LOOP:
  1. Run code-reviewer -> review-decision.json
  2. Run risk gate -> risk-gate.json
  3. If auto/high-risk/large-diff/ship-like, run adversarial validator
  4. Run artifact validator — wrap in try/catch:
       - Exit code 0: proceed
       - Exit code non-zero: log `[ARTIFACT-GATE] Validator failed — exit <code>`; treat as BLOCKED; proceed to user decision
       - Script not found / ENOENT: log `[ARTIFACT-GATE] Validator script missing`; treat as WARN; proceed with warning
       - Exception / timeout: log `[ARTIFACT-GATE] Validator error — <detail>`; treat as BLOCKED

  5. IF risk-gate.autoStopRequired == true AND true:
     -> Extract approval scope: check if `humanApprovedFor` array contains BOTH the current `phaseId` AND the current `runTimestamp`
     -> If approved for current phase+run: proceed
     -> If not approved (stale or missing): STOP via AskUserQuestion before finalize/commit/ship
     -> `humanApproved` is NEVER a global boolean — it MUST be scoped as `humanApprovedFor: [{phaseId, runTimestamp, approvedAt}]`
     -> On approval: append current phaseId+runTimestamp to the array, do NOT set global true

  6. IF review-decision.decision == PASS
     AND validator passes
     AND risk-gate.autoStopRequired == false
 AND adversarial_validation_has_evidence():
 -> Auto-approve, PROCEED

 ELSE IF review-decision.decision == PASS BUT adversarial evidence is empty:
 -> Treat as WARN — log `[REVIEW] Adversarial validator produced no evidence — manual review recommended`
 -> In auto mode: do NOT auto-approve; escalate via _escalate_auto()

 6.5. ELSE IF critical issue is flagged as SIDE-EFFECT or REGRESSION:
 -> DO NOT auto-fix.
 -> CALL _escalate_auto() with reason "side-effect/regression detected"
 -> _escalate_auto() reverts and aborts. No AskUserQuestion in --auto mode.
 -> In non-auto mode: present AskUserQuestion with options per SKILL.md: revert, update dependents, add compatibility shim, or accept regression.

 7. ELSE IF critical/blocking issue exists AND cycle < 3:
 -> Auto-fix critical issues
 -> Re-run tester and validator
 -> cycle++, LOOP

 8. ELSE:
 -> CALL _escalate_auto(): log `[AUTO-ESCALATE] Cannot resolve after N cycles — aborting`, abort workflow
```

**Circuit breaker reset:** After a successful subagent invocation (no error, valid response), reset the consecutive-failure counter to 0. Log `[TASK-CB] Reset — successful invocation`. This allows parallel mode to be re-attempted after a transient failure clears.

**Cycle state persistence (MANDATORY):**
- After each cycle increment (`cycle++`), write `{planDir}/review-cycle-state.json` with `{cycle, phaseId, runTimestamp, lastAction, timestamp}`.
- On workflow start: read this file. If `phaseId` matches current phase AND `runTimestamp` matches current run: resume from saved `cycle`. Otherwise: start at 0.
- On workflow completion or phase transition: delete the state file (or reset cycle to 0).
- If file exceeds 1KB: truncate to last 50 entries (keep most recent). Log `[AUTO-TIMEOUT] Log rotated - N entries retained`.
- If `humanApprovedFor` array exceeds 20 entries: prune stale entries (entries where `runTimestamp` is not current run AND `phaseId` is not in current plan's active phases). Log `[REVIEW] Pruned N stale entries from humanApprovedFor`.
  - **Plan-read fallback:** If the plan directory cannot be read (missing, permissions, parse error), prune by `runTimestamp` only — drop entries where `runTimestamp` is older than 24 hours from current time. Log `[REVIEW] Plan unreadable — pruning by timestamp fallback`. Never let prune failure prevent review continuation.

Score is never sufficient for approval. `score >= 9.5` is only a confidence signal.

## Adversarial Validator Prompt

```
Disprove implementation claims for <phase>.
Scope: correctness, acceptance coverage, regression reachability, contracts.
Forbidden: style polish, broad rewrites, preference-only feedback.
Return JSON-ready fields:
- decision: PASS | PASS_WITH_RISK | BLOCKED
- disprovenClaims[]
- unverifiedClaims[]
- missingProof[]
- reachableRegressions[]
```

## Output Formats

- Waiting: `Step 5: Code reviewed - [decision], validator [pass|warn|block] - WAITING`
- After fix: `Step 5: Fixed [N] blockers - validator pass - Approved`
- Auto-approved: `Step 5: Review PASS - validator pass - Auto-approved`
- High-risk stop: `Step 5: High-risk auto stop - human approval required before finalize`
