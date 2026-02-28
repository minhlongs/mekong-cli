# Research: PostHog + GrowthBook cho WellNexus CRO

## 1. PostHog React/Vite Integration

### Setup
- Package: `posthog-js` + `posthog-js/react` (React provider)
- Init trong `main.tsx` với `PostHogProvider`
- API key via `VITE_POSTHOG_KEY`, host via `VITE_POSTHOG_HOST`
- EU cloud hoặc self-hosted cho data residency

### Core Features cần dùng
- **Autocapture**: Tự track clicks, pageviews, form submissions
- **Session Replay**: Xem user behavior thực tế trên landing page
- **Feature Flags**: Server-side eval, multi-variate experiments
- **Funnels**: Định nghĩa conversion path → visualize drop-off
- **Heatmaps**: Toolbar click/scroll heatmaps

### Best Practices
- Wrap `PostHogProvider` ở root, dưới `ThemeProvider`
- Identify user sau login: `posthog.identify(userId, {email, plan})`
- Track custom events: `posthog.capture('pricing_view', {tier})`
- Group analytics by company/team cho B2B
- Sampling: 100% events, 50% session replay cho production

## 2. GrowthBook A/B Testing

### Setup
- Package: `@growthbook/growthbook-react`
- `GrowthBookProvider` wrap app, connect PostHog as data source
- Features/experiments managed via GrowthBook dashboard
- SDK key via `VITE_GROWTHBOOK_CLIENT_KEY`

### Integration PostHog → GrowthBook
- GrowthBook dùng PostHog events làm metric source
- Experiment exposure tracked via PostHog feature flag events
- Bayesian stats engine trong GrowthBook xử lý significance

### Use Cases WellNexus
- A/B test hero copy (Vietnamese vs English-first)
- Pricing page layout variants
- CTA button text/color tests
- Signup flow variants (với/không referral code)

## 3. CRO Funnel Pattern

### Conversion Funnel WellNexus
```
Landing (/) → Pricing Section (scroll) → CTA Click → Signup (/signup)
→ Dashboard (/dashboard) → First Purchase (/marketplace)
```

### PostHog Events cần track
| Event | Properties | Funnel Step |
|-------|-----------|-------------|
| `$pageview` | path=/ | 1. Landing |
| `pricing_section_viewed` | - | 2. Pricing View |
| `cta_clicked` | button, location | 3. CTA |
| `signup_started` | source, referral | 4. Signup Start |
| `signup_completed` | method | 5. Signup Done |
| `first_purchase` | product, amount | 6. Conversion |

### Drop-off Analysis
- Pricing → CTA: Test glassmorphism card hover vs static
- CTA → Signup: Test form length (minimal vs full)
- Signup → Dashboard: Test onboarding flow

## 4. Privacy / GDPR

### Việt Nam Context
- Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân
- Cần cookie consent banner
- PostHog hỗ trợ: `opt_out_capturing()`, `has_opted_in()`
- Respect `Do Not Track` header

### Implementation
- Cookie consent component trước PostHog init
- Disable session replay nếu user opt-out
- Anonymize IP trong PostHog project settings
- Data retention: 90 ngày default, có thể tùy chỉnh
