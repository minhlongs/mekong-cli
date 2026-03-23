# Binh Phap $1M Battle Plan — RaaS Revenue Campaign

> *"Victorious warriors win first and then go to war. Defeated warriors go to war first and then seek to win."* — Sun Tzu

**Target:** $1M ARR ($83K MRR) | **Current:** $0 MRR | **Platform:** api.agencyos.network (LIVE)

This document applies the 13 chapters of Binh Phap to the concrete path from $0 to $1M ARR.

---

## Phase 0: Current Arsenal (DEPLOYED)

| Asset | Status | URL |
|-------|--------|-----|
| RaaS Gateway API | LIVE v5.0.0 | api.agencyos.network |
| Landing Page | LIVE | agencyos.network |
| Dashboard | LIVE | dashboard.agencyos.network |
| Billing (Polar.sh) | CONFIGURED | $49/$149/$499 tiers |
| Mekong CLI | PUBLIC | github.com/longtho638-jpg/mekong-cli |
| M1 Max Inference | READY | Local MLX + Ollama |
| Algo-Trader | 100% TESTS | Ready for VPS delivery |

---

## Campaign 1: First Blood — $0 → $1K MRR (Month 1-2)

### Chapter 1: Calculations (始計) — ASSESS THE BATTLEFIELD

**Before spending any MCU, calculate:**

```
mekong swot "RaaS AI Agent Platform 2026"
mekong venture:five-factors "agencyos.network"
```

| Factor | Assessment |
|--------|-----------|
| Market | AI agent platforms: $2B TAM, growing 40% YoY |
| Competition | CrewAI (open-source), AgentOps (funded), LangSmith (Langchain) |
| Moat | Binh Phap DNA + OpenClaw dispatch + MCU billing + local inference |
| Timing | 2026 = "year of agents" — Gartner peak hype |
| Risk | Solo founder, no funding, bootstrap only |

**Decision gate:** Proceed. Market is hot, product is live, cost is $0.

### Chapter 13: Intelligence (用間) — GATHER INTEL FIRST

```
mekong scout "competitor pricing AI agent platforms"
mekong audit "agencyos.network full-stack"
```

**Intel targets:**
- Where do AI builders hang out? (HN, Reddit, Discord, Twitter/X)
- What do they pay for? (hosting, credits, API access)
- What pain do they have? (agent orchestration, billing, deployment)

### Chapter 12: Fire Attack (火攻) — FIRST STRIKE

**Launch sequence (5 simultaneous strikes):**

```
mekong launch "Show HN: Mekong CLI — AI runs your business"
mekong outreach "Reddit r/SaaS r/artificial r/startups"
mekong content "Twitter thread: Solo founder built AI business platform"
mekong content "LinkedIn: How I built a $0 infra AI platform"
mekong campaign "Product Hunt launch prep"
```

**Target:** 10 paying customers × $49 = $490 MRR
**Fallback:** 3 customers × $149 = $447 MRR

### Chapter 5: Momentum (兵勢) — RIDE THE WAVE

After first customers, amplify:

```
mekong growth:experiment "referral program 20% credit bonus"
mekong content "case study: first customer results"
```

**Success metric:** $1K MRR = ~20 Starter or ~7 Pro customers

---

## Campaign 2: Establish Territory — $1K → $10K MRR (Month 3-6)

### Chapter 3: Strategic Attack (謀攻) — WIN WITHOUT FIGHTING

**Don't compete on features. Compete on simplicity.**

```
mekong plan "Developer onboarding: pip install → first command in 60 seconds"
mekong brainstorm "What makes devs stay: credits vs subscription vs usage"
```

**Strategy:** Make signup → first-value < 5 minutes. No credit card required for first 10 MCU.

### Chapter 10: Terrain (地形) — MAP THE MARKET

```
mekong venture:terrain "AI developer tools market segments"
mekong tam "Robot-as-a-Service for solo founders"
```

**3 terrain types to exploit:**
1. **Solo founders** — need everything, pay $49-149/mo, high volume
2. **Small agencies** — need client delivery automation, pay $149-499/mo
3. **Enterprise** — need white-label, pay $499+/mo, low volume, high value

### Chapter 4: Disposition (軍形) — BUILD UNBREAKABLE PRODUCT

```
mekong cook "Self-serve onboarding wizard"
mekong cook "Usage dashboard with real-time MCU tracking"
mekong cook "Webhook integrations (Zapier/Make/n8n)"
mekong test "Full integration test suite"
mekong review "Security audit before scaling"
```

**Defense-first features:**
- Rate limiting per tier
- Credit exhaustion warnings (webhook at 10% remaining)
- Automatic downgrade (not cut-off) at zero balance
- 99.9% uptime SLA for Pro+

### Chapter 9: The March (行軍) — STEADY WEEKLY PROGRESS

```
# Every Monday
mekong standup "Weekly metrics: MRR, churn, NPS, feature requests"

# Every Friday
mekong sprint "Ship 1 customer-requested feature per week"
```

**Growth formula:** 20% week-over-week MRR growth for 16 weeks = $1K → $10K

---

## Campaign 3: Scale the Army — $10K → $50K MRR (Month 7-12)

### Chapter 2: Waging War (作戰) — MANAGE RESOURCES

```
mekong finance "Monthly P&L with CAC/LTV analysis"
mekong budget "Marketing budget: reinvest 30% of MRR"
```

**Resource allocation at $10K MRR:**
- $3K → Marketing/content (30%)
- $1K → Infrastructure scaling (10%)
- $6K → Founder salary + reinvestment (60%)

### Chapter 6: Void & Substance (虛實) — EXPLOIT COMPETITOR GAPS

```
mekong competitive "CrewAI vs AgentOps vs Mekong — feature matrix"
mekong venture:void-substance "Where are competitors hollow?"
```

**Known competitor gaps to exploit:**
- CrewAI: No billing, no deployment, no business layer
- AgentOps: Monitoring only, no execution engine
- LangSmith: Tracing only, expensive, enterprise-focused
- **Our edge:** Full stack (plan → execute → verify → bill) + $0 infra

### Chapter 7: Maneuvering (軍爭) — FAST ITERATION

```
mekong deploy "Weekly releases every Tuesday"
mekong fix "< 4 hour response time on customer bugs"
```

**Speed advantages:**
- Solo founder = 0 coordination overhead
- OpenClaw = AI does 80% of feature work
- CF Workers = instant global deployment
- Binh Phap loop = automatic quality gates

### Chapter 11: Nine Situations (九地) — CRITICAL DECISIONS

At $10K-$50K MRR, decide:
```
mekong founder:validate "Should I raise funding or stay bootstrap?"
mekong swot "Bootstrap vs Series A at $50K MRR"
```

**Decision matrix:**
- If CAC < $100 and LTV > $500 → Stay bootstrap, keep 100% equity
- If CAC > $200 or churn > 10% → Consider funding for growth
- If enterprise demand > 30% of pipeline → Hire first employee

---

## Campaign 4: Siege the Castle — $50K → $1M ARR (Month 13-24)

### Chapter 8: Nine Variations (九變) — ADAPT OR DIE

```
mekong debug "Why are customers churning?"
mekong ops:health-sweep "Full platform health at scale"
```

**At this scale, problems change:**
- Performance at 1000+ concurrent users
- Support ticket volume
- Feature request prioritization
- Enterprise security compliance (SOC2, GDPR)

### Chapter 12: Fire Attack (火攻) — ENTERPRISE ASSAULT

```
mekong campaign "Enterprise AI platform — white-label OpenClaw"
mekong outreach "CTO outreach: 50 enterprise prospects"
mekong sales:pipeline-build "Enterprise funnel with demo → trial → close"
```

**Enterprise pricing at scale:**
- Custom pricing: $2K-10K/mo per enterprise customer
- 10 enterprise customers × $5K = $50K MRR = $600K ARR
- + 200 self-serve × $149 = $30K MRR = $360K ARR
- **Total: ~$1M ARR**

---

## The Victory Equation

```
$1M ARR = (200 × $149/mo) + (10 × $5K/mo) + (100 × $49/mo)
        = $29,800/mo + $50,000/mo + $4,900/mo
        = $84,700/mo × 12
        = $1,016,400 ARR
```

| Segment | Customers | Price | MRR | % of Total |
|---------|-----------|-------|-----|------------|
| Starter | 100 | $49 | $4,900 | 6% |
| Pro | 200 | $149 | $29,800 | 35% |
| Enterprise | 10 | $5,000 | $50,000 | 59% |
| **Total** | **310** | — | **$84,700** | **100%** |

---

## OpenClaw Standing Orders

These dispatch rules are ALWAYS active:

| Trigger | Chapter | Auto-Dispatch |
|---------|---------|---------------|
| New signup | 13 | `/audit` customer onboarding funnel |
| Customer churns | 8 | `/debug` churn reason → `/fix` product gap |
| MRR drops 2 weeks | 1 | `/swot` → recalculate strategy |
| Competitor launches | 6 | `/competitive` → find their void |
| Revenue milestone hit | 5 | `/marketing` amplify + `/content` case study |
| Security alert | 13→8 | `/security` → `/incident` → `/fix` |
| Weekly cadence | 9 | `/standup` Monday, `/sprint` Friday |
| Monthly cadence | 2 | `/finance:monthly-close` |
| Quarterly cadence | 1 | `/swot` + `/okr` review |

---

*"In war, the way is to avoid what is strong and strike at what is weak."*

**First blood: Post Show HN. Get 10 customers. Everything else follows.**
