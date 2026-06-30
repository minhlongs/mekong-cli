---
name: ck:adversarial-review
description: "Spawn N independent reviewer subagents to adversarially critique code changes with refutation-based voting. Triggers on 'review this', 'check my work', 'is this good?', or before merging any PR with 500+ lines changed. Iterates until findings degrade to nitpicks. Based on Anthropic's internal adversarial-review pattern."
user-invocable: true
when_to_use: "Invoke for fresh-eyes code review before merge, after large changes, or when the author suspects blind spots."
category: utilities
keywords: [review, adversarial, code-review, security, quality, multi-agent, voting, STRIDE, OWASP]
argument-hint: "[--reviewers N] [--iterations N] [--fix] [--scope <glob>]"
metadata:
  author: claudekit
  attribution: "Core pattern from Anthropic internal adversarial-review; STRIDE/OWASP integration from ck:security (Udit Goenka, MIT)"
  license: MIT
  version: "1.0.0"
  upstream: ClaudeKit adversarial-review (ported from Mekong CLI 2026-06)
---

# ck:adversarial-review — Multi-Reviewer Adversarial Code Review

Spawns **N independent subagents** with no context from the current session. Each reviewer evaluates the diff from a distinct perspective. Findings are aggregated via **refutation-based voting**: reviewers challenge each other's findings, and only findings that survive refutation are kept. The loop iterates until only nitpicks remain.

## When to Use

- Before merging any PR with 500+ lines changed
- After implementing a feature the author is uncertain about
- When the author says "review this" or "check my work"
- As a quality gate before major deployments
- When ck:code-review found issues and a second adversarial pass is needed

## When NOT to Use

- Purely cosmetic changes (CSS, copy edits)
- Generated code (lockfiles, build artifacts)
- Trivial changes under 50 lines — use `ck:code-review` instead

---

## Modes

| Mode | Invocation | Behavior |
|------|-----------|----------|
| Standard | `/ck:adversarial-review` | 3 reviewers, 1 iteration, report only |
| Deep | `/ck:adversarial-review --reviewers 5 --iterations 3` | 5 reviewers, up to 3 iterations |
| Fix loop | `/ck:adversarial-review --fix` | Review → fix → re-review until clean |
| Scoped | `/ck:adversarial-review --scope src/auth/**/*.ts` | Review only matching files |

---

## Step 1: Collect the Diff

```bash
# Determine review scope
SCOPE="${1:-main..HEAD}"
git diff ${SCOPE} > /tmp/adversarial-diff.txt
echo "Files changed: $(git diff --name-only ${SCOPE} | wc -l)"
echo "Lines changed: $(git diff --stat ${SCOPE} | tail -1)"
```

Filter out generated artifacts using `.gitignore` patterns. Never review lockfiles or build output.

## Step 2: Select Review Perspectives

Assign each reviewer a distinct perspective. The standard set:

| # | Perspective | Focus Areas |
|---|-------------|-------------|
| 1 | **Security** (STRIDE + OWASP) | Injection, auth bypass, secret exposure, IDOR, XSS, CSRF, SSRF |
| 2 | **Correctness** | Edge cases, off-by-one, null handling, race conditions, state machines |
| 3 | **Performance** | O(n^2) loops, memory leaks, blocking calls, N+1 queries, cache misses |
| 4 | **Architecture** | Coupling, abstraction level, separation of concerns, layer violations |
| 5 | **Testing** | Untested paths, flaky patterns, missing assertions, mock overuse |

For fewer reviewers, merge perspectives: Security+Performance, Correctness+Testing, Architecture.

## Step 3: Spawn Independent Reviewers

Each reviewer is a **fresh subagent** with NO access to the current session's conversation. Each receives ONLY:

1. The diff (`/tmp/adversarial-diff.txt`)
2. The repo's CLAUDE.md (for context on architecture and conventions)
3. Their assigned perspective and review criteria

### Spawning via ClaudeKit Tools

Use the `code-reviewer` agent or `Task` tool to spawn each reviewer:

```
Spawn reviewer-1 with perspective: Security (STRIDE + OWASP)
Spawn reviewer-2 with perspective: Correctness
Spawn reviewer-3 with perspective: Architecture
```

Each reviewer returns a structured findings list:

```json
{
  "perspective": "Security",
  "findings": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW|NITPICK",
      "category": "Injection|Auth|XSS|...",
      "file": "path/to/file.ts",
      "line": 42,
      "description": "What is wrong",
      "refutations": []
    }
  ]
}
```

### ClaudeKit Integration

- **ck:code-review**: Run first for baseline diff review; feed its findings into adversarial loop
- **ck:security**: Run STRIDE + OWASP audit in parallel with adversarial reviewers for security perspective
- **code-reviewer agent**: Use for each independent reviewer spawn
- **ck:scenario**: Use after review to generate edge-case tests for found gaps

## Step 4: Refutation-Based Voting

After all reviewers return findings, run the **refutation round**:

1. Each reviewer sees ALL findings from other reviewers
2. Reviewers may **refute** findings they believe are incorrect, duplicates, or nitpicks
3. A finding **survives** if it receives zero refutations, or if refutations are themselves refuted
4. Findings with surviving refutations are **downgraded** or **dismissed**

### Voting Rules

| Scenario | Outcome |
|----------|---------|
| Finding proposed by 1, refuted by 1 | Downgrade one level (CRITICAL→HIGH, etc.) |
| Finding proposed by 2+ reviewers independently | Auto-upgrade one level |
| Finding refuted with code evidence | Dismissed |
| Finding refuted as "already fixed in diff" | Dismissed |
| Refutation itself refuted | Original finding stands |

## Step 5: Severity Classification

Apply severity levels consistently:

| Severity | Description | Action |
|----------|-------------|--------|
| **CRITICAL** | Exploitable now, data breach or RCE risk | Block merge, fix immediately |
| **HIGH** | Exploitable with moderate effort, significant impact | Fix before merge |
| **MEDIUM** | Limited exploitability or impact | Fix in same sprint |
| **LOW** | Theoretical risk, defense-in-depth | Backlog |
| **NITPICK** | Style, naming, minor improvement | Optional |

### Security Findings Are Auto-CRITICAL

Per Mekong convention: any finding in the Security perspective that involves injection, auth bypass, or secret exposure is automatically CRITICAL. Never downgrade security findings to nitpick without explicit justification.

## Step 6: Iterate

```
ITERATION = 1
LOOP:
  1. Spawn N independent reviewers with the diff
  2. Collect findings
  3. Run refutation round
  4. Aggregate surviving findings
  5. IF surviving findings are all NITPICK → DONE
  6. IF ITERATION < MAX → Fix CRITICAL/HIGH, re-run with updated diff, ITERATION++
  7. ELSE → Report remaining findings, stop
```

Default: 3 reviewers, max 2 iterations. Override with `--reviewers N --iterations N`.

## Step 7: Output Report

```
## Adversarial Review Report

### Summary
- Reviewers: N
- Iterations: M
- Files scanned: X
- Findings: C critical, H high, M medium, L low, N nitpick

### Surviving Findings

| # | Severity | Perspective | File:Line | Description | Fix Recommendation |
|---|----------|-------------|-----------|-------------|-------------------|
| 1 | Critical | Security | api/auth.ts:45 | SQL string concatenation | Use parameterized queries |
| 2 | High | Correctness | utils/cache.ts:22 | No null check on user input | Add guard clause |

### Dismissed Findings
(Findings that were refuted and dismissed — kept for audit trail)

### Refutation Log
| Finding | Refuted By | Reason |
|---------|-----------|--------|
| Security: api/auth.ts:45 | Reviewer-3 | Already uses parameterized query in v2 |
```

## Fix Mode (--fix)

When `--fix` is provided:

1. After each iteration, apply fixes for all CRITICAL and HIGH findings
2. Re-collect the diff and re-run reviewers
3. Continue until no CRITICAL/HIGH findings remain or max iterations reached
4. Each fix commit follows: `fix(security|correctness|...): <short description>`

## Gotchas

- **Fresh eyes only**: Each reviewer subagent must NOT have access to the current session's conversation. Spawn via `code-reviewer` agent or Task tool with isolated context.
- **Filter generated code**: Never review package-lock.json, build artifacts, or `.gitignore`d files.
- **Security = auto-CRITICAL**: Never downgrade injection/auth-bypass/secret-exposure findings without explicit justification.
- **Review log**: Log all findings (surviving and dismissed) to `.claude/review-log.jsonl` for pattern analysis.
- **Layer violations**: In layered architectures (seed/tree/forest/land), flag imports that violate layer boundaries as MEDIUM findings.

## Integration with ClaudeKit Skills

| Skill | Relationship |
|-------|--------------|
| **ck:code-review** | Run first for baseline; feed findings into adversarial loop |
| **ck:security** | Parallel STRIDE + OWASP audit; provides Security perspective depth |
| **ck:scenario** | Generate edge-case tests for correctness gaps found |
| **ck:autoresearch** | Use for iterative fix loops on confirmed findings |
| **ck:predict** | Run before review for persona debate on risky changes |
| **code-reviewer agent** | Spawn as independent reviewer subagent |

## Example Invocations

```bash
# Standard review — 3 reviewers, 1 iteration
/ck:adversarial-review

# Deep review — 5 reviewers, up to 3 iterations
/ck:adversarial-review --reviewers 5 --iterations 3

# Review + fix loop
/ck:adversarial-review --fix

# Scoped review — auth layer only
/ck:adversarial-review --scope src/seed/auth/**/*.ts

# Full pipeline: baseline review → adversarial → fix
/ck:code-review --scope src/api/
/ck:adversarial-review --fix --iterations 3
```

---

## Lineage

Ported from Mekong CLI `adversarial-review` skill with enhancements:
- Multi-reviewer refutation-based voting (extends Anthropic's single-reviewer pattern)
- STRIDE + OWASP integration from `ck:security`
- ClaudeKit toolchain integration (code-reviewer agent, ck:code-review, ck:scenario)
- Layer architecture awareness (seed/tree/forest/land import rules)
- Fix mode with iterative re-review

Source: Mekong CLI `adversarial-review` skill (ported 2026-06)
Merged with: `/Users/macbook/.claude/skills/ck-security/SKILL.md`
