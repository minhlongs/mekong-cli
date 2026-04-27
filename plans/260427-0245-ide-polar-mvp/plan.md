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
| 01 | [Backend Gateway Deploy](phase-01-backend-deploy-config.md) | 1-2 ngày | ☐ Pending | Code |
| 02 | [Polar Dashboard Setup](phase-02-polar-products-setup.md) | 1h | ☐ Pending | **Human** |
| 03 | [License Gating Middleware](phase-03-license-gating.md) | 2-3 ngày | ☐ Pending | Code |
| 04 | [IDE UI MVP — CLI-in-browser](phase-04-ide-ui-mvp.md) | 5-7 ngày | ☐ Pending | Code |
| 05 | [E2E Browser Verification](phase-05-e2e-browser-test.md) | 1 ngày | ☐ Pending | Code |

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

## Open questions

1. Polar products đã được tạo trên dashboard chưa? Ai có account access?
2. Domain `api.mekong.dev` đã trỏ Cloudflare chưa? Hay cần cấu hình DNS?
3. Email sender (cho license delivery) dùng gì? Resend/SendGrid/AWS SES?
4. JWT issuer/audience claim format đã chuẩn chưa cho cross-domain (api ↔ ide)?
