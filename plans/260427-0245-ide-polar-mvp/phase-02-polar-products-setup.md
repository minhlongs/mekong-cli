# Phase 02: Polar Dashboard Setup

**Priority:** P0 — Blocks Phase 03
**Status:** ☐ Pending
**Effort:** 1h
**Owner:** **HUMAN** — Claude không có quyền tạo Polar account/products

## Context Links

- `src/api/polar_webhook.py:32` — `POLAR_WEBHOOK_SECRET` env var
- `src/polymarket/billing.py:40-42` — product ID → tier mapping (currently placeholders)
- `.env.example:50-51` — Polar env vars expected

## Overview

Code Polar webhook đã ready (367 lines, 55 tests pass). Phase này yêu cầu **người vận hành** tạo products thật trên Polar dashboard và copy IDs vào env.

## Why Human-Only

Polar dashboard yêu cầu:
- Email login + 2FA
- Stripe Connect cho payout (KYC)
- Bank account info
- Manual product creation UI

Không có Polar Admin API public cho create-product flows.

## Checklist (Human Action Required)

### Step 1: Create Polar Account

- [ ] Truy cập https://polar.sh/signup
- [ ] Đăng ký với email Binh Phap Venture Studio
- [ ] Verify 2FA
- [ ] Connect Stripe (KYC + bank info — ~30 phút)
- [ ] Create organization "Mekong CLI" hoặc "Binh Phap"

### Step 2: Create Products

Dashboard → Products → New Product cho mỗi tier:

| Product Name | Price | Billing | Description |
|---|---|---|---|
| Mekong Starter | $49/mo | Recurring monthly | 200 MCU/month, 1 user |
| Mekong Growth | $149/mo | Recurring monthly | 1,000 MCU/month, 3 users |
| Mekong Pro | $499/mo | Recurring monthly | 5,000 MCU/month, 10 users |

Sau khi tạo, mỗi product có ID format `prod_xxxxx`. Copy 3 IDs.

### Step 3: Webhook Endpoint

Dashboard → Settings → Webhooks → Add Webhook:

- URL: `https://api.mekong.dev/webhook/polar` (cần Phase 01 deploy xong)
- Events: tick all (`subscription.created`, `subscription.cancelled`, `subscription.updated`, `order.created`)
- Secret: dashboard generate ngẫu nhiên — **copy ngay**, chỉ hiện 1 lần

### Step 4: Update Environment

Trên Fly.io (production):
```bash
flyctl secrets set \
  POLAR_WEBHOOK_SECRET="whsec_xxx" \
  POLAR_STARTER_PRODUCT_ID="prod_xxx_starter" \
  POLAR_GROWTH_PRODUCT_ID="prod_xxx_growth" \
  POLAR_PRO_PRODUCT_ID="prod_xxx_pro" \
  -a mekong-gateway
```

Update local `.env` (dev):
```env
POLAR_WEBHOOK_SECRET=whsec_test_xxx
POLAR_STARTER_PRODUCT_ID=prod_xxx_starter
POLAR_GROWTH_PRODUCT_ID=prod_xxx_growth
POLAR_PRO_PRODUCT_ID=prod_xxx_pro
```

### Step 5: Test Mode First

- [ ] Polar dashboard → toggle to "Test mode"
- [ ] Tạo test products (sandbox prices, $1 hoặc $0.50)
- [ ] Test webhook delivery với Stripe test card `4242 4242 4242 4242`
- [ ] Verify webhook hit `/webhook/polar` returns 200 (Fly.io logs)
- [ ] Sau khi pass, chuyển sang Live mode + real prices

### Step 6: Update Code Mapping

File `src/polymarket/billing.py:40-42` hiện tại:
```python
os.getenv("POLAR_STARTER_PRODUCT_ID", "prod_starter"): "starter",
os.getenv("POLAR_PRO_PRODUCT_ID", "prod_pro"): "pro",
os.getenv("POLAR_ENTERPRISE_PRODUCT_ID", "prod_enterprise"): "elite",
```

Cần thêm `POLAR_GROWTH_PRODUCT_ID` mapping → tier `"growth"`. (Code change sẽ ở Phase 03.)

## Success Criteria

- 3 products tạo trên Polar (Starter/Growth/Pro)
- Webhook secret đã set vào Fly.io secrets
- Test webhook thành công (signature verify pass, event logged)
- Documents in `docs/polar-setup.md` (Phase 03 sẽ tạo) chứa product IDs

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Stripe Connect KYC delay | Có thể cần 1-3 ngày verify; chuẩn bị giấy tờ trước |
| Webhook secret leak | Rotate ngay nếu nghi lộ; Polar cho phép regenerate |
| Test mode → Live mode quên flip | Checklist deploy ghi rõ; CI/CD env var khác |

## Open Questions

- Polar phí gì? (đọc https://polar.sh/pricing)
- Có cần Stripe Connect Standard hay Express? (Express dễ hơn, ít KYC)
- Refund policy khi user huỷ giữa chừng?

## Next Steps

Sau Phase 02 done → Phase 03 wire license gating + update product mapping in code.
