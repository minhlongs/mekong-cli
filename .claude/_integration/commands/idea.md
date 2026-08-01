---
description: "Idea pipeline: validate -> BMC -> PRD -> execution handoff (ultracode mode)"
argument-hint: "<your business idea in 1-3 sentences> [--auto] [--deep] [--parallel]"
allowed-tools: Bash, Read, Write, Agent
---

# /idea — Agentic BizPlan OS: Zero→IPO Company Architecture Generator

**MANDATORY GATE:** OpenClaw will NOT run 5-layer commands until this step completes.
**Input:** A business idea (1-3 sentences)
**Output:** Full company blueprint in `.mekong/company.json` + execution plan

**AUTO-EXECUTE MODE:** When `--auto` is present, execute all steps without waiting for user input.
**DEEP RESEARCH:** When `--deep` is present, spawn researcher agents for each phase.
**PARALLEL EXECUTION:** When `--parallel` is present, run independent phases concurrently.

## Your Business Idea
$ARGUMENTS

## Execution

```bash
python3 -m src.main idea run $ARGUMENTS
```

## Pipeline Phases

| Phase | Name | Description |
|-------|------|-------------|
| 1 | Validate | Read project-idea.md blueprint, classify stage (Zero→PSF / PMF→Early Scale / Scale-Up / Pre-IPO) |
| 2 | Business Model Canvas | Archetype, channels, revenue model, cost structure |
| 3 | PRD | MVP features, non-functional requirements, tech stack |
| 4 | Execution Handoff | Next commands, execution order, MVP scope |

## Ultracode Mode

When `--deep` is present, delegate each phase to specialist agents:
- Phase 1 → researcher (market validation)
- Phase 2 → researcher (business model patterns)
- Phase 3 → planner (architecture decisions)
- Phase 4 → planner (execution roadmap)

When `--parallel` is present, run all phases concurrently via Workflow.

## Output

- Console: Rich formatted summary (Panel with idea, stage, archetype, output path)
- JSON: `--json` flag for machine-readable output
- Files: Written to `plans/company-blueprint/` (configurable via `--output-dir`)

## Next Steps

After pipeline completes:
1. `/mk:plan` — Create implementation plan from PRD
2. `/mk:cook` — Execute the plan
3. `/mk:test` — Verify implementation
4. `/mk:code-review` — Review before merge
