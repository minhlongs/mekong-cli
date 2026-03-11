# Affiliate Program Design — Mekong CLI

**Status:** Design phase | **Launch:** Q3 2026 (after $3K MRR) | **Platform:** Polar.sh built-in

---

## Why Affiliate Makes Sense for Dev Tools

Developer tools spread via word-of-mouth from trusted peers. An affiliate program formalizes and rewards this. When a senior dev recommends Mekong CLI to their team or Twitter followers, they should earn from that referral.

Polar.sh has native affiliate/referral support — zero additional infrastructure needed.

---

## Program Structure

### Tier 1: Community Affiliate (Default)

| Parameter | Value |
|-----------|-------|
| Commission | 20% recurring for 12 months |
| Cookie window | 60 days |
| Minimum payout | $20 |
| Payout schedule | Monthly via Stripe |
| Who qualifies | Anyone with unique referral link |

**Example:** Affiliate refers 5 Starter customers → earns $49 × 5 × 20% = $49/mo for 12 months.

### Tier 2: Creator Affiliate (Invited)

For YouTubers, newsletter authors, influential developers with >1K followers.

| Parameter | Value |
|-----------|-------|
| Commission | 30% recurring for 12 months |
| Dedicated landing page | Custom slug (mekong-cli.dev/ref/[name]) |
| Co-marketing support | README mention, article collaboration |
| Who qualifies | Invitation only, >1K relevant audience |

### Tier 3: Agency Reseller (Future, Q4 2026)

For agencies that bundle Mekong CLI into client deliverables.

| Parameter | Value |
|-----------|-------|
| Discount | 30% off Enterprise tier |
| White-label | Not available (brand required) |
| Commission model | Margin on resale |

---

## Commission Economics

At 20% recurring commission:

| Referral | Tier | Monthly Revenue | Commission | Net to Mekong |
|----------|------|----------------|-----------|--------------|
| 1 Starter | $49 | $49 | $9.80 | $39.20 |
| 1 Pro | $149 | $149 | $29.80 | $119.20 |
| 1 Enterprise | $499 | $499 | $99.80 | $399.20 |

Gross margin after commission: ~60% (down from 75%). Still healthy.

---

## Affiliate Recruitment Targets

| Profile | Channel | Approach |
|---------|---------|----------|
| OSS maintainers (Python, CLI tools) | GitHub | Direct invite after launch |
| Dev tool YouTubers (< 50K subs) | YouTube | Email outreach |
| Newsletter authors (AI/dev focused) | Twitter, Substack | DM with pitch |
| IndieHackers power users | IH profile | Comment → DM |
| Twitter dev influencers | Twitter | Build relationship first |

**First 10 affiliates:** Personal outreach only. No mass email.

---

## Polar.sh Affiliate Setup

```bash
# Polar.sh dashboard → Benefits → Affiliate
# 1. Enable affiliate program
# 2. Set commission rate: 20%
# 3. Set cookie duration: 60 days
# 4. Generate referral link format: /ref/[username]
# 5. Add affiliate dashboard link to docs
```

---

## Affiliate Content Kit

Provide affiliates with:
- [ ] Pre-written tweet templates (3 options)
- [ ] Demo GIF they can embed
- [ ] One-paragraph description for newsletters
- [ ] Unique tracking link via Polar.sh
- [ ] Monthly performance report email

---

## Launch Criteria

Before launching affiliate program:
- [ ] MRR > $3,000 (margin to give commissions)
- [ ] Churn rate stable (< 8%/mo)
- [ ] Polar.sh affiliate feature confirmed active
- [ ] Affiliate landing page created
- [ ] 3 founding affiliates recruited personally
