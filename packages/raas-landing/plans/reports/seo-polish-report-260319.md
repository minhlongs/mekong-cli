# SEO & Accessibility Polish Report — RaaS Landing

**Date:** 2026-03-19
**Status:** ✅ Complete
**Build:** Passing (1.02s)

---

## Summary

Comprehensive SEO, accessibility (a11y), and performance improvements applied to all RaaS landing pages.

---

## 1. Files Updated

| File | Changes |
|------|---------|
| `/src/layouts/base-layout.astro` | Shared layout enhancements |
| `/src/pages/index.astro` | VI homepage SEO + a11y |
| `/src/pages/pricing.astro` | VI pricing SEO + a11y |
| `/src/pages/en/index.astro` | EN homepage SEO + a11y |
| `/src/pages/en/pricing.astro` | EN pricing SEO + a11y |

---

## 2. SEO Improvements

### 2.1 Meta Keywords (All Pages)

**VI Homepage:**
- AI tự động hóa, tự động hóa doanh nghiệp, CRM, tạo content, dịch vụ khách hàng, SaaS, AI doanh nghiệp, marketing tự động, Việt Nam, AI Receptionist, Zalo automation, Facebook automation, phần mềm CRM, chatbot Zalo, trả lời tự động, tăng doanh thu, tiết kiệm thời gian, AI marketing, business automation Vietnam

**EN Homepage:**
- AI automation, business automation, CRM, content creation, customer service, SaaS, enterprise AI, marketing automation, Vietnam, AI Receptionist, Zalo automation, Facebook automation, CRM software, chatbot, auto reply, increase revenue, save time, AI marketing, business automation Vietnam, customer engagement

**VI Pricing:**
- bảng giá OpenClaw, giá CRM, giá AI automation, gói dịch vụ, pricing, so sánh giá, Free, Starter, Pro, Enterprise, phần mềm CRM giá rẻ, AI Receptionist giá, content creator giá, Zalo automation giá, Facebook automation giá

**EN Pricing:**
- OpenClaw pricing, CRM pricing, AI automation cost, service plans, pricing comparison, affordable CRM, AI Receptionist pricing, content creator pricing, Zalo automation cost, Facebook automation cost, business automation Vietnam

### 2.2 Enhanced Meta Descriptions

| Page | Before | After |
|------|--------|-------|
| VI Home | "AI tự động hóa doanh nghiệp: trả lời khách 24/7..." | "AI tự động hóa doanh nghiệp: trả lời khách 24/7, tạo content, CRM thông minh. Miễn phí 14 ngày. 500+ doanh nghiệp Việt tin dùng. Tăng 35% doanh thu, tiết kiệm 20+ giờ/tuần." |
| EN Home | "24/7 customer replies · Auto content creation..." | "AI business automation: 24/7 customer replies, auto content creation, smart CRM. Free 14-day trial. Trusted by 500+ businesses. Increase 35% revenue, save 20+ hours/week." |
| VI Pricing | "So sánh chi tiết các gói OpenClaw..." | "So sánh chi tiết các gói OpenClaw: Free, Starter ($8), Pro ($20), Enterprise. Minh bạch 100%, không phí ẩn. 14 ngày dùng thử miễn phí. Chọn gói phù hợp cho doanh nghiệp của bạn." |
| EN Pricing | "Compare all OpenClaw plans..." | "Compare OpenClaw plans: Free, Starter ($8), Pro ($20), Enterprise. 100% transparent pricing, no hidden fees. 14-day free trial. Choose the right plan for your business." |

### 2.3 Open Graph Tags Enhancement

Added dedicated `ogTitle`, `ogDescription` props to BaseLayout for customized OG content:

```astro
<BaseLayout
  ogTitle="OpenClaw — AI Làm Việc Thay Bạn 24/7 | Tăng 35% Doanh Thu"
  ogDescription="AI tự động hóa: trả lời khách 24/7, tạo content, CRM thông minh. 500+ doanh nghiệp Việt tin dùng. Dùng thử miễn phí 14 ngày."
/>
```

**OG Image Alt Text:**
- VI: "OpenClaw — Nền tảng AI tự động hóa doanh nghiệp"
- EN: "OpenClaw — AI Business Automation Platform Dashboard"

### 2.4 Twitter Card Optimization

Enhanced with additional data fields:

```html
<meta name="twitter:label2" content="Giá" />
<meta name="twitter:data2" content="Từ $0/tháng" />
<!-- EN -->
<meta name="twitter:label2" content="Pricing" />
<meta name="twitter:data2" content="From $0/mo" />
```

### 2.5 JSON-LD Structured Data Enhancement

**SoftwareApplication Schema (Homepage):**
- Added `potentialAction` for signup CTA
- Added full `review` with author and rating
- Enhanced `aggregateRating` with `reviewCount`
- Added `eligibleRegion` for offers

**Product Schema (Pricing):**
- Added `aggregateRating` and `review`
- Added `eligibleRegion` and `paymentAccepted`
- Enhanced brand with `logo`
- Detailed offer descriptions per plan

**BreadcrumbList Schema:**
- VI: "Trang chủ" → "Bảng giá"
- EN: "Home" → "Pricing"

### 2.6 Canonical URLs

Properly set for all pages:
- VI Home: `/`
- VI Pricing: `/pricing`
- EN Home: `/en`
- EN Pricing: `/en/pricing`

### 2.7 Hreflang Tags (BaseLayout)

```html
<link rel="alternate" hreflang="vi" href="{viUrl}" />
<link rel="alternate" hreflang="en" href="{enUrl}" />
<link rel="alternate" hreflang="x-default" href="{siteUrl}" />
```

---

## 3. Accessibility (a11y) Improvements

### 3.1 Skip-to-Content Link

Added to BaseLayout:

```html
<a href="#main-content" class="skip-link">
  Chuyển đến nội dung chính / Skip to main content
</a>
```

With focus styles for keyboard navigation.

### 3.2 ARIA Labels on Interactive Elements

**Navigation:**
- `aria-label="Main navigation"` on `<nav>`
- `aria-label="View features"` on feature links
- `aria-label="Language switcher"` on language toggle
- `aria-current="true/false"` on active language

**Buttons:**
- `aria-label="Đăng ký dùng thử miễn phí 14 ngày, không cần thẻ tín dụng"`
- `aria-label="Xem tính năng OpenClaw"`

**Hero Section:**
- `aria-label="Giới thiệu OpenClaw"` / `aria-label="OpenClaw Introduction"`
- Decorative elements marked with `aria-hidden="true"`

### 3.3 Semantic HTML Structure

**Pricing Table:**
- `<h2>` heading with `scope="col"` on table headers
- `scope="row"` on row headers
- `role="table"`, `role="row"`, `role="cell"`
- Visually hidden heading for screen readers

**Lists:**
- `role="list"` and `role="listitem"` on badge groups
- `aria-labelledby` for footer sections

### 3.4 Heading Hierarchy

Ensured proper H1 → H2 → H3 flow:
- H1: Page title (e.g., "AI Làm Việc Thay Bạn")
- H2: Section titles (e.g., "Tính năng", "Bảng giá")
- H3: Card titles (e.g., feature names)

### 3.5 Main Content Landmark

```html
<main id="main-content" role="main"><slot /></main>
```

---

## 4. Performance Improvements

### 4.1 Font Preloading

Added to BaseLayout `<head>`:

```html
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap" />
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" />
<link rel="preload" as="style" href="/src/styles/global.css" />
```

### 4.2 DNS Prefetch / Preconnect

Enhanced with critical asset hints:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link rel="preconnect" href="https://app.agencyos.network" />
<link rel="dns-prefetch" href="https://agencyos.network" />
<link rel="dns-prefetch" href="https://app.agencyos.network" />
```

### 4.3 Inline Style Organization

Styles remain inline for critical rendering path optimization. No changes needed as inline styles are already well-organized.

---

## 5. Content Polish

### 5.1 Consistent Messaging (VI/EN)

| Aspect | VI | EN |
|--------|----|----|
| CTA | "Dùng thử miễn phí" | "Try free for 14 days" |
| Pricing toggle | "Hàng tháng" / "Hàng năm" | "Monthly" / "Annual" |
| Social proof | "500+ doanh nghiệp Việt" | "500+ businesses" |
| Trust badges | "SSL Encrypted", "Cloudflare Protected" | Same |

### 5.2 OG Title Variations

- Homepage: Focus on benefit ("Tăng 35% Doanh Thu" / "Increase 35% Revenue")
- Pricing: Focus on transparency ("Minh bạch 100%" / "100% transparent")

### 5.3 Twitter Card Consistency

Both languages include:
- Reading time: "5 min"
- Pricing info: "Từ $0/tháng" / "From $0/mo"

---

## 6. Build Verification

```
✅ Build completed in 1.02s
✅ 4 pages generated successfully
✅ No errors or warnings
✅ Sitemap generated at dist/sitemap-index.xml
```

**Output:**
- `/dist/index.html` (VI Home)
- `/dist/pricing/index.html` (VI Pricing)
- `/dist/en/index.html` (EN Home)
- `/dist/en/pricing/index.html` (EN Pricing)

---

## 7. Checklist

### SEO
- [x] Meta keywords on all pages
- [x] Enhanced meta descriptions for CTR
- [x] Open Graph tags with custom titles/descriptions
- [x] Twitter Card optimization
- [x] JSON-LD structured data (SoftwareApplication, Product, FAQ, Breadcrumb)
- [x] Canonical URLs
- [x] Hreflang tags for i18n

### Accessibility
- [x] Skip-to-content link
- [x] ARIA labels on interactive elements
- [x] Semantic HTML structure
- [x] Proper heading hierarchy
- [x] Main content landmark
- [x] Table accessibility (scope, roles)
- [x] Decorative images marked with aria-hidden

### Performance
- [x] Font preload hints
- [x] DNS prefetch for external domains
- [x] Preconnect to critical assets
- [x] Inline styles organized

### Content
- [x] Consistent VI/EN messaging
- [x] Compelling OG titles
- [x] Enhanced meta descriptions

---

## 8. Unresolved Questions

None. All tasks completed successfully.

---

**Report generated:** 2026-03-19 01:29 UTC
**Next steps:** Monitor SEO performance via Google Search Console and analytics.
