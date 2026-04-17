---
description: "SDLC phase 3 — Code: architecture → task backlog. Reads DESIGN_OUTPUT.md, scaffolds TASKS.todo, prints fullstack-developer agent prompt."
argument-hint: [feature-slug, e.g. auth-mfa]
allowed-tools: Read, Write, Bash, Task
---

# /sdlc:code — Code Phase

**Phase 3 of 4** in the agentic SDLC. Reads `DESIGN_OUTPUT.md` + `CLAUDE.code.md` contract → scaffolds `TASKS.todo` → prints fullstack-developer agent prompt.

## Dispatch

```bash
mekong code new $ARGUMENTS
```

## Output

`.mekong/TASKS.todo` populated with actionable implementation tasks derived from the design. Each task lists: file(s) to touch, acceptance criteria, test plan, estimated effort.

## Integration

Developer wraps agent invocations with `@observe_agent("name")` decorator (per `docs/code-standards.md` §8). Emits events via `emit_mission_event()` for offline eval tracking.

Metrics tracked during code phase:
- `agent.invocation_ms` — execution latency
- `agent.token_cost_usd` — per-call LLM cost
- `agent.retry_total` — retry counter
- `agent.model_drift_score` — (when baseline established)
- `mlx.gpu_utilization_percent` — (M1 Max GPU when using MLX)

## Next

```bash
mekong deploy new $ARGUMENTS   # or /sdlc:deploy $ARGUMENTS
```

## Contract

`.mekong/phases/CLAUDE.code.md` — fullstack-developer agent instructions (YAGNI/KISS, task decomposition, file ownership, test-first).

## Related

- `/sdlc` — full flow overview
- `/sdlc:design` ← previous phase
- `/sdlc:deploy` → next phase
