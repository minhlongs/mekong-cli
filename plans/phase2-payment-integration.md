# ROIaaS PHASE 2: PAYMENT INTEGRATION

**Date:** 2026-03-05 18:27
**Priority:** HIGH

---

## 🎯 Objectives

1. **Polar.sh Integration** - Payment processing for license tiers
2. **Multi-region License Validation** - Global license key verification
3. **Webhook Handling** - Subscription events, payment success/failure

---

## 📋 Scope

### Part 1: Polar.sh Payment Integration

| Component | File | Description |
|-----------|------|-------------|
| Payment Service | `src/raas/payment_service.py` | Polar.sh API client |
| Webhook Handler | `src/raas/webhook_handler.py` | Subscription events |
| Billing Models | `src/raas/models/billing.py` | Subscription, Invoice |

### Part 2: Multi-region License Validation

| Component | File | Description |
|-----------|------|-------------|
| License Server | `apps/raas-license-server/` | Centralized validation |
| Edge Functions | `apps/raas-edge/` | Cloudflare Workers for global validation |
| Cache Layer | `src/raas/cache.py` | Redis-backed license cache |

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|------------|
| Payment | Polar.sh API |
| Edge | Cloudflare Workers |
| Cache | Redis (Upstash) |
| Database | Supabase PostgreSQL |

---

## 📊 License Tiers

| Tier | Price/month | Features |
|------|-------------|----------|
| FREE | $0 | Core agents only |
| PRO | $29 | All premium agents, 100K tokens |
| ENTERPRISE | $299 | Unlimited, priority support, SSO |

---

## 🔒 Security Requirements

1. **Signed License Keys** - RSA-256 signature verification
2. **Hardware Fingerprinting** - Bind license to machine
3. **Rate Limiting** - Prevent brute-force validation
4. **Audit Logging** - Track all validation attempts

---

## 📝 Implementation Plan

### Phase 2A: Polar.sh Integration (Week 1)

1. Create Polar.sh products & prices
2. Implement checkout flow
3. Handle webhook events
4. Update license tiers based on payment

### Phase 2B: Multi-region Validation (Week 2)

1. Deploy edge functions (Cloudflare)
2. Add Redis caching layer
3. Implement RSA signature verification
4. Add hardware fingerprinting

---

## 🧪 Testing Requirements

- [ ] Payment webhook tests
- [ ] License validation tests
- [ ] Rate limiting tests
- [ ] Edge function tests

---

## 📈 Success Metrics

| Metric | Target |
|--------|--------|
| Payment success rate | >95% |
| License validation latency | <100ms |
| Edge cache hit rate | >90% |
| Failed validation rate | <1% |

---

*Plan created: 2026-03-05*
