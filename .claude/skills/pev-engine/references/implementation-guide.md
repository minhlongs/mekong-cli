# PEV Engine — Implementation Guide

## ClaudeKit Integration Pattern

The PEV engine runs **inside Claude Code's context**. Claude acts as the executor — using its Bash tool for shell commands, its LLM access for LLM steps, and its WebFetch/WebSearch for browse steps.

### Execution Flow

```
User Goal
    │
    ▼
[PLAN] — Claude decomposes goal into steps with deps + verify criteria
    │
    ▼
[EXECUTE] — Claude runs each step via appropriate tool:
    │   shell → Bash tool
    │   llm   → Claude's own reasoning
    │   api   → WebFetch/WebSearch or Bash (curl)
    │   tool  → Skill invocation
    │   browse → WebFetch
    │
    ▼
[VERIFY] — Verifier checks results against criteria
    │
    ▼
[HEAL] — On failure: retry with backoff, then rollback
```

### Step Execution by Mode

| Mode | ClaudeKit Tool | Notes |
|------|---------------|-------|
| `shell` | Bash | Sanitize before exec; capture stdout/stderr |
| `llm` | Claude reasoning | No API call needed — use context |
| `api` | WebFetch / Bash (curl) | Handle 4xx (no retry) vs 5xx (retry) |
| `tool` | Skill invocation | Route to appropriate skill |
| `browse` | WebFetch | Fetch URL, extract content |

### DAG Scheduling Algorithm

```
1. Build dependency graph from step.deps
2. Initialize: completed = {}, failed = {}, cancelled = {}
3. While not all steps terminal:
   a. Find ready steps (all deps in completed)
   b. Execute ready steps in parallel (up to concurrency limit)
   c. For each completed step:
      - If passed: add to completed
      - If failed: add to failed, cancel all transitive dependents
4. If any step failed: trigger rollback
```

### Self-Healing Protocol

When a shell step fails:
1. Check retry policy — if attempts remain, wait (backoff) and retry
2. If retries exhausted AND LLM available:
   a. Generate corrected command via LLM prompt
   b. Execute corrected command
   c. If succeeds: mark `self_healed = true`
   d. If fails: proceed to rollback
3. If no LLM available: proceed directly to rollback

### Rollback Protocol

```
For each completed step (in reverse order):
  If step has rollback commands:
    Sanitize each command
    Execute via Bash tool
    Record success/failure
```

### Quality Gates (Binh Phap)

After all steps complete, run quality gates on the final output:
- **Tech Debt**: 0 TODO/FIXME
- **Clean Logs**: 0 console.log / print()
- **Type Safety**: 0 `:any` types
- **Security**: 0 vulnerabilities

## Recipe YAML Format

```yaml
recipe:
  name: "Deploy to Production"
  description: "Build, test, and deploy"
  concurrency: 4

steps:
  - id: step-001
    title: "Install dependencies"
    mode: shell
    command: "npm install"
    deps: []
    verify:
      exit_code: 0
    retry:
      max_attempts: 3
      backoff: exponential

  - id: step-002
    title: "Run tests"
    mode: shell
    command: "npm test"
    deps: [step-001]
    verify:
      exit_code: 0
      output_contains: ["pass"]

  - id: step-003
    title: "Deploy"
    mode: shell
    command: "npm run deploy"
    deps: [step-002]
    verify:
      exit_code: 0
    rollback:
      - "npm run rollback"
```

## Error Handling Matrix

| Scenario | Action |
|----------|--------|
| Shell exit != expected | Retry per policy, then rollback |
| LLM unavailable | Skip step, mark warning, continue |
| API 5xx | Retry with backoff |
| API 4xx | No retry, fail immediately |
| File not found (verify) | Fail step, no retry |
| Output mismatch | Fail step, retry if policy allows |
| Circular dependency | Fail recipe before execution |
| Max depth exceeded (50) | Fail recipe |

## Concurrency Limits

- Default: 4 parallel workers
- Override via `concurrency` in recipe header
- Steps without deps always eligible for parallel execution
- Failed steps cancel all transitive dependents immediately
