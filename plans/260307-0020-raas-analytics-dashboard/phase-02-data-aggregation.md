---
title: "Phase 2 - Data Aggregation"
description: "Aggregate usage data, revenue calculations, user activity metrics"
status: pending
priority: P2
effort: 2h
parent: 260307-0020-raas-analytics-dashboard
---

# Phase 2 - Data Aggregation

## Context Links
- Phase 1: [phase-01-analytics-api.md](./phase-01-analytics-api.md)
- Usage Metering: `src/lib/usage_metering_service.py`
- Usage Tracker: `src/usage/usage_tracker.py`

## Overview
Implement data aggregation logic để aggregate usage data, calculate revenue, và user activity metrics từ Phase 4 usage events.

## Key Insights
- Phase 4 đã có `usage_events` table với command/feature tracking
- Subscription data từ Polar/Stripe webhooks (Phase 3)
- Cần aggregate data theo ngày/tuần/tháng cho analytics

## Requirements

### Functional
- Aggregate usage events theo thời gian (daily, weekly, monthly)
- Calculate revenue từ subscription + overage charges
- User activity metrics (active users, session counts)
- Caching layer cho performance optimization

### Non-Functional
- Efficient SQL queries với indexes
- Cache invalidation strategy
- Background job cho aggregation (optional)

## Architecture

```
┌─────────────────────────────────────────────┐
│           Data Aggregation Layer             │
├─────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐        │
│  │   Usage      │  │   Revenue    │        │
│  │  Aggregator  │  │  Aggregator  │        │
│  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                 │
│  ┌──────▼─────────────────▼──────┐         │
│  │    Aggregation Service         │         │
│  │    (src/analytics/aggregator)  │         │
│  └──────┬─────────────────────────┘         │
│         │                                   │
│  ┌──────▼───────┐  ┌──────────────┐        │
│  │   Cache      │  │  Repository  │        │
│  │   Layer      │  │   Queries    │        │
│  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────┘
```

## Related Code Files

### Files to Create
- `src/analytics/aggregator.py` - Main aggregation service
- `src/analytics/cache.py` - Caching layer
- `src/db/queries/analytics_queries.py` - Analytics-specific queries

### Files to Modify
- `src/db/repository.py` - Add aggregation methods

## Implementation Steps

### Step 1: Usage Aggregation
Tạo aggregation methods:
- `aggregate_usage_by_day(key_id: str, month: str)` - Daily usage
- `aggregate_usage_by_feature(key_id: str, days: int)` - Feature breakdown
- `aggregate_usage_by_command(key_id: str, days: int)` - Command breakdown
- `get_top_features(limit: int)` - Top used features
- `get_top_commands(limit: int)` - Top used commands

### Step 2: Revenue Aggregation
Revenue calculations:
- `calculate_mrr(month: str)` - Monthly Recurring Revenue
- `calculate_arr(year: str)` - Annual Recurring Revenue
- `calculate_usage_revenue(month: str)` - Overage charges
- `aggregate_revenue_by_tier(month: str)` - Tier breakdown

### Step 3: Activity Metrics
User activity tracking:
- `get_daily_active_users(date: str)` - DAL metric
- `get_weekly_active_users(week: str)` - WAL metric
- `get_monthly_active_users(month: str)` - MAL metric
- `get_user_retention_rate(months: int)` - Retention rate

### Step 4: Caching Layer
Cache implementation:
- In-memory cache với TTL
- `get_cached(key: str)` - Get cached data
- `set_cached(key: str, data: Any, ttl: int)` - Set cache
- `invalidate_cache(pattern: str)` - Cache invalidation
- Auto-refresh cache cho periodic data

## Todo List
- [ ] Create `src/analytics/aggregator.py`
- [ ] Create `src/analytics/cache.py`
- [ ] Create `src/db/queries/analytics_queries.py`
- [ ] Implement usage aggregation methods
- [ ] Implement revenue aggregation methods
- [ ] Implement activity metrics methods
- [ ] Implement caching layer
- [ ] Add cache invalidation logic
- [ ] Test aggregation accuracy

## Success Criteria
- [ ] Aggregation queries return correct data
- [ ] Cache hit rate > 80% for common queries
- [ ] Query response time < 100ms (cached)
- [ ] Query response time < 1s (uncached)
- [ ] No N+1 query issues
- [ ] Memory usage reasonable

## Risk Assessment
- **Memory usage**: Giới hạn cache size, eviction policy
- **Data staleness**: TTL appropriate cho từng loại data
- **Query performance**: Add indexes cho analytics queries

## SQL Indexes

```sql
-- Usage events indexes
CREATE INDEX IF NOT EXISTS idx_usage_events_created_at
ON usage_events(created_at);

CREATE INDEX IF NOT EXISTS idx_usage_events_key_id_created
ON usage_events(key_id, created_at);

CREATE INDEX IF NOT EXISTS idx_usage_events_event_type
ON usage_events(event_type, created_at);

-- License indexes
CREATE INDEX IF NOT EXISTS idx_licenses_tier
ON licenses(tier);

CREATE INDEX IF NOT EXISTS idx_licenses_created_at
ON licenses(created_at);
```

## Next Steps
- Phase 3: Dashboard UI
- Phase 4: Visualizations
