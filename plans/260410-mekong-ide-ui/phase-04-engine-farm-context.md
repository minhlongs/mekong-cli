---
phase: 4
title: "Engine Farm Monitor + Context Visualizer"
status: pending
effort: 4h
depends_on: [1, 2]
---

# Phase 4: Engine Farm Monitor + Context Visualizer

## Context
- Screen 3 (Engine Farm, 1440x900): Engine cards, RAM/GPU bars, system resources, start/stop
- Screen 5 (Context Visualizer, 1440x340): Token bar, compression timeline, metrics

## Files to Create

```
app/(ide)/engines/
├── page.tsx                           # Engine Farm route

app/(ide)/context/
├── page.tsx                           # Context Visualizer route (or embed in IDE)

components/
├── engines/
│   ├── engine-farm-page.tsx           # Full page layout with grid of engine cards
│   ├── engine-card.tsx                # Single engine: name, model, status, resource bars
│   ├── resource-bar.tsx               # RAM/GPU/VRAM usage bar with label + percentage
│   ├── engine-controls.tsx            # Start/stop/restart buttons per engine
│   ├── system-resources-panel.tsx     # Overall system: CPU, RAM, GPU totals
│   └── index.ts
├── context/
│   ├── context-visualizer.tsx         # Main visualizer component
│   ├── token-usage-bar.tsx            # Horizontal bar: used/cached/available tokens
│   ├── compression-timeline.tsx       # Timeline showing context compression events
│   ├── context-metrics-row.tsx        # Tokens used, cache hits, est. cost, compression %
│   └── index.ts

lib/types/
├── engine-types.ts                    # Engine, EngineStatus, ResourceUsage
├── context-types.ts                   # ContextMetrics, CompressionEvent, TokenUsage
```

## Engine Farm Layout

```
┌─────────────────────────────────────────────────────┐
│ Engine Farm Monitor          [System Resources ━━━] │
├─────────────┬─────────────┬─────────────┬───────────┤
│ ┌─────────┐ │ ┌─────────┐ │ ┌─────────┐ │ ┌───────┐│
│ │ Sonnet  │ │ │ Opus    │ │ │ Qwen    │ │ │ Local ││
│ │ ◉ Live  │ │ │ ◉ Live  │ │ │ ○ Idle  │ │ │ ● Off ││
│ │ RAM ━━━ │ │ │ RAM ━━━ │ │ │ RAM ━━  │ │ │ RAM ━ ││
│ │ GPU ━━  │ │ │ GPU ━━━ │ │ │ GPU ━   │ │ │ GPU   ││
│ │ [Stop]  │ │ │ [Stop]  │ │ │ [Start] │ │ │[Start]││
│ └─────────┘ │ └─────────┘ │ └─────────┘ │ └───────┘│
└─────────────┴─────────────┴─────────────┴───────────┘
```

## Context Visualizer Layout

```
┌─────────────────────────────────────────────────────┐
│ Context Usage  [████████████░░░░░░░░] 62K / 100K    │
├─────────────────────────────────────────────────────┤
│ Compression Timeline                                 │
│ ──●──────●──────●──────────●──── now                │
│   c1     c2     c3         c4                       │
├──────────┬──────────┬──────────┬────────────────────┤
│ 62.1K    │ 14 hits  │ $0.04    │ 38% compressed     │
│ tokens   │ cache    │ cost     │ ratio              │
└──────────┴──────────┴──────────┴────────────────────┘
```

## Implementation Steps

1. **Create `engine-types.ts`** — Engine (id, name, model, provider, status: 'running'|'idle'|'stopped'|'error'), ResourceUsage (ram, gpu, vram as 0-100 numbers), EngineConfig.

2. **Create `context-types.ts`** — TokenUsage (used, cached, total), CompressionEvent (timestamp, before, after, ratio), ContextMetrics.

3. **Create `resource-bar.tsx`** — Horizontal bar with gradient fill. Green <60%, yellow 60-80%, red >80%. Shows label + "X%" text.

4. **Create `engine-card.tsx`** — Card (from DS) containing: engine name, model name, status dot (green/yellow/red), two resource-bars (RAM, GPU), engine-controls.

5. **Create `engine-controls.tsx`** — Start (green), Stop (danger), Restart (secondary) buttons. Disabled states based on engine status.

6. **Create `system-resources-panel.tsx`** — Aggregated view: total CPU, RAM, GPU across all engines. Three resource-bars.

7. **Create `engine-farm-page.tsx`** — CSS Grid (auto-fill, minmax 280px). Maps engine list to engine-cards. System resources panel at top.

8. **Create `token-usage-bar.tsx`** — Segmented bar: used (teal), cached (blue), available (muted). Labels above segments.

9. **Create `compression-timeline.tsx`** — Horizontal timeline with dots at compression events. Hover shows before/after token counts.

10. **Create `context-metrics-row.tsx`** — Four metric cells: tokens used, cache hits, est. cost, compression ratio.

11. **Create `context-visualizer.tsx`** — Composes: token-usage-bar, compression-timeline, context-metrics-row. Can be standalone page or embeddable strip (340px height).

12. **Create routes** — `app/(ide)/engines/page.tsx` renders engine-farm-page. Optionally embed context-visualizer at bottom of main IDE layout.

## Mock Data
`lib/mock/engine-mock-data.ts` — 4 engines (Sonnet, Opus, Qwen, Local MLX) with varying status/resources.

## Success Criteria
- [ ] Engine cards render with resource bars
- [ ] Start/stop buttons change engine status (local state)
- [ ] System resources panel shows aggregates
- [ ] Token usage bar renders with segments
- [ ] Compression timeline shows events
- [ ] Metrics row displays all 4 values
- [ ] `pnpm build` succeeds
