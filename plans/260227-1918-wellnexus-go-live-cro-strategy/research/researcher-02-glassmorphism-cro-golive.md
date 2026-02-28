# Research: Glassmorphism 2.0 + CRO + Go-Live Checklist

## 1. Glassmorphism 2.0 (2025-2026)

### Evolution từ v1
- **V1**: Simple blur + transparency → flat feeling
- **V2**: Multi-layer depth + gradient borders + glow effects + micro-interactions
- WellNexus đã implement Aura Elite = Glassmorphism 2.0 foundation

### CRO-Optimized Patterns
- **Pricing cards**: Accent glass cho recommended tier + glow effect → +23% CTR (industry benchmark)
- **CTA buttons**: Gradient accent + hover glow + translateY → draws attention
- **Trust badges**: Glass-light background → subtle but visible
- **Testimonials**: Glass cards with avatar border glow

### Dark Theme Luxury Branding
- WellNexus palette (#0f0f1e → #1a1a2e) = premium positioning
- Purple accent (#667eea → #764ba2) = trust + innovation
- Dual theme (dark/light) already implemented → good for accessibility

## 2. SaaS Landing CRO Patterns

### Hero Section (above fold)
- Clear value proposition trong 5 giây
- Single CTA button (gradient accent)
- Social proof ngay dưới hero (logos, stats)
- Benchmark: Hero → CTA click = 3-7% conversion

### Pricing Table Optimization
- 3-4 tiers maximum
- Highlight recommended tier (accent glass + badge)
- Annual vs Monthly toggle
- Feature comparison table dưới pricing cards
- Money-back guarantee badge

### Social Proof Patterns
- Customer count / revenue stats
- Testimonial carousel với glassmorphism cards
- Trust badges (security, payment providers)
- "As seen in" media logos

### CTA Best Practices
- Action-oriented text: "Bắt Đầu Miễn Phí" > "Đăng Ký"
- Contrast color (accent gradient trên dark bg)
- Micro-interaction: hover scale + glow
- Urgency elements (limited slots, countdown)

## 3. Framer Motion Micro-interactions

### High-Impact Animations
- **Scroll reveal**: `whileInView` + stagger children → +15% engagement
- **Hover effects**: `whileHover={{ scale: 1.02, y: -4 }}` trên cards
- **Number counters**: `useSpring` cho stats animation
- **Parallax**: Subtle background movement on scroll

### Performance Rules
- `will-change: transform` cho animated elements
- `layout` prop chỉ khi cần layout animations
- `prefers-reduced-motion` respect (đã có trong design system)
- Lazy load animations below fold

## 4. Go-Live Technical Checklist

### SEO (Critical)
- [x] Meta tags (react-helmet-async) — đã có
- [x] robots.txt + sitemap.xml — đã có
- [x] OG images — đã có
- [ ] Structured data (JSON-LD) cho Organization + Product
- [ ] Vietnamese hreflang tag

### Analytics (Phase 2 Focus)
- [ ] PostHog integration (events + session replay)
- [ ] GrowthBook A/B testing
- [ ] Conversion funnel tracking
- [ ] Error tracking enhanced (Sentry đã có)

### Performance
- [ ] Lighthouse score > 90 (all categories)
- [ ] Core Web Vitals: LCP < 2.5s, FID < 100ms, CLS < 0.1
- [ ] Image optimization (WebP/AVIF)
- [ ] Code splitting per route

### Security
- [x] CSP headers — đã có (vercel.json)
- [x] HSTS — đã có
- [x] Sentry error tracking — đã có
- [ ] Rate limiting trên API endpoints
- [ ] Cookie consent banner

### Monitoring
- [x] Sentry — đã có
- [ ] Uptime monitoring (UptimeRobot/BetterStack)
- [ ] Performance budget alerts
- [ ] Revenue/conversion dashboards
