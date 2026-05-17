---
argument-hint: help | save [message] | remember [context] | (no args for help)
description: Manage claude-mem operations and memory context (requires claude-mem MCP)
allowed-tools: Bash(claude-mem:*), Bash(echo:*), Bash(cat:*)
---

## Claude-Mem Command Handler

> **Note:** Requires `claude-mem` MCP plugin configured. See https://github.com/grll/claude-mem

### Check for help command first
!`[ -z "$ARGUMENTS" ] || [ "$ARGUMENTS" = "help" ] && printf '%s\n' '## 🧠 Claude-Mem Help' '' '**Available Commands:**' '' '• /ck-claude-mem save [message] - Quick save of conversation overview' '• /ck-claude-mem remember [query] - Search saved memories' '• /ck-claude-mem help - Show this help' '' '**Quick Shortcuts:**' '• /ck-save - Direct save' '• /ck-remember - Direct search' '' '**About /ck-save:**' 'Quick way to save an overview to claude-mem without processing the' 'entire transcript. Use this when you dont need a detailed archive,' 'just a summary of key points and decisions.' '' '**If claude-mem MCP not configured:**' 'Run: npx claude-mem install' 'Or configure chroma MCP manually' && exit 0`

### Process other commands
Handle claude-mem operation: $ARGUMENTS

If $ARGUMENTS starts with "save":
- Write an overview of the current conversation context
- Add it to claude-mem using the chroma MCP tools
- Always use primitive types (strings, numbers, booleans) for MCP Chroma calls
- Save the overview using: `claude-mem save "your overview message"`

If $ARGUMENTS starts with "remember":
- Search claude-mem for relevant memories using the query
- Display the most relevant memories from previous sessions
- Use chroma_query_documents to find and present context

---

*Ported from claudekit ~/.claude/commands/claude-mem.md — 2026-04-16*
