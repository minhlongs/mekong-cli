# Sales Pipeline — Mekong CLI

**Model:** Product-led, self-serve | **Updated:** March 2026

---

## Funnel Stages

```
AWARENESS → CONSIDERATION → TRIAL → ACTIVATION → CONVERSION → RETENTION
```

| Stage | Definition | Volume Target (Q2) | Conversion |
|-------|-----------|-------------------|-----------|
| Awareness | Sees Mekong CLI mentioned anywhere | 5,000 | → 10% |
| Consideration | Visits GitHub or docs site | 500 | → 50% |
| Trial | Runs `pip install mekong-cli` | 250 | → 20% |
| Activation | Runs first successful mission | 50 | → 60% |
| Conversion | Pays for Starter ($49) | 30 | → 70% |
| Retention | Active at Day 30 | 21 | ~70% |

---

## Stage-by-Stage Optimization

### Stage 1 → 2: Awareness to Consideration
**Bottleneck:** Making the pitch compelling enough to click
- README headline must answer "what is this and why do I care" in 10 seconds
- Demo GIF shows result, not process
- GitHub stars as social proof

**Metrics:** Referral traffic sources, README bounce rate (time on page proxy)

### Stage 2 → 3: Consideration to Trial
**Bottleneck:** Install friction
- `pip install mekong-cli` must work on first try (no dependency hell)
- README quickstart: 3 commands max to first output
- Error messages must be helpful, not cryptic

**Metrics:** PyPI install count, GitHub clone count

### Stage 3 → 4: Trial to Activation
**Bottleneck:** First mission success
- First command must work without LLM API key setup friction
- Onboarding wizard: `mekong setup` should guide through LLM config
- Default to OpenRouter (easiest signup) as recommended provider

**Metrics:** % of installs that run at least one command (telemetry opt-in)

### Stage 4 → 5: Activation to Conversion
**Bottleneck:** Willingness to pay
- Free tier must be generous enough to prove value (5 free MCU on install?)
- Upgrade prompt shown after first successful mission: "Loved it? Get 200 MCU/mo for $49"
- Polar.sh checkout must be frictionless (< 3 clicks)

**Metrics:** Trial → paid conversion rate (target 20%)

### Stage 5 → 6: Conversion to Retention
**Bottleneck:** Habit formation
- Weekly usage reminder if no command in 7 days
- Showcase what others built (#showcase Discord)
- New command releases keep product fresh

**Metrics:** Day-30 retention rate (target 70% for Starter)

---

## Pipeline by Tier

### Starter ($49/mo) — Self-serve
- No sales touch needed
- Polar.sh handles checkout
- Automated welcome email on signup

### Pro ($149/mo) — Light touch
- Automated upgrade prompt when Starter hits 80% MCU
- "Book a 20-min call" option for Pro prospects
- Custom use case walkthrough offered

### Enterprise ($499/mo) — High touch
- Inbound only (no cold outreach at this stage)
- Schedule demo call
- Custom onboarding + Slack channel
- Invoice billing option (not Polar.sh)

---

## Pipeline Health Metrics

| Metric | Target | Current | Alert |
|--------|--------|---------|-------|
| Trial signups/mo | 50 | 0 (pre-launch) | < 10 |
| Trial → paid conversion | 20% | — | < 10% |
| Time to first mission | < 5 min | — | > 15 min |
| Upgrade rate (Starter → Pro) | 20% | — | < 10% |
| Churn rate | < 6%/mo | — | > 10% |

---

## Q2 Pipeline Actions

- [ ] Add free MCU trial (5 credits on install, no card required)
- [ ] Build `mekong setup` onboarding wizard
- [ ] Implement upgrade prompt post-mission
- [ ] Set up Polar.sh webhook → welcome email
- [ ] Create #showcase Discord channel
