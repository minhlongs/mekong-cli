---
phase: 3
title: "Agent Chat + Tool Execution Panels"
status: complete
effort: 4h
depends_on: [2]
---

# Phase 3: Agent Chat + Tool Execution Panels

## Context
- Screen 2 (Agent Dashboard, 360x900): Pipeline visualizer, live tool calls, model status, context footer
- Screen 4 (Tool Execution, 420x900): Read/write/execute/meta/blocked tool categories
- Both live in the right panel (320px) of the IDE shell

## Files to Create

```
components/
├── agent/
│   ├── agent-chat-panel.tsx           # Chat UI with message list + input
│   ├── chat-message.tsx               # Single message (user/agent/system)
│   ├── chat-input.tsx                 # Input bar with send button + model selector
│   ├── model-selector.tsx             # Dropdown: architect/reasoning/audit/trading
│   ├── model-status-card.tsx          # Model name, provider, latency, status dot
│   ├── pipeline-visualizer.tsx        # Vertical step flow: plan→execute→verify
│   ├── pipeline-step.tsx              # Single pipeline step with status icon
│   ├── context-footer.tsx             # Token count, cache hits, cost
│   └── index.ts
├── tools/
│   ├── tool-execution-panel.tsx       # Tool list grouped by category
│   ├── tool-category-group.tsx        # Collapsible group (Read/Write/Execute/Meta/Blocked)
│   ├── tool-card.tsx                  # Single tool: name, description, status, last run
│   ├── tool-call-log.tsx             # Live feed of tool invocations
│   ├── tool-call-entry.tsx           # Single tool call: tool name, args, result, duration
│   └── index.ts

lib/
├── types/
│   ├── agent-types.ts                 # ChatMessage, PipelineStep, ModelConfig
│   └── tool-types.ts                  # ToolDef, ToolCall, ToolCategory
```

## Architecture

Right panel switches between two views via tab:
```
┌─── Right Panel (320px) ──────┐
│ [Chat] [Tools]               │  ← tab switcher
├──────────────────────────────┤
│ Chat View:                   │
│  ┌─ Pipeline Visualizer ──┐ │
│  │ ● Plan → Execute → ✓   │ │
│  └─────────────────────────┘ │
│  ┌─ Messages ──────────────┐ │
│  │ user: Fix the auth bug  │ │
│  │ agent: Reading files... │ │
│  │ system: Tool: Read()    │ │
│  └─────────────────────────┘ │
│  ┌─ Model Status ─────────┐ │
│  │ ◉ Sonnet 4  12ms       │ │
│  └─────────────────────────┘ │
│  ┌─ Input ─────────────────┐ │
│  │ [message...] [▶] [🔽]  │ │
│  └─────────────────────────┘ │
│  ── Context Footer ──────── │
│  1.2K tokens | 3 hits | $0.02│
└──────────────────────────────┘
```

## Implementation Steps

1. **Create `agent-types.ts`** — Types for ChatMessage (role, content, timestamp, model), PipelineStep (id, label, status), ModelConfig (name, provider, color from tokens).

2. **Create `tool-types.ts`** — ToolDef (name, description, category, permissions), ToolCall (tool, args, result, duration, timestamp), ToolCategory enum.

3. **Create `chat-message.tsx`** — Renders user/agent/system messages. Agent messages show model color badge (`--model-architect`, etc.). System messages show tool calls inline.

4. **Create `model-selector.tsx`** — Dropdown with 4 model options. Each shows color dot + name. Selected model shown in chat input area.

5. **Create `chat-input.tsx`** — Text input + send button + model selector trigger. Shift+Enter for newline, Enter to send.

6. **Create `agent-chat-panel.tsx`** — Composes: pipeline-visualizer (top), message list (scroll), model-status-card, chat-input (bottom), context-footer.

7. **Create `pipeline-visualizer.tsx` + `pipeline-step.tsx`** — Horizontal step flow. Steps: Plan, Execute, Verify. Each step: pending/active/done/error. Active step pulses.

8. **Create `model-status-card.tsx`** — Model name, provider tag, latency number, green/yellow/red status dot.

9. **Create `context-footer.tsx`** — Compact bar: tokens used / limit, cache hit count, estimated cost.

10. **Create tool components** — `tool-execution-panel.tsx` groups tools into 5 categories. Each `tool-category-group.tsx` is collapsible. `tool-card.tsx` shows tool name, description, approval status. `tool-call-log.tsx` is live feed of recent calls.

11. **Wire right panel tabs** — Add tab switcher in `right-panel.tsx`: [Chat] / [Tools] tabs toggle between agent-chat-panel and tool-execution-panel.

## Mock Data
Create `lib/mock/agent-mock-data.ts` and `lib/mock/tool-mock-data.ts` for development. These get replaced by API in Phase 7.

## Success Criteria
- [x] Chat panel renders messages with model color coding
- [x] Model selector switches between 4 models
- [x] Pipeline visualizer shows step progression
- [x] Tool panel shows 5 categories with tool cards
- [x] Tool call log displays entries with duration
- [x] Tab switching between Chat and Tools works
- [x] `pnpm build` succeeds
