---
phase: 5
title: "Task Tracker + CashClaw Trading"
status: completed
effort: 4h
depends_on: [1, 2]
---

# Phase 5: Task Tracker + CashClaw Trading

## Context
- Screen 7 (Task Tracker, 1440x900): Kanban (To Do/In Progress/Done), task detail panel, dependency DAG
- Screen 8 (CashClaw Trading, 1440x900): Position cards, fair value cache, LLM signal feed, controls

## Files to Create

```
app/(ide)/tasks/
├── page.tsx                           # Task Tracker route

app/(ide)/trading/
├── page.tsx                           # CashClaw Trading route

components/
├── tasks/
│   ├── task-tracker-page.tsx          # Full page: kanban + detail panel
│   ├── kanban-board.tsx               # Three-column kanban layout
│   ├── kanban-column.tsx              # Single column (To Do / In Progress / Done)
│   ├── task-card.tsx                  # Draggable task card in kanban
│   ├── task-detail-panel.tsx          # Right-side detail: description, deps, metadata
│   ├── dependency-dag.tsx             # Simple DAG visualization (SVG lines)
│   └── index.ts
├── trading/
│   ├── trading-page.tsx               # Full trading dashboard layout
│   ├── position-card.tsx              # Single position: ticker, PnL, size, status
│   ├── position-grid.tsx              # Grid of position cards
│   ├── fair-value-cache-table.tsx     # Table: ticker, fair value, current, edge %
│   ├── llm-signal-feed.tsx            # Scrolling feed of LLM trading signals
│   ├── signal-entry.tsx               # Single signal: model, direction, confidence, time
│   ├── trading-controls.tsx           # Buy/sell/close buttons + size input
│   └── index.ts

lib/types/
├── task-types.ts                      # Task, TaskStatus, TaskDependency
├── trading-types.ts                   # Position, FairValue, Signal, TradeAction
```

## Task Tracker Layout

```
┌──────────────────────────────────────┬──────────────┐
│ Kanban Board                         │ Task Detail  │
│ ┌──────────┬──────────┬──────────┐  │              │
│ │ To Do    │ Progress │ Done     │  │ Title        │
│ │ ┌──────┐ │ ┌──────┐ │ ┌──────┐│  │ Description  │
│ │ │Task 1│ │ │Task 3│ │ │Task 5││  │ Status       │
│ │ │      │ │ │      │ │ │      ││  │ Assignee     │
│ │ └──────┘ │ └──────┘ │ └──────┘│  │ Dependencies │
│ │ ┌──────┐ │ ┌──────┐ │        │  │ ┌──────────┐ │
│ │ │Task 2│ │ │Task 4│ │        │  │ │  DAG      │ │
│ │ └──────┘ │ └──────┘ │        │  │ └──────────┘ │
│ └──────────┴──────────┴──────────┘  │              │
└──────────────────────────────────────┴──────────────┘
```

## CashClaw Trading Layout

```
┌────────────────────┬─────────────────────────────────┐
│ Positions          │ Fair Value Cache                 │
│ ┌────┐ ┌────┐     │ AAPL  $189  $192  +1.6%         │
│ │AAPL│ │NVDA│     │ NVDA  $820  $845  +3.0%         │
│ │+2.3│ │-0.8│     │ TSLA  $175  $168  -4.0%         │
│ └────┘ └────┘     │ ...                              │
├────────────────────┼─────────────────────────────────┤
│ Trading Controls   │ LLM Signal Feed                 │
│ [Buy] [Sell]       │ ● Sonnet: BUY AAPL 85% 10:42   │
│ Size: [___] [Close]│ ● Opus: HOLD NVDA 60% 10:41    │
│                    │ ● DeepSeek: SELL TSLA 90% 10:40 │
└────────────────────┴─────────────────────────────────┘
```

## Implementation Steps

### Task Tracker

1. **Create `task-types.ts`** — Task (id, title, description, status, owner, blockedBy, blocks), TaskStatus enum (todo/in_progress/done).

2. **Create `task-card.tsx`** — Card with title, status badge, owner avatar placeholder, dependency count. Click to select. Drag handle for kanban.

3. **Create `kanban-column.tsx`** — Column header (title + count), droppable area, list of task-cards. Uses HTML drag-and-drop API (no library).

4. **Create `kanban-board.tsx`** — Three kanban-columns side by side. State: task list with drag-drop to move between columns.

5. **Create `task-detail-panel.tsx`** — Right panel (360px). Shows selected task: title (editable), description, status dropdown, owner, blocked-by list, blocks list.

6. **Create `dependency-dag.tsx`** — Simple SVG rendering. Nodes = task cards (small), edges = arrows between blockedBy relationships. Auto-layout: topological sort, left-to-right.

7. **Create `task-tracker-page.tsx`** — Grid: kanban-board (left 2/3), task-detail-panel (right 1/3). Toggle DAG view via button.

### CashClaw Trading

8. **Create `trading-types.ts`** — Position (ticker, size, entryPrice, currentPrice, pnl, status), FairValue (ticker, fairValue, current, edge), Signal (model, direction, ticker, confidence, timestamp).

9. **Create `position-card.tsx`** — Card: ticker bold, PnL (green/red), size, entry vs current price.

10. **Create `position-grid.tsx`** — CSS Grid of position-cards. Auto-fill minmax(200px).

11. **Create `fair-value-cache-table.tsx`** — DataTable (from DS): ticker, fair value, current, edge %. Edge colored green (positive) / red (negative).

12. **Create `signal-entry.tsx`** — Single row: model dot (colored by `--model-*` token), direction (BUY/SELL/HOLD badge), ticker, confidence %, timestamp.

13. **Create `llm-signal-feed.tsx`** — Scrolling list of signal-entries. Auto-scroll to bottom on new entries.

14. **Create `trading-controls.tsx`** — Buy (success), Sell (danger), Close (secondary) buttons. Size input field. Ticker display.

15. **Create `trading-page.tsx`** — Four-quadrant grid: positions (top-left), fair-value-cache (top-right), controls (bottom-left), signal-feed (bottom-right).

16. **Create routes** — `app/(ide)/tasks/page.tsx` and `app/(ide)/trading/page.tsx`.

## Mock Data
- `lib/mock/task-mock-data.ts` — 8 tasks across 3 statuses with dependencies
- `lib/mock/trading-mock-data.ts` — 5 positions, 10 fair values, 20 signals

## Success Criteria
- [x] Kanban renders 3 columns with draggable cards
- [x] Task detail panel shows selected task info
- [x] Dependency DAG renders with SVG lines
- [x] Position cards show PnL with correct colors
- [x] Fair value table renders with edge coloring
- [x] Signal feed scrolls with model-colored entries
- [x] `npx tsc --noEmit` exits 0
