---
description: "SDLC phase 1 — Spec: feature idea → requirements. Dispatches to `mekong spec new <feature>`. Scaffolds .mekong/SPEC_OUTPUT.md, prints planner agent prompt."
argument-hint: [feature-slug, e.g. auth-mfa]
allowed-tools: Read, Write, Bash, Task
---

# /sdlc:spec — Spec Phase

**Phase 1 of 4** in the agentic SDLC. Reads `CLAUDE.spec.md` contract → scaffolds `SPEC_OUTPUT.md` → prints planner agent prompt.

## Dispatch

```bash
mekong spec new $ARGUMENTS
```

## Output

`.mekong/SPEC_OUTPUT.md` populated with sections: Problem Statement, Objectives, Requirements (functional + non-functional), Metrics, Risks, Out of Scope.

## Next

```bash
mekong design new $ARGUMENTS   # or /sdlc:design $ARGUMENTS
```

## Contract

`.mekong/phases/CLAUDE.spec.md` — planner agent instructions (requirements gathering, user-story format, FR/NFR split, success metrics).

## Related

- `/sdlc` — full flow overview
- `/sdlc:design`, `/sdlc:code`, `/sdlc:deploy` — subsequent phases
