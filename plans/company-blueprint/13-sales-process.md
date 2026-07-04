# 13. Sales Process + Channels

> Sales pipeline, go-to-market channels, and CRM for mekong-cli.

## Pipeline Stages

### 1. Lead (organic install or signup)
- **Source detection**: Track which funnel entry point the user arrived through (npm install, GitHub clone, website signup, referral).
- **Capture**: Auto-collect during CLI onboarding wizard (email + company name) or via website form.
- **Lead score**: Weighted by source (referral > direct > organic) and company profile (startup / agency / enterprise).
- **Triage**: Unknown companies go to nurture; known ICP targets flagged for founder outreach.
- **Goal**: 100% of leads captured and scored before next stage.
- **Exit criteria**: Valid email + company name recorded in CRM.

### 2. Active Trial (installed + configured)
- **Trigger**: User completes `mekong init` or runs a first command after signup.
- **Onboarding check**: Has the user run at least 3 different commands? Have they set up a key (BYOK or built-in)?
- **Engagement signal**: Commands run per session, features explored, errors encountered.
- **Timebox**: 14-day trial clock starts at first `mekong` command.
- **Nurture triggers**:
  - Day 1: Send getting-started guide (email).
  - Day 3: Check engagement — if idle, send re-engagement email with video walkthrough.
  - Day 7: Mid-trial check-in — offer 1-on-1 founder call.
  - Day 12: Trial-expiry warning + upgrade prompt.
- **Goal**: User runs 10+ commands and explores at least 2 skill categories.
- **Exit criteria**: Trial expired (moves to Churned) or user requests pricing/demo (moves to Qualified).

### 3. Qualified (requested pricing or demo)
- **Trigger**: User clicks "Pricing" in CLI, fills a contact form, or replies to a nurture email requesting more info.
- **Classification**:
  - Self-serve intenders — likely fit for Starter tier; route to automated upgrade flow.
  - Demo requesters — high-intent, likely Growth or Pro; route to founder sales call.
- **Touches**:
  - Same-day reply (founder or auto-reply with calendar link).
  - Pre-call brief: gather company size, use-case, budget range.
  - Send case studies relevant to their industry/role.
- **Goal**: Schedule a call or send a proposal within 48 hours.
- **Exit criteria**: Proposal sent (moves to Proposal) or prospect goes silent > 7 days (moves to Closed Lost).

### 4. Proposal (custom quote for Growth/Pro)
- **Trigger**: Founder and prospect agree to discuss pricing beyond Starter tier.
- **Proposal components**:
  - Tier recommendation (Growth vs Pro) with justification.
  - Custom pricing based on usage volume (seats, commands/month, storage).
  - Implementation timeline (self-serve < 1 day; guided setup 1-2 weeks).
  - Success metrics and expected ROI.
- **Follow-up cadence**:
  - Day 0: Send proposal PDF + calendar for Q&A call.
  - Day 3: Follow-up email with testimonials.
  - Day 7: Final follow-up with time-limited discount (optional).
- **Goal**: Close within 14 days of proposal date.
- **Exit criteria**: Signed subscription (Closed Won) or prospect declines / ghosts (Closed Lost).

### 5. Closed Won (paid subscription)
- **Trigger**: Payment received (Stripe / NOWPayments invoice paid).
- **Post-sale actions**:
  - Provision tier features (unlock Growth/Pro capabilities).
  - Send welcome email with onboarding docs.
  - Schedule 30-day check-in call.
  - Assign success contact (founder or support email).
- **Metric**: Time from lead to close (target < 30 days).
- **Goal**: 90% retention at 90 days.
- **Exit criteria**: Subscription active and first onboarding call completed.

### 6. Closed Lost (churned or inactive)
- **Trigger**: Trial expired with no conversion, proposal declined, or paid subscription cancelled.
- **Sub-categories**:
  - Trial churn: Never converted from 14-day trial.
  - Proposal lost: Chose competitor, no budget, or not a fit.
  - Voluntary churn: Cancelled paid subscription.
  - Involuntary churn: Payment failure after retries.
- **Retention attempt**:
  - Trial churn: Send "come back" email with 7-day extension after 30 days.
  - Paid churn: Offer discounted re-activation + founder call within 7 days.
  - Payment failure: Auto-retry card up to 3 times; email contact after 2nd failure.
- **Data captured**: Churn reason, final usage stats, feedback (optional survey).
- **Goal**: Re-activate 15% of churned leads within 90 days.
- **Exit criteria**: Lead moved to suppression list or re-enters pipeline via new signup.

## Channels

### PLG (Product-Led Growth)
- **Channel**: Self-serve download from GitHub or npm (`npx mekong-cli`).
- **Funnel**: Install -> `mekong init` -> run commands -> trial -> upgrade to Starter.
- **Conversion lever**: Feature gating (Starter gets core skills; Growth adds advanced AI model routing, Pro adds team seats + SSO).
- **Free tier**: Perpetual free with limited command quota (100 commands/month) to drive adoption.
- **Metrics tracked**: Install-to-activation rate, activation-to-trial rate, trial-to-paid conversion, viral coefficient (invites sent per user).
- **Upgrade prompts**: In-CLI upgrade notice at quota limit, email sequence at trial milestones.
- **Advantage**: Low friction, zero sales cost, global reach via npm registry.
- **Risk**: Low conversion rate without active onboarding.

### Direct (Founder Outbound)
- **Channel**: Founder-led sales targeting ICP accounts.
- **ICP**: AI startups, agency teams building LLM workflows, enterprise R&D groups.
- **Outbound motion**: LinkedIn DM, personalized email, warm intros from network.
- **Deal size**: Growth ($500-2k/mo) and Pro ($2k-10k/mo) tiers.
- **Sales cycle**: 2-4 weeks from first touch to close.
- **Triggers for outbound**: GitHub stars + active repos in adjacent space, startup job postings mentioning AI/LLM, conference attendees.
- **Materials needed**: One-pager, case study deck, demo environment, ROI calculator.
- **Advantage**: High-touch closes larger deals; builds product feedback loop.
- **Risk**: Time-intensive; scales poorly without SDR hire.

### Partnership (Agency Resellers) — Future
- **Channel**: Agencies that resell mekong-cli to their clients.
- **Model**: White-label or co-branded CLI with agency's toolchain.
- **Revenue share**: 20% recurring commission on referrals.
- **Partner program needs**:
  - Partner portal (track referrals, commissions, support tickets).
  - Co-marketing budget (case studies, joint webinars).
  - Technical integration support.
- **Target partners**: DevOps consultancies, AI implementation agencies, cloud consulting partners.
- **Timeline**: Target Q3 2026 for pilot with 2-3 agencies.
- **Advantage**: Leverage existing customer relationships for scale.
- **Risk**: Margin compression, brand dilution, support overhead.

## CRM

### Tool Choice
- **Primary**: HubSpot Free CRM (no-cost entry with essential pipeline tracking).
- **Fallback**: Airtable + manual pipeline sheet (if HubSpot free tier limits bind).
- **Migration path**: Upgrade to HubSpot Starter ($20/mo) when active leads exceed 50.

### Fields to Track
| Field | Type | Stage |
|-------|------|-------|
| Company name | Text | All |
| Contact email | Email | All |
| Source | Enum (npm, GitHub, referral, conference, cold outbound) | Lead |
| Lead score | Number (1-100) | Lead |
| Trial start date | Date | Trial |
| Commands run | Number | Trial |
| Trial expiry date | Date | Trial |
| Tier interest | Enum (Starter, Growth, Pro) | Qualified |
| Proposal sent date | Date | Proposal |
| Proposal value | Currency | Proposal |
| Close date | Date | Closed Won / Lost |
| Churn reason | Text | Closed Lost |
| Re-activation date | Date | Closed Lost |

### Pipeline Metrics (Dashboards)
- **Lead-to-trial conversion**: % of signups that start a trial.
- **Trial-to-paid conversion**: % of trials that convert to paid.
- **Average sales cycle length**: Days from Lead to Closed Won.
- **Win rate**: Closed Won / (Closed Won + Closed Lost) per month.
- **Churn rate (monthly)**: Cancelled subscriptions / active subscriptions.
- **Net Revenue Retention**: Recurring revenue from existing customers after upgrades/downgrades/churn.
- **CAC**: Total sales + marketing cost / new customers acquired.
- **LTV**: Average revenue per customer / monthly churn rate.

### Automation Rules
- **Lead creation**: Auto-created on website form submit or CLI onboarding completion.
- **Stage advancement**: Manual trigger by founder (for direct sales) or auto-promote from Trial to Qualified when pricing page is accessed.
- **Churn detection**: Automated based on subscription status change from payment provider webhook.
- **Nurture sequences**: HubSpot workflow triggered by stage + last activity date (email sequence).
- **Alert**: Founder notified via Slack webhook when a lead enters Qualified or Proposal stage.
