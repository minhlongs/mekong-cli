# Client Operations — Mekong CLI

## Overview
Client operations covers the full customer lifecycle: onboarding new subscribers, managing ongoing relationships, collecting feedback, and driving retention. For Mekong CLI, "client ops" spans self-serve Starter/Pro users and high-touch Enterprise accounts.

---

## Customer Segments & Ops Model

| Segment | Tier | Ops Model | Primary Commands |
|---------|------|-----------|-----------------|
| Self-serve devs | Starter $49 | Automated | Email sequences, docs |
| Technical founders | Starter/Pro | Light-touch | Email + async support |
| Agency owners | Pro/Enterprise | High-touch | Dedicated onboarding |
| Enterprise teams | Enterprise $499 | White-glove | Custom onboarding + CSM |

---

## Client Onboarding (commands: `mekong business-client-onboard`, `mekong client`, `mekong people-onboard`)

### Starter/Pro Onboarding (Automated)

Triggered immediately on Polar.sh payment webhook:

```
T+0min:  Polar.sh webhook → credit grant in D1 ledger
T+1min:  Welcome email sent:
         - MCU balance: 200/1000
         - Quick start: 3 commands to run first
         - Docs link: agencyos.network/docs
         - Discord/community link

T+1hr:   Activation email:
         "Have you run your first mekong cook yet?"
         + tutorial: "mekong cook 'Create a sales email for a SaaS'"

T+24hr:  Tip email:
         Command of the day relevant to their signup context

T+7days: Check-in email:
         "How many MCU credits have you used?"
         + upsell signal: if >100 MCU used, suggest Pro
```

### Enterprise Onboarding (`mekong business-client-onboard`)

High-touch process for $499/mo accounts:

```
Week 1: Kickoff
  - 45-min video call: goals, stack, use cases
  - mekong business-client-onboard "CompanyName" → generates onboarding plan
  - Deliver: custom .env config for their LLM provider
  - Deliver: 5 commands tailored to their primary pain

Week 2: Deep Integration
  - Pair session: run mekong cook on their actual workflow
  - Connect to their tools: GitHub, Slack, Cloudflare
  - Set up mekong daemon (Tôm Hùm) for autonomous task dispatch

Week 3: Team Enablement
  - Run mekong hr-onboard equivalent for their engineers
  - Deliver: custom command templates for their business
  - Set up mekong status dashboard for their account

Week 4: Success Review
  - 30-min check-in: MCU usage review, ROI calculation
  - Identify expansion: more team members, more command categories
  - Set 90-day success criteria
```

---

## CRM & Customer Data (command: `mekong crm`)

### CRM Data Model
```
Customer record:
- ID: Polar.sh customer ID
- Tier: Starter | Pro | Enterprise
- MCU balance: live from D1 ledger
- MCU burn rate: avg credits/day (30-day rolling)
- Activation date: first command run
- Last active: last command timestamp
- Health score: composite of usage + support tickets + NPS
- Tags: [dev, founder, agency, enterprise], [activated, at-risk, churned]
```

### CRM Actions (`mekong crm`)
- **At-risk identification**: MCU burn rate drops >50% → trigger re-engagement
- **Expansion signals**: burn rate approaching tier limit → trigger upsell
- **Churn prediction**: 14+ days no activity → trigger save campaign

---

## Customer Research (command: `mekong customer-research`)

### Research Methods
1. **In-app NPS**: Triggered at Day 30 and quarterly (`mekong feedback`)
2. **Usage analytics**: MCU by command category → reveals actual use cases
3. **Exit interviews**: Triggered on cancellation (`mekong people-offboard` adapted)
4. **User interviews**: Monthly, 3-5 customers per month (`mekong ux-interview`)
5. **GitHub issues**: Feature requests as qualitative research

### Key Research Questions
- Which commands are most used? (→ double down, write more docs)
- Which commands are purchased but never run? (→ onboarding gap)
- What blocks customers from using Mekong CLI daily? (→ UX/friction)
- What would make them recommend to 3 friends? (→ referral program design)

### Research Cadence (`mekong customer-research`)
```
Weekly:   Review MCU usage analytics by command category
Monthly:  3-5 customer interviews (30 min each)
Quarterly: NPS survey to all active customers
Ongoing:  Monitor GitHub issues + Discord/community
```

---

## Feedback Loop (command: `mekong feedback`)

### Feedback Collection Points
- **Post-command**: Optional rating after each `mekong cook` run
- **Monthly NPS**: Email survey (1-10 scale + open text)
- **GitHub issues**: Direct feature requests and bug reports
- **Community Discord**: Ambient feedback from power users

### NPS Response Protocol
| NPS Score | Action | Command |
|-----------|--------|---------|
| 9-10 (Promoter) | Ask for referral, testimonial, case study | `mekong crm` |
| 7-8 (Passive) | Ask what would make it a 10 | `mekong feedback` |
| 0-6 (Detractor) | Urgent outreach within 24h, find root cause | `mekong client` |

### Feature Request Prioritization
```
1. mekong customer-research → aggregate all feedback
2. Score by: frequency × customer tier weight
3. Enterprise requests: 5x weight (higher LTV)
4. Add to roadmap via mekong roadmap
5. Communicate back to requester when shipped
```

---

## Customer Health Scoring

### Health Score Formula
```
Score (0-100) =
  MCU usage rate (40%) +     # actual vs expected burn
  Command diversity (20%) +  # breadth of commands used
  Recency (20%) +            # days since last command
  Support satisfaction (10%) + # ticket resolution NPS
  Expansion signals (10%)    # upgrade trajectory
```

### Health Segments
| Score | Segment | Action |
|-------|---------|--------|
| 80-100 | Healthy | Identify for case study/referral |
| 60-79 | Stable | Monthly check-in email |
| 40-59 | At-risk | Proactive outreach, usage review |
| 0-39 | Red | Urgent intervention, offer migration help |

---

## Customer Success Metrics

| Metric | Target | Measurement |
|--------|--------|------------|
| Time to first command | <10 min after signup | D1 event log |
| Activation rate (run 3+ commands) | >60% in week 1 | MCU ledger |
| Day 30 retention | >70% | Polar.sh renewals |
| Day 90 retention | >60% | Polar.sh renewals |
| NPS | >50 | Monthly survey |
| Support ticket resolution | <24h | Issue tracker |
| Expansion rate | 20% upgrade Starter→Pro/quarter | Polar.sh tier data |
| Enterprise renewal rate | >90% | Manual tracking |
