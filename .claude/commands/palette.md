---
description: "🔍 Command Palette — fuzzy search mekong commands by typing natural language. Vietnamese + English. Part of Warp-style TUI layer."
argument-hint: "[search-query]"
allowed-tools: Bash, Read, Agent
---
# /palette — Command Palette

Type a natural language query to fuzzy-search and execute mekong commands.
Uses the same keyword routing table as `/ask` but with interactive autocomplete.

## Usage

```bash
mekong palette                    # interactive mode — no query
mekong palette "tạo landing page" # search + autocomplete
mekong palette "fix payment"      # search + autocomplete
```

## Behavior

1. **No query** → show full command catalog (questionary select)
2. **With query** → fuzzy-match against routing table, show top 5
3. **Enter** → execute matched command via `python3 -m src.main <command>`
4. **Esc / Ctrl+C** → cancel, no action

## Routing

Uses the keyword table defined in `.claude/commands/ask.md`:
- Vietnamese patterns prioritized
- English patterns fallback
- No match → suggest `/ask` or `/brainstorm` as fallbacks

## Examples

```bash
mekong palette "code"       → suggests: cook
mekong palette "sửa lỗi"   → suggests: fix
mekong palette "kế hoạch"  → suggests: plan / brainstorm
mekong palette ""           → shows all commands grouped by category
```

## Notes

- Part of **Warp-Interactive Layer** (Approach B): palette + blocks + tmux
- Uses `questionary` for interactive prompts (already in requirements.txt)
- 0 new dependencies
- Backward compatible: existing `mekong <command>` unchanged
