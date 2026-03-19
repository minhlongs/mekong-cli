# RaaS Sales Distribution Package

**Version:** 1.0 | **Updated:** March 19, 2026

---

## Quick Start

This package contains everything you need to sell Revenue-as-a-Service (RaaS) to agencies and enterprise clients.

### What's Inside

```
sales-distribution/
├── README.md                    # This file
├── sales-deck.md                # Main pitch deck (ASCII format)
├── proposal-template.md         # Customizable proposal template
├── one-pager.md                 # Executive summary for C-level
├── faq.md                       # Common objections & responses
├── pricing-sheet.md             # Tier pricing & MCU costs
└── demos/
    ├── cli-demo.sh              # Live demo script (5 min)
    └── dashboard-walkthrough.md # Dashboard tour script
```

---

## Sales Process Overview

### Step 1: Discovery Call (30 min)

**Goal:** Qualify the prospect and identify pain points.

**Key Questions:**
1. "How do you currently bill clients for development work?"
2. "What's your biggest frustration with the hourly model?"
3. "How many developers do you have on your team?"
4. "What's your average project timeline?"

**Qualification Criteria:**
- ✅ Agency with 3+ developers
- ✅ Monthly revenue $50K+
- ✅ Already using AI tools (ChatGPT, Copilot)
- ✅ Decision maker is present

---

### Step 2: Pitch Deck Presentation (45 min)

**Goal:** Show the RaaS vision and product demo.

**Deck Flow:**
1. **Problem** (Slides 2-3): Hourly billing is broken
2. **Solution** (Slides 4-5): RaaS model + how it works
3. **Demo** (Slide 6): Live CLI execution
4. **Pricing** (Slide 7): Tier comparison
5. **ROI** (Slide 8): Case study results
6. **Close** (Slide 9): Next steps

**Demo Script:**
```bash
# 1. Show mission submission
mekong mission:create "Add user login with Google OAuth"

# 2. Show agent team execution
mekong mission:status --live

# 3. Show credit deduction
mekong credits:balance

# 4. Show deployed result
curl https://client-app.vercel.app/login
```

---

### Step 3: Proposal & Negotiation (1-3 days)

**Goal:** Get signed contract.

**Proposal Template:** See `proposal-template.md`

**Key Terms:**
- **Tier:** Starter (50 credits/mo) | Pro (200) | Agency (500) | Master (1000)
- **Contract:** 12 months minimum
- **Payment:** Monthly via Polar.sh (credit card) or invoice (enterprise)
- **SLA:** 99.9% uptime, 24h response for critical issues

**Negotiation Tactics:**
- If they say "too expensive": Show ROI calculator (Slide 8)
- If they say "need to think": Offer 14-day POC at Starter tier
- If they say "competitor is cheaper": Show comparison matrix (faq.md)

---

### Step 4: Onboarding (Week 1)

**Goal:** Get them activated and running first mission.

**Onboarding Checklist:**
- [ ] Create tenant account
- [ ] Set up billing (Polar.sh subscription)
- [ ] Configure LLM provider (BYOK or use default)
- [ ] Run first mission together
- [ ] Schedule 30-day check-in call

---

## Pricing Quick Reference

| Tier | Price/mo | Credits | Best For |
|------|----------|---------|----------|
| **Starter** | $49 | 50 | Solo consultants, freelancers |
| **Pro** | $199 | 200 | Small agencies (3-10 devs) |
| **Agency** | $499 | 500 | Growing agencies (10-50 devs) |
| **Master** | $999 | 1000 | Enterprise (50+ devs) |

**Credit Costs:**
- Simple mission (1-2 files): 1 credit
- Standard mission (3-10 files): 3 credits
- Complex mission (10+ files): 5 credits

**Example:** A typical CRUD API with auth = 3 credits (Standard)

---

## Common Objections & Responses

### "We already use GitHub Copilot"

**Response:** "Copilot is a autocomplete tool. RaaS is an autonomous agent team that executes entire missions end-to-end. Copilot helps one dev write code faster. RaaS replaces the need for multiple devs entirely."

**Proof Point:** "One client replaced 3 junior devs with RaaS and saved $180K/year."

---

### "AI can't handle complex business logic"

**Response:** "You're right — AI alone can't. But RaaS isn't just AI. It's a PEV (Plan-Execute-Verify) orchestrator that breaks complex missions into steps, executes with multiple agents, and verifies each step before proceeding."

**Proof Point:** Show case study of [Client X] who migrated their entire payment system with RaaS.

---

### "What about code quality and security?"

**Response:** "Every mission goes through 4 stages: Plan → Code → Test → Review. The Reviewer agent runs security checks (npm audit, Snyk), linting, and code quality analysis. Nothing gets deployed without passing all gates."

**Proof Point:** "We have 99.9% uptime and zero security incidents across 500+ production deployments."

---

### "Our clients won't trust AI-written code"

**Response:** "They don't have to know. You white-label RaaS as your own development team. The code is production-ready, tested, and follows best practices. Your clients see faster delivery and predictable costs."

**Proof Point:** "Agency X closed 5 enterprise deals by promising 2-week delivery — powered by RaaS."

---

## ROI Calculator

**Formula:**
```
Monthly Savings = (Hours saved per mission × Missions per month × Hourly rate) - RaaS tier cost

Example:
- Agency saves 20 hours/month with RaaS (10 missions × 2 hours each)
- Blended hourly rate: $75/hour
- Pro tier: $199/month

Savings = (20 × $75) - $199 = $1,301/month
ROI = ($1,301 / $199) × 100 = 654%
```

**Use This Script:**
1. "How many hours does your team spend on typical feature development?"
2. "What's your blended hourly rate (salary + overhead)?"
3. "If RaaS could cut that by 50%, what would that mean for your business?"

---

## Demo Environment

### Setup (5 min before call)

```bash
# 1. Ensure you have mekong CLI installed
npm install -g mekong-cli

# 2. Login with your sales account
mekong auth:login

# 3. Create a fresh project for demo
mekong project:create demo-client

# 4. Pre-load a mission
mekong mission:create "Add user registration endpoint"
```

### Demo Flow (10 min)

1. **Show mission queue:** `mekong mission:list`
2. **Run live mission:** `mekong mission:create "Add JWT authentication"`
3. **Show agent execution:** `mekong mission:status --stream`
4. **Show deployed API:** `curl https://demo-client.vercel.app/api/auth/register`
5. **Show credit deduction:** `mekong credits:history`

---

## Competitive Matrix

| Feature | RaaS | GitHub Copilot | Zapier | Traditional Agency |
|---------|------|----------------|--------|-------------------|
| Autonomous execution | ✅ | ❌ | ❌ | ❌ |
| End-to-end missions | ✅ | ❌ | ⚠️ (limited) | ✅ |
| Multi-agent teams | ✅ | ❌ | ❌ | ✅ |
| Outcome-based pricing | ✅ | ❌ (per-seat) | ❌ (per-task) | ❌ (hourly) |
| White-label option | ✅ | ❌ | ⚠️ | N/A |
| ROI tracking | ✅ | ❌ | ⚠️ | ❌ |

---

## Success Metrics

Track these KPIs for each closed deal:

| Metric | Target | How to Track |
|--------|--------|--------------|
| Time to First Mission | < 24 hours | CRM: Onboarding date → First mission timestamp |
| 30-day Retention | > 90% | CRM: Active subscriptions / Total signups |
| Credit Utilization | > 80% | Dashboard: Credits used / Credits allocated |
| Expansion Revenue | > 20% | CRM: Tier upgrades / Total accounts |
| NPS | > 50 | Survey: Quarterly customer satisfaction |

---

## Resources

### Internal Tools
- **CRM:** HubSpot (track leads, deals, pipeline)
- **Proposal:** PandaDoc (customizable templates)
- **Demo:** mekong CLI + Vercel staging environment
- **ROI Calculator:** Google Sheets (link in CRM)

### External Resources
- **Website:** agencyos.network
- **Docs:** docs.agencyos.network
- **Status:** status.agencyos.network
- **Support:** support@agencyos.network

---

## Contact

**Sales Team:**
- AE Lead: [Name] — [email]
- SDR: [Name] — [email]
- Sales Eng: [Name] — [email]

**Escalation:**
- Pricing approval: VP Sales
- Contract exceptions: Legal
- Technical deep-dive: Solutions Architect

---

*Last updated: March 19, 2026 | Version 1.0*
