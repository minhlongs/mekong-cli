---
phase: 4
title: "Event SDK"
status: pending
priority: P2
dependencies: [2]
---

# Phase 4: Event SDK — `@mekongcli/agent-sdk`

## Overview
Create a new npm package `@mekongcli/agent-sdk` providing event-driven progress tracking for agent runs. Mirrors Codebuff's `handleEvent` callback pattern but adapted to mekong-cli's PEV architecture.

## Requirements
- Event types: `step_start`, `step_end`, `tool_call`, `tool_result`, `agent_spawn`, `agent_complete`, `error`, `run_complete`
- Streaming via async iterator (modern JS pattern) + callback fallback
- Session continuity: serialize/deserialize run state for resume
- TypeScript-first with full type exports

## Architecture
```
packages/agent-sdk/
├── src/
│   ├── client.ts          — MekongAgentClient (main entry)
│   ├── events.ts          — Event type definitions
│   ├── session.ts         — RunState serialization
│   └── index.ts           — Public exports
├── package.json
├── tsconfig.json
└── README.md
```

## Related Code Files
- Create: `packages/agent-sdk/` (new package in monorepo)
- Modify: `packages/` workspace config to include agent-sdk
- Modify: `src/core/` — add event emitter hooks to RecipeExecutor

## Implementation Steps
1. Scaffold `packages/agent-sdk/` with TypeScript config
2. Define event types in `events.ts`
3. Implement `MekongAgentClient` with `run()` method and event streaming
4. Implement `RunState` serialization for session continuity
5. Add event emitter hooks to RecipeExecutor (Python → IPC bridge)
6. Write unit tests for client and event types
7. Add package to pnpm workspace

## Success Criteria
- [ ] `MekongAgentClient.run()` streams events to callback
- [ ] All event types defined with TypeScript types
- [ ] RunState can be serialized/deserialized
- [ ] Package builds and passes type check
- [ ] Existing packages unaffected
