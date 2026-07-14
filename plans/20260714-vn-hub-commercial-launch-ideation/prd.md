# Product Requirements Document — MekongMind VN Commercial Launch

**Version:** 0.1.0-draft
**Date:** 2026-07-14
**Stage:** Zero → Product-Market Fit
**Product Lead:** Founder (bootstrap)
**Analysis Layers:** [Business] + [Agentic] + [Governance]

---

## 1. Vision

MekongMind là "Hệ điều hành AI cho doanh nghiệp 1 người Việt Nam" — một platform subscription ($49/mo) thay thế 5-10 disconnected tools mà mỗi OPC Việt Nam đang dùng. AI không chỉ chat — nó EXECUTE: tạo hóa đơn TT78, đăng campaign Zalo OA, kê khai thuế TNCN/TNDN/GTGT, quản lý đơn hàng, và deploy infrastructure. Tất cả trong 1 platform, accessible qua Zalo OA — app mà 77.6M người Việt đã dùng hàng ngày.

---

## 2. Target Users

### Primary ICP: "Chị Hoa — Chủ Shop Online"

| Attribute | Detail |
|-----------|--------|
| **Age** | 25-40 |
| **Location** | HN, HCM, ĐN — thành thị Việt Nam |
| **Business** | Shop online (Shopee/Lazada/TikTok Shop), 5-50 đơn/ngày |
| **Revenue** | 20-100M VNĐ/tháng (~$800-4,000) |
| **Tech fluency** | Trung bình — dùng smartphone, Zalo, Shopee seller app. Không biết code. |
| **Current tool stack** | Sapo/KiotViet (quản lý kho) + Zalo OA (marketing) + Canva (design) + ChatGPT (content) + Wave (accounting) + Shopee Ads = 6 tools, $30-60/mo |
| **Biggest pain** | "Tôi mất 2-3 ngày mỗi tháng để kê khai thuế. Tôi không hiểu TNCN vs TNDN." |
| **Willingness to pay** | $30-60/mo nếu thấy rõ value (tiết kiệm thời gian, không phạt thuế) |
| **Discovery** | YouTube "AI cho shop online" → Facebook group → Zalo OA |

### Secondary ICP: "Anh Minh — Freelancer / KOL"

| Attribute | Detail |
|-----------|--------|
| **Age** | 22-35 |
| **Business** | Freelancer (designer, writer, dev), KOL content creator |
| **Revenue** | 10-50M VNĐ/tháng |
| **Pain** | "Tôi cần viết 10 bài/tuần cho client. Mất 10h/tuần chỉ để content." |
| **Willingness to pay** | $20-50/mo |

### Tertiary ICP: "Chị Linh — Startup Founder (Pre-Seed)**

| Attribute | Detail |
|-----------|--------|
| **Age** | 25-35 |
| **Business** | Pre-seed/seed startup, 1-3 người |
| **Pain** | "Tôi cần full-stack: marketing, accounting, product, deploy — tôi chỉ có 1 bộ não." |
| **Willingness to pay** | $49-149/mo |

---

## 3. Core Features — MVP (YAGNI)

### Must Have (Launch Blockers)

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| F1 | **Zalo OA Bot** | Chat-based AI interface accessible from Zalo app. Commands: `/help`, `/invoice`, `/campaign`, `/report`, `/tax` | ✅ Scaffolded |
| F2 | **BYOK Setup Wizard** | Step-by-step onboarding: OpenRouter key → ElevenLabs key (optional) → D-ID key (optional) → done | ✅ Existing |
| F3 | **TT78 E-Invoicing** | Tạo hóa đơn điện tử compliant TT78, gửi qua VietQR | ✅ Wired |
| F4 | **VietQR Webhook** | Confirm payment khi khách chuyển khoản qua QR | ✅ Wired |
| F5 | **Zalo OA Integration** | Auto-responder, campaign scheduler, content generation | ✅ Built |
| F6 | **MCU Credit System** | Trừ credit sau mỗi command thành công. Dashboard usage. | ✅ Existing |
| F7 | **Starter Tier Billing** | $49/mo via NOWPayments (intl) + VietQR (domestic) | ✅ Polar.sh + VietQR wired |
| F8 | **Free Pilot (50 MCU)** | Signup → 50 MCU free → experience value → upgrade prompt | ✅ Existing |
| F9 | **TNCN/TNDN Tax Helper** | AI-powered tax estimation + form preparation for OPCs | 🔄 Partial |
| F10 | **33+ Ready Commands** | Commands covering: accounting, marketing, ops, content, deployment | ✅ 443 defs |

### Should Have (Launch + 30 days)

| # | Feature | Description | Priority |
|---|---------|-------------|----------|
| F11 | **Pilot → Paid Conversion Flow** | Soft paywall: hết 50 MCU → modal "Nâng lên Starter $49/mo để tiếp tục". Biến 5-10 pilot → paid trong Q3. | P0 |
| F12 | **VietQR Recurring Billing** | Auto-debit hàng tháng qua VietQR (no manual renewal) | P0 |
| F13 | **Zalo Mini App** | MekongMind chạy TRONG Zalo app — không cần tải app riêng. Viral distribution. | P1 |
| F14 | **Onboarding Email/SMS Sequence** | 5-email sequence: Day 0 (welcome) → Day 1 (first command) → Day 3 (advanced tip) → Day 7 (case study) → Day 14 (upgrade) | P1 |
| F15 | **AI Support Triage** | Zalo bot xử lý 80% support queries → human escalation. Knowledge base trong Zalo. | P1 |
| F16 | **Usage Dashboard** | Biểu đồ MCU consumption theo tuần/tháng. Breakdown by command type. | P2 |

### Nice to Have (Post-PMF)

| # | Feature | Description |
|---|---------|-------------|
| F17 | Plugin Marketplace (Clipmart) | Developers publish plugins; MekongMind takes 20% commission |
| F18 | Agency White Label | Digital agencies resell MekongMind seats to OPC clients |
| F19 | Multi-language (EN + VI + ZH) | Expand to SEA markets |
| F20 | Behavioral Graph (ZENOS Art. 6) | Trust scoring, collusion detection for multi-agent governance |
| F21 | Mobile App (React Native) | Native iOS/Android app beyond Zalo Mini App |

---

## 4. Agentic Architecture

### Which agents automate which workflows

| Workflow | Primary Agent | Automation % | Fallback |
|----------|-------------|-------------|----------|
| Code review (PR) | code-reviewer | 90% | Human for architecture |
| Market research | researcher | 80% | Human for strategy |
| Implementation planning | planner | 85% | Human for scope |
| Test execution | tester | 95% | Human for flaky tests |
| Architecture decisions | CTO + kongming | 70% | Human for business trade-offs |
| Content generation (VN) | copywriter (cmo) | 75% | Human for brand voice |
| UI/UX design | ui-ux-designer | 60% | Human for final approval |
| Billing/Quota enforcement | forest/quota | 100% | N/A (automated) |
| Compliance checking | CTO (security) | 80% | Human for legal |
| Deployment pipeline | CI/CD + deploy | 95% | Human for rollback |
| Payment webhook (NOWPayments/VietQR) | forest/billing | 100% | NOWPayments IPN → Polar/VietQR |
| [Governance] Constitutional review | Compliance AI Cell (ZENOS) | 100% | Founder veto (Art. 1) |

### Agent orchestration pattern

```
User (Zalo OA) → Command → PEV Engine → [Plan → Execute → Verify]
                                    → Agent dispatch (parallel when independent)
                                    → ZENOS governance check (every economic action)
                                    → MCU deduction (post-success)
```

---

## 5. Tech Stack

### Frontend
| Component | Tech | Rationale |
|-----------|------|-----------|
| Web dashboard | Next.js 16 App Router | SEO, SSR, edge deploy to CF Workers |
| Mobile-first UI | Tailwind CSS + shadcn/ui | Responsive, fast iteration |
| i18n | next-intl | VN + EN bilingual |

### Backend
| Component | Tech | Rationale |
|-----------|------|-----------|
| Runtime | Cloudflare Workers | $0 tier, edge latency <100ms |
| Database | Cloudflare D1 (SQLite) | Serverless, no connection pooling |
| KV Cache | Cloudflare KV | Rate limiting, sessions |
| Storage | Cloudflare R2 | Zero egress fees |
| Orchestration | Inngest | Long-running workflows (video gen, multi-step) |
| Agent runtime | Claude Code CLI (Mekong engine) | 443 commands, 7K+ tests |

### AI/LLM
| Component | Tech | Rationale |
|-----------|------|-----------|
| LLM Router | OpenRouter | Multi-model (Claude/Gemini/GPT), BYOK |
| Primary Model | Claude Opus 4.8 / Sonnet 4.7 | Best reasoning for business tasks |
| Vietnamese LLM | Gemini (via OpenRouter) | Best VN language quality |
| Voice | ElevenLabs (optional) | VN TTS for accessibility |
| Video | D-ID (optional) | AI avatar for presentations |

### Payments
| Component | Tech | Rationale |
|-----------|------|-----------|
| International | NOWPayments | Crypto + fiat, 100+ coins, IPN webhook |
| Vietnam domestic | VietQR (NAPAS) | Bank QR transfer, recurring billing |
| [BANNED for Sophia] | Polar.sh, PayPal | — |

### Observability
| Component | Tech | Rationale |
|-----------|------|-----------|
| Analytics | PostHog | Open-source, self-hosted option |
| Error tracking | Sentry | Cloudflare Workers compatible |
| Logs | Grafana + SQLite | Mekong internal observability |

---

## 6. Success Metrics

### North Star Metric
**Weekly Active Users (WAU) who complete ≥ 1 valuable command**

Valuable commands = generates invoice, creates campaign, files tax form, deploys something.

### Supporting KPIs

| KPI | Target (Month 3) | Target (Month 12) | Measurement |
|-----|------------------|-------------------|-------------|
| **Paying Users** | 100 | 1,000 | Stripe/NOWPayments/VietQR |
| **MRR** | $15K | $49K-120K | Recurring billing |
| **Free → Paid Conversion** | 5% | 10% | Signup → first payment |
| **WAU / MAU Ratio** | 0.5 | 0.6 | Engagement health |
| **NPS** | ≥40 | ≥55 | Post-use survey via Zalo |
| **Churn (monthly)** | <8% | <5% | Cancellation tracking |
| **CAC** | <$30 | <$25 | Spend / new paid users |
| **LTV:CAC** | ≥6x | ≥12x | LTV / CAC |
| **Time to First Value** | <10 min | <5 min | Signup → first successful command |
| **Support Ticket Rate** | <10% | <5% | Users / month opening tickets |
| **LLM Cost per User** | <$5/mo | <$4/mo | MCU cost tracking |
| **Uptime** | 99.5% | 99.9% | CF Workers + D1 |

### Agentic KPIs

| KPI | Target | Measurement |
|-----|--------|-------------|
| Command success rate | ≥95% | PEV engine verify step |
| Average command latency | <30s | P50, P95 |
| Agent escalation rate | <5% | Human intervention needed |
| Agent error recovery | ≥90% | Auto-retry before escalation |

---

## 7. Risks & Mitigations

### Top 3 Risks

| # | Risk | Likelihood | Impact | Mitigation | Timeline |
|---|------|-----------|--------|-----------|----------|
| **R1** | **Zalo launches native AI features** | Medium | High | Build brand + community moat BEFORE Zalo AI ships (12-18mo). Content marketing + case studies + community. Position MekongMind as "expert OPC layer on Zalo" rather than commodity chatbot. | Now → Month 12 |
| **R2** | **No paying customer → credibility gap** | Medium | High | Close 5-10 pilot → paid conversions in Q3 BEFORE any public marketing spend. If 0 conversions after 50 pilot activations, revisit pricing before scaling. | Now → Month 3 |
| **R3** | **Domestic VN billing friction** | Medium | Medium | Prioritize VietQR recurring billing for VN customers. Cross-border $49/mo from VN cards = high decline rate. VietQR = instant, familiar, no decline. | Month 1-2 |

### Secondary Risks

| # | Risk | Mitigation |
|---|------|-----------|
| R4 | LLM cost inflation | MCU model with volume pricing negotiation; cache common commands |
| R5 | Zalo OA policy violation (AI content) | Legal review before scaling automated campaign publishing |
| R6 | Competitor copycat (Sapo/KiotViet add AI) | Fast community building + VN-first compliance moat |
| R7 | Founder burnout | Agent workforce handles 80%+ of execution; founder focuses on vision + community |

---

## 8. Unresolved Questions

1. **VN legal entity:** Founder đã đăng ký công ty VN hay hoạt động dưới hình thức cá nhân? Ảnh hưởng đến invoice hợp lệ và payment processing.
2. **Pilot-to-paid conversion incentive:** Pilot users có biết sẽ bị charge không? Hiện tại pilots chạy free credits → cần soft paywall hoặc time-limited free period.
3. **Zalo OA content compliance:** AI generate content đăng lên Zalo OA — có vi phạm Zalo content policy không? Cần legal review.
4. **Support model cho non-tech OPCs:** Zalo message → human agent? AI triage → human escalation? Cần define trước 100 users.
5. **TT78 registration:** MekongMind có đăng ký với TCT (Tổng cục Thuế) làm nhà cung cấp hóa đơn điện tử không? Hay user tự đăng ký và dùng MekongMind như tool?

---

## 9. Launch Checklist (Gate Criteria)

- [ ] VietQR recurring billing live (domestic VN)
- [ ] Pilot → paid conversion flow (soft paywall + email)
- [ ] Zalo Mini App MVP (viral distribution)
- [ ] 5 paying customers (proof of concept)
- [ ] NPS survey instrumented
- [ ] Support triage bot live
- [ ] LLM cost tracking per-user
- [ ] Legal review: TT78 + Zalo OA content policy
- [ ] Content engine: 5 VN articles + 3 YouTube videos
- [ ] Analytics (PostHog) instrumented on key funnels

---

*PRD generated 2026-07-14. Layers: [Business] + [Agentic] + [Governance]*
*Inputs: GO/NO-GO (24/30 GO), BMC, Mekong docs (pricing, GTM, unit economics, personas), ZENOS constitution*
