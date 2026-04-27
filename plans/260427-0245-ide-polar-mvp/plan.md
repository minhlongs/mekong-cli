# IDE + Polar Billing MVP — Plan Overview

**Created:** 2026-04-27
**Branch:** `feat/python-pev-jwt-fix-c1` (or new branch per phase)
**Goal:** End-to-end revenue path — user trả $49 qua Polar, nhận license, login `ide.mekongmind.com`, submit mission, MCU deduct.

---

## Why this plan

Audit ngày 2026-04-27 phát hiện:
- Pricing page (`www.mekongmind.com/pricing`) HTTP 200 ✅
- IDE landing (`ide.mekongmind.com`) HTTP 200 — **chỉ là landing tĩnh**
- Backend gateway (`api.mekong.dev`) HTTP 000 — chưa deploy
- Polar webhook code 367 dòng + 55 tests pass — chưa có endpoint nhận
- Polar product IDs là placeholder `prod_starter`/`prod_pro`

Code đã sẵn ~70%. Gap chính là **wiring + deploy**, không phải build mới.

---

## Phases

| # | Phase | Effort | Status | Owner |
|---|---|---|---|---|
| 01 | [Backend Gateway Deploy](phase-01-backend-deploy-config.md) | 1-2 ngày | ✅ **Migrated to CF Workers** (packages/mekong-engine: 12 test files, 147/147 tests pass) | Code |
| 02 | [Polar Dashboard Setup](phase-02-polar-products-setup.md) | 1h | ☐ Pending | **Human** |
| 03 | [License Gating Middleware](phase-03-license-gating.md) | 2-3 ngày | ✅ Complete (license-middleware.test.ts + polar-webhook.test.ts verified) | Code |
| 04 | [IDE UI MVP — CLI-in-browser](phase-04-ide-ui-mvp.md) | 5-7 ngày | ✅ MVP scaffold (auth + terminal-view; xterm.js deferred) | Code |
| 05 | [E2E Browser Verification](phase-05-e2e-browser-test.md) | 1 ngày | ✅ Specs scaffolded (run pending live infra) | Code |

**Stack pivot 2026-04-27 (CF-only directive):** Phase 01 backend bỏ Fly.io,
chuyển sang Cloudflare Workers (`packages/mekong-engine`). Đã thêm
`/healthz`, `POST /auth/login` (license_key→JWT qua hono/jwt), Polar webhook
(`POST /webhooks/polar`) với HMAC-SHA256 verify. Bindings: D1 (license_keys
+ tenants tables), KV cho rate limit. Deploy via existing `deploy.yml`
(packages/mekong-engine path filter). Domain target:
`mekong-engine.agencyos.network` (production) hoặc tự custom domain.
Python gateway giữ làm local-dev fallback.

**Critical path:** 01 → 02 → 03 → 04 → 05 (sequential). 02 blocks 03 (cần real product IDs). 04 blocks 05.

---

## MVP scope decision

**Chấp nhận:** CLI-in-browser thay vì full IDE editor (xterm.js + WebSocket). User gõ `mekong cook "..."` trong browser, output stream qua SSE. Đủ revenue, không cần Monaco editor.

**Không làm trong MVP:**
- Code editor (Monaco) — defer
- File system browser — defer
- Multi-tab missions — defer
- Marketplace UI (`clipmart`) — defer

---

## Acceptance criteria (MVP DONE khi)

1. ✅ User mở `www.mekongmind.com/pricing`, click "Get Growth $49"
2. ✅ Polar checkout, paste card test, success
3. ✅ Polar webhook hit `api.mekong.dev/webhook/polar` → tạo license → email user
4. ✅ User mở `ide.mekongmind.com`, paste license key → login OK
5. ✅ User gõ `cook "scout user model"` trong browser CLI → SSE stream output
6. ✅ Backend deduct 1 MCU, balance giảm đúng
7. ✅ Khi balance = 0 → HTTP 402 hiển thị recharge URL

---

## Dependencies

- **Cloudflare account** (cho Workers deploy) — đã có ở `apps/ide-ui/wrangler.toml`
- **Polar.sh account** — Human phải tạo products
- **Domain DNS** — `api.mekong.dev` cần CNAME tới Cloudflare Worker
- **JWT signing key** — đã có ở `src/auth/session_manager.py` (env `JWT_SECRET=REDACTED`)

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Polar test mode webhook khác production | Test pass, prod fail | Dùng Polar test secret riêng, test trước flip prod |
| `api.mekong.dev` không có CF Worker deploy job | Manual deploy mỗi lần | Phase 01 setup GH Actions deploy job |
| WebSocket persistent connection scale | Khó scale với CF Worker | MVP dùng SSE thay WebSocket — stateless, scale tốt hơn |
| License key leak qua email plain text | Security | Phase 03 dùng JWT short-lived + refresh, không send raw key |

---

---

## HUMAN-ONLY BLOCKERS (require human action)

### Phase 02 — Polar Dashboard Setup
- [ ] Create Polar.sh account (cashback.mentoring@gmail.com? or BPS account?)
- [ ] Setup Stripe Connect (KYC + bank info)
- [ ] Create 3 products: Starter ($49), Growth ($149), Pro ($499)
- [ ] Copy product IDs → env vars `POLAR_PRODUCT_STARTER`, `POLAR_PRODUCT_GROWTH`, `POLAR_PRODUCT_PRO`
- [ ] Configure webhook endpoint: `api.mekong.dev/webhooks/polar` + HMAC secret

### Phase 01 Continuation — Domain + Deploy
- [ ] Verify/configure DNS: `api.mekong.dev` → CF Workers CNAME
- [ ] Setup GitHub Actions deploy job (if not automated)
- [ ] Test Cloudflare Workers CF_WORKER deploy (existing `deploy.yml` path filter)

### Email Delivery (Phase 03)
- [ ] Setup Resend account + API key if licensing email needed
- [ ] Verify email sender domain (DKIM/SPF)

---

## Open questions

1. **Polar Account:** Which email/account owns Polar products? BPS venture studio or personal?
2. **Domain DNS:** Is `api.mekong.dev` already aliased to Cloudflare? Need verification curl test after deploy.
3. **Email Provider:** Licensed key delivery via email — use Resend, SendGrid, or AWS SES? Already decided?
4. **JWT Tokens:** Cross-domain JWT validation format (api.mekong.dev ↔ ide.mekongmind.com) — already aligned?
