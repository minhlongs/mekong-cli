# Chapter 12: Fire Attack — Launch Strategy

## Two Fronts, One Week

### Front 1: Mekong CLI — Show HN (Open Source)

**Goal:** 50+ upvotes, 10+ GitHub stars, 3 signups for $49 Starter

**Timing:** Tuesday 2026-03-24, 9:30am ET (8:30pm VN)
- Weekday morning ET = peak HN traffic
- Tuesday/Wednesday historically best days

**Pre-launch (tonight):**
- [x] README compelling with 3-command demo
- [x] QUICKSTART works end-to-end
- [x] npm packages installable
- [x] CI GREEN
- [x] Repo 71MB (shallow clone ~30MB)
- [x] Show HN draft ready

**Launch day (Tuesday):**
1. Post Show HN (use draft from `plans/reports/show-hn-260323-2130-launch-draft.md`)
2. Reply to EVERY comment within 1 hour
3. Cross-post: Twitter/X, Reddit r/opensource, r/programming, r/artificial
4. Dev.to article (repurpose Show HN body)

**Week 1 metrics to track:**
- GitHub stars
- npm installs (`npm info @mekongcli/openclaw-engine` weekly downloads)
- HN upvotes + comments
- Polar.sh signups (MCU purchases)

---

### Front 2: Algo-trader — First Customer (Product)

**Goal:** 1 paying customer on VPS within 7 days

**Status:**
- [x] 2398/2398 tests GREEN
- [x] VPS deployment guide ready
- [x] postinstall hardened
- [ ] Customer identified
- [ ] Pricing set
- [ ] VPS provisioned

**Customer acquisition:**
1. **Warm leads:** Crypto trading communities (Telegram, Discord)
2. **Positioning:** "AI-powered algo trading — Polymarket 80% + CEX/DEX 20%"
3. **Pricing model:**
   - Setup fee: $500 (one-time, covers VPS setup + configuration)
   - Monthly: $200/mo (hosting + monitoring + updates)
   - Revenue share: 10% of profits (optional tier)
4. **Demo:** Run live backtest on Polymarket, show P&L

**Delivery checklist:**
- [ ] Provision Ubuntu 22.04 VPS (DigitalOcean/Hetzner)
- [ ] Follow `docs/vps-deployment-guide.md`
- [ ] Configure customer's exchange API keys
- [ ] Set up PM2 monitoring + alerts
- [ ] 48h burn-in period before going live
- [ ] Weekly P&L report automated

---

## Revenue Path to $1M ARR

| Source | Price | Customers | MRR | ARR |
|--------|-------|-----------|-----|-----|
| Mekong Starter | $49/mo | 100 | $4,900 | $58,800 |
| Mekong Pro | $149/mo | 50 | $7,450 | $89,400 |
| Mekong Enterprise | $499/mo | 20 | $9,980 | $119,760 |
| Algo-trader Setup | $500 | 20 | — | $10,000 |
| Algo-trader Monthly | $200/mo | 50 | $10,000 | $120,000 |
| Algo-trader Rev Share | ~10% | 20 | $25,000 | $300,000 |
| **Total** | | | **$57,330** | **$698,000** |

Gap to $1M: need ~25% more customers OR higher rev share performance.

---

## This Week's Actions

| Day | Mekong CLI | Algo-trader |
|-----|-----------|-------------|
| Mon (tonight) | Final review, prep social posts | Identify 3 warm leads |
| Tue | **Show HN launch 9:30am ET** | Message leads with demo offer |
| Wed | Reply to HN, fix issues from feedback | Schedule demo call |
| Thu | Dev.to article, Reddit posts | Run live backtest for prospect |
| Fri | First week metrics report | Close first customer |

---

## Unresolved Questions

1. Algo-trader pricing: $500 setup + $200/mo or flat $300/mo all-in?
2. VPS provider: DigitalOcean ($24/mo) vs Hetzner ($10/mo)?
3. Rev share tracking: automated or honor system?
4. Show HN: use main title or alt title?
