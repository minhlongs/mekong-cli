---
phase: 3
title: "Tool Restriction"
status: pending
priority: P2
dependencies: [2]
---

# Phase 3: Tool Restriction — Per-Agent Tool Allowlisting

## Overview
Implement tool allowlisting so agents can only invoke tools they're authorized for. Codebuff's `toolNames` pattern → mekong-cli's `allowedTools` on AgentBase.

## Requirements
- ToolRegistry already exists (4 modes: shell/llm/api/tool) — extend with allowlist check
- Each tool gets a canonical name (e.g., `read_files`, `run_terminal_command`, `code_search`)
- AgentDispatcher filters available tools before LLM call based on agent's `allowedTools`
- Empty `allowedTools` = all tools (backward compat default)

## Architecture
```
ToolRegistry (existing)
├── register(name, handler, mode)     ← unchanged
├── get(name)                         ← unchanged
├── list_for_agent(agent)            ← NEW (filters by allowedTools)
└── validate_call(agent, tool_name)  ← NEW (raises if not allowed)
```

## Related Code Files
- Modify: `src/core/tool_registry.py` — add `list_for_agent()` and `validate_call()`
- Modify: `src/core/agent_dispatcher.py` — call `list_for_agent()` when building LLM tool list
- Create: `src/core/tool_names.py` — canonical tool name constants (mirrors Codebuff's ToolName union)

## Implementation Steps
1. Define canonical tool names in `tool_names.py`
2. Add `list_for_agent()` and `validate_call()` to ToolRegistry
3. Wire into AgentDispatcher: filter tool list before sending to LLM
4. Add integration test: agent with restricted tools cannot call unauthorized ones

## Success Criteria
- [ ] Agent with `allowedTools=['read_files']` cannot invoke `run_terminal_command`
- [ ] Agent with empty `allowedTools` gets all tools (backward compat)
- [ ] Tool restriction enforced at dispatcher level (not just client-side)
- [ ] Existing tests pass
