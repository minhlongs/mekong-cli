---
title: "BMad Method Installation and Integration"
description: "Install and validate BMad Method agile AI framework (36.2K stars), test 4 phases, and integrate with Mekong-CLI workflow."
status: pending
priority: P1
effort: 4h
branch: master
tags: [bmad, framework, agile, planning, integration]
created: 2026-02-18
---

# BMad Method Installation and Integration Plan

## Context
The BMad Method is a highly structured agile AI development framework with 36.2K stars. It offers scale-adaptive intelligence, 4 distinct phases (Analysis, Planning, Solutioning, Implementation), and "Party Mode" for multi-agent collaboration. This plan aims to install, validate, and integrate BMad into the Mekong-CLI ecosystem, comparing it with existing ClaudeKit workflows.

## Objectives
1.  **Install**: Successfully install BMad Method and BMad Builder modules.
2.  **Validate**: Test all 4 phases of the BMad workflow on a dummy feature.
3.  **Compare**: Analyze overlaps and synergies with ClaudeKit and CCPM.
4.  **Integrate**: Define a layered strategy combining BMad (Planning) + ClaudeKit (Execution).
5.  **Document**: Capture intelligence in `knowledge/bmad-method-framework-intel.md`.

## Phases

### Phase 1: Installation & Setup
- [ ] Install BMad Method module via `npx bmad-method install`.
- [ ] Verify installation with `/bmad-help`.
- [ ] Install BMad Builder module (`bmb`).

### Phase 2: Workflow Validation (The "Test Drive")
- [ ] **Analysis**: Run `/bmad-brainstorming` for a "Test Feature" (e.g., a simple CLI calculator).
- [ ] **Planning**: Run `/bmad-bmm-create-prd` to generate `PRD.md`.
- [ ] **Solutioning**:
    - [ ] Run `/bmad-bmm-create-architecture` -> `architecture.md`.
    - [ ] Run `/bmad-bmm-create-epics-and-stories` (Post-architecture).
    - [ ] Run `/bmad-bmm-check-implementation-readiness`.
- [ ] **Implementation**:
    - [ ] Run `/bmad-bmm-sprint-planning`.
    - [ ] Run `/bmad-bmm-dev-story` for a single story.
    - [ ] Run `/bmad-bmm-code-review`.
- [ ] **Review**:
    - [ ] Test `/bmad-bmm-correct-course`.
    - [ ] Test `/bmad-bmm-retrospective`.
- [ ] **Party Mode**: Test multi-agent collaboration if applicable during solutioning.

### Phase 3: Strategic Analysis & Integration
- [ ] **Comparative Analysis**:
    - [ ] Map BMad phases to ClaudeKit commands (e.g., `/plan:hard`).
    - [ ] Compare BMad vs CCPM.
- [ ] **Strategy Definition**: Create a layered strategy (BMad Strategy + CK Execution + CCPM PM).

### Phase 4: Documentation
- [ ] Create `knowledge/bmad-method-framework-intel.md`.
- [ ] Document installation steps, command mappings, and strategic value.

## Success Criteria
- BMad commands are executable.
- A full cycle from Brainstorming to Code Review is completed for the test feature.
- A clear "Binh Phap" strategy document exists defining how BMad fits into the Mekong ecosystem.
