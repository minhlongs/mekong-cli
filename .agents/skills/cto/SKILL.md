---
name: cto
description: >-
  CTO command suite — architecture decisions, team management, observability, deploy, incident response, roadmap, budget, code review.
---

# /cto — CTO Command Suite & Engineering Leadership

Provides senior technical leadership intelligence, automated architecture reviews, and engineering health metrics:

## Available Sub-Commands

### `mekong cto` (Executive Overview)
- View composite engineering health score (0–100) and grade (A+ to D).
- Inspect working tree state, test coverage, and top execution priorities.

### `mekong cto architect <title>` (Architecture Decision Records)
- Generate formal Architecture Decision Records (ADRs) with context, decision, consequences, and alternatives.
- Use `--export` to write to `reports/cto/architect/ADR-XXX.md`.

### `mekong cto review [path]` (Code Quality & Security Review)
- Automated static analysis scanning for dynamic code execution (`eval`/`exec`), hardcoded credentials/tokens, unsafe subprocess (`shell=True`), bare `except: pass`, and unresolved debt.
- Severity classification: CRITICAL, HIGH, MEDIUM, LOW.

### `mekong cto scorecard` (Engineering Health Scorecard)
- Compute quantitative breakdown across automated tests, git velocity, security posture, and modularity.
- Use `--export <path>` to save machine-readable telemetry.

### `mekong cto health` (Stack Diagnostics)
- Verify Python runtime, virtualenv status, git repository cleanliness, pytest runner, and ruff linter availability.

### `mekong cto roadmap` (Technical Roadmap)
- Synthesize 3-horizon technical roadmap: Horizon 1 (NOW: blockers/debt), Horizon 2 (NEXT: scaling/architecture), Horizon 3 (LATER: platform/swarm).

---

## CLI Invocation

```bash
# Executive engineering overview
mekong cto

# Document architecture decision record
mekong cto architect "Event Streaming Gateway" --export

# Automated code review
mekong cto review src/core/

# Engineering scorecard in JSON for CI/CD
mekong cto scorecard --json

# Stack health check
mekong cto health

# 3-horizon roadmap
mekong cto roadmap
```

## Native MCP Tools

- `mekong_cto_scorecard()`: Returns composite engineering health score, grade, and metric breakdown.
- `mekong_cto_review(target_path: str = "")`: Scans target path or repository for security vulnerabilities and code smells.
- `mekong_cto_architect(title: str, context: str = "", decision: str = "")`: Generates a structured ADR with alternatives and consequences.
