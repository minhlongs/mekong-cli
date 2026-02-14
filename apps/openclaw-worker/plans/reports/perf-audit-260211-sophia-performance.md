# Performance Audit Report — Sophia AI Factory

**Date:** 2026-02-11 | **Mode:** Auto + 4 Parallel Agents | **Scope:** Bundle Size, Lazy Loading, Image Optimization, Core Web Vitals

---

## Tổng Hợp Findings

| Category | Findings | Fixed | Remaining |
|----------|----------|-------|-----------|
| Bundle Size | 3 | 2 | 1 |
| Lazy Loading | 4 | 0 | 4 |
| Image Optimization | 4 | 1 | 3 |
| Core Web Vitals | 5 | 2 | 3 |

---

## ĐÃ FIX (5 files, mission này)

### 1. `components/ui/floating-element-background-animation.tsx` — DELETED
- **Vấn đề:** Dead code — `FloatingElement` + `FloatingBackground` không được import ở bất kỳ đâu trong app
- **Impact:** Import `framer-motion` vô nghĩa, tăng bundle nếu tree-shaking miss
- **Fix:** Xóa file

### 2. `components/ui/staggered-grid-with-framer-motion.tsx` — DELETED
- **Vấn đề:** Dead code — `StaggeredGrid` không được import ở bất kỳ đâu
- **Impact:** Tương tự file #1
- **Fix:** Xóa file
- **Note:** `framer-motion` vẫn là dependency hợp lệ — 5 file khác dùng (fade-in-view, hero, social-proof, roi-calculator, dashboard-stats)

### 3. `components/video-preview.tsx` — Image + Video Optimization
- **Vấn đề:**
  - `Image` component thiếu `sizes` prop → Next.js gửi ảnh full viewport width
  - `video` element thiếu `preload="metadata"` → browser có thể tải toàn bộ video
- **Fix:**
  - Thêm `sizes="(max-width: 672px) 100vw, 672px"` (max-w-2xl = 672px)
  - Thêm `preload="metadata"` cho video tag

### 4. `dashboard/components/campaign-list.tsx` — Supabase Client Stability
- **Vấn đề:** `createBrowserClient()` gọi trong component body → tạo reference mới mỗi render → `useEffect([supabase])` re-subscribe realtime channel liên tục
- **Fix:** Wrap trong `useMemo()` với `[supabaseUrl, supabaseAnonKey]` dependencies → stable reference

### 5. `components/discovery/filter-panel.tsx` — Range Slider Debounce (INP)
- **Vấn đề:** Range slider `onChange` gọi `onFilterChange()` trên MỌI mouse move → cascade re-render toàn bộ discovery page
- **Fix:** Local state `localMinSps` + `useEffect` debounce 300ms → slider responsive, re-render only khi user dừng kéo

---

## CÒN LẠI (cần mission tiếp theo)

### Bundle Size (1 item)

| # | File | Vấn đề | Fix Recommendation |
|---|------|--------|-------------------|
| 1 | `next.config.ts` | Thiếu `optimizePackageImports` cho `lucide-react` | Thêm `experimental.optimizePackageImports: ['lucide-react']` |

### Lazy Loading (4 items)

| # | File | Vấn đề |
|---|------|--------|
| 1 | 6 dynamic imports | Thiếu `loading` fallback (Skeleton/Spinner) |
| 2 | Setup wizard 4 steps | Imported eagerly — nên chuyển sang `next/dynamic` |
| 3 | `react-markdown` | Static import (~30KB) — chỉ dùng trong guide pages |
| 4 | 15 route segments | Thiếu `loading.tsx` (dashboard đã có 10/10) |

### Image Optimization (3 items)

| # | File | Vấn đề |
|---|------|--------|
| 1 | `next.config.ts` | Thiếu `minimumCacheTTL` cho image cache |
| 2 | Social sharing | Không có OG image (`opengraph-image.tsx`) |
| 3 | `public/` | favicon.ico 25.9KB quá lớn (nên < 5KB) |

### Core Web Vitals (3 items)

| # | File | Vấn đề |
|---|------|--------|
| 1 | `hero.tsx` | LCP: `"use client"` + FadeInView (opacity:0) delay LCP element |
| 2 | Onboarding banner | CLS: Banner dismissal gây layout shift |
| 3 | `pricing-section.tsx` | INP: `alert()` blocks main thread on error |

---

## Điểm Tích Cực

- 21 `next/dynamic` instances — coverage tốt (landing page 8/9 sections dynamic)
- Dashboard 10/10 route segments có `loading.tsx`
- React Compiler enabled — auto-memoization
- `next/font/google` self-hosted — không third-party font request
- AVIF + WebP enabled trong `next.config.ts`
- 0 `<img>` tags — toàn bộ dùng `next/image`
- CSS-only hero background — không ảnh nặng
- `lucide-react` tree-shakeable (chỉ import icons dùng)
- Supabase singleton pattern ở server-side (`createClient()`)

---

**Score tổng thể: 7/10** → Sau fixes: **7.5/10**
