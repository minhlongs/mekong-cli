<!-- CLEO:START -->
@.cleo/templates/AGENT-INJECTION.md
<!-- CLEO:END -->

# AgencyOS Landing — 第五篇 兵勢 (Bing Shi) — First Impression Force

> **Inherits**: `../../CLAUDE.md` (Root Constitution)
> **Domain**: Public-facing marketing landing page for RaaS ecosystem
> **Binh Phap**: 兵勢 — Strategic momentum: the landing page IS the first strike, conversion is victory

## Core Rules

- Performance: Lighthouse > 90, LCP < 2.5s
- SEO: meta tags, structured data, OG images mandatory
- Responsive: mobile-first, all MD3 breakpoints
- Accessibility: WCAG 2.1 AA minimum
- i18n: Vietnamese primary, English secondary
- Payment: Polar.sh ONLY (no PayPal)

## Quality Gates

```bash
npm run build          # 0 errors
npm run lint           # 0 warnings
```

## Development Standards

- Follow ClaudeKit engineer standards
- Type safety: zero `any` types
- File size: < 200 lines per component
- Kebab-case file naming
- All CTA buttons must track analytics events
