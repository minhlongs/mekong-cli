# Phase Implementation Report

### Executed Phase
- Phase: wire-notification-backup-openclaw-engine
- Plan: none (direct task)
- Status: completed

### Files Modified
- `packages/mekong-cli-core/src/cli/commands/notification.ts` — 149 lines (+import MekongEngine, +showEngineHealth helper, +engine param, +submitMission on send, +health footer on list/config)
- `packages/mekong-cli-core/src/cli/commands/backup.ts` — 170 lines (+import MekongEngine, +showEngineHealth helper, +engine param, +classifyComplexity on create, +submitMission on restore, +health footer on list/schedule)

### Tasks Completed
- [x] Added `import type { MekongEngine }` to both files
- [x] Added `showEngineHealth()` DRY helper to both files (exact spec)
- [x] Changed both `registerXCommand` signatures: `engine?: MekongEngine` (optional)
- [x] `notification send`: fire-and-forget `submitMission` for delivery optimization
- [x] `notification list`: engine health footer via `showEngineHealth`
- [x] `notification config`: engine status footer via `showEngineHealth`
- [x] `backup create`: `classifyComplexity(opts.type)` + health footer
- [x] `backup restore`: fire-and-forget `submitMission` for restore verification (non-dry-run only)
- [x] `backup list`: engine stats footer via `showEngineHealth`
- [x] `backup schedule`: engine health footer via `showEngineHealth`
- [x] All engine calls wrapped in try/catch with `/* engine not ready */`
- [x] Double optional chaining: `engine?.openclaw?.method()`
- [x] Both files under 200 lines

### Tests Status
- Type check: pass (`npx tsc --noEmit` → `ok (no errors)`)
- Unit tests: not run (out of scope for this task)

### Issues Encountered
None. `classifyComplexity` return type is `string` from the SDK — cast to union literal type with `as typeof complexity` to satisfy strict TS without `any`.

### Next Steps
- Caller sites (likely `index.ts` or CLI entry) may need to pass `engine` argument to `registerNotificationCommand` and `registerBackupCommand` — not in this file's ownership, left for the integrating phase.

### Docs impact
minor — no architectural change, additive SDK wiring only
