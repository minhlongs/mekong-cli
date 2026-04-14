# Phase Implementation Report

## Executed Phase
- Phase: wire-openclaw-cost-and-benchmark-to-real-sdk
- Plan: none (direct task)
- Status: completed

## Files Modified
- `packages/mekong-cli-core/src/cli/commands/openclaw-cost.ts` — 163→175 lines, added engine param + live getHealth() calls in summary/optimize
- `packages/mekong-cli-core/src/cli/commands/openclaw-benchmark.ts` — 194→200 lines, added engine param + real submitMission() loop in run subcommand
- `packages/mekong-cli-core/tests/commands/openclaw-cost.test.ts` — created, 138 lines, 19 tests
- `packages/mekong-cli-core/tests/commands/openclaw-benchmark.test.ts` — created, 153 lines, 16 tests

## Tasks Completed
- [x] Changed `registerOpenClawCostCommand` signature to accept `MekongEngine`
- [x] `summary` — calls `engine.openclaw?.getHealth()` for live missionsCompleted/Failed/agiScore; labels "Live engine data" vs "Demo data"
- [x] `optimize` — uses `getHealth()` for real failure rate + agiScore-based tips; circuit breaker state check
- [x] `breakdown` + `budget` — kept as demo (per spec; needs metering DB)
- [x] Changed `registerOpenClawBenchmarkCommand` signature to accept `MekongEngine`
- [x] `run` — submits real missions via `engine.openclaw.submitMission()` per category; measures duration; scores 100-if-completed/40-if-failed; falls back to mock if engine absent or throws
- [x] `results`, `leaderboard`, `export` — kept mock history (per spec)
- [x] Test files created with `createMockEngine()` pattern; all `registerXCommand(program, mockEngine)` calls correct

## Tests Status
- Type check: pass (0 errors in owned files; 4 errors in `index.ts` which is lead-owned and expected)
- Unit tests: 35/35 passed (2 test files)
- Integration tests: n/a

## Issues Encountered
- Root `vitest.config.ts` include pattern (`packages/**/src/**/*.test.ts`) excludes `tests/` dir — must run tests via package-level vitest: `cd packages/mekong-cli-core && npx vitest run ...`
- `index.ts` (lead-owned) shows 4 TS2554 errors for the 4 commands now requiring 2 args — lead must pass `engine` when registering

## Next Steps
- Lead updates `index.ts` to pass `engine` to `registerOpenClawCostCommand` and `registerOpenClawBenchmarkCommand`
- Docs impact: none
