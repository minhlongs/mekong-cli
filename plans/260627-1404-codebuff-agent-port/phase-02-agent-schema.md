---
phase: 2
title: "Agent Schema"
status: pending
priority: P2
dependencies: [1]
---

# Phase 2: Agent Schema — Unified Agent Definition

## Overview
Extend `AgentBase` with Codebuff-inspired fields (`allowedTools`, `spawnableAgents`, `inputSchema`, `outputMode`, `stepHooks`) while preserving backward compatibility. Existing agents continue to work without changes.

## Requirements
- Add optional fields to AgentBase — no breaking changes
- `allowedTools`: list of tool names this agent may invoke (default: all tools from assigned skills)
- `spawnableAgents`: list of agent IDs this agent can delegate to (enables sub-agent spawning)
- `inputSchema` / `outputMode`: optional JSON schema for input validation and output format control
- `stepHooks`: optional async hooks (`onStepStart`, `onStepEnd`, `onToolCall`) for generator-like control flow

## Architecture
```
AgentBase (existing)
├── id, name, role          ← unchanged
├── skills                  ← unchanged
├── allowedTools: []        ← NEW (default: derived from skills)
├── spawnableAgents: []     ← NEW
├── inputSchema             ← NEW (optional)
├── outputMode              ← NEW ('last_message' | 'all_messages' | 'structured')
└── stepHooks               ← NEW (dict of async callbacks)
```

## Related Code Files
- Modify: `src/core/agent_base.py` — add new fields with defaults
- Modify: `src/core/agent_registry.py` — validate allowedTools at registration
- Create: `src/core/agent_schema.py` — schema validation helpers (JSON Schema)
- Modify: `src/core/agent_dispatcher.py` — enforce tool restrictions at dispatch time

## Implementation Steps
1. Add fields to AgentBase with safe defaults (backward compat)
2. Create `agent_schema.py` with JSON Schema validation
3. Update AgentRegistry to validate `allowedTools` against registered tools
4. Update AgentDispatcher to filter tool calls by agent's `allowedTools`
5. Add unit tests for schema validation

## Success Criteria
- [ ] Existing agents (GitAgent, FileAgent, ShellAgent) work unchanged
- [ ] New agents can declare `allowedTools` and get enforcement
- [ ] `spawnableAgents` enables delegation via CollaborationProtocol
- [ ] All existing tests pass
