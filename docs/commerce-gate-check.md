# Commerce Gate Check — Weekly Status
**Date:** 2026-07-22  
**Lead:** @sun-tzu (fable) + @kongming  
**Source of truth:** `docs/commerce-playbook.md`

## lock đã chốt

| Module | Status | Evidence |
|--------|--------|----------|
| `docs/commerce-playbook.md` | ✅ Done — thesis + dispatch loop + pricing doctrine | New file |
| `src/raas/billing.py` | ✅ Done — `POLAR_PRODUCT_MAP` mở rộng 5-tier + webhook→topology binding | `:25-34`, `:271-286` |
| `src/binh_phap/topology.py` | ✅ Done — `COMMERCIAL_CHAPTERS`, `record_mrr_event()`, 3 dispatch loops force `STRATEGIC` | `:98`, `:182-184`, `:302-311`, `:386-451` |
| `src/cli/commands/commerce_status.py` | ✅ Done — canonical commerce state view (render verified) | New file |
| `src/raas/revenue_router.py` | ✅ Done — `CREDIT_MAP` 5-tier doctrine | `:30-36` |
| `src/raas/checkout_router.py` | ✅ Done — `interval` field + annual routing | `:38`, `:71-76` |
| `src/raas/nowpayments_router.py` | ✅ Done — IPN router wired | New file |
| `src/gateway.py` | ✅ Done — `nowpayments_router` mounted | `:29`, `:92` |

## blocked / cần manual

| Task | Blocker | Next owner |
|------|---------|------------|
| Swap checkout sang NOWPayments `create_invoice()` | Env vars chưa set trong repo; Sophia setup runtime | Sophia cung cấp env |
| `binh_phap_commands.py` status patch | Indent 1-space constraint; đang dùng `commerce_status.py` thay | Manual patch khi cần |
| VN promo + VietQR activation | Chờ bật trong Polar/NOWPayments dashboard | Manual |

## tuần tới (Week 5+)

1. Sophia set `NOWPAYMENTS_API_KEY` + `NOWPAYMENTS_IPN_SECRET` → mình swap checkout flow
2. Test `/webhooks/nowpayments` IPN end-to-end
3. Activate VN promo (first 100 50% off + early bird $29/mo)
4. Plugin marketplace backend (license API + payout scheduler)
5. Consulting retainer (`mekong goal`) + commercial Binh Phap loop

---
*Neo bởi @kongming. Mọi quyết định tham chiếu `@sun-tzu` (fable) hoặc `src/cli/binh_phap_commands.py`.*
