# Plan: nhipdieuxanh-agent Implementation

## Context

`nhipdieuxanh-agent` (Nhip Điệu Xanh = Green Rhythm) is a new agent to be added to the `agent-core` package. It follows the established BaseAgent pattern used by CEO, Developer, Tester, Reviewer, Analyst, Ops, and ToolEnabled agents.

## Current State

- **Package**: `packages/agent-core/` — contains BaseAgent + 7 specialized agents
- **Pattern**: Each agent = a Python file with a `ROLE_PROMPT` string (Vietnamese) + a class extending `BaseAgent`
- **Registration**: All agents exported from `agent_core/agents/__init__.py`
- **Orchestrator**: `SoloCompanyOrchestrator` uses CEO→Developer→Tester→Reviewer chain
- **Tests**: 10 test files in `tests/`, all passing (66 tests)

## Implementation Steps

### Step 1: Create nhipdieuxanh_agent.py
- Path: `packages/agent-core/src/agent_core/agents/nhipdieuxanh_agent.py`
- Define `NHIPDIEUXANH_ROLE_PROMPT` — a Vietnamese role prompt for the agent's purpose
- Create `NhipDieuAnhAgent(BaseAgent)` class with appropriate methods
- Follow exact pattern from existing agents (ceo.py, analyst.py)

### Step 2: Register in __init__.py
- Add import: `from agent_core.agents.nhipdieuxanh_agent import NhipDieuAnhAgent`
- Add to `__all__` list

### Step 3: Write unit tests
- Path: `packages/agent-core/tests/test_nhipdieuxanh_agent.py`
- Test instantiation, run() method, parse_json() inheritance
- Use respx for mocking LLM calls (follow existing test patterns)

### Step 4: Run tests
- `cd packages/agent-core && python -m pytest tests/test_nhipdieuxanh_agent.py -v`
- Verify all tests pass

## Decisions Made

1. **Agent purpose**: "Nhip Điệu Xanh" = Green Rhythm — an agent focused on sustainability/green initiatives, eco-friendly planning, or environmental impact analysis (default assumption; refine if user specifies)
2. **Language**: Vietnamese role prompt (consistent with all existing agents)
3. **Methods**: Minimal — just `run()` inherited from BaseAgent + one domain-specific method if applicable

## Unresolved Questions

1. What is the specific domain/purpose of nhipdieuxanh-agent? (eco-sustainability, green logistics, environmental consulting?)
2. Should it be a standalone agent or integrated into the orchestrator pipeline?
3. Does it need tool access (ToolEnabledAgent) or is standard BaseAgent sufficient?
