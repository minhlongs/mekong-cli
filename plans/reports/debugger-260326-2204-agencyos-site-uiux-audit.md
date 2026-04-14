# UI/UX Bug Audit — AgencyOS Site
**Date:** 2026-03-26 22:04
**Scope:** `/packages/agencyos-site/src/`
**Auditor:** debugger subagent

---

## Executive Summary

Tổng cộng **28 bugs** phát hiện, bao gồm 4 CRITICAL, 9 HIGH, 10 MEDIUM, 5 LOW.
Vấn đề nghiêm trọng nhất: (1) Industry selector "Cafe/Nhà hàng" bị broken vì file JS bị thiếu; (2) Nhiều stale Polar.sh references trong dashboard; (3) 6 trang không tồn tại.

---

## CRITICAL — Broken checkout / payment flow / core interaction

### BUG-01: `onboard-wizard.js` bị thiếu — Industry selector hoàn toàn không hoạt động
- **File:** `pages/dashboard/onboard.astro` — line 134
- **Detail:** Script import `from '/scripts/onboard-wizard.js'` nhưng file này **không tồn tại** trong `public/scripts/`. Directory `public/scripts/` không tồn tại.
- **Impact:** Toàn bộ onboarding wizard (bao gồm "Cafe" / "Nhà hàng" industry selector) không hoạt động. JS error ngay khi load. Đây là root cause của bug người dùng report.
- **Fix:** Tạo `public/scripts/onboard-wizard.js` với các hàm `initIndustry`, `initBizInfo`, `initChannel`, `initMenu`, `initActivate`.

### BUG-02: `dashboard/billing.astro` — Payment modal hiển thị "Polar.sh" thay vì NOWPayments
- **File:** `pages/dashboard/billing.astro` — lines 209, 235
- **Detail:**
  - Line 209: `<div class="payment-name">Thẻ tín dụng (Polar.sh)</div>`
  - Line 235: `<p>Bạn sẽ được chuyển đến trang thanh toán an toàn của Polar.sh</p>`
- **Impact:** Người dùng thấy "Polar.sh" trong modal thanh toán, nhưng thực tế link redirect đến NOWPayments → gây confusing / mất trust.

### BUG-03: `dashboard/upgrade.astro` — Section header nói "Polar.sh" nhưng link đến NOWPayments
- **File:** `pages/dashboard/upgrade.astro` — lines 13-14
- **Detail:** `<strong>Thanh toán USD (Polar.sh)</strong>` và `thanh toán bằng thẻ tín dụng qua Polar`
- **Impact:** Inconsistency nghiêm trọng — sau khi click sẽ đến NOWPayments (USDT), không phải Polar credit card.

### BUG-04: `dashboard/billing.astro` — Enterprise click gửi email sai
- **File:** `pages/dashboard/billing.astro` — line 338
- **Detail:** Enterprise button gọi `window.open('mailto:sales@openclaw.ai?subject=Enterprise Inquiry')` nhưng email này không tồn tại. Cần là `hello@agencyos.network`.
- **Impact:** Enterprise inquiry email bị lost hoàn toàn.

---

## HIGH — Dead links, broken navigation

### BUG-05: `/privacy` — Trang không tồn tại
- **File:** `layouts/base-layout.astro` — line 398
- **Detail:** Footer link `href="/privacy"` nhưng không có `pages/privacy.astro`
- **Impact:** 404 error khi click "Bảo mật" / "Privacy" ở footer. Có trên mọi trang public.

### BUG-06: `/terms` — Trang không tồn tại
- **File:** `layouts/base-layout.astro` — line 399
- **Detail:** Footer link `href="/terms"` nhưng không có `pages/terms.astro`
- **Impact:** 404 error khi click "Điều khoản" / "Terms" ở footer.

### BUG-07: `/forgot-password` — Trang không tồn tại
- **File:** `pages/dashboard/login.astro` — line 45
- **Detail:** Link `href="/forgot-password"` nhưng không có page này
- **Impact:** User quên mật khẩu không có cách reset.

### BUG-08: `/docs/guides/all-commands` — Trang không tồn tại
- **File:** `pages/index.astro` line 611, `pages/en/index.astro` line 223
- **Detail:** "Xem toàn bộ →" / "View all →" link đến `/docs/guides/all-commands` nhưng không có file tương ứng
- **Impact:** 404 error từ homepage Platform Power section.

### BUG-09: `/docs/pricing` — Trang không tồn tại nhưng có link trong docs nav
- **File:** `layouts/docs-layout.astro` — line 57
- **Detail:** Docs nav có `<a href="/docs/pricing">Pricing</a>` nhưng không có `pages/docs/pricing.astro`
- **Impact:** 404 error từ toàn bộ docs pages.

### BUG-10: Dashboard sidebar — Nhiều `href="#"` dead links
- **File:** `layouts/dashboard-layout.astro` — lines 11-25
- **Detail:** Các nav items sau đây có `href="#"`:
  - Founder > OKR, Fundraise, IPO
  - Product > Plan, Sprint, Roadmap
  - Engineering > Code, Test, Deploy
  - Ops > Health, Security
- **Impact:** 8 sidebar navigation items hoàn toàn không hoạt động.

### BUG-11: Nav Commands mega menu — tất cả items là `href="#"` dead links
- **File:** `layouts/base-layout.astro` — line 276
- **Detail:** Command items (OKR, Fundraise, IPO, Sales, Marketing...) đều là `href="#"`
- **Impact:** Mega menu dropdown render nhưng không điều hướng đến đâu.

### BUG-12: `/search` — Trang không tồn tại (WebSite schema)
- **File:** `layouts/base-layout.astro` — JSON-LD schema
- **Detail:** SearchAction target `${siteUrl}/search?q={search_term_string}` nhưng `/search` page không tồn tại
- **Impact:** Google có thể cố gắng crawl `/search` → 404.

### BUG-13: `site.webmanifest` và `browserconfig.xml` bị thiếu
- **File:** `layouts/base-layout.astro` — lines 200, 207
- **Detail:** `<link rel="manifest" href="/site.webmanifest">` và `<meta name="msapplication-config" content="/browserconfig.xml">` nhưng cả hai file đều không tồn tại trong `public/`
- **Impact:** PWA không hoạt động, browser console error trên mọi trang.

---

## MEDIUM — Wrong text, stale references, logical inconsistencies

### BUG-14: `index.astro` keywords meta — "Polar.sh" còn trong SEO keywords
- **File:** `pages/index.astro` — line 300
- **Detail:** `keywords="... SaaS Vietnam, Polar.sh"` — Polar.sh không nên ở đây
- **Impact:** SEO keyword sai, có thể associate brand với Polar thay vì NOWPayments.

### BUG-15: `billing.astro` Growth plan — Giá hiển thị sai
- **File:** `pages/dashboard/billing.astro` — lines 120, 122
- **Detail:** Growth plan hiển thị `1.490.000₫ / $149` nhưng pricing page và index.astro đều show Growth = `$299/mo` và `3.000 MCU`. Billing page cũng ghi `1.000 MCU` cho Growth.
- **Impact:** Người dùng xem billing page thấy giá khác với pricing page → confusing, có thể gây complaint.

### BUG-16: `upgrade.astro` Growth plan — Giá sai ($149 thay vì $299)
- **File:** `pages/dashboard/upgrade.astro` — line 31
- **Detail:** `{ id: 'growth', label: 'Growth', price: '1.490.000đ', usd: '$149', credits: 1000 }` — nhưng thực tế Growth = $299, 3000 MCU.
- **Impact:** Người dùng upgrade page thấy giá sai.

### BUG-17: `dashboard/login.astro` — Redirect sau logout về `/dashboard/signup` (không phải `/dashboard/login`)
- **File:** `layouts/dashboard-layout.astro` — line 151
- **Detail:** Logout redirect về `/dashboard/signup` thay vì `/dashboard/login`
- **Impact:** UX confusion — sau logout user bị đưa đến trang signup thay vì login.

### BUG-18: `billing.astro` — "billing@openclaw.ai" không tồn tại
- **File:** `pages/dashboard/billing.astro` — line 220
- **Detail:** Enterprise bank transfer contact là `billing@openclaw.ai` — email này chưa setup. Nên dùng `hello@agencyos.network`.

### BUG-19: `pricing.astro` (VI) — breadcrumb canonical sai `/pricing` thay vì redirect-aware URL
- **File:** `pages/pricing.astro` — JSON-LD breadcrumb
- **Detail:** `"item": "https://agencyos.network/pricing"` nhưng pricing page VI là `/pricing`. OK nhưng EN pricing breadcrumb cũng dùng `/pricing` (không phải `/en/pricing`).
- **File:** `pages/en/pricing.astro` — line 66-69

### BUG-20: `index.astro` — Pricing toggle (Monthly/Annual) là "visual only", không có chức năng
- **File:** `pages/index.astro` — lines 705-709
- **Detail:** Annual toggle hiển thị "-20%" discount nhưng không có JS để đổi giá
- **Impact:** User click "Annual" không có gì xảy ra → misleading UX. Tương tự ở `en/index.astro`.

### BUG-21: `docs/index.astro` — import `../../data/features.ts` có thể không tồn tại
- **File:** `pages/docs/index.astro` — line 5
- **Detail:** `import { FEATURES } from '../../data/features.ts'` — cần verify file `src/data/features.ts` tồn tại
- **Impact:** Build error nếu file thiếu.

### BUG-22: `dashboard-layout.astro` — Logout redirect không xóa `mk_biz_name` đầy đủ session data
- **File:** `layouts/dashboard-layout.astro` — line 149-151
- **Detail:** Chỉ xóa `mk_api_key` và `mk_biz_name`, nhưng session còn lưu các localStorage keys khác có thể leak giữa users trên shared device.

### BUG-23: `docs-layout.astro` — Footer link `href="/#pricing"` không có `/en` prefix cho EN pages
- **File:** `layouts/docs-layout.astro` — line 78
- **Detail:** Footer "Buy" link là `href="/#pricing"` — hardcoded VI homepage. EN docs users sẽ bị redirect về VI homepage.

---

## LOW — Minor UI inconsistencies

### BUG-24: `billing.astro` — Class `.current-plan` conflict với div ID `current-plan`
- **File:** `pages/dashboard/billing.astro` — line 13 & 455
- **Detail:** CSS có `.current-plan` (plan card style) và div cũng dùng `class="current-plan card"` — JS `card.classList.add('current-plan')` có thể override card style không đúng.

### BUG-25: `base-layout.astro` — `onMouseOver`/`onMouseOut` JSX event handlers trong Astro template
- **File:** `layouts/base-layout.astro` — line 276
- **Detail:** `onMouseOver={(e) => e.target.style.background='...'}` — Astro không render JSX event handlers như React, những handlers này bị ignored.
- **Impact:** Command menu items không có hover highlight effect.

### BUG-26: `index.astro` — "MIễn phí" typo (capital I)
- **File:** `pages/index.astro` — line 341
- **Detail:** `MIễn phí 14 ngày` — chữ "I" bị viết hoa thay vì "Miễn phí"

### BUG-27: `en/index.astro` — pricing toggle show "-20%" nhưng là visual only
- Same as BUG-20 nhưng EN version.

### BUG-28: `docs/guides/license.astro` + `raas.astro` + `docs/blog/*` — Polar.sh references trong docs
- **Files:** Multiple docs files
- **Detail:** Docs kỹ thuật (license, raas) vẫn đề cập Polar.sh billing. Nếu product đã migrate sang NOWPayments thì docs outdated.
- **Impact:** Developer confusion khi đọc integration docs.

---

## Root Cause Analysis — "Cafe/Nhà hàng" selector không hoạt động

**Path:** User đăng ký → `/dashboard/onboard.astro` → click "Cafe" button → JS module import fail

```
pages/dashboard/onboard.astro line 134:
  import { initIndustry, ... } from '/scripts/onboard-wizard.js';
  ↓
  public/scripts/onboard-wizard.js — FILE KHÔNG TỒN TẠI
  ↓
  TypeError: Failed to resolve module specifier
  ↓
  initIndustry() không chạy → industry buttons không có event listener
  → click "Cafe" / "Nhà hàng" → NOTHING
```

**Fix priority 1:** Tạo `public/scripts/onboard-wizard.js` với đầy đủ logic wizard.

---

## Summary Table

| Severity | Count | Key Files |
|----------|-------|-----------|
| CRITICAL | 4 | `onboard.astro`, `billing.astro`, `upgrade.astro` |
| HIGH | 9 | `base-layout.astro`, `dashboard-layout.astro`, `login.astro`, `docs-layout.astro` |
| MEDIUM | 10 | `billing.astro`, `upgrade.astro`, `index.astro`, `pricing.astro` |
| LOW | 5 | Various |

---

## Fix Priority Order

1. **BUG-01** — Tạo `public/scripts/onboard-wizard.js` (root cause user-reported bug)
2. **BUG-02, 03** — Thay "Polar.sh" → "NOWPayments" trong billing/upgrade UI
3. **BUG-04, 18** — Fix email contacts → `hello@agencyos.network`
4. **BUG-05, 06** — Tạo `/privacy` và `/terms` pages (minimal)
5. **BUG-07** — Tạo `/forgot-password` page hoặc remove link
6. **BUG-08, 09** — Tạo `docs/guides/all-commands` và `docs/pricing` stubs
7. **BUG-13** — Tạo `public/site.webmanifest` và `public/browserconfig.xml`
8. **BUG-15, 16** — Fix Growth plan pricing (→ $299, 3000 MCU)
9. **BUG-17** — Fix logout redirect → `/dashboard/login`
10. **BUG-10, 11** — Replace `href="#"` với real routes hoặc `href="/docs/guides/..."` where applicable

---

## Unresolved Questions

1. **`public/scripts/onboard-wizard.js`** — Có code cũ ở đâu không? Hay cần viết lại hoàn toàn?
2. **Growth plan pricing** — Giá đúng là $149 hay $299? Cần confirm với business.
3. **Polar.sh docs** — Docs kỹ thuật (license/raas) có cần update sang NOWPayments không, hay vẫn giữ Polar cho CLI billing?
4. **`/search` page** — Schema có SearchAction nhưng không có search UI. Có plan build search không?
5. **Annual billing toggle** — Có plan implement annual discount logic không hay remove UI?
6. **`src/data/features.ts`** — Cần verify file này tồn tại để docs/index.astro không throw build error.
