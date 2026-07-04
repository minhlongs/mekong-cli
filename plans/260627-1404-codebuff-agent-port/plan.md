---
title: "Port Codebuff Multi-Agent Coordination to mekong-cli"
description: "Port CodebuffAI/codebuff's multi-agent coordination pattern (agent schema, tool restriction, event SDK, pipeline stages) into mekong-cli's existing PEV architecture. Augment, don't replace."
status: pending
priority: P2
branch: "fix/layer2-ruff-tech-debt"
tags: [agent-system, sdk, codebuff-port]
blockedBy: []
blocks: []
created: "2026-06-27T07:30:56.099Z"
createdBy: "ck:plan"
source: skill
---

# Port Codebuff Multi-Agent Coordination to mekong-cli

## Overview

Port CodebuffAI/codebuff's proven multi-agent coordination pattern into mekong-cli's existing PEV (Plan-Execute-Verify) architecture. Four capabilities: (1) unified agent schema with tool restriction, (2) event-driven SDK package, (3) specialized pipeline stages, (4) async step hooks. All additive — no breaking changes.

## Source Manifest

| Field | Value |
|-------|-------|
| Repo | `CodebuffAI/codebuff` |
| URL | https://github.com/CodebuffAI/codebuff |
| Key files | `agents/types/agent-definition.ts`, `agents/types/tools.ts`, `sdk/src/client.ts` |
| Commit | latest main (fetched via WebFetch) |

## Source Anatomy

| Component | Description | Port Decision |
|-----------|-------------|---------------|
| `AgentDefinition` interface | id, displayName, model, toolNames, spawnableAgents, inputSchema, outputMode, handleSteps | **PORT** — extend AgentBase |
| Tool system (30 built-in) | read_files, write_file, run_terminal_command, code_search, etc. | **ADAPT** — map to existing ToolRegistry |
| SDK `handleEvent` | async callback streaming events | **PORT** — new `@mekongcli/agent-sdk` package |
| Multi-agent pipeline | FilePicker → Planner → Editor → Reviewer | **ADAPT** — compose within PEV stages |
| Generator `handleSteps` | async generator for programmatic control | **DEFER** — add optional stepHooks instead |

## Dependency Matrix

| Component | Action | Files |
|-----------|--------|-------|
| AgentBase schema | MODIFY | `src/core/agent_base.py`, `src/core/agent_registry.py` |
| Tool restriction | MODIFY | `src/core/tool_registry.py`, `src/core/agent_dispatcher.py` |
| Event SDK | CREATE | `packages/agent-sdk/` (new package) |
| Pipeline stages | CREATE | `src/core/pipeline_stages.py`, `src/agents/*_agent.py` |
| Integration | MODIFY | `src/core/orchestrator.py`, `src/core/hybrid_router.py` |

## Decision Matrix

| Decision | Source's Way | Our Way | Rationale |
|----------|-------------|---------|-----------|
| Agent control flow | Async generator `handleSteps` | Sync `execute()` + optional `stepHooks` | Preserve existing contract |
| Tool restriction | Per-agent `toolNames` | Per-agent `allowedTools` on AgentBase | Same concept, local naming |
| Event SDK | Separate `@codebuff/sdk` | Separate `@mekongcli/agent-sdk` | Follows existing package pattern |
| Pipeline | 4-stage standalone | 4 stages composed within PEV | Augment, don't replace |
| MCP support | `mcpServers` config | Defer (YAGNI) | Not needed for v1 |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing agents | Low | High | All new fields have safe defaults |
| Tool restriction too restrictive | Medium | Medium | Empty allowedTools = all tools (opt-in) |
| SDK package conflicts | Low | Low | New workspace entry, isolated |
| Pipeline stages slow down runs | Medium | Low | Stages are opt-in via `--pipeline` flag |

**Overall Risk: LOW-MEDIUM** — additive changes only, backward compatible.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Research](./phase-01-research.md) | Pending |
| 2 | [Agent Schema](./phase-02-agent-schema.md) | Pending |
| 3 | [Tool Restriction](./phase-03-tool-restriction.md) | Pending |
| 4 | [Event SDK](./phase-04-event-sdk.md) | Pending |
| 5 | [Pipeline Stages](./phase-05-pipeline-stages.md) | Pending |
| 6 | [Integration](./phase-06-integration.md) | Pending |
| 7 | [Test](./phase-07-test.md) | Pending |
| 8 | [Review](./phase-08-review.md) | Pending |

## Dependencies

No cross-plan dependencies detected.
