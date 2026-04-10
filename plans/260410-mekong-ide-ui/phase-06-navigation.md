---
phase: 6
title: "Navigation — Top Bar + Command Palette"
status: complete
effort: 3h
depends_on: [2]
---

# Phase 6: Navigation (Top Bar + Cmd+K Palette)

## Context
- Navigation Components from .pen: Top bar, Command Palette (Cmd+K)
- Screen 6 (Permission Dialog, 520x400): Command block, detail rows, approve/deny

## Files to Create

```
components/
├── navigation/
│   ├── top-bar.tsx                    # Full-width top bar (36px height)
│   ├── top-bar-menu-item.tsx          # Single menu item (File, Edit, View, etc.)
│   ├── breadcrumb.tsx                 # Path breadcrumb in center of top bar
│   ├── command-palette.tsx            # Cmd+K overlay — search + action list
│   ├── command-palette-item.tsx       # Single command result row
│   ├── command-palette-provider.tsx   # Context provider for registering commands
│   └── index.ts
├── dialogs/
│   ├── permission-dialog.tsx          # Tool approval: command block + approve/deny
│   ├── permission-detail-row.tsx      # Single detail row (tool, args, risk level)
│   └── index.ts

hooks/
├── use-command-palette.ts             # State + keyboard shortcut (Cmd+K)
├── use-keyboard-shortcuts.ts          # Global keyboard shortcut registry
```

## Top Bar Layout

```
┌──────────────────────────────────────────────────────────┐
│ ≡  File  Edit  View  Go  Terminal  Help  │  ~/project/src/auth.ts  │  ◉ Connected │
└──────────────────────────────────────────────────────────┘
```

## Command Palette

```
┌─────────────────────────────────────┐
│ > Search commands...          Cmd+K │
├─────────────────────────────────────┤
│ 📄 Open File              Cmd+O    │
│ 🔍 Find in Files           Cmd+F   │
│ ⚙️ Toggle Terminal          Ctrl+`  │
│ 🚀 Run Task...             Cmd+R   │
│ 📊 Open Engine Farm                 │
│ 💬 Focus Agent Chat        Cmd+J   │
│ 📋 Open Task Tracker               │
│ 💰 Open Trading View               │
└─────────────────────────────────────┘
```

## Permission Dialog (Screen 6)

```
┌────────── Permission Required ──────────┐
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ $ rm -rf node_modules && npm i    │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Tool:     Bash                          │
│  Risk:     ● Medium                      │
│  Scope:    Current directory             │
│  Agent:    Sonnet 4                      │
│                                          │
│  ☐ Always allow this tool                │
│                                          │
│  [Deny]                    [Approve]     │
└──────────────────────────────────────────┘
```

## Implementation Steps

1. **Create `use-keyboard-shortcuts.ts`** — Global keydown listener. Register/unregister shortcuts. Prevent default on matched combos. Map: key combo string → callback.

2. **Create `use-command-palette.ts`** — State: open/closed, search query, filtered commands. Opens on Cmd+K. Escape to close. Arrow keys to navigate. Enter to execute.

3. **Create `command-palette-provider.tsx`** — React context. Components register commands: { id, label, shortcut?, icon?, action, category }. Provides search + execute functions.

4. **Create `command-palette-item.tsx`** — Row: icon, label, shortcut badge (right-aligned). Hover highlight. Active state for keyboard nav.

5. **Create `command-palette.tsx`** — Modal overlay (centered, 520px wide). Search input at top. Filtered list of command-palette-items. Categories: Navigation, Editor, Tools, View.

6. **Create `top-bar-menu-item.tsx`** — Menu label. Hover shows dropdown (not implemented yet — placeholder). Click triggers action.

7. **Create `top-bar.tsx`** — 36px height. Left: hamburger icon + menu items (File, Edit, View, Go, Terminal, Help). Center: breadcrumb. Right: connection status dot + label.

8. **Create `breadcrumb.tsx`** — Shows current path. Segments separated by `/`. Last segment bold. Click segment to navigate.

9. **Create `permission-detail-row.tsx`** — Label (muted) + value pair. Risk level shows colored dot.

10. **Create `permission-dialog.tsx`** — Modal (520x400). Code block showing command. Detail rows: tool, risk, scope, agent. "Always allow" checkbox. Deny (secondary) + Approve (primary) buttons.

11. **Wire into IDE shell** — Add top-bar to `app/(ide)/layout.tsx` above ide-shell. Wrap with command-palette-provider. Register default commands for all routes.

12. **Register route commands** — Each screen registers its palette commands on mount (e.g., Engine Farm registers "Start Engine", "Stop All").

## Keyboard Shortcuts Summary

| Shortcut | Action |
|----------|--------|
| Cmd+K | Open command palette |
| Cmd+B | Toggle sidebar |
| Ctrl+` | Toggle terminal |
| Cmd+J | Focus agent chat |
| Cmd+1-7 | Switch to screen 1-7 |
| Escape | Close palette / dialog |

## Success Criteria
- [x] Top bar renders with menu items and breadcrumb
- [x] Cmd+K opens command palette
- [x] Palette search filters commands
- [x] Arrow keys + Enter navigate/execute commands
- [x] Permission dialog renders with approve/deny
- [x] Keyboard shortcuts work globally
- [x] `pnpm build` succeeds
