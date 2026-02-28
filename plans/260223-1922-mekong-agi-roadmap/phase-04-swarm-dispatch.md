# Phase 04 — Multi-Agent Swarm Task Distribution

**Context:** [plan.md](plan.md) | [audit-results.md](research/audit-results.md)

## Overview
- **Date:** 2026-02-23
- **Priority:** P1 (critical AGI gap)
- **Status:** pending
- **Effort:** 3h

## Key Insights
- `swarm.py` có `SwarmRegistry` — chỉ manage node registry (add/remove/heartbeat)
- **THIẾU HOÀN TOÀN:** task distribution, load balancing, result aggregation
- `orchestrator.py` không integrate với SwarmRegistry
- `agents/` directory tồn tại (`git_agent.py`, `file_agent.py`, etc.) — local agents ready
- Mekong architecture mô tả multi-agent nhưng hiện chỉ chạy single-thread
- `event_bus.py` EXISTS — publish/subscribe pattern có sẵn để coordinate

## Requirements
- `SwarmDispatcher` class: distribute tasks across registered nodes via HTTP
- Local agent routing: `git` task → `GitAgent`, `file` task → `FileAgent`
- `orchestrator.py` phải có option `use_swarm=True` để parallel execution
- Fallback to local execution nếu swarm không available

## Related Files
- `src/core/swarm.py` — SwarmRegistry (extend thêm dispatcher)
- `src/core/orchestrator.py` — integrate SwarmDispatcher
- `src/agents/git_agent.py`, `file_agent.py`, `shell_agent.py` — local agents
- `src/core/event_bus.py` — event coordination

## Architecture
```
RecipeOrchestrator.run_from_recipe()
    ↓ (if use_swarm=True)
SwarmDispatcher.dispatch(steps: List[RecipeStep])
    ├── Route git-steps → GitAgent (local or remote node)
    ├── Route file-steps → FileAgent (local or remote node)
    └── Route shell-steps → ShellAgent (local or remote node)
    ↓
Aggregate results → List[ExecutionResult]
    ↓
RecipeVerifier validates all results
```

## Implementation Steps

1. **swarm.py** — Thêm `SwarmDispatcher` class:
   ```python
   class SwarmDispatcher:
       def __init__(self, registry: SwarmRegistry):
           self.registry = registry
           self._local_agents = {
               "git": GitAgent(), "file": FileAgent(), "shell": ShellAgent()
           }

       def dispatch(self, step: RecipeStep) -> ExecutionResult:
           agent_type = self._route_step(step)
           healthy = self.registry.get_healthy_nodes()
           if healthy:
               return self._dispatch_remote(step, healthy[0])
           return self._dispatch_local(step, agent_type)
   ```

2. **swarm.py** — Thêm health-aware node selection:
   ```python
   def get_healthy_nodes(self) -> List[SwarmNode]:
       return [n for n in self._nodes.values() if n.status == "healthy"]
   ```

3. **orchestrator.py** — Thêm `use_swarm` parameter:
   ```python
   def __init__(self, ..., use_swarm: bool = False):
       self.dispatcher = SwarmDispatcher(SwarmRegistry()) if use_swarm else None
   ```

4. **orchestrator.py** — Trong `run_from_recipe`, route qua dispatcher nếu enabled

5. Verify với existing `test_shell_agent.py`, `test_git_agent.py`

## Todo
- [ ] Thêm `SwarmDispatcher` vào `swarm.py`
- [ ] Implement `_route_step()` — map step type → local agent
- [ ] Implement `_dispatch_remote()` — HTTP POST đến node
- [ ] Implement `_dispatch_local()` — gọi local agent trực tiếp
- [ ] Integrate vào `orchestrator.py` với `use_swarm=False` default
- [ ] Viết test cho SwarmDispatcher

## Files Sẽ Sửa (max 4)
1. `src/core/swarm.py`
2. `src/core/orchestrator.py`
3. `tests/test_smart_router.py` (thêm dispatch test)

## Success Criteria
- `SwarmDispatcher.dispatch(step)` route đúng agent local
- `orchestrator.run_from_recipe(recipe, use_swarm=True)` không lỗi
- Git steps → `GitAgent`, File steps → `FileAgent`
- Fallback hoạt động khi không có node remote

## Risk
- High: phức tạp, dễ over-engineer
- **YAGNI:** chỉ implement local routing trước, remote nodes là optional
- HTTP remote dispatch có thể skip trong V1

## Next Steps
→ Phase 05: Learning Loop
