# Brainstorm Summary: Mekong-CLI Architecture

## Overview
Four parallel plans were generated to reduce risk across the highest-leverage seams:

| Plan | Target | Goal | Document |
|------|--------|------|----------|
| A | src/core god-module | Split into bounded subpackages without changing runtime behavior | docs/plans/260712-2100-plan-a-split-core.md |
| B | harness/PEV duplication | Make core/orchestrator the single source of truth and retire duplicate loops | docs/plans/260712-2100-plan-b-merge-pev.md |
| C | cleo-new Rust boundary | Add one canonical interface contract and a Python facade around cleo-new | docs/plans/260712-2100-plan-c-cleonew-boundary.md |
| D | agent system synchronization | Create a single registry and event flow for .claude and .agent systems | docs/plans/260712-2100-plan-d-agent-registry.md |

## Key Findings
- src/core is a dense hub with mixed domain and infrastructure concerns.
- PEV and core both implement planning, execution, and verification stacks.
- cleo-new is a high-volume cross-language seam without a formal contracting layer.
- The two agent systems are parallel and likely to drift without a registry and shared contract.

## Open Questions
- Which plan should be sequenced first?
- Is daemon concurrency locking for missions.json already handled?
- Should cleo-new boundary changes be owned by Rust or Python teams?
- What is the target test surface for agent registry changes?

Created plans ready for review in docs/plans/
