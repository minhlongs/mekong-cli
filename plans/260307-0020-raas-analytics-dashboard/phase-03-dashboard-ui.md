---
title: "Phase 3 - Dashboard UI"
description: "React dashboard với revenue metrics cards, usage charts, ROI calculator"
status: pending
priority: P2
effort: 2.5h
parent: 260307-0020-raas-analytics-dashboard
---

# Phase 3 - Dashboard UI

## Context Links
- Phase 1: [phase-01-analytics-api.md](./phase-01-analytics-api.md)
- Phase 2: [phase-02-data-aggregation.md](./phase-02-data-aggregation.md)
- Reference: `apps/algo-trader/dashboard/src/pages/analytics-page.tsx`

## Overview
Tạo Analytics Dashboard UI với React/TypeScript, bao gồm revenue metrics cards, usage trend charts, và ROI calculator.

## Key Insights
- algo-trader đã có analytics page implementation
- Có thể reuse components từ algo-trader dashboard
- API integration với FastAPI backend từ Phase 1

## Requirements

### Functional
- Dashboard page với routing
- Revenue metrics cards (MRR, ARR, Growth Rate)
- Active licenses metric (DAL)
- Usage trend charts
- ROI calculator UI
- Tier distribution visualization

### Non-Functional
- Responsive design
- Loading states
- Error boundaries
- API error handling

## Architecture

```
dashboard/src/
├── pages/
│   └── analytics-page.tsx      # Main dashboard page
├── components/
│   ├── revenue-metrics-card.tsx
│   ├── revenue-trend-chart.tsx
│   ├── revenue-by-tier.tsx
│   ├── roi-calculator.tsx
│   ├── active-licenses-card.tsx
│   └── usage-heatmap.tsx
├── hooks/
│   └── use-analytics.ts        # Analytics data fetching
└── api/
    └── analytics.ts            # API client
```

## Related Code Files

### Files to Create
- `dashboard/src/pages/analytics-page.tsx`
- `dashboard/src/components/revenue-metrics-card.tsx`
- `dashboard/src/components/revenue-trend-chart.tsx`
- `dashboard/src/components/revenue-by-tier.tsx`
- `dashboard/src/components/roi-calculator.tsx`
- `dashboard/src/components/active-licenses-card.tsx`
- `dashboard/src/hooks/use-analytics.ts`
- `dashboard/src/api/analytics.ts`

### Files to Modify
- `dashboard/src/App.tsx` - Add analytics route
- `dashboard/src/components/sidebar-navigation.tsx` - Add navigation link

## Implementation Steps

### Step 1: API Client
Tạo `dashboard/src/api/analytics.ts`:
- `getRevenueAnalytics()` - Revenue metrics
- `getActiveLicenses()` - DAL metric
- `getChurnRate()` - Churn rate
- `getRevenueByTier()` - Tier breakdown
- `getROI(keyId: string)` - ROI calculation
- `getUsageSummary(keyId: string)` - Usage summary

### Step 2: Custom Hook
Tạo `dashboard/src/hooks/use-analytics.ts`:
- `useAnalytics()` - Main analytics hook
- Data fetching with React Query
- Loading/error states
- Auto-refresh interval

### Step 3: Metrics Cards
Revenue metrics components:
- `RevenueMetricsCard` - MRR, ARR, Growth
- `ActiveLicensesCard` - DAL, WAL, MAL
- `ChurnRateCard` - Churn rate metric

### Step 4: Charts
Visualization components:
- `RevenueTrendChart` - Line chart với MRR trend
- `RevenueByTier` - Pie/bar chart tier breakdown
- `UsageTrendChart` - Usage over time

### Step 5: ROI Calculator
Interactive component:
- Input: License key, period
- Output: ROI %, time saved, cost comparison
- Visual metrics display

### Step 6: Dashboard Page
Main page layout:
- Grid layout với responsive design
- Section organization
- Data refresh controls

## Todo List
- [ ] Create `dashboard/src/api/analytics.ts`
- [ ] Create `dashboard/src/hooks/use-analytics.ts`
- [ ] Create `dashboard/src/components/revenue-metrics-card.tsx`
- [ ] Create `dashboard/src/components/revenue-trend-chart.tsx`
- [ ] Create `dashboard/src/components/revenue-by-tier.tsx`
- [ ] Create `dashboard/src/components/roi-calculator.tsx`
- [ ] Create `dashboard/src/components/active-licenses-card.tsx`
- [ ] Create `dashboard/src/pages/analytics-page.tsx`
- [ ] Add route to `dashboard/src/App.tsx`
- [ ] Add navigation link to sidebar
- [ ] Add loading states
- [ ] Add error handling

## Success Criteria
- [ ] Dashboard renders correctly
- [ ] All metrics display accurate data
- [ ] Charts render properly
- [ ] ROI calculator functional
- [ ] Responsive on mobile/tablet
- [ ] Loading states present
- [ ] Error handling works
- [ ] No TypeScript errors

## Design Notes

### Color Scheme
- Revenue: Green (#10B981)
- Usage: Blue (#3B82F6)
- ROI: Purple (#8B5CF6)
- Alerts: Red (#EF4444)

### Chart Library
- Recharts (nếu đã có trong project)
- Chart.js (alternative)

### Layout
```
┌─────────────────────────────────────────────┐
│         Analytics Dashboard                  │
├─────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │   MRR   │ │   DAL   │ │  Churn  │       │
│  └─────────┘ └─────────┘ └─────────┘       │
│  ┌───────────────────┐ ┌───────────────────┐│
│  │  Revenue Trend    │ │  Revenue by Tier  ││
│  │  (Line Chart)     │ │  (Pie Chart)      ││
│  └───────────────────┘ └───────────────────┘│
│  ┌───────────────────┐ ┌───────────────────┐│
│  │   ROI Calculator  │ │   Usage Trend     ││
│  └───────────────────┘ └───────────────────┘│
└─────────────────────────────────────────────┘
```

## Next Steps
- Phase 4: Additional Visualizations
- Phase 5: Tests
