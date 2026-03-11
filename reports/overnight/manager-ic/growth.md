# Growth Engineer Report — Mekong CLI
*Role: Growth Engineer | Date: 2026-03-11*

---

## Growth Model

Mekong CLI is a pure PLG (Product-Led Growth) motion. The product is the funnel.
Growth levers are: acquisition (GitHub stars → pip installs), activation (first
successful `mekong cook`), retention (MCU credit renewal), and expansion (tier upgrade).

```
ACQUISITION          ACTIVATION           RETENTION          EXPANSION
GitHub star      →   pip install      →   first cook     →   credit renewal
HN / Reddit          mekong init          second cook        tier upgrade
Word of mouth        LLM configured       weekly usage       team seats
```

---

## Activation Funnel Analysis

Current estimated funnel (baseline — needs instrumentation):

| Step | Est. Rate | Drop Reason |
|------|-----------|-------------|
| GitHub star → pip install | 40% | Friction: need to read README first |
| pip install → first cook | 62% | Friction: 3 env var exports required |
| first cook → success | 70% | LLM API errors, model not found |
| success → credit purchase | 12% | Unclear value prop for paid tier |
| credit purchase → month 2 | 75% | Good if first cook worked |

**Biggest lever: pip install → first cook (38% drop)**
Fix: `mekong init --wizard` interactive LLM setup. Estimated lift: +15% activation.

---

## PLG Motions

### Motion 1: Free-Forever with Ollama
Ollama path = zero cost, zero friction after initial setup. Viral because:
- Developer installs, shares with colleague
- "It's free" removes budget objection entirely
- Ollama users become advocates on r/LocalLLaMA

Growth tactic: Create `mekong init --ollama` one-command Ollama setup.
Auto-pulls `qwen2.5-coder`, sets env vars, runs test cook.

### Motion 2: GitHub Star → Email Sequence
On star: trigger 3-email onboarding sequence via ConvertKit.
Day 0: Quick start (2 steps). Day 3: "Did your first cook work?" Day 7: Pro tier pitch.

### Motion 3: Show HN Launch
Single HN post drives 500-2,000 GitHub stars in 24 hours for strong projects.
Requirements before launch: GIF demo, clean README, working `make self-test`.

### Motion 4: Viral Command Output
When `mekong cook` succeeds, output includes:
```
✓ Mission complete. Built with Mekong CLI (github.com/longtho638-jpg/mekong-cli)
```
Developers copy-paste terminal output to Slack/Twitter → passive brand exposure.

### Motion 5: Plugin Ecosystem Flywheel
Community plugins → more use cases → more installs → more plugin contributors.
Target: 10 community plugins within 90 days of plugin registry launch.

---

## Viral Loops

**Loop 1: Open Source Contribution**
User hits limitation → opens GitHub issue → contributor fixes → user shares fix →
new contributor discovers project → loop repeats.

**Loop 2: Command Sharing**
`mekong cook "Build X"` produces shareable output. Developer posts to Twitter/HN.
Viewers see terminal demo → visit GitHub → star → install → loop.

**Loop 3: Team Adoption**
One developer on a team installs → shares with team → team adopts →
team grows → Enterprise tier upgrade → more revenue → more features.

---

## Activation Metrics (North Star)

**North Star Metric: Weekly Active Cooks (WAC)**
Definition: unique users who ran at least one `mekong cook` in the past 7 days.

Supporting metrics:
| Metric | Definition | Target (90 days) |
|--------|-----------|-----------------|
| Time to first cook (TTFC) | pip install → first `mekong cook` success | <5 min |
| Day-7 retention | Users who cook again in first week | >40% |
| Day-30 retention | Users who cook again in first month | >25% |
| Feature breadth | Avg commands used per active user/week | >3 |
| Credit refill rate | % users who refill before expiry | >60% |

---

## Instrumentation Plan

Tools: PostHog (open source, self-hostable on CF) + CF Analytics.

Events to track:
```python
# In src/main.py — add analytics calls
posthog.capture('pip_install', {'version': VERSION})
posthog.capture('mekong_cook_started', {'model': model_provider})
posthog.capture('mekong_cook_success', {'duration_sec': elapsed, 'steps': step_count})
posthog.capture('mekong_cook_failed', {'error': error_type})
posthog.capture('pricing_page_viewed', {})
posthog.capture('credit_purchased', {'tier': tier, 'amount': amount})
```

Privacy: opt-out flag `--no-telemetry`. Disclose in README.

---

## Growth Experiments (Prioritized)

| Experiment | Hypothesis | Metric | Effort |
|------------|-----------|--------|--------|
| `mekong init --wizard` | Reduces TTFC from 10min → 2min | TTFC, D7 retention | Medium |
| Viral footer in cook output | +5% GitHub referral traffic | GitHub referrals | Low |
| Ollama one-click setup | +20% activation on macOS | pip→cook conversion | Low |
| Show HN launch | +1,000 GitHub stars in 24hrs | Stars, installs | Low |
| Email onboarding sequence | +8% free→paid conversion | Conversion rate | Medium |

---

## Q2 Growth Actions

- [ ] Instrument funnel with PostHog (opt-out telemetry)
- [ ] Build `mekong init --wizard` (highest leverage activation fix)
- [ ] Set up GitHub star → email automation (ConvertKit or Loops.so)
- [ ] Prepare Show HN submission (after wizard ships)
- [ ] Add viral footer to successful `mekong cook` output
- [ ] Create PostHog dashboard with WAC as North Star metric
