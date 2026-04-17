# @mekong/reports

Typed API contract + mock data for Mekong IDE report pages.

**Contract-first:** types are stable before any live backend exists.
Swap `source: "mock"` to `source: "api"` when Gateway ships — consumers unchanged.

## Install

```bash
pnpm add @mekong/reports
```

## Usage

```ts
import {
  getDepartmentCommands,
  getPricingTiers,
  listMissions,
  getMission,
} from '@mekong/reports';

// Next.js App Router server component
const { data: commands } = await getDepartmentCommands('engineering');
const tiers = getPricingTiers();
const { data: missions } = await listMissions({ status: 'running' });
const { data: mission } = await getMission('msn_001');
```

## Exported Types

| Type | Description |
|---|---|
| `DepartmentCommand` | slug, title, description, mcu, layer |
| `PricingTier` | id, name, priceUsdCents, creditsPerMonth, features |
| `Mission` | id, title, status, createdAt, completedAt?, mcuUsed? |
| `MissionStatus` | `pending \| running \| completed \| failed` |
| `ReportPage<T>` | `{ data, fetchedAt, source }` wrapper |

## Build

```bash
pnpm --filter @mekong/reports build
```

Outputs `dist/index.js` (CJS), `dist/index.mjs` (ESM), `dist/index.d.ts`.

## Tests

```bash
pnpm --filter @mekong/reports test
```

See `contract.md` for Gateway endpoint spec and Zod migration path.
