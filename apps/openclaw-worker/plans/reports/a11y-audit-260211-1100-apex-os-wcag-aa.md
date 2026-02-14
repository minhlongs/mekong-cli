# WCAG 2.1 AA Accessibility Audit — apex-os

**Date:** 2026-02-11 | **Files scanned:** 321 TSX/JSX | **Mission:** 1/N (max 5 file/mission)

---

## ĐÃ SỬA (5 file)

### 1. `src/components/os/sidebar.tsx`
| Fix | WCAG | Chi tiết |
|-----|------|---------|
| Collapse toggle buttons | 4.1.2 | Thêm `aria-label` + `aria-expanded`, thay Users icon → ChevronRight/Left |
| Nav links khi collapsed | 4.1.2, 1.1.1 | Đổi `title` → `aria-label` (screen readers không đọc `title` đáng tin) |
| Logout button khi collapsed | 4.1.2 | Đổi `title` → `aria-label` |
| Upgrade link khi collapsed | 4.1.2 | Đổi `title` → `aria-label` |

### 2. `src/components/os/dock.tsx`
| Fix | WCAG | Chi tiết |
|-----|------|---------|
| Icon-only links | 4.1.2, 1.1.1 | Thêm `aria-label={item.label}` cho mỗi Link |
| Navigation landmark | 2.4.1 | Đổi `<div>` → `<nav aria-label="Quick navigation">` |
| Active state | 1.3.1 | Thêm `aria-current="page"` cho active link |
| Tooltip decorative | 1.3.1 | Thêm `aria-hidden="true"` cho tooltip (tránh đọc trùng) |

### 3. `src/components/pricing/PricingModal.tsx`
| Fix | WCAG | Chi tiết |
|-----|------|---------|
| Modal role | 4.1.2 | Thêm `role="dialog"` + `aria-modal="true"` |
| Modal label | 4.1.2 | Thêm `aria-labelledby="pricing-modal-title"` + `id` cho h2 |

### 4. `src/components/checkout/UpgradeModal.tsx`
| Fix | WCAG | Chi tiết |
|-----|------|---------|
| Modal role | 4.1.2 | Thêm `role="dialog"` + `aria-modal="true"` |
| Modal label | 4.1.2 | Thêm `aria-labelledby="upgrade-modal-title"` + `id` cho h2 |

### 5. `src/app/[locale]/layout.tsx`
| Fix | WCAG | Chi tiết |
|-----|------|---------|
| Skip nav target | 1.3.1, 2.4.1 | Đổi `<div id="main-content">` → `<main id="main-content">` |

---

## CHƯA SỬA (10 file — mission tiếp theo)

| # | File | Vấn đề | WCAG |
|---|------|--------|------|
| 1 | `src/app/layout.tsx` | Hardcoded `lang="en"` — cần dynamic theo locale | 3.1.1 |
| 2 | `src/app/[locale]/dashboard/wallet/page.tsx` | 2 modal (deposit + withdraw) thiếu `role="dialog"` | 4.1.2 |
| 3 | `src/components/dashboard/SignalInspector.tsx` | Modal thiếu `role="dialog"` | 4.1.2 |
| 4 | `src/components/dashboard/ConnectExchange.tsx` | Modal thiếu `role="dialog"` | 4.1.2 |
| 5 | `src/components/admin/AdminExchangeManager.tsx` | Modal thiếu `role="dialog"` + close button thiếu `aria-label` | 4.1.2 |
| 6 | `src/app/[locale]/settings/page.tsx` | Modal thiếu `role="dialog"` | 4.1.2 |
| 7 | `src/app/[locale]/admin/providers/components/AuditLogViewer.tsx` | Modal thiếu `role="dialog"` | 4.1.2 |
| 8 | `src/components/IndicatorPanel.tsx` | Toggle button thiếu `aria-expanded` | 4.1.2 |
| 9 | `src/components/dashboard/SmartSwitchWizard.tsx` | Progress bar thiếu `role="progressbar"` + aria-value* | 4.1.2, 1.3.1 |
| 10 | `src/components/ai/AIChat.tsx` | Chat area thiếu `aria-live` + dùng deprecated `onKeyPress` | 4.1.3, 2.1.1 |

---

## PASS (Không có vấn đề)

- Alt text: 3/3 images đều có alt ✅
- Form labels: Tất cả form đã có label associations ✅
- Skip navigation: Đã có skip link (đã fix target semantic) ✅

## GHI CHÚ

- Build fail do Sentry MODULE_NOT_FOUND (pre-existing, không liên quan a11y changes)
- TypeScript compilation: 0 errors cho các file đã sửa
- Color contrast cần runtime testing (Lighthouse/aXe) — không thể verify qua code review
