# Phase Implementation Report

### Executed Phase
- Phase: wire-monitor-workflow-openclaw
- Plan: none (direct task)
- Status: completed (with 1 known blocker in out-of-scope file)

### Files Modified
- `packages/mekong-cli-core/src/cli/commands/monitor.ts` — 163 lines (was 194)
- `packages/mekong-cli-core/src/cli/commands/workflow.ts` — 148 lines (was 110)

### Tasks Completed
- [x] Added `import type { MekongEngine } from '../../core/engine.js'` to both files
- [x] Changed both signatures to `registerXCommand(program: Command, engine: MekongEngine): void`
- [x] Added `showEngineHealth()` DRY helper in both files (identical per spec)
- [x] `monitor uptime`: calls `showEngineHealth()` to show engine uptime, missionsCompleted, agiScore, circuitBreakerState
- [x] `monitor alerts`: fire-and-forget `void engine.openclaw?.submitMission()` for AI alert correlation
- [x] `monitor sla`: inline try/catch block shows AGI score, circuit breaker state, missionsFailed
- [x] `workflow run`: calls `classifyComplexity(wf.name)` before execution, fire-and-forget `submitMission` for AI analysis
- [x] `workflow history`: calls `showEngineHealth()` as footer
- [x] `workflow create`: calls `classifyComplexity(name)` for step count recommendation
- [x] All engine calls wrapped in try/catch with `/* engine not ready */` fallback
- [x] `health.uptime` converted via `Math.round(health.uptime / 1000)` for seconds display
- [x] No use of `health.status` or `maxMcu`
- [x] `void engine.openclaw?.submitMission()` pattern used (not conditional on result)
- [x] Both files under 200 lines

### Tests Status
- Type check (owned files): pass — zero errors in monitor.ts and workflow.ts
- Pre-existing errors (out-of-scope): deploy.ts (3), team.ts (3) — not introduced by this task
- index.ts lines 134-135: `Expected 2 arguments, but got 1` — expected; index.ts is out-of-scope

### Issues Encountered
- `index.ts` still calls `registerMonitorCommand(program)` and `registerWorkflowCommand(program)` with 1 arg. Must be updated by owner of `index.ts` to pass `engine` as second argument:
  ```ts
  registerMonitorCommand(program, engine);
  registerWorkflowCommand(program, engine);
  ```

### Next Steps
- Owner of `index.ts` must update lines 134-135 to pass `engine`
- Pre-existing errors in `deploy.ts` and `team.ts` should be addressed separately

### Unresolved Questions
- None for this task scope
