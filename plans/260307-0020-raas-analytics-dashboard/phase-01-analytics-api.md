---
title: "Phase 1 - Analytics API"
description: "Analytics service core và FastAPI routes"
status: pending
priority: P1
effort: 2h
parent: 260307-0020-raas-analytics-dashboard
---

# Phase 1 - Analytics API

## Context Links
- Parent Plan: [plan.md](../plan.md)
- Reference: `/Users/macbookprom1/mekong-cli/apps/algo-trader/src/analytics/revenue-analytics.ts`
- Usage Tracker: `src/usage/usage_tracker.py`
- Repository: `src/db/repository.py`

## Overview
Tạo Analytics API foundation với service layer và API routes cho revenue tracking, user metrics, và ROI calculation.

## Key Insights
- Reference implementation từ algo-trader/src/analytics/revenue-analytics.ts (TypeScript)
- Port sang Python với async/await pattern tương tự
- Sử dụng LicenseRepository có sẵn cho data access

## Requirements

### Functional
- MRR (Monthly Recurring Revenue) calculation
- DAL (Daily Active Licenses) tracking
- Churn rate analysis
- Revenue by tier breakdown
- ROI calculation per license
- Usage aggregation

### Non-Functional
- Async operations cho performance
- Type hints đầy đủ
- Error handling với proper logging
- Response schemas với Pydantic

## Architecture

```
src/analytics/
├── raas_analytics.py       # Main analytics service
├── roi_calculator.py       # ROI calculation engine
└── __init__.py

src/api/routes/
├── analytics_routes.py     # FastAPI analytics endpoints
```

## Related Code Files

### Files to Create
- `src/analytics/raas_analytics.py` - Analytics service core
- `src/analytics/roi_calculator.py` - ROI calculation logic
- `src/analytics/__init__.py` - Module exports
- `src/api/routes/analytics_routes.py` - API routes

### Files to Modify
- `src/db/repository.py` - Add analytics query methods
- `src/api/app.py` - Register analytics routes

## Implementation Steps

### Step 1: Analytics Service Core
Tạo `src/analytics/raas_analytics.py` với:
- `RaaSAnalyticsService` class (singleton pattern)
- `get_mrr(month: str)` - Monthly Recurring Revenue
- `get_dal(date: str)` - Daily Active Licenses
- `get_churn_rate(month: str)` - Churn rate calculation
- `get_revenue_by_tier(month: str)` - Revenue breakdown
- `get_usage_summary(key_id: str, days: int)` - Usage aggregation

### Step 2: ROI Calculator
Tạo `src/analytics/roi_calculator.py` với:
- `ROICalculator` class
- `calculate_roi(key_id: str, period_days: int)` - ROI calculation
- `get_time_saved(key_id: str)` - Time savings metrics
- `get_cost_comparison(key_id: str)` - Build vs buy analysis
- `get_value_metrics(key_id: str)` - Value demonstration

### Step 3: Repository Extensions
Thêm vào `src/db/repository.py`:
- `get_revenue_events(month: str)` - Revenue event queries
- `get_active_licenses(date: str)` - Active license queries
- `get_cancellations(month: str)` - Cancellation queries
- `get_usage_aggregation(key_id: str, days: int)` - Usage stats

### Step 4: API Routes
Tạo `src/api/routes/analytics_routes.py` với:
- `GET /api/v1/analytics/revenue` - Revenue metrics
- `GET /api/v1/analytics/active-licenses` - DAL metric
- `GET /api/v1/analytics/churn` - Churn rate
- `GET /api/v1/analytics/by-tier` - Revenue by tier
- `GET /api/v1/analytics/roi/{key_id}` - ROI calculation
- `GET /api/v1/analytics/usage-summary/{key_id}` - Usage summary

## Todo List
- [ ] Create `src/analytics/raas_analytics.py`
- [ ] Create `src/analytics/roi_calculator.py`
- [ ] Create `src/analytics/__init__.py`
- [ ] Add repository methods to `src/db/repository.py`
- [ ] Create `src/api/routes/analytics_routes.py`
- [ ] Register routes in `src/api/app.py`
- [ ] Add Pydantic response schemas
- [ ] Add error handling and logging

## Success Criteria
- [ ] All analytics endpoints respond correctly
- [ ] MRR calculation accurate
- [ ] DAL calculation correct
- [ ] Churn rate calculation correct
- [ ] ROI calculation meaningful
- [ ] No circular imports
- [ ] Type hints complete
- [ ] Logging comprehensive

## Risk Assessment
- **Data accuracy**: Test với sample data để verify calculations
- **Performance**: Use caching cho expensive queries
- **Complexity**: Keep formulas simple, iterate sau

## Security Considerations
- Admin-only access cho analytics endpoints (ADMIN tier license)
- Rate limiting cho API endpoints
- No sensitive data exposure trong responses

## Next Steps
- Phase 2: Data Aggregation
- Phase 3: Dashboard UI
