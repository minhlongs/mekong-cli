# Business Model Canvas — MekongMind VN Commercial Launch

**Date:** 2026-07-14
**Stage:** Zero → Product-Market Fit
**Analysis Layers:** [Business] + [Agentic] + [Governance]

---

## 1. Value Propositions

### Primary (customers hire us to…)

| # | Value Prop | Evidence |
|---|-----------|----------|
| VP1 | Replace 8-12 SaaS tools ($80-150/mo) with ONE AI platform ($49/mo) | Kit doanh nghiệp cá nhân (OPC) trung bình dùng: Sapo/KiotViet (invoicing), Zalo OA (marketing), Meta Ads (ads), Toggl (time), Wave (accounting), Canva (design), ChatGPT (AI), Mailchimp (email) → 8 tools × $6-19/mo |
| VP2 | AI executes, not just chats — generates invoices, files taxes, deploys campaigns | MekongMind có 443 command definitions đã wired; TT78 invoicing + VietQR webhook + Zalo OA integration đã tồn tại |
| VP3 | Vietnamese-first AI — hiểu TNCN/TNDN/GTGT, Zalo OA, VietQR, TT78 | Không competitor nào có native VN compliance layer |
| VP4 | BYOK (Bring Your Own Keys) — privacy, không lock-in | OpenRouter + ElevenLabs + D-ID → founder kiểm soát data |

### Secondary

| # | Value Prop |
|---|-----------|
| VP5 | Phân bổ MCU credit → biết chính xác chi phí AI mỗi tháng. Không hidden API bills. |
| VP6 | 10 business layers (Founder → Worker) → từ ý tưởng đến execution trong 1 platform |
| VP7 | Cloudflare-only infra → $0 hosting cost = margin ưu tiên <br> [Agentic] AI agents execute 80%+ of OPC workflows autonomously <br> [Governance] ZENOS constitution ensures human supremacy (Article 1) |

---

## 2. Customer Segments

### Primary ICP

| Segment | Profile | Size (VN) | WTP | Priority |
|---------|---------|-----------|-----|----------|
| **OPC Shop Owner** | Chủ shop online (Shopee/Lazada/TikTok Shop), 25-40 tuổi, quản lý 5-50 đơn/ngày | ~800K | $30-60/mo | #1 |
| **Freelancer/KOL** | Freelancer, KOLs, content creators trên MXH, cần content calendar + invoicing | ~500K | $20-50/mo | #2 |
| **FBA/Dropshipper** | Bán hàng quốc tế, cần content + order management + accounting | ~100K | $49-99/mo | #3 |

### Secondary Segments

| Segment | Profile | Priority |
|---------|---------|----------|
| **Marketing Agency** | Digital agency 2-10 người, white-label opportunity | #4 |
| **Startup Founder** | Pre-seed/seed VN startup founder, lean stack | #5 |

### Tertiary (future)

| Segment | Trigger |
|---------|---------|
| B2B2C Agency White Label | Agency buys seats at $149-499/mo |
| Enterprise OPCs | >$10K/mo revenue, need dedicated support |

**Jobs-to-be-Done:**
- "Khi tôi nhận đơn hàng mới, tôi muốn AI tự tạo hóa đơn, gửi Zalo, và cập nhật kế toán" — ít nhất 3 tools hiện tại để làm điều này
- "Tôi muốn viết content 10 bài/tuần cho Facebook mà chỉ tốn 2 giờ, không 10 giờ"
- "Tôi sợ nhất là nhầm lẫn khi kê khai thuế TNCN/TNDN — tôi không phải kế toán"

---

## 3. Channels

### Acquisition Channels (priority order)

| # | Channel | CAC Target | Notes |
|---|---------|-----------|-------|
| 1 | **Zalo Official Account (organic)** | ~$5-15 | OA hiện có → pilot users onboarded qua Zalo. Phễu: Zalo OA → landing page → signup → free pilot → paid |
| 2 | **Content Marketing (VN)** | ~$10-25 | YouTube channel "AI cho doanh nghiệp 1 người" + blog MekongMind. SEO cho từ khóa: "phần mềm quản lý bán hàng AI", "hóa đơn điện tử tự động", "kế toán dành cho freelancer" |
| 3 | **Community** | ~$0-5 | Indie Hackers VN, Facebook groups (Digital Nomad VN, Freelancer VN), MekongMind Discord. Referral loop: invite 3 friends → +200 MCU bonus |
| 4 | **Zalo Mini App discovery** | ~$3-10 | MekongMind Zalo Mini App → viral trong Zalo ecosystem. Không cần tải app riêng |
| 5 | **Tiktok/YouTube short-form** | ~$15-30 | Demo videos: "10 giây tạo hóa đơn TT78 bằng AI" → 1M views → 1K signups |
| 6 | **Partnerships** | ~$0-20 | Digital marketing agencies (resell), accounting software (referral), e-commerce platforms (Shopee/Lazada integration) |

### Distribution

- **Digital-first:** Cloudflare Workers → edge deploy → <100ms globally. No on-prem option needed.
- **Zalo OA as primary channel:** 77.6M MAU (Sep 2024), #1 messaging app in VN. MekongMind bot accessible from within Zalo.
- **BYOK model:** No operator credentials required. Customer brings their own LLM key.

---

## 4. Customer Relationships

| Type | Implementation | Tools |
|------|---------------|-------|
| **Self-Serve (Primary)** | Setup Wizard → BYOK keys → free pilot → paid. No human touch. | Setup Wizard, Zalo OA bot, documentation |
| **Community (Secondary)** | Discord/VN group for peer support, feature requests, showcase | Discord, Zalo Group |
| **High-Touch (Enterprise only)** | Dedicated onboarding call for Pro tier + custom integrations | Zalo support, video call |
| **AI-First Support** | Zalo Bot → AI triage → human escalation if confidence < threshold | Zalo OA bot → support queue |

**Retention strategy:**
- Weekly AI-generated "Business Health Report" sent via Zalo OA (value reinforcement)
- Community-driven feature voting (democratic roadmap)
- Onboarding completion rate as leading churn indicator

---

## 5. Revenue Streams

### Primary: Subscription Tiers

| Tier | Price (VNĐ) | Price (USD) | MCU/mo | Target Segment |
|------|-------------|-------------|--------|----------------|
| **Free** | 0 | $0 | 50 | Trial, exploration |
| **Starter** | 1.199K VNĐ | $49/mo | 300 | Solo founders testing |
| **Growth** | 3.499K VNĐ | $149/mo | 1,200 | Growing business |
| **Scale** | 6.999K VNĐ | $299/mo | 3,500 | Scaling operation |
| **Pro** | 11.999K VNĐ | $499/mo | 7,000 | Max capacity |

> USD pricing for intl; VNĐ pricing via VietQR domestic billing (3% conversion boost).

### Secondary: Add-on Revenue (future)

| Stream | Model | Est. Contribution |
|--------|-------|------------------|
| Premium plugins | 20% marketplace commission | 5-10% of revenue |
| Overage credits | $0.10/MCU overage | 5% of revenue |
| Annual prepayment | 25% discount vs monthly | Improve cash flow, reduce churn |
| B2B2C agency seats | $149-499/seat/mo | 15-20% of revenue (Year 2+) |

### Revenue Projection (Year 1)

| Month | Users (paid) | ARPU | MRR | ARR |
|-------|-------------|------|-----|-----|
| M1-3 | 50 | $35 | $1,750 | — |
| M4-6 | 200 | $45 | $9,000 | — |
| M7-9 | 500 | $49 | $24,500 | — |
| M10-12 | 1,000 | $49 | $49,000 | $294K |

**SOM conservative:** 500-1,000 paying users × $49/mo average = $294K-588K ARR (end Year 1).

---

## 6. Key Resources

| Category | Resource | Notes |
|----------|---------|-------|
| **Technology** | 443 command definitions + PEV orchestration engine | Core IP — 7K+ tests, production-grade |
| **Infrastructure** | Cloudflare Workers + D1 + R2 + KV | $0 infra cost tier |
| **LLM Layer** | OpenRouter (multi-model: Claude/Gemini/GPT) | Customer's own key (BYOK) |
| **Data** | ZENOS constitution, VN domain rules (TT78, Zalo API, VietQR) | Regulatory moat |
| **Brand** | "AI OS cho doanh nghiệp 1 người Việt Nam" positioning | First-mover in VN OPC AI |
| **Community** | Founder-led content (YouTube, Discord, Zalo Group) | Low-CAC acquisition |
| **Payment** | NOWPayments (intl) + VietQR (domestic) | Dual-rail billing |

### Agentic Resources

| Agent | Role | Automation % |
|-------|------|-------------|
| Code-reviewer | PR quality gate | 90% automated |
| Researcher | Market research, competitive intel | 80% automated |
| Planner | Implementation roadmaps | 85% automated |
| Tester | Test suite execution + coverage | 95% automated |
| CTO | Architecture decisions, security audits | 70% automated |
| [Governance] | Compliance, audit trail via ZENOS constitution | 100% automated |

---

## 7. Key Activities

| Activity | Owner | Frequency |
|----------|-------|-----------|
| Product development (new commands, integrations) | Mekong team | Weekly sprints |
| Content creation (VN YouTube, blog, Zalo posts) | Founder | 3x/week |
| Community management (Discord, Zalo Group) | Founder + community manager | Daily |
| Pilot user onboarding + feedback collection | Founder | Weekly |
| Competitor monitoring (Zalo AI, Sapo, KiotViet) | Researcher agent | Weekly |
| LLM cost optimization (model routing, caching) | Engineering | Monthly |
| Legal/compliance review (tax law changes) | Advisor | Quarterly |
| Customer support triage + escalation | Zalo bot + human | Real-time |

### Critical Path

```
Week 1-2: VietQR recurring billing (domestic VN)
Week 2-4: Pilot → paid conversion flow (5-10 users)
Week 4-8: Zalo Mini App MVP (viral distribution)
Week 8-12: Content engine (20 VN articles + 10 YouTube videos)
Month 3-6: First 100 paying users, iterate on onboarding
Month 6-12: Scale to 1,000 users, B2B2C partnership pilot
```

---

## 8. Key Partnerships

| Partner | Type | Value |
|---------|------|-------|
| **Zalo (VNG)** | Distribution | OA + Mini App = 77.6M MAU reach |
| **OpenRouter** | LLM API | Multi-model routing, competitive pricing |
| **ElevenLabs** | Voice AI | Vietnamese TTS for accessibility |
| **D-ID** | Video AI | AI avatar for presentations |
| **Cloudflare** | Infrastructure | $0 tier → margin advantage |
| **NOWPayments** | Intl payments | Crypto/fiat, 100+ coins |
| **VietQR/NAPAS** | Domestic payments | VN bank transfers, recurring billing |
| **MISA / 1PAC** | Accounting integration | TT78 compliance, tax filing |
| **E-commerce platforms** | Channel | Shopee, Lazada, TikTok Shop integrations |

> Zalo partnership risk: Zalo could launch competing AI features in 12-18 months. Mitigation → entrench via community + content before then.

---

## 9. Cost Structure

### Fixed Costs (~$2,000-3,000/mo at scale)

| Cost | Amount | Notes |
|------|--------|-------|
| Founder salary | $2,000/mo | Bootstrap, reinvests revenue |
| Cloud infra (CF Workers) | $0-50/mo | Free tier until 10M requests |
| LLM API (customer-funded) | $5-15/user/mo | Passed through MCU model |
| Domain + tools | $50/mo | VN domain, monitoring |
| **Total Fixed** | **~$2,100/mo** | Lean bootstrap |

### Variable Costs (per customer)

| Cost | Per Customer |
|------|-------------|
| LLM (average 150 MCU/user at $0.03/MCU) | $4.50/mo |
| Payment processing (2.9% + $0.30) | $1.72/mo (on $49) |
| Support (estimated 5% ticket rate × 15 min × $20/hr) | $0.25/mo |
| **Total Variable** | **$6.47/mo** |

### Unit Economics Summary

| Metric | Value | Target |
|--------|-------|--------|
| Revenue (Starter) | $49/mo | — |
| Variable cost | $6.47/mo | — |
| **Gross margin** | **87%** | ≥80% |
| LTV (6 months avg) | $294 | — |
| CAC target | <$25 | <$50 |
| **LTV:CAC** | **12x** | ≥3x |
| Payback period | <1 month | <3 months |

> Margin compresses at scale without LLM volume pricing. Watch per-command API cost trajectory.

---

## Governance Layer

| Concern | Implementation | Status |
|---------|---------------|--------|
| Human supremacy | ZENOS Art. 1 — founder veto on all economic decisions | ✅ Designed |
| Financial sovereignty | ZENOS Art. 5 — particles choose payment rails | ✅ Implemented (Polar + NOWPayments + VietQR) |
| Behavioral integrity | ZENOS Art. 6 — trust graph + collusion detection | 🔄 Planned (Phase 7) |
| Right to exit | ZENOS Art. 8 — data export, IP portability | ✅ Protocol-level |
| Anti-capture | ZENOS Art. 9 — term limits, founder veto, sunset clauses | ✅ Designed |

---

*BMC generated 2026-07-14. Layers: [Business] + [Agentic] + [Governance]*
*Inputs: GO/NO-GO report, GTM strategy doc, pricing strategy doc, unit economics model, ZENOS constitution, market research x2 (pending)*
