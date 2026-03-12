# Mekong CLI v5.0 — Growth Experiment: Free vs Credit Model
**Generated:** 2026-03-12 overnight | **Op:** CMO agent + analytics

---

## Experiment Overview

**Hypothesis:** Users who experience a successful `mekong cook` before hitting
a paywall convert to paid at 3x the rate of users who see pricing first.

**Test:** A/B test two onboarding flows for new pip installs.
**Duration:** 30 days (2026-03-12 → 2026-04-12)
**Sample size needed:** 200 installs per variant (400 total)
**Primary metric:** 14-day paid conversion rate
**Secondary metrics:** 7-day retention, MCU consumption, NPS

---

## Variant A: Free Tier First (Control)

```
Install → mekong health (free) → mekong cook "task" (5 free MCU)
→ credits exhausted → upgrade prompt → Starter $49
```

**Free allowance:** 5 MCU on first install (enough for 1 complex task)
**Paywall trigger:** MCU balance hits 0
**Upgrade prompt:**
```
You've used your 5 free credits.

Starter plan: 50 credits / $49/month
  → mekong upgrade starter
  → or: mekong-cli.dev/pricing

Credits only consumed on successful task delivery.
```

**Expected behavior:** User sees real value before paying.
Risk: Users who complete 1 task may feel "done" and churn.

---

## Variant B: Credit Purchase First (Challenger)

```
Install → mekong health (free) → mekong cook "task" → PAYWALL
→ forced upgrade before first cook → Starter $49
```

**Free allowance:** 0 MCU (health, status, version only free)
**Paywall trigger:** First cook/plan/deploy attempt
**Upgrade prompt:**
```
mekong cook requires credits.

Starter plan: 50 credits / $49/month — $0.98/credit
  → mekong upgrade starter
  → or: mekong-cli.dev/pricing

Why credits? You only pay for successful task delivery.
Failed tasks cost 0 MCU.
```

**Expected behavior:** Higher friction → lower signup volume but higher intent.
Risk: Users bounce before experiencing value.

---

## Variant C: Freemium Forever (Exploration)

```
Install → mekong health (free) → mekong cook --dry-run (free, plan only)
→ full execution requires credits → Starter $49
```

**Free allowance:** Unlimited dry-runs (plan phase only, no execute)
**Paywall trigger:** First real execution (not dry-run)
**Upgrade prompt:**
```
Your plan is ready. Execute it with credits.

Plan preview (free):
  Step 1: [generated step]
  Step 2: [generated step]

To execute: mekong upgrade starter (50cr/$49/mo)
Credits only consumed on success.
```

**Expected behavior:** High engagement (free plan is useful) → informed buyers.
Risk: "Dry-run is enough" — users never convert.

---

## Measurement Framework

### Funnel Metrics (per variant)

| Stage | Metric | Tracking |
|-------|--------|---------|
| Install | pip installs | PyPI stats + PostHog |
| Activation | mekong health run | PostHog event |
| First cook | mekong cook attempted | PostHog event |
| Paywall hit | upgrade prompt shown | PostHog event |
| Conversion | Polar.sh subscription created | Webhook → PostHog |
| Retention D7 | active at day 7 | PostHog cohort |
| Retention D14 | active at day 14 | PostHog cohort |

### Statistical Significance

```
Baseline conversion assumption: 5% (industry avg for CLI dev tools)
Target improvement: 2x (10% conversion)
Required sample: 196 per variant (80% power, p<0.05, two-tailed)
Using 200 per variant to be safe: 400 total installs needed
Expected time to significance: 30 days at current install rate
```

---

## Predicted Outcomes

| Variant | Install→Trial | Trial→Paid | Overall CVR | MRR/100 installs |
|---------|--------------|------------|-------------|-----------------|
| A (free 5 MCU) | 80% | 12% | 9.6% | $470 |
| B (pay first) | 40% | 22% | 8.8% | $431 |
| C (dry-run free) | 70% | 15% | 10.5% | $514 |

**Prediction:** Variant C wins on CVR. Variant A wins on absolute signups.
**Recommendation if C wins:** Ship freemium dry-run as default onboarding.

---

## Secondary Experiments (Queue for Month 2)

### Experiment 2: Credit Pack vs Subscription
**Hypothesis:** One-time credit packs ($19/20cr) convert casual users who
won't commit to monthly subscription.

**Test:** Add credit pack option to upgrade prompt alongside subscription.
**Metric:** Revenue per install (RPM), not just CVR.

### Experiment 3: Referral Credits
**Hypothesis:** "Give a friend 5 free credits, get 5 yourself" drives
organic growth faster than paid acquisition.

**Test:** Add referral code to post-signup flow.
**Metric:** Referred installs as % of total, referral CVR vs organic.

### Experiment 4: Annual vs Monthly Pricing
**Hypothesis:** Annual billing (2 months free) improves LTV and reduces churn.

**Test:** Show annual option prominently in upgrade flow.
**Metric:** Annual uptake rate, 90-day retention vs monthly cohort.

---

## Implementation Notes

```python
# PostHog feature flag for variant assignment
posthog.get_feature_flag(
    'onboarding_variant',
    distinct_id=machine_fingerprint,  # src/core/machine_fingerprint.py
    groups={'tenant': tenant_id}
)
# Returns: 'free_5mcu' | 'pay_first' | 'dry_run_free'

# MCU gate variant logic (src/core/mcu_gate.py)
if variant == 'free_5mcu' and first_install:
    grant_credits(tenant_id, 5, reason='free_trial')
elif variant == 'dry_run_free':
    allow_dry_run_without_credits()
else:
    enforce_paywall_on_first_cook()
```

Machine fingerprint: src/core/machine_fingerprint.py ensures consistent
variant assignment per device across sessions.

---

## Decision Timeline

| Date | Action |
|------|--------|
| 2026-03-12 | Experiment starts, 3 variants live |
| 2026-03-26 | Mid-point check (200 installs) — kill clearly losing variant |
| 2026-04-12 | Experiment ends — pick winner |
| 2026-04-15 | Ship winning variant as default onboarding |
| 2026-04-20 | Begin Experiment 2 (credit packs) |

**GROWTH EXPERIMENT: DESIGNED — READY TO INSTRUMENT AND LAUNCH**
