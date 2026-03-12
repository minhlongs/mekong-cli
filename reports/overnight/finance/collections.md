# Collections Report — March 2026
**Generated:** 2026-03-12 | **Period:** YTD 2026 | **Status:** Pre-Revenue

---

## Executive Summary

No accounts receivable. No collections activity. Zero customers to date.
This report establishes the collections framework and billing template for
when RaaS credit sales begin. All billing infrastructure is live and ready.

---

## Current AR Status

| Metric              | Value | Notes                          |
|---------------------|-------|--------------------------------|
| Total AR            | $0    | No invoices issued             |
| Current (0–30 days) | $0    | —                              |
| Overdue (31–60)     | $0    | —                              |
| Overdue (61–90)     | $0    | —                              |
| Overdue (90+)       | $0    | —                              |
| Bad Debt Reserve    | $0    | —                              |
| **Total Owed**      | **$0**|                                |

---

## MCU Credit Billing Model (Live — Awaiting First Customer)

The MCU (Mekong Credit Unit) system is fully implemented and ready for collections:

### Credit Pack Tiers

| Tier       | Price/mo | Credits | Per-Credit Cost | Overage    |
|------------|----------|---------|-----------------|------------|
| Starter    | $49      | 200     | $0.245          | N/A        |
| Pro        | $149     | 1,000   | $0.149          | N/A        |
| Enterprise | $499     | Unlimited | —             | N/A        |

### Billing Flow (Implemented)

```
Customer signs up
  → Polar.sh checkout page
  → Webhook fires to src/api/ (Standard Webhooks spec)
  → D1 ledger credited with MCU units
  → Customer can call /v1/missions endpoint
  → Each successful delivery debits MCU ledger
  → Zero balance → HTTP 402 response
  → Customer prompted to top up via Polar.sh
```

### Key Files (Billing Infrastructure)

- `apps/algo-trader/src/jobs/cloudflare-d1-database-client.ts` — ledger storage
- `apps/algo-trader/src/jobs/cloudflare-kv-cache-adapter.ts` — session cache
- `apps/algo-trader/src/jobs/cloudflare-queues-producer-consumer.ts` — async billing events
- `src/api/` — HTTP 402 gateway + Polar webhook handlers

---

## Collections Policy (Template for Future Use)

### Payment Terms
- **Subscription:** Monthly prepaid, auto-renew via Polar.sh
- **Credits:** Non-refundable once consumed
- **Unused credits:** Carry forward 30 days post-billing cycle
- **Enterprise:** Net-30 invoicing available on request

### Dunning Sequence (Polar.sh Managed)

| Day | Action                                    |
|-----|-------------------------------------------|
| 0   | Payment due — auto-charge card on file    |
| 1   | Failed payment — email notification       |
| 3   | Retry charge + warning email              |
| 7   | Account suspended (HTTP 402 on all calls) |
| 14  | Second retry                              |
| 30  | Account terminated, data export offered   |

### Dispute Resolution
- Billing disputes: support@agencyos.network
- Response SLA: 48 hours
- Refund policy: Pro-rated for unused days, enterprise only
- Chargeback handling: Polar.sh manages disputes directly

---

## Revenue Recognition Policy

Per ASC 606 / IFRS 15 (simple SaaS application):

- **Subscription revenue:** Recognized ratably over subscription period
- **Credit packs (prepaid):** Recognized when MCU credit is consumed
- **Enterprise:** Recognized per milestone or monthly ratable (per contract)
- **Refunds:** Deducted from recognized revenue in period issued

---

## Future Collections Metrics (Track from First Customer)

| KPI                        | Target    | Alert Threshold    |
|----------------------------|-----------|--------------------|
| DSO (Days Sales Outstanding)| <5 days  | >15 days           |
| AR > 30 days / Total AR    | 0%        | >5%                |
| Chargeback rate            | <0.1%     | >0.5% (Polar risk) |
| Failed payment rate        | <3%       | >8%                |
| Recovery rate (failed pay) | >80%      | <60%               |

---

## Polar.sh Integration Checklist

- [x] Polar.sh account created
- [x] Products configured (3 tiers)
- [x] Webhook endpoint live
- [x] Standard Webhooks signature verification
- [x] D1 ledger debit/credit handlers
- [x] HTTP 402 zero-balance gate
- [ ] First real transaction — PENDING
- [ ] Dunning email templates — PENDING (Polar.sh default active)
- [ ] Revenue dashboard — PENDING (manual until $1K MRR)

---

## Notes

- No PII stored in Mekong systems. Polar.sh holds all payment data (PCI-compliant).
- Tax collection: Polar.sh handles VAT/GST for international customers (merchant of record model).
- Invoices: Issued automatically by Polar.sh. No manual invoicing needed pre-enterprise.

---

*Next collections review: Upon first customer acquisition.*
