# Portfolio Commands Implementation — Report

## TASK 1 — `lib/portfolio.ts`
Status: Already implemented at `lib/portfolio.ts` with:
- `listVentures(venturesRoot)` — returns `VentureSummary[]` sorted by `updatedAt` desc
- `getVentureDetail(venturesRoot, ventureId)` — returns full detail with decisions + recent events
- `compareVentures(venturesRoot, ids)` — returns `VentureComparison` with dimensions

Dependencies: `lib/venture-toml-parser.ts` (TOML parser)

## TASK 2 — `tools/cli/venture.ts` CLI commands
Status: Already wired in `cmds` router:
- `portfolio` → calls `listVentures(ROOT/ventures)` and prints summary
- `compare <id1> <id2>` → calls `compareVentures()` and prints table
- `status [id]` → summary without id, detail with id

## TASK 3 — Verification results

### `portfolio`
- Output: 2 ventures listed (table format working)
- Both ventures show with correct IDs, names, types, phases

### `compare`
- Output: side-by-side comparison table with dimensions [name, type, phase, status, decisionsCount, eventsCount]
- Works with both venture IDs

### `status`
- Without arg: summary counts
- With arg: per-venture detail (phase, decisions count, events count)

## Unresolved questions
None.
