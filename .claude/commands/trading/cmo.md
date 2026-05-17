---
description: ⚡⚡⚡⚡⚡⚡ CMO Marketing Command — brand, community, content, growth, revenue, competitive analysis
argument-hint: [action: quarterly|monthly|weekly] [focus: brand|content|community|growth|revenue|compete|launch]
---

**Ultrathink parallel** CMO marketing operations: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader`
**ROLE:** CMO — growth officer. Brand, community, content, revenue.
**REF:** `docs/cmo-sops.md` | `docs/ceo-sops.md`

---

## CMO COMMAND ARCHITECTURE

```
/trading:cmo                    ← THIS: Full marketing review
/trading:cmo:content            ← Content strategy + calendar
/trading:cmo:growth             ← Growth metrics + funnel analysis
/trading:cmo:launch             ← Launch playbook (PH/HN/social)
```

---

## PIPELINE — 8 Steps (Parallel Where Possible)

### 1. BRAND HEALTH CHECK

Audit current brand presence:
- GitHub repo: stars, forks, watchers, issues
- README quality: hero demo, badges, quickstart
- Social: Twitter followers, engagement rate
- Community: Discord members, active/day
- SEO: keyword rankings for target terms

```bash
# GitHub stats (if public)
gh api repos/{owner}/{repo} --jq '.stargazers_count, .forks_count, .open_issues_count'
```

### 2. CONTENT AUDIT (Parallel — 2 Agents)

**Agent A — Content Inventory:**
- List all published content (blog, threads, tutorials)
- Categorize by pillar (70% educational, 20% showcase, 10% community)
- Identify gaps in content calendar
- Report: ≤80 lines

**Agent B — Competitive Content:**
- Scan competitor content (Freqtrade, Hummingbot, 3Commas blogs)
- Identify trending topics in algo trading
- SEO keyword opportunities
- Report: ≤80 lines

### 3. COMMUNITY HEALTH

| Platform | Metric | Target | Current |
|----------|--------|--------|---------|
| Discord | Members | {target} | {current} |
| Discord | DAU | 20% of members | {current} |
| Telegram | Subscribers | {target} | {current} |
| Twitter/X | Followers | {target} | {current} |
| GitHub | Stars | {target} | {current} |
| GitHub | Contributors | {target} | {current} |

Community sentiment: positive/neutral/negative ratio

### 4. GROWTH FUNNEL (AARRR)

```
Acquisition:  GitHub visitors → {N}/week (target: 500)
                ↓ (conversion: XX%)
Activation:   First backtest → {N}/week (target: 30% of installs)
                ↓ (conversion: XX%)
Retention:    Weekly active → {N}/week (target: 40% of activated)
                ↓ (conversion: XX%)
Revenue:      Paid users → {N} (target: 5% of WAT)
                ↓ (conversion: XX%)
Referral:     Stars+forks → {N}/week (target: 20/week)
```

Identify weakest funnel stage → prioritize fix.

### 5. REVENUE ANALYSIS

| Tier | Price | Users | MRR | Trend |
|------|-------|-------|-----|-------|
| Free | $0 | {N} | $0 | — |
| PRO | $29/mo | {N} | ${N} | ↑↓→ |
| TEAM | $99/mo | {N} | ${N} | ↑↓→ |
| Enterprise | Custom | {N} | ${N} | ↑↓→ |

Total MRR: ${N} vs target: ${target}

### 6. COMPETITIVE POSITIONING

| Factor | Us | Freqtrade | Hummingbot | 3Commas |
|--------|----|-----------|-----------:|---------|
| Open source | ✅ | ✅ | ✅ | ❌ |
| CLI-first | ✅ | ❌ | ❌ | ❌ |
| Stealth | ✅ | ❌ | ❌ | ❌ |
| Safety | ✅ | ⚠️ | ⚠️ | ⚠️ |
| AI-powered | ✅ | ❌ | ❌ | ⚠️ |
| Tests | 1216 | ~200 | ~300 | ? |

Positioning gap analysis + messaging recommendations.

### 7. ACTION PLAN

Based on all data, generate prioritized action list:

| Priority | Action | Channel | Owner | Deadline |
|----------|--------|---------|-------|----------|
| P0 | {action} | {channel} | CMO | {date} |
| P1 | {action} | {channel} | CMO | {date} |
| P2 | {action} | {channel} | CMO | {date} |

### 8. REPORT

Save: `plans/reports/cmo-{period}-{date}-marketing-review.md`

```markdown
## CMO Marketing Review — {period} {date}

### Executive Summary
[3-5 bullets: growth, content, community, revenue]

### Brand Health
[GitHub stats, social presence, SEO rankings]

### Content Performance
[Top content, gaps, calendar status]

### Community Metrics
[Platform breakdown, sentiment, engagement]

### Growth Funnel (AARRR)
[Conversion rates, weakest stage]

### Revenue
[MRR breakdown, trend, vs target]

### Competitive Position
[Market map, differentiation, threats]

### Action Items
- [ ] {Priority action items with deadlines}
```

---

## USAGE

```bash
# Full quarterly marketing review
/trading:cmo quarterly

# Monthly growth check
/trading:cmo monthly

# Weekly content review
/trading:cmo weekly

# Specific focuses
/trading:cmo brand            # Brand audit
/trading:cmo content          # Content strategy
/trading:cmo community        # Community health
/trading:cmo growth           # Growth funnel
/trading:cmo revenue          # Revenue analysis
/trading:cmo compete          # Competitive analysis
/trading:cmo launch           # Launch playbook

# Sub-commands
/trading:cmo:content          # Deep content planning
/trading:cmo:growth           # Growth metrics + optimization
/trading:cmo:launch           # PH/HN launch workflow
```
