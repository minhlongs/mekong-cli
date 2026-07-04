---
phase: 1
title: "Research"
status: pending
priority: P2
dependencies: []
---

# Phase 1: Research

## Overview
Deep-dive into Codebuff's agent definition schema, tool system, SDK event pattern, and mekong-cli's existing agent infrastructure to produce a precise porting specification.

## Requirements
- Map every Codebuff agent field to mekong-cli equivalent or gap
- Catalog all 30 built-in tools and classify which are NEW vs EXISTS in mekong-cli
- Document SDK event types and streaming contract
- Identify all integration touchpoints in mekong-cli (AgentBase, ToolRegistry, HybridRouter, RecipeExecutor)

## Related Code Files
- Read: `src/core/agent_base.py`, `src/core/agent_registry.py`, `src/core/agent_dispatcher.py`
- Read: `src/core/hybrid_router.py`, `src/core/llm_client.py`
- Read: `src/core/planner.py`, `src/core/executor.py`, `src/core/verifier.py`
- Read: `src/core/collaboration.py`, `src/core/swarm.py`
- Read: `packages/` (existing SDK packages)
- Read: Codebuff `agents/types/agent-definition.ts`, `agents/types/tools.ts`, `sdk/src/client.ts`

## Implementation Steps
1. Spawn researcher agent to fetch Codebuff source (GitHub API + raw file reads)
2. Scout mekong-cli agent layer (core/ + packages/)
3. Produce gap analysis: Codebuff feature → mekong-cli equivalent → action (PORT/ADAPT/DEFER)
4. Document PEV-to-pipeline mapping (how Codebuff's 4 stages fit inside mekong-cli's 3-stage PEV)

## Success Criteria
- [ ] Gap analysis table complete (all Codebuff features mapped)
- [ ] mekong-cli integration points identified with exact file paths
- [ ] Risk assessment documented (breaking changes, backward compat)
- [ ] Research report written to `plans/reports/`
