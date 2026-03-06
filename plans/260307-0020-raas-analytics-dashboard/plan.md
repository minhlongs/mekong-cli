---
title: "ROIaaS Phase 5 - Analytics Dashboard"
description: "Analytics dashboard với revenue tracking, user metrics, và ROI calculator cho RaaS platform"
status: pending
priority: P2
effort: 8h
branch: master
tags: [raas, analytics, dashboard, phase-5, roi]
created: 2026-03-07
---

# ROIaaS Phase 5 - Analytics Dashboard

## Context
- **Project**: mekong-cli
- **Phase**: ROIaaS Phase 5 (Analytics) - Final phase trong 5-phase ROIaaS framework
- **Existing**: UsageMetering, UsageTracker, UsageQueue (Phase 4 hoàn thành)
- **Reference**: algo-trader/src/analytics/revenue-analytics.ts (TypeScript implementation pattern)

## Requirements từ HIEN_PHAP_ROIAAS.md

### 1. Revenue Tracking
- Theo dõi doanh thu từ license subscriptions
- MRR (Monthly Recurring Revenue) calculation
- Usage-based revenue từ overage charges
- Revenue breakdown by tier (FREE/PRO/ENTERPRISE)

### 2. User Metrics
- Số lượng users, active users (DAL - Daily Active Licenses)
- Usage patterns per command/feature
- User activity trends
- Churn rate analysis

### 3. ROI Calculator
- Tính ROI cho khách hàng dựa trên usage vs cost
- Time saved metrics
- Cost comparison (build vs buy)
- Value demonstration dashboard

### 4. Premium Data Visualizations
- Revenue trend charts
- User growth charts
- ROI visualization
- Usage heatmaps

## Success Criteria

- [ ] Analytics API hoàn chỉnh với đầy đủ endpoints
- [ ] Dashboard UI với revenue metrics, user charts
- [ ] ROI calculator functional
- [ ] Tests coverage > 80%
- [ ] Documentation updated

## Dependencies

- Phase 4 (Usage Metering) - ✅ COMPLETED
- Phase 3 (Webhook Integration) - ✅ COMPLETED
- Phase 2 (License Management UI) - ✅ COMPLETED
- Phase 1 (License Gate) - ✅ COMPLETED

## Implementation Overview

### Phase 1: Analytics API (2h)
- [ ] Task 1.1: Tạo `src/analytics/raas_analytics.py` - Analytics service core
- [ ] Task 1.2: Tạo `src/api/routes/analytics_routes.py` - FastAPI routes
- [ ] Task 1.3: Repository methods cho analytics queries
- [ ] Task 1.4: ROI calculation engine

### Phase 2: Data Aggregation (2h)
- [ ] Task 2.1: Aggregate usage data từ usage_events table
- [ ] Task 2.2: Revenue calculations từ subscription data
- [ ] Task 2.3: User activity metrics aggregation
- [ ] Task 2.4: Caching layer cho performance

### Phase 3: Dashboard UI (2.5h)
- [ ] Task 3.1: Dashboard page component
- [ ] Task 3.2: Revenue metrics cards
- [ ] Task 3.3: Usage trend charts (Chart.js/Recharts)
- [ ] Task 3.4: ROI calculator UI component

### Phase 4: Visualizations (1h)
- [ ] Task 4.1: Revenue trend chart component
- [ ] Task 4.2: User growth chart
- [ ] Task 4.3: Tier distribution pie chart
- [ ] Task 4.4: Usage heatmap

### Phase 5: Tests (0.5h)
- [ ] Task 5.1: API tests cho analytics endpoints
- [ ] Task 5.2: Service unit tests
- [ ] Task 5.3: Integration tests

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Analytics Dashboard                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Revenue   │  │    User     │  │     ROI     │         │
│  │   Metrics   │  │   Metrics   │  │  Calculator │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                  ┌───────▼────────┐                         │
│                  │  Analytics API │                         │
│                  │  (FastAPI)     │                         │
│                  └───────┬────────┘                         │
│                          │                                  │
│         ┌────────────────┼────────────────┐                 │
│         │                │                │                 │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐         │
│  │   Usage     │  │  Revenue    │  │    User     │         │
│  │   Events    │  │  Analytics  │  │   Activity  │         │
│  │  (Phase 4)  │  │  (Phase 5)  │  │  (Phase 5)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance với large datasets | High | Caching, pagination, date ranges |
| Data accuracy | High | Unit tests, reconciliation checks |
| Complex ROI calculations | Medium | Simple formulas first, iterate |
| UI chart library compatibility | Low | Use existing project dependencies |

## Next Steps

1. Implement Phase 1 - Analytics API foundation
2. Implement Phase 2 - Data aggregation logic
3. Implement Phase 3 - Dashboard UI components
4. Implement Phase 4 - Data visualizations
5. Implement Phase 5 - Comprehensive tests
6. Update documentation

## Unresolved Questions

- Dashboard UI sẽ dùng React/TypeScript hay Python-based dashboard?
- Có cần real-time updates qua WebSocket không?
- Data retention policy cho analytics events (90 days như usage_events)?
