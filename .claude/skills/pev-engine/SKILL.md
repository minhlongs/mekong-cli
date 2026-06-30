---
name: pev-engine
description: |
  Plan-Execute-Verify engine for Claude Code. Orchestrates multi-step workflows with
  DAG scheduling, retry with backoff, verification gates, and self-healing rollback.
  Use when executing complex tasks that need structured decomposition, parallel execution,
  and quality validation before completion.
version: 1.0.0
when_to_use: "Invoke for multi-step tasks with dependencies, DAG-based parallel execution, verification gates, or workflows needing retry/rollback on failure."
user-invocable: true
category: workflow
keywords:
  - pev
  - dag
  - parallel
  - verification
  - retry
  - rollback
  - self-healing
metadata:
  version: 1.0.0
  upstream: Mekong CLI PEV engine (ported 2026-06)
license: MIT
argument-hint: "<goal or recipe.yaml>"
---

# PEV Engine — Plan-Execute-Verify for Claude Code

## Overview

The PEV engine decomposes goals into executable steps, runs them with DAG-aware
parallelism, and validates every step against verification criteria. Failed steps
trigger automatic retry with backoff; persistent failures roll back to a clean state.

```
Goal → [PLAN] → Recipe (DAG of steps)
           ↓
      [EXECUTE] → Parallel DAG traversal
           ↓
      [VERIFY] → Gate checks per step
           ↓
      [HEAL]   → Retry / rollback on failure
```

## When to Use

- Multi-step tasks with dependencies between steps
- Tasks needing verification gates (build, test, deploy)
- Workflows where parallel execution saves time
- Operations requiring rollback on failure

## Core Concepts

### Recipe
A recipe is an ordered list of steps, each with:
- `id` — unique identifier
- `title` — human-readable name
- `mode` — execution mode: `shell` | `llm` | `api` | `tool` | `browse`
- `command` — what to run (shell command, LLM prompt, API call, tool name, URL)
- `deps` — step IDs this step depends on (for DAG scheduling)
- `verify` — verification criteria for this step
- `retry` — retry policy override (optional)

### Execution Modes

| Mode | Command Field | Description |
|------|--------------|-------------|
| `shell` | bash command | Run a shell command, capture stdout/stderr |
| `llm` | prompt text | Send to LLM via available provider |
| `api` | URL or JSON object | HTTP request (GET/POST with optional body) |
| `tool` | tool name + args | Invoke a registered tool |
| `browse` | URL | Fetch and analyze a web page |

### Verification Criteria

Each step can define:
- `exit_code: 0` — command must exit with this code
- `file_exists: ["path"]` — file must exist after step
- `file_not_exists: ["path"]` — file must NOT exist
- `output_contains: ["text"]` — stdout must contain this text (supports regex)
- `output_not_contains: ["text"]` — stdout must NOT contain this text

### Retry Policy

Default retry policy (Temporal-inspired):
- `max_attempts: 3` — stop after 3 total attempts
- `initial_interval: 1000ms` — first retry delay
- `backoff: exponential` — delay doubles each attempt
- `max_interval: 60000ms` — cap on delay
- `jitter: full` — randomize delay to prevent thundering herd
- `non_retryable: [2]` — exit code 2 means don't retry (bad input)

## Execution Instructions

### Step 1: Plan

Given a user goal, decompose into atomic steps:

```
1. Identify independent workstreams (can run in parallel)
2. Identify sequential dependencies (must run after)
3. Assign execution mode to each step
4. Define verification criteria for each step
5. Set retry policy per step (or use default)
```

Output format for each step:
```yaml
- id: step-001
  title: "Short description"
  mode: shell
  command: "npm run build"
  deps: []
  verify:
    exit_code: 0
  retry:
    max_attempts: 3
    backoff: exponential
```

### Step 2: Execute (DAG Scheduling)

Traverse the DAG:
1. Find all steps with satisfied dependencies (ready queue)
2. Execute ready steps in parallel (up to concurrency limit, default 4)
3. Mark completed steps, cascade failures to dependents
4. Repeat until all steps complete or a terminal failure occurs

```
while ready_steps exist:
    ready = [steps where all deps are completed]
    execute ready in parallel
    if any step failed:
        if retryable: schedule retry with backoff
        else: mark failed, cancel dependents, trigger rollback
```

### Step 3: Verify

For each completed step, run all verification checks:
- Run checks in order: exit_code → file_exists → file_not_exists → output_contains → output_not_contains
- Aggregate results into a VerificationReport
- If any check fails AND strict_mode is on → step is FAILED

### Step 4: Heal (Self-Recovery)

On step failure:
1. Check retry policy — if attempts remain, wait (backoff) and retry
2. If retries exhausted:
   a. Run rollback actions for the failed step (if defined)
   b. Run rollback actions for all completed steps that depend on the failed step
   c. Report failure with full context

## Rollback Actions

Each step can define `rollback`:
```yaml
- id: step-001
  rollback:
    - "rm -f ./dist/"
    - "git checkout -- src/"
```

Rollback runs in reverse completion order when a downstream step fails.

## Concurrency Control

- Default: 4 parallel workers
- Steps without `deps` run concurrently
- Steps with unsatisfied `deps` wait
- Failed steps cancel all transitive dependents
- Use `concurrency: N` in recipe header to override

## Error Handling

| Scenario | Action |
|----------|--------|
| Shell exit code != expected | Retry per policy, then rollback |
| LLM unavailable | Skip step, mark warning, continue |
| API timeout (5xx) | Retry with backoff |
| API client error (4xx) | No retry, fail immediately |
| File not found in verify | Fail step, no retry |
| Output mismatch | Fail step, retry if policy allows |

## Output Format

After execution, produce a structured report:

```json
{
  "status": "completed" | "failed" | "partial",
  "total_steps": N,
  "passed": N,
  "failed": N,
  "skipped": N,
  "duration_ms": N,
  "steps": [
    {
      "id": "step-001",
      "title": "...",
      "status": "passed" | "failed" | "skipped",
      "attempts": N,
      "duration_ms": N,
      "verification": {
        "passed": N,
        "failed": N,
        "checks": [...]
      }
    }
  ],
  "errors": ["..."],
  "rollback_actions_run": N
}
```

## Integration with Claude Code

When invoked as a skill:

1. **Parse the recipe** from the user's request or a provided YAML/JSON recipe file
2. **Execute the PEV loop** — plan, execute, verify, heal
3. **Report results** — structured JSON summary to the user
4. **Stop on failure** — do not continue past a failed step unless `continue_on_error: true`

## TypeScript Reference Implementation

When implementing this skill in TypeScript, use these interfaces:

```typescript
interface Step {
  id: string;
  title: string;
  mode: 'shell' | 'llm' | 'api' | 'tool' | 'browse';
  command: string;
  deps: string[];
  verify?: VerificationCriteria;
  retry?: RetryPolicy;
  rollback?: string[];
  timeout_ms?: number;
}

interface VerificationCriteria {
  exit_code?: number;
  file_exists?: string[];
  file_not_exists?: string[];
  output_contains?: string[];
  output_not_contains?: string[];
}

interface RetryPolicy {
  max_attempts?: number;
  initial_interval_ms?: number;
  backoff?: 'fixed' | 'exponential' | 'full_jitter';
  max_interval_ms?: number;
  non_retryable_exit_codes?: number[];
}

interface StepResult {
  id: string;
  status: 'passed' | 'failed' | 'skipped' | 'retrying';
  attempts: number;
  duration_ms: number;
  stdout: string;
  stderr: string;
  exit_code: number;
  verification: VerificationReport;
  error?: string;
}

interface VerificationReport {
  passed: boolean;
  checks: VerificationCheck[];
}

interface VerificationCheck {
  name: string;
  status: 'passed' | 'failed' | 'warning';
  message: string;
  expected?: string | number | boolean;
  actual?: string | number | boolean;
}
```

## Constraints

- Max 4 parallel workers (configurable via `concurrency`)
- Step output truncated to 10KB to prevent memory bloat
- Rollback only runs for steps that completed successfully
- LLM steps are skipped (not failed) when no LLM is available
- Shell commands are sanitized: no `rm -rf /`, no `sudo`, no `eval`
- Max recipe depth: 50 steps
