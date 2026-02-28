# Phase 02: GrowthBook A/B Testing

## Context
- Parent: [plan.md](./plan.md)
- Depends on: [Phase 01](./phase-01-posthog-integration.md)
- Project: `/Users/macbookprom1/mekong-cli/apps/well`

## Overview
- **Priority**: P1
- **Status**: ⬜ pending
- **Mô tả**: Setup GrowthBook SDK kết nối PostHog làm data source cho A/B experiments

## Key Insights
- GrowthBook = experiment management layer, PostHog = data/metrics layer
- Client-side SDK — feature flags evaluate locally, không thêm latency
- Free tier GrowthBook Cloud đủ cho MVP (3 experiments, unlimited flags)

## Requirements
- GrowthBook provider wrap app (dưới PostHog provider)
- Feature flags evaluate client-side
- PostHog events tự động track experiment exposure
- Env vars: `VITE_GROWTHBOOK_CLIENT_KEY`, `VITE_GROWTHBOOK_API_HOST`

## Related Code Files

### Sửa (3 files)
1. `src/main.tsx` — Thêm GrowthBookProvider
2. `src/lib/analytics.ts` — Thêm experiment tracking methods
3. `package.json` — Thêm `@growthbook/growthbook-react`

## Implementation Steps

1. Install GrowthBook SDK
   ```bash
   cd apps/well && pnpm add @growthbook/growthbook-react
   ```

2. Update `src/main.tsx`:
   - Import `GrowthBook`, `GrowthBookProvider` từ SDK
   - Init GrowthBook instance với PostHog trackingCallback
   - Hierarchy: `<PostHogProvider>` → `<GrowthBookProvider>` → `<App/>`

3. Update `src/lib/analytics.ts`:
   - Thêm `trackExperiment(experimentId, variationId)` method
   - GrowthBook trackingCallback gọi `posthog.capture('$experiment_started', ...)`

## Todo List
- [ ] Install `@growthbook/growthbook-react`
- [ ] Setup GrowthBook Cloud account + API key
- [ ] Thêm GrowthBookProvider vào `main.tsx`
- [ ] Connect PostHog làm data source trong GrowthBook dashboard
- [ ] Thêm experiment tracking vào `analytics.ts`
- [ ] Test: tạo 1 feature flag, verify evaluate đúng

## Success Criteria
- Feature flags hoạt động client-side
- Experiment exposure events xuất hiện trong PostHog
- GrowthBook dashboard hiển thị experiment results
- Build passes, 0 TS errors

## Risk Assessment
- **SDK conflicts**: GrowthBook + PostHog cùng dùng feature flags — dùng GrowthBook cho experiments, PostHog cho simple flags
- **Flicker**: Feature flag evaluate trước render → `antiFlicker` option trong SDK

## Next Steps
- Phase 03: Dùng PostHog + GrowthBook track conversion funnel
