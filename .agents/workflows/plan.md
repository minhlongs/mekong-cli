---
description: "Create implementation plan with research and analysis. Modes: hard (deep), fast (quick), standard (balanced)."
---

# /plan — Implementation Planning

**AUTO-EXECUTE MODE.** Create plan without asking which mode — detect automatically based on complexity.

## Mode Detection

| Mode | When to Use | Behavior |
|------|-------------|----------|
| `hard` | Complex features, multi-system changes | Deep research → multi-phase plan → detailed steps |
| `fast` | Simple changes, styling, configs | Quick scout → single-phase plan → key steps only |
| (default) | Most tasks | Balanced research → structured plan |

User can override by saying: "plan:hard" or "plan:fast"

## Instructions

1. **Scout** the codebase to understand current state
2. **Research** the technical approach (skip if fast mode)
3. **Create plan** in `plans/` directory
4. **Break into phases** with clear TODO checklists
5. **Present** plan to user for review before implementation

## Plan Structure

```
plans/{date}-{slug}/
├── plan.md              # Overview (< 80 lines)
├── phase-01-*.md        # Detailed phase files (hard mode)
├── phase-02-*.md
└── ...
```

## Hard Mode (deep analysis)

When mode is `hard`:
- Analyze architecture implications across the codebase
- Include risk assessment and alternatives
- Create detailed phase files with step-by-step instructions
- Include success criteria and validation methods
- Research similar implementations for reference

## Fast Mode (quick planning)

When mode is `fast`:
- Scout only, skip deep research
- Single plan.md file (no separate phases)
- Bullet-point steps
- Focus on what to change, not why

## Standard Mode

When no mode specified:
- Moderate research depth
- Plan.md overview + 1-2 phase files
- Clear task breakdown with estimates
- Brief risk notes
