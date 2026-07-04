# 17 - Risk + Scenario OS

> Risk register, scenario analysis, and response playbooks for Mekong CLI.

---

## 1. Risk Register

| # | Risk | Impact | Probability | Mitigation |
|---|------|--------|------------|------------|
| R01 | AI model providers shut down | Critical | Low | Support multiple providers (Ollama, Claude, Gemini) |
| R02 | Competitor builds similar tool | High | Medium | First-mover advantage + community moat |
| R03 | LLM API costs eat margin | Medium | Medium | Local-first option via Ollama / MLX |
| R04 | Zero paying customers | Critical | Medium | Fix billing immediately, gate features |
| R05 | Security breach / data leak | Critical | Low | Local-first = data stays on user machine |
| R06 | Single point of failure (maintainer) | High | Medium | Document all flows, recruit co-maintainers |
| R07 | Dependency supply chain attack | High | Low | Lock files, Dependabot + npm audit in CI |
| R08 | CLI breaks on new OS / arch | Medium | Medium | Cross-platform CI matrix (macOS, Linux, Windows) |
| R09 | Users bypass payment (piracy) | Medium | Low | Self-hosted license key, honor system |
| R10 | Cloud provider cost overrun | Medium | Low | Serverless + usage caps per deployment |

---

## 2. Scenario Analysis

### Scenario A: Model Provider Shutdown (R01)

**Trigger:** OpenAI, Anthropic, or Ollama discontinues API access or free tier.

**Impact:**
- Users on cloud-only mode lose all functionality
- Reputation damage from sudden outage
- Migration time to alternate provider

**Response:**
1. Detect failure via health-check endpoint
2. Fall back to secondary provider in provider chain config
3. Notify user: "Provider X unreachable — routed to Y"
4. If all cloud providers down, prompt user to enable local Ollama

**Recovery target:** 15-minute automatic failover.

---

### Scenario B: Zero Revenue (R04)

**Trigger:** 90 days post-launch with zero paid conversions.

**Impact:**
- Cannot fund infrastructure or development
- Project viability in question
- Community loses confidence

**Response:**
1. Survey free-tier users: what is the blocker?
2. Check price point vs willingness-to-pay
3. Add trial-gated premium features (team sharing, priority support)
4. Consider one-time payment instead of subscription

**Escape condition:** 5+ paid users within 30 days of pricing change.

---

### Scenario C: Competitor Launch (R02)

**Trigger:** A well-funded competitor releases CLI AI tool with overlapping features.

**Impact:**
- Slowed user acquisition
- Pressure to race on features instead of quality
- Community fragmentation

**Response:**
1. Double down on Mek的不同iators: workflow plans, local-first, no-VC independence
2. Publish comparison page showing honest trade-offs
3. Focus on existing user happiness over new-user chase
4. Invest in community content (tutorials, templates, integrations)

**Do NOT:** panic-ship features, lower prices, or engage in FUD.

---

### Scenario D: Security Incident (R05)

**Trigger:** Reported vulnerability (CVE, GitHub disclosure, or user report).

**Impact:**
- Credential exposure (API keys stored in config)
- Trust erosion
- Possible fork / migration away

**Response:**
1. Immediate: verify report, reproduce locally
2. If confirmed: patch within 24 hours
3. Release security advisory with severity, scope, fix version
4. Rotate any exposed secrets
5. Post-mortem: how did it happen? How to prevent recurrence?

**Prevention:** All secrets encrypted at rest; config directory has 0700 permissions; no telemetry by default.

---

### Scenario E: Maintainer Burnout / SPOF (R06)

**Trigger:** Maintainer unavailable for 2+ weeks with open issues and PRs.

**Impact:**
- Unmerged PRs pile up
- Critical bugs go unfixed
- Community feels abandoned

**Response:**
1. Immediately: add co-maintainers from active community
2. Document every deploy, release, and decision process
3. Set up automated CI/CD so releases need minimal human touch
4. Create `docs/maintainer-handover.md` with runbook

**Prevention:** Start shared-maintainer model before burnout hits.

---

## 3. Response Playbooks by Severity

### Critical (R01, R04, R05)

| Step | Action | Owner | Time |
|------|--------|-------|------|
| 1 | Acknowledge incident | Lead | < 1 h |
| 2 | Communicate to users (GitHub + Discord) | Lead | < 2 h |
| 3 | Apply hotfix or mitigation | Engineer | < 24 h |
| 4 | Root cause analysis | Lead | < 48 h |
| 5 | Deploy permanent fix | Engineer | < 72 h |
| 6 | Post-mortem published | Lead | < 1 week |

### High (R02, R06, R07)

| Step | Action | Owner | Time |
|------|--------|-------|------|
| 1 | Assess impact scope | Lead | < 1 day |
| 2 | Draft response plan | Lead | < 2 days |
| 3 | Execute mitigation | Engineer | < 1 week |
| 4 | Monitor effectiveness | All | Ongoing |

### Medium (R03, R08, R09, R10)

| Step | Action | Owner | Time |
|------|--------|-------|------|
| 1 | Log and track in issues | Anyone | < 1 week |
| 2 | Schedule for next milestone | Lead | Next sprint |
| 3 | Implement fix | Engineer | Per sprint |
| 4 | Verify resolution | QA / CI | Before close |

---

## 4. Risk Budget

| Quarter | Acceptable critical risks | Acceptable high risks | Target residual risk |
|---------|--------------------------|----------------------|----------------------|
| Q3 2026 | 0 | 1 | Low |
| Q4 2026 | 0 | 0 | Very low |

---

## 5. Review Cadence

- **Weekly:** Check active risks during standup
- **Monthly:** Full risk register review, update probabilities
- **Quarterly:** Scenario walkthrough (tabletop exercise)
- **Per release:** Verify mitigations for affected risks
