---
title: "Hub Transformation: Industrial RaaS Engine"
description: "Transform mekong-cli into a production-grade RaaS operating system with Hub SDK architecture"
status: pending
priority: P1
effort: 16h
branch: master
tags: [architecture, refactor, core-engine, bmad-integration]
created: 2026-02-07
---

# Hub Transformation: Industrial RaaS Engine

## 始計 (Initial Calculations)

Transform mekong-cli from prototype into Industrial RaaS Engine by absorbing Sophia AI Factory quintessence, standardizing Hub SDK architecture, wiring Plan-Execute-Verify engine, and integrating 169 BMAD workflows.

## Strategic Phases

| Phase | Focus | Effort | Status |
|-------|-------|--------|--------|
| [01](phase-01-absorb-quintessence.md) | Absorb Quintessence | 3h | Pending |
| [02](phase-02-standardize-packages.md) | Standardize Packages | 2h | Pending |
| [03](phase-03-wire-engine.md) | Wire Engine | 6h | Pending |
| [04](phase-04-integrate-bmad.md) | Integrate BMAD | 3h | Pending |
| [05](phase-05-verify-quality.md) | Verify Quality | 2h | Pending |

## Success Criteria

- ✅ All vibe-* packages moved to `packages/core/`
- ✅ Hub SDK structure enforced across all packages
- ✅ LLM-powered planner operational
- ✅ Multi-mode executor (shell/LLM/API) functional
- ✅ 169 BMAD workflows accessible
- ✅ Binh Phap quality gates passing
- ✅ Zero regression in existing CLI commands

## Dependencies

- Antigravity Proxy operational
- Python 3.11+ with Typer, Rich, Pydantic
- Access to `apps/sophia-ai-factory/packages/`
- Access to `_bmad/` workflows

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing CLI | Extensive testing after each phase |
| Package import conflicts | Careful dependency mapping before moves |
| LLM integration instability | Fallback to shell-only mode |
| BMAD workflow incompatibility | Gradual integration with verification |

## Execution Strategy

**Sequential execution** - Each phase builds on previous. No parallel execution due to file structure dependencies.

**Rollback plan** - Git checkpoints after each phase completion.

**Verification loop** - Build + Type Check + Test after every phase.
