# Phase B6: Agent Factory (Steps 19-23)

## Goal
Config-driven agent construction — eliminate manual wiring in main.py.

## Current State
- Agents manually instantiated: `CEOAgent(llm=llm)`, `DeveloperAgent(llm=llm)`, etc.
- No configuration layer for agent roles, prompts, or capabilities
- `agents/registry.yaml` exists but minimal

## Implementation
1. **Design agent config schema (YAML):**
   ```yaml
   agents:
     - name: ceo
       role: planner
       role_prompt: "You are the CEO..."
       tools: [plan, delegate]
     - name: developer
       role: executor
       role_prompt: "You are the Developer..."
       tools: [write_code, run_tests]
   ```
2. **Build `harness/agents/factory.py`:**
   - `AgentFactory.load_config(path)` → parse YAML
   - `AgentFactory.create(name, llm, memory)` → instantiate from config
   - Support inheritance (base config + per-agent overrides)
3. **Wire seed agents through factory** — refactor `seed/main.py` to use factory
4. **Add new agent types** from existing `src/agents/`:
   - `database_agent.py` → DatabaseAgent
   - `monitor_agent.py` → MonitorAgent
   - `social_reply_agent.py` → SocialReplyAgent
   - `review_agent.py` → ReviewAgent

## New Import Pattern
```python
from src.agents.factory import AgentFactory
factory = AgentFactory("config/agents.yaml")
ceo = factory.create("ceo", llm=llm, memory=memory)
```

## Verification
- Factory creates all 4 seed agents with correct role_prompt
- New agents (database, monitor, social) discoverable via factory
- Config change → agents update without code changes
- Existing `seed/main.py` pipeline still works

## Risk: HIGH (new architecture, affects core pipeline)
