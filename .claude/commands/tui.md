---
description: "🖥️ TUI Mode — launch Warp-style interactive terminal with command palette + block output + multi-pane layout. Uses tmux + rich + questionary."
argument-hint: "[initial-command]"
allowed-tools: Bash, Read
---
# /tui — Warp-Style Interactive TUI

Launch a full-screen interactive terminal mode with:
- **Left pane:** command palette (fuzzy search)
- **Top-right:** block output history
- **Bottom-right:** raw process output

## Usage

```bash
mekong tui                    # Launch TUI with empty palette
mekong tui "cook landing"     # Launch + pre-fill palette query
mekong tui --single-pane      # Fallback: single pane (no tmux)
```

## Behavior

1. **tmux available?** → launch 3-pane session
   - Pane 0 (left, 80 cols): `mekong palette` interactive
   - Pane 1 (top-right): block history viewer
   - Pane 2 (bottom-right): raw command output

2. **tmux NOT available?** → fallback to single-pane mode
   - Runs `mekong palette` in current terminal
   - No multi-pane, but full palette functionality preserved

3. **With initial command** → pre-fill palette query + auto-execute top match

## Dependencies

- `tmux` (optional, for multi-pane): `brew install tmux`
- `rich` + `questionary`: already in requirements.txt
- 0 new dependencies

## Examples

```bash
# Launch full TUI
mekong tui

# Launch with a specific query
mekong tui "fix payment error"

# Force single-pane (no tmux)
mekong tui --single-pane
```

## Implementation

`cli/tui/tmux_launcher.py` — TmuxLauncher class
`cli/tui/blocks.py` — BlockRenderer for output blocks
`cli/tui/palette.py` — CommandPicker (already built in Phase 1)

## Notes

- Part of **Warp-Interactive Layer** (Approach B)
- Backward compatible: existing `mekong <command>` unchanged
- Bilingual VI+EN
