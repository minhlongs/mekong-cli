# Plan B: Resolve harness/PEV duplication with core orchestrator

## Context
src/harness/pev has its own planner/executor/verifier/runner/telemetry modules.
src/core already contains executor.py, planner.py, verifier.py, core/orchestrator/.
Two runtime loops for the same contract is a classic duplication risk.

## Observations
- PEV reimplements roles that already exist in core.
- Observability and structured logging are duplicated across both trees.
- Progress tracking and memory stacks exist in both paths.
- The daemon and PEV loops likely operate on overlapping domains.

## Proposal
- Make src/core/orchestrator the single source of truth for planning, execution, and verification.
- Move harness/PEV stack into core/orchestrator/pev as an explicit extension or adapter.
- Preserve harness wiring by keeping thin adapter modules for backward compatibility.

## Steps
- Inventory cross-tree usages from imports/calls.
- Merge pev/planner behavior into core/planner via adapters.
- Merge pev/executor and pev/verifier into core/orchestrator.
- Extract shared observability helpers into one module.
- Update imports and delete duplicate code only after replacements are stable.

## Acceptance Criteria
- pytest still passes after the merge.
- No duplicated truth states for failed/successful missions.
- Duplication hotspots like ExecutionHistory.append and raas -> core are not made worse.
> Created: 2026-07-12
