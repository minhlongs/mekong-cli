# Gap Report + 6-Month Roadmap — Mekong CLI

**Date:** 2026-07-04
**Status:** Initial assessment
**Scope:** Mekong CLI product readiness for paying customers

---

## 1. Executive Summary

Mekong CLI has a working CLI tool with 115+ commands and an SDLC pipeline (spec/design/code/deploy/eval), but it has zero revenue, zero conversion infrastructure, zero marketing, and zero customer success. The product is at the "build trap" phase -- functional but unfunded. This report catalogs the critical gaps and lays out a 6-month roadmap to bridge from project to business.

---

## 2. Critical Gaps

### GAP 1: NO ACTIVE BILLING (HIGHEST PRIORITY)

MCU (Mekong Credit Unit) credits exist only in documentation. The Polar.sh integration was started but never completed. There is no way to:

- Accept payment of any kind
- Meter usage
- Enforce tier limits
- Issue invoices or receipts
- Handle refunds or disputes

Without billing, all other business functions are moot.

### GAP 2: NO CONVERSION FUNNEL

An install script exists (`curl ... | sh`) but there is no trial-to-paid flow:

- No free tier vs. paid tier demarcation
- No usage limits enforced in the CLI
- No upsell prompts at any point
- No email capture on install
- No activation event tracking

Users can run the full product indefinitely for free with no friction to convert.

### GAP 3: NO CRM

There is zero pipeline tracking infrastructure:

- No lead database
- No lead scoring model
- No sales stage definitions
- No outreach sequencing
- No deal tracking

Every user is invisible until they voluntarily appear in a GitHub issue or Discord.

### GAP 4: NO METRICS

No actionable business metrics exist:

- No AARRR (Acquisition, Activation, Retention, Revenue, Referral) dashboard
- No North Star metric defined
- No daily/weekly/monthly active user tracking
- No conversion rate measurement
- No churn tracking (because there are no paying users)
- No revenue dashboards

Decisions are made entirely on anecdote and instinct.

### GAP 5: NO CONTENT MARKETING

The product has zero discoverability outside of direct referrals:

- Zero SEO -- no blog, no docs site indexed by search engines
- Zero social media presence -- no Twitter/X, no LinkedIn, no YouTube
- Zero community posts -- no Indie Hackers, no Hacker News launches
- Zero case studies or testimonials
- Zero thought leadership or tutorials

When someone searches for "AI agent CLI" or "SDLC automation tool," Mekong CLI does not appear anywhere.

### GAP 6: NO CUSTOMER SUCCESS

Once a user installs Mekong CLI, there is no structured support:

- No onboarding flow or walkthrough
- No knowledge base or FAQ
- No support channel (no email, no chat, no ticketing system)
- No success milestones or check-ins
- No feedback loop

Users who hit a wall silently churn.

---

## 3. 6-Month Roadmap

### Month 1: Monetization Foundation

**Objective:** Enable paying customers.

- **Billing system** -- Integrate NOWPayments (crypto) or Stripe for subscription billing
- **Tier enforcement** -- Gate premium features (large-scale eval, parallel agents, custom plans) behind tier checks
- **Trial flow** -- 14-day free trial with email capture, then degraded free tier
- **Usage metering** -- Count MCU consumption per user, enforce per-tier caps
- **Invoice generation** -- Automated monthly receipts

Deliverable: First $1 of revenue.

### Month 2: Landing Page + Waitlist

**Objective:** Establish a credible web presence.

- **Landing page** -- Single-page site with hero, demo GIF, feature list, pricing table, CTA
- **Interactive demo** -- Embed a terminal-asciinema or interactive playground
- **Waitlist** -- Capture emails for early access ("Launching Q3 2026")
- **Pricing page** -- Three tiers (Free, Pro, Enterprise) with clear feature comparison
- **Changelog / roadmap page** -- Public-facing for community trust

Deliverable: 500 waitlist signups.

### Month 3: Content Marketing Launch

**Objective:** Drive organic awareness.

- **Blog launch** -- Weekly posts: tutorials, architecture deep-dives, use-case walkthroughs
- **Twitter/X** -- Daily posting cadence: tips, snippets, launch progress, community highlights
- **Indie Hackers** -- Build-in-public thread: revenue, learnings, metrics
- **Hacker News** -- Launch post + Show HN with demo
- **SEO foundation** -- Keyword research, meta tags, sitemap, structured data

Deliverable: 10k monthly organic site visits, 100 followers on Twitter.

### Month 4: CRM + Outbound Sales

**Objective:** Convert awareness into pipeline.

- **CRM setup** -- Deploy HubSpot / Salesforce / self-hosted option with pipeline stages
- **Lead scoring** -- Define ICP signals: CLI installs, eval runs, plan creation frequency
- **Outbound sequencing** -- 50 cold emails/week to dev-tool buyers (CTOs, platform engineers)
- **Referral program** -- "Invite a teammate, both get 500 bonus MCU"
- **Case studies** -- Interview 3 active power users, publish their stories

Deliverable: 50 qualified leads in pipeline, 5 active trials.

### Month 5: Metrics Dashboard + OKR Tracking

**Objective:** Data-driven decision making.

- **North Star metric** -- Define primary metric (e.g., "Weekly Active Eval Runs" or "MCU consumed/week")
- **AARRR dashboard** -- Real-time board showing acquisition through referral
- **Usage analytics** -- Per-feature adoption rates, drop-off funnels
- **Customer health scores** -- Engagement + satisfaction composite per account
- **Weekly business review** -- Automated report to stakeholder email

Deliverable: Single source of truth for all business metrics.

### Month 6: First 100 Paying Customers

**Objective:** Validate product-market fit at scale.

- **Referral engine** -- In-product "share Mekong" with trackable links
- **Affiliate program** -- 20% lifetime commission for blog/video/community referrals
- **Paid acquisition** -- Small-budget Google Ads + Twitter Ads ($500/mo test)
- **Enterprise sales** -- 5-target account list with personalized demos
- **Churn reduction** -- Win-back email sequence for lapsed trials
- **Community launch** -- Official Mekong CLI Discord with support channels

Deliverable: 100 paying accounts, $5k MRR.

---

## 4. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Billing integration drags past Month 1 | Medium | High | Start NOWPayments + Stripe in parallel; whichever ships first wins |
| No developer willingness to pay | High | Critical | Validate via pre-orders on landing page in Month 2; pivot to enterprise-only if self-serve fails |
| Content marketing yields zero traction | Medium | Medium | Test 5 angles in Month 3; double down on top 2 only |
| Single-person founder burnout | Medium | High | Automate everything (deploy, billing, support bot); outsource content writing |
| Open-source competitor emerges | Low | Medium | Focus on integrated SDLC pipeline as moat; commoditize the CLI layer |

---

## 5. Immediate Next Steps

1. Accept that billing is the only real priority until money flows
2. Pick ONE payment provider (NOWPayments or Stripe) and finish integration this week
3. Gate two premium features behind tier check to create conversion pressure
4. Publish the landing page with waitlist capture -- even if ugly
5. Ship something every day and post about it publicly

---

*File: /Users/macbook/mekong-cli/plans/company-blueprint/03-gap-report.md*
