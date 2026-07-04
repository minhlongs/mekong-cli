# Master Framework — Mekong IDE: The One-Person Company Platform
# Khung Phân Tích Tổng Thể — Mekong IDE: Nền Tảng Công Ty Một Người

**Generated:** 2026-07-04
**Stage:** PMF -> Early Scale (chuyển tiếp / transition)
**Product:** Mekong CLI v6.0 — 342+ commands, 542 skills, 567 machine contracts
**Pricing:** $49–$499/mo (MCU credit system)
**Target ARR:** $1.2M trong 12 tháng
**Current Paying Customers:** 0

> *"Mekong CLI is an AI-operated business platform. Open source. Universal LLM."*
> *"Mekong CLI là nền tảng vận hành doanh nghiệp bằng AI. Mã nguồn mở. LLM đa năng."*

---

## 1. Stage Detection / Xác Định Giai Đoạn

### Current Position / Vị Trí Hiện Tại: PMF -> Early Scale Transition

| Dimension / Khía Cạnh | Status / Trạng Thái | Evidence / Bằng Chứng |
|---|---|---|
| **Product** / Sản phẩm | v6.0 tồn tại đầy đủ | 342 commands, 542 skills, PEV engine, agent layer, LLM router, 6-layer architecture |
| **Pricing** / Định giá | Đã định nghĩa rõ | MCU credits: Starter $49 (200 credits), Growth $149 (1,000), Pro $499 (5,000) |
| **GTM Strategy** / Chiến lược thị trường | Đã có lý thuyết | Open source community + Clipmart marketplace + CLI viral loop |
| **Paying Customers** / Khách trả phí | **0** | Chưa có luồng thanh toán tự động nào hoạt động trên production |
| **Traction** / Đà tăng trưởng | Technical traction | GitHub repo public, MIT license, cộng đồng mở, nhưng zero revenue |
| **Distribution** / Phân phối | Chưa có | CLI-based, chưa có landing page, chưa có SEO, chưa có ads |

### What This Means / Ý Nghĩa

Mekong CLI has built an impressive product (v6.0, full architecture, 3-provider LLM support, PEV engine) but has **zero revenue validation**. The product is feature-complete for a technical user but has never gone through the crucible of real conversion — trial -> pay -> retain.

```
PMF Spectrum / Phổ PMF:
[---BEFORE---|-------PMF-------|----EARLY SCALE----|----GROWTH----]
              ^ Mekong is HERE  -->  MUST validate conversion before scaling
                ĐANG Ở ĐÂY          PHẢI xác thực chuyển đổi trước khi mở rộng
```

### The Critical Question / Câu Hỏi Quyết Định

> "Is the product valuable enough that someone will pay $49/mo for it?"
> "Sản phẩm có đủ giá trị để ai đó trả $49/tháng không?"

We do NOT know the answer yet because:
- Không ai từng thử quy trình dùng thử -> trả phí (no trial-to-paid flow exists)
- Không có analytics để biết ai đang dùng, dùng gì, dùng bao lâu
- Không có CRM hay email sequence để nuôi dưỡng leads

---

## 2. Tri-Layer Architecture / Kiến Trúc Ba Lớp

### [Business] / [Kinh Doanh] — Lớp Doanh Nghiệp

**Model:** SaaS B2B platform for solo founders
**Mô hình:** Nền tảng SaaS B2B cho founder một người

| Element / Yếu Tố | Detail / Chi Tiết |
|---|---|
| **Product** | CLI-based AI business operating system with 300+ commands across 6 layers (Studio, Founder, Business, Product, Engineering, Ops) |
| **Pricing Tiers** | Starter $49/mo (200 MCU), Growth $149/mo (1,000 MCU), Pro $499/mo (5,000 MCU) |
| **Target Customer** | Solo founders, indie hackers, one-person companies building AI-native businesses |
| **TAM** | 50M solo founders globally (2026 estimate: 50M+ registered one-person LLCs + informal independents) |
| **SAM** | 5M tech-savvy solo founders who use CLI tools and understand AI agents |
| **SOM** | 50,000 early adopters willing to pay for AI business ops (0.1% of TAM) |
| **Year-1 Target** | 1,000 paying customers = $588K–$2.4M ARR (blended ARPU $49–$199) |

**Revenue Breakdown / Phân Tích Doanh Thu (Target 1,000 Customers):**

| Tier / Hạng | Price | Target Customers | MRR | ARR |
|---|---|---|---|---|
| Starter | $49/mo | 500 (50%) | $24,500 | $294,000 |
| Growth | $149/mo | 300 (30%) | $44,700 | $536,400 |
| Pro | $499/mo | 200 (20%) | $99,800 | $1,197,600 |
| **Total** | | **1,000** | **$169,000** | **$2,028,000** |

> Blended ARPU: $169/mo. Conservative target: $1.2M ARR (60% of blended max).

**Unit Economics (Target) / Kinh Tế Đơn Vị:**

| Metric | Target | Notes |
|---|---|---|
| CAC | $50–$150 | Organic + content-driven acquisition (low-cost GTM) |
| Monthly Churn | < 5% | SaaS benchmark for < $200/mo products |
| LTV | $1,000–$3,000 | At $49–$149/mo, 20-month avg retention |
| LTV:CAC | 10:1–20:1 | Must maintain > 3:1 to be healthy |
| Gross Margin | 85%+ | LLM API costs are the primary COGS (est. 10–15% of revenue) |

---

### [Agentic] / [Tác Nhân AI] — Lớp Tự Động Hóa

**39 AI Agents (Autonomous Execution / Thực Thi Tự Động):**

| Layer / Tầng | Agents | Role / Vai Trò |
|---|---|---|
| **7 C-Level** | CEO, CTO, CFO, COO, CMO, CPO, CSO | Strategic decisions, resource allocation, performance monitoring |
| **31 Department Heads** | Sales (3), Marketing (4), Engineering (5), Product (3), Finance (3), HR (3), Operations (4), Legal (2), Security (2), Data (2) | Daily execution, reporting, analysis |
| **1 Governance** | OpenClaw CTO | Constitution enforcement, audit, escalation |

**Autonomy Principle / Nguyên Tắc Tự Chủ:**
- All 39 agents execute autonomously within their domain
- Human only makes strategic decisions (approvals, pivots, major investments)
- OpenClaw CTO agent acts as the constitutional referee

**Current Reality / Thực Tế Hiện Tại:**
- Agents exist as skill definitions and command definitions (`.claude/skills/`, `.claude/commands/`)
- Agent dispatch is via CLI command routing (not a live multi-agent system)
- True autonomous execution (PEV loop) exists in the engine but hasn't been tested in production with real paying users
- The 39-agent architecture is **documented but not yet exercised** in a real business context

---

### [Governance] / [Quản Trị] — Lớp Điều Hành

| Component / Thành Phần | Status / Trạng Thái |
|---|---|
| **MCU Credit System** | Đã định nghĩa trong CLAUDE.md và ZENOS.md. Chưa có implementation. |
| **Polar.sh Billing** | Kế hoạch trong docs. Polar.sh webhooks -> license provisioning. Chưa triển khai. |
| **ZenOS Constitution** | Tồn tại (`ZENOS.md`, 9 articles, 187 lines). Là xương sống governance. |
| **HTTP 402 Payment Required** | Đã thiết kế trong API gateway. Chưa code. |
| **Audit Trail** | Đã lên kế hoạch (mọi transaction đều log). Chưa implement. |

**Governance Gap / Khoảng Cách Quản Trị:**
```
ZENOS.md (constitution)
    |
    v
MCU Credit Rules (defined in docs)
    |
    v
Polar.sh Webhooks (planned)
    |
    v
HTTP 402 Enforcement (designed)
    |
    v
ACTUAL BILLING CODE (DOES NOT EXIST)  <-- CRITICAL GAP
```

The governance layer has **constitutional clarity** but **zero runtime enforcement**. The entire billing pipeline is documented theory.

---

## 3. Core Metrics / Các Chỉ Số Cốt Lõi

### North Star Metric / Chỉ Số Sao Bắc Đẩu

> **Monthly Active Paying Users (MAPU)** — Số người dùng trả phí hoạt động hàng tháng

Not MAU (monthly active users), not downloads, not stars. **Paying users** — because zero revenue means zero business.

### Metric Tree / Cây Chỉ Số

```
MAPU (Monthly Active Paying Users) = 1,000 target
  |
  ├── Acquisition / Tiếp cận
  │   ├── Website visitors: 10,000/mo (target)
  │   ├── Trial sign-ups: 500/mo (5% conversion)
  │   ├── Organic traffic: 60% of total (SEO + content)
  │   └── Referral rate: 20% of new sign-ups
  │
  ├── Activation / Kích hoạt
  │   ├── Trial -> First command executed: 80%
  │   ├── Trial -> 3 sessions: 50%
  │   └── Trial -> Pay: 10% (500 trials -> 50 paid)
  │
  ├── Revenue / Doanh thu
  │   ├── ARPU: $49–$199/mo blended
  │   ├── MRR: $49K–$169K (at 1,000 customers)
  │   └── ARR: $588K–$2.0M
  │
  └── Retention / Giữ chân
      ├── Monthly churn: < 5%
      ├── 12-month retention: > 50%
      └── LTV: $1,000–$3,000
```

### Current Metrics vs Target / Hiện Tại vs Mục Tiêu

| Metric | Current | Target (Month 12) | Gap |
|---|---|---|---|
| Paying Customers | 0 | 1,000 | **INFINITE** |
| Trial Sign-ups | 0 | 500/mo | INFINITE |
| Website Visitors | 0 (no website) | 10,000/mo | INFINITE |
| MRR | $0 | $49K–$169K | INFINITE |
| MCU Credits Issued | 0 | 200K–5M/mo | INFINITE |
| Content Published | 0 | 48 articles/year | INFINITE |

> **Key Insight:** Every metric is at zero because the conversion infrastructure does not exist. The product works. The pricing is defined. The constitution is written. But the bridge from "product works" to "customer pays" has not been built.

### Market Context / Bối Cảnh Thị Trường

| Factor | Data | Implication |
|---|---|---|
| **TAM: Solo Founders** | 50M globally (2026) | Massive market, micro-SaaS + AI-native businesses exploding |
| **Competitors** | Superhuman ($30/mo), Motion ($34/mo), Notion AI ($10/mo), GitHub Copilot ($10/mo) | Mekong is more comprehensive (300+ commands) but less polished |
| **AI Agent Platforms** | AutoGPT, CrewAI, LangChain (open source) | Mekong differentiates with 6-layer business architecture + constitution |
| **Market Trend** | AI agent adoption accelerating | Timing is right but urgency is high — window won't stay open forever |

---

## 4. Key Gaps Analysis / Phân Tích Khoảng Cách

### Gap 1: No Active Billing Automation / Không Có Tự Động Hóa Thanh Toán

**What exists / Hiện trạng:**
- MCU credit pricing defined in CLAUDE.md ($49–$499/mo)
- Polar.sh mentioned as billing provider
- HTTP 402 concept documented
- ZENOS.md article on credit system

**What is MISSING / Thiếu:**

| Component | Why Critical | Effort |
|---|---|---|
| Polar.sh webhook endpoint | Need a live endpoint to receive subscription events | 1–2 days |
| MCU credit allocation on payment | When someone pays $49, they must get 200 credits | 1 day |
| MCU deduction on command execution | Every command call must decrement credits | 3–5 days |
| Zero-balance enforcement (HTTP 402) | Block execution when credits = 0 | 2 days |
| Credit top-up flow | Allow customers to buy more credits mid-cycle | 2 days |
| License key / token provisioning | Generate license for CLI authentication | 1 day |
| Billing reconciliation / invoice | Generate invoices, track payment history | 2 days |

**Total Effort:** ~12–15 days of engineering
**Risk:** Without this, revenue is literally impossible. **This is the #1 blocker.**

> "You cannot collect money if the payment pipe is not connected."
> "Bạn không thể thu tiền nếu ống thanh toán chưa được nối."

---

### Gap 2: No Conversion Funnel / Không Có Phễu Chuyển Đổi

**What exists / Hiện trạng:**
- `git clone` + `source scripts/shell-init.sh` — technical install flow
- CLI only (no web UI for onboarding)
- No trial experience
- No upgrade/downgrade flow

**What is MISSING / Thiếu:**

| Funnel Stage | Missing | Impact |
|---|---|---|
| **Awareness** | No landing page, no SEO, no content marketing | Nobody knows Mekong exists outside GitHub |
| **Interest** | No blog, no case studies, no comparison pages | Visitors don't understand value proposition |
| **Trial** | No free tier, no time-limited trial, no sandbox | Cannot evaluate before paying |
| **Conversion** | No checkout page, no payment form, no upgrade flow | Cannot pay even if they want to |
| **Onboarding** | No welcome email, no tutorial, no "first command" guide | High activation friction |
| **Retention** | No usage analytics, no engagement emails, no churn prediction | Cannot measure or improve retention |

**The Full Funnel Gap / Khoảng Cách Phễu Đầy Đủ:**

```
AWARE     INTEREST     TRIAL     PAY     USE     RETAIN
  |           |          |         |       |        |
  X           X          X         X       ~        X
GitHub     No blog    No CLI   No pay-  CLI     No churn
only                  sandbox  ment     works   tracking
```

**Proposed Quick-Win Funnel / Phễu Chiến Thắng Nhanh:**
1. Landing page: mekong.sh (or subdomain) — 1-page with pricing, features, demo GIF
2. Trial flow: `npx mekong-cli trial` — creates 7-day free account with 50 MCU credits
3. Upgrade: `mekong billing subscribe --tier growth` — Polar.sh checkout link
4. Activation: Post-install wizard (welcome message, first command suggestion, 5-minute onboarding)

---

### Gap 3: No CRM or Sales Pipeline / Không Có CRM Hoặc Kênh Bán Hàng

**What exists / Hiện trạng:**
- Zero CRM infrastructure
- No lead capture form
- No email list
- No sales pipeline stages
- No customer communication channel

**What is MISSING / Thiếu:**

| Element | Why Needed | Build or Buy |
|---|---|---|
| Lead capture | Know who's interested, follow up | Simple form on landing page (buy: Mailchimp/ConvertKit free tier) |
| Email sequences | Onboarding, nurture, re-engagement | Buy: ConvertKit ($0–$29/mo) |
| In-app notifications | Usage tips, credit alerts, upgrade prompts | Build: CLI notification system |
| Support channel | Customer questions, bug reports | Buy: Discord + GitHub Issues (free) |
| Pipeline tracking | Know how many leads -> trials -> paid | Build: Simple SQLite database + dashboard |

**Proposed Stack / Stack Đề Xuất:**
- **CRM:** Minimal — GitHub Discussions + Discord (free, zero maintenance)
- **Email:** ConvertKit free tier (up to 1,000 subscribers)
- **Analytics:** PostHog self-hosted (or Plausible for landing page)
- **Support:** Discord community + GitHub Issues
- **Cost:** $0/month until 1,000+ users

---

### Gap 4: No Content Marketing or SEO / Không Có Content Marketing Hoặc SEO

**What exists / Hiện trạng:**
- GitHub README.md
- CLAUDE.md (internal dev instructions)
- ZENOS.md (constitution document)
- No blog, no tutorials, no case studies, no SEO strategy

**What is MISSING / Thiếu:**

| Content Type | Topic Ideas | Impact |
|---|---|---|
| Blog articles | "How to run a one-person company with AI agents" | SEO + authority |
| Tutorials | "Build your first AI business in 10 minutes with Mekong" | Trial conversion |
| Case studies | (Need first customer first — chicken-and-egg) | Social proof |
| Comparison pages | "Mekong vs AutoGPT vs CrewAI" | Competitive positioning |
| Video demos | CLI screencasts, architecture walkthroughs | Visual learners |
| Open source guides | "How to contribute to Mekong CLI" | Community growth |

**SEO Keyword Targets / Từ Khóa SEO Mục Tiêu:**
- "one person company platform"
- "AI business operating system"
- "solo founder AI tools"
- "CLI for business operations"
- "AI agent platform for startups"
- "autonomous AI CEO"
- "open source business automation"

**Content Strategy (90-Day Sprint):**

| Month | Articles | Focus | Distribution |
|---|---|---|---|
| Month 1 | 4 | Product deep-dives, architecture explainers | Dev.to, Hacker News, Reddit r/indiehackers |
| Month 2 | 4 | Tutorials, "how to" guides | Medium, LinkedIn, Twitter/X |
| Month 3 | 4 | Comparisons, thought leadership | Product Hunt, Indie Hackers, newsletter |

---

### Gap 5: No Metrics Dashboard / Không Có Dashboard Chỉ Số

**What exists / Hiện trạng:**
- Revenue: $0 (not tracked because none exists)
- Usage: Not tracked (no analytics on CLI usage)
- Customers: 0 (no customer database)
- Commands executed: Not measured
- MCU credits: Not issued, not consumed, not tracked

**What is MISSING / Thiếu:**

| Dashboard | Metrics to Track | Implementation |
|---|---|---|
| **Revenue** | MRR, ARR, ARPU, churn, LTV | PostHog or custom SQLite |
| **Usage** | Commands run, agents active, sessions per user | CLI telemetry (opt-in) |
| **Customers** | Sign-ups, trials, activations, upgrades, downgrades | Simple event log |
| **MCU System** | Credits issued, consumed, remaining balances | MCU ledger in SQLite/D1 |
| **Acquisition** | Website visits, traffic sources, conversion rates | Plausible (free tier) |

**Why This Hurts / Tại Sao Đau:**
> "You cannot improve what you do not measure."
> "Bạn không thể cải thiện những gì bạn không đo lường."

Without metrics, every decision is guessing:
- Which commands are most valuable? Unknown.
- Which features drive conversion? Unknown.
- Where do users churn? Unknown.
- Is $49 the right price? Unknown.

---

## 5. Actionable Next Steps / Các Bước Tiếp Theo Khả Thi

### Month 1 Priority / Ưu Tiên Tháng 1: Build the Revenue Pipe

| # | Task | Owner | Timeline | Dependencies |
|---|---|---|---|---|
| 1 | Implement Polar.sh webhook endpoint | Engineering | Week 1 | None |
| 2 | MCU credit ledger (issue + deduct) | Engineering | Week 1–2 | Task #1 |
| 3 | CLI authentication with license token | Engineering | Week 2 | Task #2 |
| 4 | Trial flow: `npx mekong-cli trial` (7 days, 50 MCU) | Engineering | Week 2–3 | Task #3 |
| 5 | Landing page at mekong.sh | Product + Engineering | Week 2–3 | None |
| 6 | PostHog analytics for CLI usage | Engineering | Week 3 | Task #2 |
| 7 | Trial -> Upgrade flow (billing subscribe command) | Engineering | Week 3–4 | Task #4 |
| 8 | First blog post: "Introducing Mekong CLI v6" | Marketing | Week 2 | Task #5 |

### Month 2 Priority / Ưu Tiên Tháng 2: Drive Traffic

| # | Task | Owner | Timeline |
|---|---|---|---|
| 1 | SEO optimization of landing page + docs | Marketing | Week 5 |
| 2 | Post on Hacker News + Product Hunt | Marketing | Week 5–6 |
| 3 | 4 tutorial blog posts | Marketing + Product | Week 6–7 |
| 4 | Open Discord community | Community | Week 5 |
| 5 | Create demo screencast (2 min) | Product | Week 6 |
| 6 | Outreach to 20 indie founders for beta | Sales | Week 6–7 |

### Month 3 Priority / Ưu Tiên Tháng 3: Optimize Conversion

| # | Task | Owner | Timeline |
|---|---|---|---|
| 1 | Analyze trial -> pay conversion metrics | Product | Week 9 |
| 2 | A/B test pricing page | Marketing | Week 9–10 |
| 3 | Email nurture sequence (5 emails) | Marketing | Week 10 |
| 4 | Feature request + feedback loop | Product | Week 10 |
| 5 | First customer case study | Marketing | Week 11–12 |
| 6 | Referral program (10% credit for referral) | Product | Week 12 |

---

## 6. Risks / Rủi Ro

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **No one pays $49/mo for a CLI** | Medium | Critical | Validate with 20 beta users before full launch; test $19/mo starter tier |
| **LLM API costs exceed revenue** | Medium | High | Set hard MCU caps; negotiate volume pricing with OpenRouter; cache common responses |
| **Open source cannibalizes paid** | High | Low | Free tier is deliberate — it drives adoption; paid = advanced features + credits |
| **Churn > 10% monthly** | Medium | High | Focus on onboarding quality; build "aha moment" in first session; measure before optimizing |
| **Polar.sh billing integration breaks** | Low | Critical | Have Stripe as backup (do NOT use Polar for Sophia, but Mekong has no restrictions) |
| **GitHub stars != paying users** | Guaranteed | High | Stars are vanity metric. Focus entirely on conversion, not GitHub popularity. |

---

## 7. Summary / Tổng Kết

### The Paradox / Nghịch Lý

> *"Mekong CLI v6.0 is a fully-functional AI business operating system with 342 commands, a PEV engine, 39 agent definitions, and a constitutional governance framework. But it has zero paying customers because the pipeline from 'product exists' to 'customer pays' has never been built."*
>
> *"Mekong CLI v6.0 là hệ điều hành doanh nghiệp AI đầy đủ chức năng với 342 lệnh, engine PEV, 39 định nghĩa tác nhân và khung hiến pháp quản trị. Nhưng nó có không khách hàng trả phí vì đường ống từ 'sản phẩm tồn tại' đến 'khách hàng trả tiền' chưa bao giờ được xây."*

### The 4-Step Rescue / Giải Cứu 4 Bước

1. **Build the payment pipe** (Month 1) — Polar.sh + MCU ledger + HTTP 402 enforcement
2. **Create the customer funnel** (Month 1–2) — Landing page + trial flow + activation wizard
3. **Drive awareness** (Month 2–3) — Content marketing + SEO + community + Product Hunt
4. **Measure and optimize** (Month 3+) — Analytics -> conversion experiments -> pricing iteration

### The Bottom Line / Kết Luận Cuối Cùng

**Mekong CLI has a $1.2M ARR product but a $0 revenue business.**

The code is written. The architecture is sound. The pricing is defined. But the business infrastructure — billing, funnel, CRM, content, metrics — is entirely absent. These are not hard engineering problems. They are implementation gaps that can be closed in 3 months of focused execution.

The question is not "can Mekong generate revenue?"
The question is **"will someone pay $49/mo for a CLI?"**
And the only way to answer that is to build the funnel and **let the market speak.**

---

*Generated by Mekong CLI — 2026-07-04*
*Analysis framework for /Users/macbook/mekong-cli/plans/company-blueprint/00-framework.md*
