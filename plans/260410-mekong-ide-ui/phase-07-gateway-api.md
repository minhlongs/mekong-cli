---
phase: 7
title: "Wire to Gateway API"
status: complete
effort: 4h
depends_on: [3, 4, 5]
---

# Phase 7: Wire to Gateway API

## Context
- Gateway runs at `localhost:8000` (M1 Max dev) or `api.mekongmind.com` (prod)
- Replace all mock data with real API calls
- WebSocket for real-time: chat messages, tool calls, engine status

## Files to Create

```
lib/
├── api/
│   ├── api-client.ts                  # Base fetch wrapper with auth + error handling
│   ├── api-config.ts                  # Base URL from env, headers, timeout
│   ├── endpoints/
│   │   ├── agent-api.ts               # POST /chat, GET /pipeline, GET /models
│   │   ├── engine-api.ts              # GET /engines, POST /engines/:id/start|stop
│   │   ├── tool-api.ts               # GET /tools, POST /tools/:id/approve
│   │   ├── task-api.ts               # CRUD /tasks, PATCH /tasks/:id/status
│   │   ├── trading-api.ts            # GET /positions, GET /signals, POST /trade
│   │   └── context-api.ts            # GET /context/usage, GET /context/compression
│   └── index.ts

├── ws/
│   ├── ws-client.ts                   # WebSocket connection manager
│   ├── ws-events.ts                   # Event type definitions
│   └── use-ws-subscription.ts         # React hook for WS subscriptions

hooks/
├── use-agent-chat.ts                  # Chat state + send message + receive stream
├── use-engines.ts                     # Engine list + start/stop mutations
├── use-tasks.ts                       # Task CRUD + kanban state
├── use-trading.ts                     # Positions + signals + trade actions
├── use-context-metrics.ts             # Token usage + compression events
```

## API Architecture

```
Browser ──HTTP──> Gateway :8000
   │                 │
   │──WebSocket──>   │
   │    /ws/chat     │──> LLM Providers
   │    /ws/events   │──> Engine Farm
   │                 │──> Tool Runtime
```

## Environment Variable
```
NEXT_PUBLIC_API_URL=http://localhost:8000   # dev
NEXT_PUBLIC_API_URL=https://api.mekongmind.com  # prod
```

## Implementation Steps

1. **Create `api-config.ts`** — Read `NEXT_PUBLIC_API_URL` from env. Default headers (Content-Type, Accept). Timeout 30s.

2. **Create `api-client.ts`** — Wrapper around fetch. Methods: get, post, patch, delete. Error handling: parse JSON errors, throw typed ApiError. Auth token from localStorage (future).

3. **Create endpoint modules** — Each module exports typed functions:
   - `agent-api.ts`: `sendMessage(msg)`, `getModels()`, `getPipeline(sessionId)`
   - `engine-api.ts`: `listEngines()`, `startEngine(id)`, `stopEngine(id)`, `getSystemResources()`
   - `tool-api.ts`: `listTools()`, `approveTool(id)`, `getToolCalls(limit)`
   - `task-api.ts`: `listTasks()`, `createTask(data)`, `updateTask(id, data)`, `deleteTask(id)`
   - `trading-api.ts`: `getPositions()`, `getFairValues()`, `getSignals(limit)`, `executeTrade(action)`
   - `context-api.ts`: `getTokenUsage()`, `getCompressionHistory()`

4. **Create `ws-client.ts`** — WebSocket manager: connect, reconnect (exponential backoff), disconnect. Channels: `/ws/chat`, `/ws/events`. Parse JSON messages. Emit typed events.

5. **Create `ws-events.ts`** — Event types: ChatMessageEvent, ToolCallEvent, EngineStatusEvent, SignalEvent, ContextUpdateEvent.

6. **Create `use-ws-subscription.ts`** — Hook: subscribe to WS channel, return messages, auto-cleanup on unmount.

7. **Create data hooks** — Each hook manages: fetch on mount, WebSocket updates, loading/error states, optimistic updates for mutations.
   - `use-agent-chat.ts` — Messages array, sendMessage (POST + WS stream), model selection
   - `use-engines.ts` — Engine list, start/stop (POST + optimistic), WS status updates
   - `use-tasks.ts` — Task list, CRUD operations, drag-drop status changes
   - `use-trading.ts` — Positions, fair values, signals (WS real-time), trade execution
   - `use-context-metrics.ts` — Token usage, compression events, polling or WS

8. **Replace mock data in all components** — Import hooks instead of mock data. Add loading skeletons + error states.

9. **Add connection status indicator** — Top bar shows green dot (connected), yellow (reconnecting), red (disconnected). Based on WS connection state.

10. **Graceful fallback** — If API unavailable, show mock data with "Demo Mode" banner. Useful for static export / CF Pages without backend.

## Error Handling Pattern
```typescript
// Every API call follows this pattern:
const { data, error, isLoading } = useEngines()
// Components render: loading skeleton → error state → data
```

## Success Criteria
- [ ] All screens fetch data from gateway API when available
- [ ] WebSocket connects and receives real-time updates
- [ ] Chat messages stream via WebSocket
- [ ] Engine start/stop triggers real API calls
- [ ] Graceful fallback to demo mode when API offline
- [ ] Connection status visible in top bar
- [ ] `pnpm build` succeeds (static export with client-side fetching)
