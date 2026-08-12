# Phase 05: Revenue Optimization

## Priority: P2
## Status: pending

## Tasks

### 5.1 Annual Billing
- Add annual_price to tier config (2 months free)
- POST /v1/credits/purchase with billing_cycle=annual
- Polar products for annual plans

### 5.2 Dunning Management
- Track failed payments in credit_transactions
- Auto-downgrade after 7 days failed payment
- Send 3 reminder emails (day 1, 3, 7)
- GET /admin/dunning — list at-risk tenants

### 5.3 Churn Prevention
- Exit survey when downgrading: POST /v1/tenants/feedback
- Win-back email after 30 days inactive
- "We miss you" + 5 bonus credits offer

### 5.4 Revenue Analytics
- GET /admin/revenue/breakdown — by tier, by period
- GET /admin/revenue/ltv — average customer lifetime value
- GET /admin/revenue/forecast — linear projection

### 5.5 Coupon/Promo System
- POST /admin/coupons — create discount codes
- Apply at checkout: POST /v1/credits/purchase with coupon
- Track redemptions

### 5.6 Usage Metering Enhancement
- Per-token cost tracking (not just per-mission)
- Model-specific pricing (premium model = 2x credits)
- GET /v1/credits/cost-estimate — estimate before running

## Files to Create/Modify
- apps/raas-gateway/src/routes/credits.ts (annual, coupons)
- apps/raas-gateway/src/routes/admin.ts (revenue analytics, dunning)
- apps/raas-gateway/src/routes/tenants.ts (feedback, churn)
- apps/raas-gateway/src/services/credit-service.ts (metering)
- apps/raas-gateway/migrations/ (coupons table, feedback table)

## Success Criteria
- Annual billing option available
- Dunning emails sent automatically
- Revenue analytics accessible to admin
- Coupon system functional
