---
title: "BMad Method — Test, Compare & Document"
description: "Test all BMad phases, compare with ClaudeKit/CCPM, define layered strategy, document intel"
status: pending
priority: P1
effort: 3h
branch: master
tags: [bmad, planning, framework, integration]
created: 2026-02-20
---

# BMad Method — Test, Compare & Document

## Context
- Research: `research/researcher-01-bmad-method-overview.md`
- Research: `research/researcher-02-bmad-vs-claudekit-ccpm.md`
- BMad Version: 6.0.0-Beta.7 (installed 2026-02-18)
- Config: `_bmad/bmm/config.yaml`
- Output Dir: `_bmad-output/`

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | Verify Installation & `/bmad-help` | ✅ Mostly done | [phase-01](phase-01-verify-installation.md) |
| 2 | Test Planning Phases (Architecture → Epics → Readiness) | pending | [phase-02](phase-02-test-planning-phases.md) |
| 3 | Test Implementation Phase (Sprint → Dev → Review → Retro) | pending | [phase-03](phase-03-test-implementation-phase.md) |
| 4 | Test Advanced Features (Party Mode, Correct Course) | pending | [phase-04](phase-04-test-advanced-features.md) |
| 5 | Compare BMad vs ClaudeKit vs CCPM + Layered Strategy | pending | [phase-05](phase-05-compare-and-integrate.md) |
| 6 | Document Intel in `knowledge/` | pending | [phase-06](phase-06-document-intel.md) |

## Already Done (steps 1, 3, 4, 14)
- ✅ BMad v6.0.0-Beta.7 installed (`_bmad/`, 55 commands)
- ✅ `/bmad-brainstorming` — output: `_bmad-output/brainstorming/brainstorming-session-2026-02-19.md`
- ✅ `/bmad-bmm-create-prd` — output: `_bmad-output/planning-artifacts/prd.md`
- ✅ BMad Builder (BMB) module installed

## Key Dependencies
- Phase 2 → Phase 3 (architecture must exist before sprint planning)
- Phase 3 → Phase 4 (need story context for advanced flow)
- Phase 5 → Phase 6 (comparison findings feed into intel doc)

## Success Criteria
- All 4 workflow phases tested with real outputs
- Layered BMad + ClaudeKit + CCPM strategy defined
- `knowledge/bmad-method-framework-intel.md` created and complete
