---
description: "Codebase Memory MCP — knowledge graph for code intelligence"
argument-hint: "[install|index|status|search <query>]"
---

# /codebase-memory — Code Intelligence MCP

## Usage
```
/codebase-memory install          # Install codebase-memory-mcp binary
/codebase-memory index            # Index current project
/codebase-memory status           # Show index status
/codebase-memory search <query>   # Search codebase (via MCP)
```

## About
Codebase Memory MCP indexes your codebase into a knowledge graph:
- Functions, classes, call chains, dependencies
- HTTP routes and cross-service links
- 158 languages supported
- 14 MCP tools: search, trace, architecture, impact analysis

## Setup
1. Run `/codebase-memory install` (one-time)
2. Run `/codebase-memory index` (per project)
3. MCP tools auto-discovered via `.mcp.json`

## Implementation
- Install: `bash scripts/install-codebase-memory.sh`
- Index: `codebase-memory-mcp --index .`
