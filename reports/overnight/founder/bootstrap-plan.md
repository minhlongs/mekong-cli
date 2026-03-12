# Mekong CLI — Bootstrap Independence Calculator
*Generated: 2026-03-12 | Stage: Pre-revenue v0.2.0 | 1 founder*

---

## 1. RAMEN PROFITABILITY CALCULATOR

**Monthly burn (Vietnam founder, Saigon):**

```
Personal costs:
  Rent (Saigon District 3-7)     $300
  Food                           $200
  Utilities + transport          $100
  Health insurance               $100
  Misc / social                  $100
  ─────────────────────────────  ────
  Personal subtotal              $800

Business costs (CF infra = $0):
  Domains + SSL                   $10
  LLM API testing (OpenRouter)    $30
  Misc tools / subscriptions      $10
  ─────────────────────────────  ────
  Business subtotal               $50

Total bare minimum                $850
Buffer 20%                        $170
─────────────────────────────────────
RAMEN TARGET (monthly)          $1,020
```

**Users needed to hit ramen:**

```
┌─────────────────────┬─────────┬─────────┬─────────────┐
│ Tier                │ Price   │ Users   │ MRR         │
├─────────────────────┼─────────┼─────────┼─────────────┤
│ Starter only        │ $49/mo  │   21    │ $1,029      │
│ Pro only            │ $149/mo │    7    │ $1,043      │
│ Enterprise only     │ $499/mo │    3    │ $1,497      │
│ Mixed (realistic)   │ ~       │ 15S+3P  │ $1,182      │
│   15 Starter        │ $49     │   15    │   $735      │
│    3 Pro            │ $149    │    3    │   $447      │
└─────────────────────┴─────────┴─────────┴─────────────┘

RAMEN = 21 Starter OR 7 Pro OR 3 Enterprise customers
Realistic mix target: 15 Starter + 3 Pro = $1,182/mo
```

**Time estimate to ramen (realistic):**
- With daily content + cold outreach: 60-90 days
- With Product Hunt launch: potentially 30 days if top 5
- Without active marketing: 180+ days

---

## 2. BOOTSTRAP PATH TO $1M ARR

**Monthly targets (conservative path):**

```
┌──────┬───────────┬──────────────────────────────────────────────────┐
│ Mo   │ MRR       │ Key Actions                                       │
├──────┼───────────┼──────────────────────────────────────────────────┤
│  M1  │ $0→$500   │ Ship Polar.sh billing, public launch HN/Reddit    │
│  M2  │ $500      │ First 10 paid users, setup services bridge        │
│  M3  │ $1,020    │ RAMEN — 21 paid users, stop bleeding              │
│  M4  │ $2,000    │ Annual plan push (save 2 months), LTD option      │
│  M5  │ $3,500    │ Content flywheel: dev blog + 2 tutorials/week     │
│  M6  │ $5,000    │ Agency tier ($299?) → 10 agency clients           │
│  M7  │ $7,500    │ SEA market: VIISA/Pioneer apply                   │
│  M8  │ $10,000   │ $10K MRR = $120K ARR milestone                   │
│  M9  │ $14,000   │ Hire 1 contractor (part-time growth)              │
│ M10  │ $18,000   │ Enterprise outreach (teams, small corps)          │
│ M11  │ $22,000   │ $250K ARR run rate                                │
│ M12  │ $28,000   │ $336K ARR — evaluate raise vs. stay bootstrapped  │
├──────┼───────────┼──────────────────────────────────────────────────┤
│ M18  │ $50,000   │ $600K ARR — profitable, team of 3                 │
│ M24  │ $83,000   │ $1M ARR — independence achieved                   │
└──────┴───────────┴──────────────────────────────────────────────────┘
```

**6 Bootstrap Strategies for Mekong CLI:**

**1. Charge from Day 1 (MCU Credits)**
- MCU billing already architected (HTTP 402 on zero balance)
- Polar.sh webhooks in place
- Action: activate billing gate immediately, no free tier for new signups
- Offer 50 MCU free trial (one-time), then pay-as-you-go
- $49 Starter = 200 MCU/mo — enough for ~40 cook tasks/day

**2. Annual Plans Early (Cash Flow)**
- Annual Starter: $490 (save $98) — collect $490 upfront
- Annual Pro: $1,490 (save $298) — collect $1,490 upfront
- 10 annual Starter users = $4,900 cash runway extension
- Push annual from M3 onward with "founding member" badge
- Cap: first 50 founding members get annual at 2-month discount

**3. Services Bridge (Setup Mekong CLI for Companies)**
- "Mekong CLI Setup" service: $500-$1,500 one-time
  - Install + configure on company infra
  - Connect to their LLM API keys
  - Train team on 289 commands
  - Custom `.claude/skills/` for their workflows
- Target: CTOs of 10-50 person tech companies in Vietnam/SEA
- 5 setups/month = $2,500-$7,500 bridge revenue
- Convert setup clients to Enterprise subscriptions ($499/mo)

**4. Lifetime Deals**
- AppSumo / PitchGround LTD: $199-$299 one-time
- Limit to 200 LTDs (prevent LTD dependency)
- 200 LTDs x $249 = $49,800 cash injection
- Cap MCU at 500/mo for LTD tier (cost-controlled)
- Timing: M4-M6, before real traction (avoid selling too cheap)

**5. Content Compounding**
- Dev blog at mekong.dev or mekong-cli.dev
  - "How I replaced my entire dev workflow with 289 CLI commands"
  - "PEV Engine explained: Plan-Execute-Verify for AI agents"
  - "Building a company with 1 founder + AI (OpenClaw method)"
- YouTube: screen recordings of mekong cook solving real problems
- Twitter/X: daily builds in public thread
- Hacker News: "Show HN: I built an AI CLI that runs a company"
- Expected: 3-6 month lag before content converts to MRR

**6. Niche Then Expand**
- Phase 1 (M1-M6): Solo AI developers — 289 commands, PEV engine, TypeScript/Python
- Phase 2 (M6-M12): Technical founders — /plan, /sprint, /sales, /marketing commands
- Phase 3 (M12+): Small agencies (3-10 person) — parallel agents, team features
- Phase 4 (M18+): Enterprise — compliance, SSO, audit trail, custom models
- Each phase 10x the addressable market

---

## 3. WHEN TO RAISE (IF EVER)

**Raise if ALL conditions met:**
- [ ] MRR > $50K ($600K ARR) and growing 15%+ MoM
- [ ] Clear $10M+ ARR path visible (enterprise deals in pipeline)
- [ ] Growth bottlenecked by capital, NOT by product/distribution
- [ ] Specific use of funds: hire senior engineers, sales, not survival
- [ ] Comfortable giving up 15-25% equity and board seat
- [ ] Need to move faster than bootstrapping allows

**Do NOT raise if:**
- MRR < $25K — too early, bad leverage
- Raising for runway (not growth) — fix unit economics first
- No clear path to $10M ARR — investors won't like story
- Product still pre-PMF — dilute yourself finding it alone
- CF free tier still covers infra — no infra cost pressure

**Vietnam Founder Advantage:**
- $1,020/mo ramen = extremely low bar vs. US ($5K+)
- Longer runway per dollar raised
- Can stay bootstrapped much longer than US counterpart

---

## 4. ALTERNATIVES DATABASE

**Revenue-Based Financing:**
- Clearco / Capchase: need $10K+ MRR, US entity required
- Pipe: SaaS revenue financing, 3-12 month advances
- Lighter Capital: $50K-$3M, 8-15% flat fee
- Wait until M6+ MRR > $10K to explore

**Vietnam Grants:**
- NATIF (National Technology Innovation Fund): up to $500K VND equivalent
  - Apply: natif.gov.vn, quarterly rounds
  - Requirement: Vietnamese company, tech product
- VINTECH City: Hanoi-based, funding + mentorship
  - Apply: vintech.city
- VSMA (Vietnam Silicon Valley): bridge to US market
  - Apply: vietnamsiliconvalley.com
- NIC (National Innovation Center): Ministry of Planning
  - apply: nic.vn — grants + subsidized coworking

**Global Cloud Credits (Free Infra):**
- AWS Activate: $100K credits (apply via accelerator)
- Google for Startups: $200K credits
- Azure for Startups: $150K credits
- Cloudflare for Startups: extended limits (already using CF)
- Anthropic API credits: apply at anthropic.com/startups
- OpenRouter credits: contact directly

**Accelerators:**

Global:
- YC (Y Combinator): $500K for 7% — apply twice/year
  - Best fit: after $10K MRR or exceptional growth metrics
- Pioneer.app: $10K non-dilutive + community — apply anytime
  - Best fit: M1, immediately — build in public + apply
- Antler: pre-seed, global cohorts including SEA
- Entrepreneur First: pre-team or 1-founder track

SEA / Vietnam:
- VIISA (Vietnam Innovative Startup Accelerator): $20K-$50K
  - Apply: viisa.vn — 2 cohorts/year
- Do Ventures: seed-stage SEA
- Iterative: YC-style for SEA, $150K for 10%
  - Apply: iterative.vc — strong fit for Mekong CLI

**Strategic / Angel:**
- DevTools angels: seek via Twitter/HN, devtools.fm community
- Vietnam Angel Network (VAN): local high-net-worth
- HATCH! Ventures: Vietnam early-stage

---

## 5. BOTTOM LINE SUMMARY

```
╔══════════════════════════════════════════════════════════════╗
║           MEKONG CLI BOOTSTRAP INDEPENDENCE PLAN             ║
╠══════════════════════════════════════════════════════════════╣
║  Founder burn          $1,020/mo (Vietnam advantage)         ║
║  Infra cost            $0/mo (Cloudflare free tier)          ║
║  Ramen users needed    21 Starter OR 7 Pro OR 3 Enterprise   ║
║  Ramen timeline        60-90 days with active outreach       ║
╠══════════════════════════════════════════════════════════════╣
║  MILESTONES                                                   ║
║  M3   $1K MRR   → Ramen profitability                        ║
║  M8   $10K MRR  → $120K ARR, real business                   ║
║  M12  $28K MRR  → $336K ARR, evaluate options                ║
║  M24  $83K MRR  → $1M ARR, independence achieved             ║
╠══════════════════════════════════════════════════════════════╣
║  CASH INJECTION LEVERS (in priority order)                   ║
║  1. Annual plans ($490-$1,490) → immediate cash flow         ║
║  2. Services bridge ($500-$1,500/setup) → 5/mo = $5K        ║
║  3. Lifetime deals (200 x $249 = $49,800 one-time)           ║
╠══════════════════════════════════════════════════════════════╣
║  RAISE THRESHOLD                                             ║
║  Only if: MRR > $50K + 15%+ MoM + capital-bottlenecked      ║
║  First apply: Pioneer.app (M1) + VIISA (M3) + YC (M6+)      ║
╠══════════════════════════════════════════════════════════════╣
║  COMPETITIVE MOAT                                            ║
║  289 commands + PEV engine + 5-layer arch + universal LLM   ║
║  0 infra lock-in + open source trust + Vietnam cost base     ║
╚══════════════════════════════════════════════════════════════╝

NEXT 3 ACTIONS (this week):
  1. Activate Polar.sh billing gate (MCU credits live)
  2. Apply Pioneer.app — build-in-public narrative ready
  3. Write first HN Show HN post + publish mekong.dev blog
```

---
*Docs impact: none — standalone report*
