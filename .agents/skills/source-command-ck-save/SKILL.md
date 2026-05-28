---
name: "source-command-ck-save"
description: "Write an overview and save with Codex-mem"
---

# source-command-ck-save

Use this skill when the user asks to run the migrated source command `ck-save`.

## Command Template

**Write an overview** of the current conversation context and:
1. **Add it to Codex-mem** using the chroma MCP tools. Always use primitive types (strings, numbers, booleans) when calling MCP Chroma tools directly. Arrays should be comma-separated strings, and nested objects should be flattened.
2. **Save the overview to index** using the Codex-mem CLI tool: `Codex-mem save "your overview message"`
