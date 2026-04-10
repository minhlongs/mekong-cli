---
phase: 2
title: "Main IDE Layout — Core Shell"
status: completed
effort: 5h
depends_on: [1]
---

# Phase 2: Main IDE Layout (Screen 1)

## Context
- Screen 1 from .pen: 1440x900, three-panel layout
- Left Sidebar: 48px, vertical nav icons
- Center Panel: tab bar + code editor + terminal
- Right Panel: 320px, agent chat with model routing

## Overview
Build the IDE chrome — the persistent shell that wraps all screens. Resizable panels, tab management, integrated terminal placeholder.

## Files to Create

```
app/(ide)/
├── layout.tsx                         # IDE shell with three panels
├── page.tsx                           # Default: main editor view
├── loading.tsx                        # Skeleton loader

components/
├── layout/
│   ├── ide-shell.tsx                  # Three-panel layout orchestrator
│   ├── left-sidebar.tsx               # 48px icon nav rail
│   ├── left-sidebar-nav-item.tsx      # Single nav icon + tooltip
│   ├── center-panel.tsx               # Tab bar + content area
│   ├── right-panel.tsx                # 320px chat/tool panel
│   ├── panel-resizer.tsx              # Drag handle for panel resize
│   └── index.ts                       # Barrel export
├── editor/
│   ├── tab-bar.tsx                    # File tabs with close button
│   ├── tab-item.tsx                   # Single tab component
│   ├── editor-area.tsx                # Code display area (read-only initially)
│   ├── terminal-panel.tsx             # Bottom terminal (collapsible)
│   └── index.ts
```

## Architecture

```
┌──────────┬──────────────────────────┬──────────┐
│  Left    │     Center Panel          │  Right   │
│  48px    │  ┌──────────────────┐    │  320px   │
│          │  │ Tab Bar          │    │          │
│  [icons] │  ├──────────────────┤    │  Agent   │
│          │  │                  │    │  Chat    │
│          │  │  Editor Area     │    │          │
│          │  │                  │    │  Model   │
│          │  ├──────────────────┤    │  Select  │
│          │  │ Terminal (toggle) │    │          │
│          │  └──────────────────┘    │          │
└──────────┴──────────────────────────┴──────────┘
```

## Implementation Steps

1. **Create `ide-shell.tsx`** — CSS Grid layout: `grid-template-columns: 48px 1fr 320px`. State for panel visibility (right panel toggleable, terminal collapsible).

2. **Create `left-sidebar.tsx`** — Fixed 48px. Nav items: Explorer, Search, Git, Extensions, Engine Farm, Tasks, Trading. Each item = lucide icon + tooltip. Active state with accent-teal left border.

3. **Create `left-sidebar-nav-item.tsx`** — Icon, tooltip, active state, onClick routing.

4. **Create `center-panel.tsx`** — Flex column: tab-bar (36px), editor-area (flex-1), terminal-panel (200px, collapsible).

5. **Create `tab-bar.tsx` + `tab-item.tsx`** — Horizontal scrollable tabs. Active tab uses `--surface-active`. Close button on hover. "+" button to add tab.

6. **Create `editor-area.tsx`** — Placeholder code display with line numbers. Monospace font (`JetBrains Mono` or `Fira Code` via next/font). Syntax highlighting deferred to Phase 7 (API-driven).

7. **Create `terminal-panel.tsx`** — Dark terminal area at bottom. Toggle via Ctrl+`. Monospace, green-on-dark styling. Output-only initially.

8. **Create `right-panel.tsx`** — 320px fixed. Hosts agent chat (Phase 3) or tool panel (Phase 3). Toggle visibility with sidebar button.

9. **Create `panel-resizer.tsx`** — Draggable divider between center and right panel. Mouse drag to resize. Min/max constraints (center min 600px, right min 280px max 480px).

10. **Create `app/(ide)/layout.tsx`** — Import ide-shell, wrap children. Import fonts.

11. **Create `app/(ide)/page.tsx`** — Default editor view with sample content.

## Keyboard Shortcuts (wire in this phase)
- `Ctrl+`` — toggle terminal
- `Ctrl+B` — toggle left sidebar expand
- `Ctrl+Shift+B` — toggle right panel

## Success Criteria
- [x] Three-panel layout renders at 1440x900
- [x] Left sidebar icons navigate between routes
- [x] Tabs can be opened/closed
- [x] Terminal panel toggles
- [x] Right panel resizable via drag handle
- [ ] `pnpm build` succeeds (blocked: pnpm workspace conflict in monorepo; tsc --noEmit passes)
