---
title: "Phase 4 - Visualizations"
description: "Revenue trend charts, user growth charts, ROI visualization, usage heatmaps"
status: pending
priority: P3
effort: 1h
parent: 260307-0020-raas-analytics-dashboard
---

# Phase 4 - Visualizations

## Context Links
- Phase 3: [phase-03-dashboard-ui.md](./phase-03-dashboard-ui.md)
- Dashboard: `dashboard/src/pages/analytics-page.tsx`

## Overview
Additional data visualizations cho comprehensive analytics dashboard.

## Visualizations

### 1. Revenue Trend Chart
- Line chart với MRR over time (6-12 months)
- Growth rate indicators
- Projection trend (optional)

### 2. User Growth Chart
- Active users over time (DAL/WAL/MAL)
- New vs churned users
- Net growth rate

### 3. Tier Distribution
- Pie chart: % revenue by tier
- Bar chart: user count by tier
- ARPA comparison

### 4. Usage Heatmap
- Commands/features usage by hour/day
- Peak usage times
- Popular features highlight

### 5. ROI Visualization
- ROI comparison by customer
- Time saved metrics
- Cost savings breakdown

## Related Code Files

### Files to Create
- `dashboard/src/components/user-growth-chart.tsx`
- `dashboard/src/components/usage-heatmap.tsx`
- `dashboard/src/components/roi-comparison-chart.tsx`

### Files to Modify
- `dashboard/src/pages/analytics-page.tsx` - Add new charts

## Todo List
- [ ] Create `dashboard/src/components/user-growth-chart.tsx`
- [ ] Create `dashboard/src/components/usage-heatmap.tsx`
- [ ] Create `dashboard/src/components/roi-comparison-chart.tsx`
- [ ] Integrate into dashboard page
- [ ] Add tooltips and legends
- [ ] Responsive design for charts

## Success Criteria
- [ ] All charts render correctly
- [ ] Data updates in real-time
- [ ] Tooltips show correct values
- [ ] Responsive on all screen sizes
- [ ] No performance issues

## Next Steps
- Phase 5: Tests
