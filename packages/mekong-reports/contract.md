# @mekong/reports — API Contract

> Contract-first spec. Types are stable before any live backend exists.
> When Gateway `/v1/*` routes ship (C1 phase), update `source: "mock"` → `source: "api"` only.

## Endpoints (future Gateway)

### GET /v1/missions

Returns list of agent execution missions.

**Response shape:**
```json
{
  "missions": [
    {
      "id": "msn_001",
      "title": "Bootstrap ide-ui",
      "status": "completed",
      "createdAt": "2026-04-17T08:00:00.000Z",
      "completedAt": "2026-04-17T09:15:00.000Z",
      "mcuUsed": 5
    }
  ]
}
```

**Status values:** `pending | running | completed | failed`

**Query params:**
- `?status=running` — filter by status

**Error codes:**
- `200` — success
- `401` — unauthenticated (if route is gated)
- `500` — gateway error → consumer falls back to empty state, never crashes

---

### GET /v1/departments/:slug/commands

Returns commands for a department.

**Response shape:**
```json
{
  "commands": [
    {
      "slug": "cook",
      "title": "Cook — Full Feature Build",
      "description": "...",
      "mcu": 5,
      "layer": "engineering"
    }
  ]
}
```

---

## TypeScript Consumer Pattern

```ts
import { getDepartmentCommands, getPricingTiers, listMissions } from '@mekong/reports';

// Department page (Next.js App Router server component)
const { data: commands } = await getDepartmentCommands('engineering');

// Pricing section (synchronous)
const tiers = getPricingTiers();

// Mission table
const { data: missions } = await listMissions({ status: 'running' });
```

## Zod Migration Path

When live API ships, wrap fetchers with Zod parse:

```ts
import { z } from 'zod';

const MissionSchema = z.object({
  id: z.string(),
  title: z.string(),
  status: z.enum(['pending', 'running', 'completed', 'failed']),
  createdAt: z.string().datetime(),
  completedAt: z.string().datetime().optional(),
  mcuUsed: z.number().optional(),
});
```

Parse failures → log + return empty state. Never crash the page.
