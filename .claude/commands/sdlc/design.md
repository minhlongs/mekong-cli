---
description: "SDLC phase 2 — Design: requirements → architecture. Reads SPEC_OUTPUT.md, scaffolds DESIGN_OUTPUT.md, prints architect agent prompt."
argument-hint: [feature-slug, e.g. auth-mfa]
allowed-tools: Read, Write, Bash, Task
---

# /sdlc:design — Design Phase

**Phase 2 of 4** in the agentic SDLC. Reads `SPEC_OUTPUT.md` + `CLAUDE.design.md` contract → scaffolds `DESIGN_OUTPUT.md` → prints architect agent prompt.

## Dispatch

```bash
mekong design new $ARGUMENTS
```

## Output

`.mekong/DESIGN_OUTPUT.md` populated with: Architecture Overview, Component Diagram, ADR (Architecture Decision Records), File Ownership Matrix, API/Schema changes, Risk assessment.

## Next

```bash
mekong code new $ARGUMENTS   # or /sdlc:code $ARGUMENTS
```

## Contract

`.mekong/phases/CLAUDE.design.md` — architect agent instructions (ADR format, file-ownership declaration, concurrency considerations).

## Related

- `/sdlc` — full flow overview
- `/sdlc:spec` ← previous phase
- `/sdlc:code` → next phase
