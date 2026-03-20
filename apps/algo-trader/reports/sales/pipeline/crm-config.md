# CRM Configuration Guide — Algo Trader RaaS

**Generated:** 2026-03-19 | **Recommended CRM:** HubSpot (free tier to start) | **Alternative:** Pipedrive, Close.com

---

## CRM Selection

### Recommended: HubSpot (Free Tier)

**Why HubSpot:**
- Free for up to 1M contacts
- Built-in email tracking
- Meeting scheduling (Calendly alternative)
- Pipeline visualization
- Integration with LinkedIn Sales Navigator
- Scalable to Sales Hub Pro ($50/user/month)

**Setup Time:** 2-4 hours

### Alternatives

| CRM | Price | Best For | Limitation |
|-----|-------|----------|------------|
| Pipedrive | $15-99/user/month | Visual pipeline | No free tier |
| Close.com | $49-149/user/month | Built-in calling | Expensive |
| Salesforce | $25-300/user/month | Enterprise | Overkill for early stage |
| Notion + Airtable | $10-20/month | DIY, flexible | Manual setup |

---

## CRM Setup Steps

### Step 1: Create Account

1. Go to [hubspot.com](https://hubspot.com)
2. Sign up for free account
3. Select "Sales Hub" during onboarding
4. Skip paid add-ons (for now)

### Step 2: Configure Pipeline

**Navigate:** Sales → Deals → Pipelines → Create Pipeline

**Pipeline Name:** "Algo Trader Sales Pipeline"

**Create 6 Stages:**

| Stage | Name | Probability |
|-------|------|-------------|
| 0 | Prospecting | 5% |
| 1 | Qualified | 20% |
| 2 | Demo Completed | 40% |
| 3 | Pilot Active | 60% |
| 4 | Negotiation | 80% |
| 5 | Closed Won | 100% |
| 6 | Closed Lost | 0% |

### Step 3: Create Custom Properties

**Navigate:** Settings → Properties → Create Property

**Company Properties:**

| Property Name | Type | Options (if dropdown) |
|---------------|------|----------------------|
| Segment | Dropdown | Prop Shop, Family Office, HNW Trader, Enterprise, Partnership |
| Lead Score | Number | 0-100 |
| AUM Range | Dropdown | <$1M, $1-10M, $10-50M, $50-100M, $100M-$1B, $1B+ |
| Trading Volume | Dropdown | <$100K/day, $100K-$1M, $1M-$10M, $10M-$50M, $50M+ |
| Current Stack | Text | — |
| Competitor | Text | — |
| Tech Maturity | Dropdown | Beginner, Intermediate, Advanced, Expert |

**Contact Properties:**

| Property Name | Type | Options (if dropdown) |
|---------------|------|----------------------|
| Persona | Dropdown | Quant Trader, CTO/Tech Lead, Managing Partner, Individual Trader |
| Decision Authority | Dropdown | Decision Maker, Influencer, Gatekeeper, End User |
| LinkedIn URL | URL | — |
| Twitter Handle | Text | — |
| Timezone | Dropdown | PST, EST, GMT, CET, SGT, AEST, etc. |
| Preferred Contact | Dropdown | Email, LinkedIn, Phone, Twitter |

**Deal Properties:**

| Property Name | Type | Options (if dropdown) |
|---------------|------|----------------------|
| Expected MRR | Currency | — |
| Expected ARR | Currency | — |
| Tier | Dropdown | Starter, Pro, Enterprise, RaaS License |
| Pilot Start Date | Date | — |
| Pilot End Date | Date | — |
| Close Date | Date | — |
| Loss Reason | Dropdown | Price, Building In-House, Not Ready, Competitor, Regulatory, Features, Timing |
| Next Step | Text | — |
| Next Step Date | Date | — |

### Step 4: Import Leads

**Navigate:** Contacts → Contacts → Import

**CSV Format:**

```csv
Company,Contact First Name,Contact Last Name,Email,LinkedIn,Segment,Lead Score,AUM Range,Persona
"Jump Trading",John,Smith,john@jumptrading.com,linkedin.com/in/johnsmith,Prop Shop,95,$10B+,Quant Trader
```

**Import Mapping:**
- Company → Company Name
- Contact First Name → First Name
- Contact Last Name → Last Name
- Email → Email
- LinkedIn → LinkedIn URL (custom property)
- Segment → Segment (custom property)
- Lead Score → Lead Score (custom property)
- AUM Range → AUM Range (custom property)
- Persona → Persona (custom property)

**Import:** 50 leads from lead-list.md

### Step 5: Set Up Email Tracking

**Navigate:** Settings → Sales → Email

**Enable:**
- Email open tracking ✓
- Click tracking ✓
- Reply tracking ✓
- Unsubscribe link ✓

**Connect Gmail/Outlook:**
1. Click "Connect account"
2. Authorize HubSpot
3. Enable sync

### Step 6: Create Email Templates

**Navigate:** Sales → Email → Templates → Create Template

**Create templates for:**
1. Initial Outreach (Prop Shop)
2. Initial Outreach (Family Office)
3. Initial Outreach (HNW Trader)
4. Follow-up
5. Demo Invitation
6. Pilot Proposal
7. Proposal Sent
8. Break-up Email

**Copy templates from:** `outreach-sequences.md`

### Step 7: Create Sequences

**Navigate:** Sales → Sequences → Create Sequence

**Create 5 sequences:**
1. Prop Shop Outreach (7 touches, 21 days)
2. Family Office Outreach (6 touches, 18 days)
3. HNW Trader Outreach (5 touches, 14 days)
4. Enterprise Outreach (8 touches, 30 days)
5. Partnership Outreach (6 touches, 20 days)

**For each sequence:**
1. Add email templates for each touch
2. Set delay between touches (Days 1, 3, 5, 8, 12, 17, 21)
3. Add LinkedIn tasks for sales rep
4. Enable auto-enroll for new leads by segment

### Step 8: Set Up Meeting Links

**Navigate:** Sales → Meetings → Create Meeting Link

**Create 3 meeting types:**

| Meeting Type | Duration | Buffer | Questions |
|--------------|----------|--------|-----------|
| Discovery Call | 30 min | 15 min | "What's your current trading setup?", "What strategies interest you?", "What's your budget range?" |
| Product Demo | 45 min | 30 min | "Which exchanges do you use?", "Any specific strategies?", "Who else should attend?" |
| Pilot Onboarding | 60 min | 30 min | "API keys ready?", "Which strategies to test?", "Success criteria?" |

**Embed Calendly alternative** directly in HubSpot.

### Step 9: Create Dashboards

**Navigate:** Reports → Dashboards → Create Dashboard

**Dashboard 1: Sales Pipeline Overview**

| Report | Type | Filter |
|--------|------|--------|
| Deals by Stage | Funnel | All deals |
| Deals Created | Trend | Last 30 days |
| Deals Closed Won | Trend | Last 30 days |
| Pipeline Value | Single number | All open deals |
| Avg Deal Size | Single number | Closed won |
| Sales Cycle Length | Single number | Closed won |

**Dashboard 2: Activity Metrics**

| Report | Type | Filter |
|--------|------|--------|
| Emails Sent | Trend | Last 7/30 days |
| Email Open Rate | Single number | Last 30 days |
| Email Reply Rate | Single number | Last 30 days |
| Calls Booked | Trend | Last 30 days |
| Demos Completed | Trend | Last 30 days |
| Meetings Completed | Trend | Last 30 days |

**Dashboard 3: Rep Performance** (when team grows)

| Report | Type | Filter |
|--------|------|--------|
| Deals Closed | Bar chart | By rep |
| Revenue Closed | Bar chart | By rep |
| Activity Volume | Bar chart | By rep |
| Conversion Rate | Bar chart | By rep |

### Step 10: Set Up Automation

**Navigate:** Automation → Workflows → Create Workflow

**Workflow 1: Lead Assignment**

```
Trigger: New lead created
Action: Assign to [Your Name]
Action: Set lead status to "New"
Action: Send notification "New lead: [Company]"
```

**Workflow 2: Stage Aging Alert**

```
Trigger: Deal in stage > X days
Conditions:
  - Stage = Qualified AND age > 14 days → Alert AE
  - Stage = Demo AND age > 10 days → Alert Manager
  - Stage = Pilot AND age > 35 days → Alert VP Sales
  - Stage = Negotiation AND age > 30 days → Alert VP Sales
Action: Create task "Follow up on aging deal"
```

**Workflow 3: Pilot Expiry Reminder**

```
Trigger: Pilot End Date is in 3 days
Action: Send email to AE "Pilot ending for [Company]"
Action: Create task "Prepare pilot results report"
```

**Workflow 4: Post-Demo Follow-up**

```
Trigger: Deal stage changed to "Demo Completed"
Wait: 1 day
Action: Send email "Thanks for the demo — here's what we discussed"
Action: Create task "Send pilot proposal"
```

---

## CRM Data Entry Standards

### Company Naming

- Use legal company name when known
- Otherwise use DBA/trading name
- Be consistent: "Jump Trading" not "Jump Trading LLC" or "Jump"

### Contact Naming

- First Name: Given name (not nickname unless preferred)
- Last Name: Family name
- Format: "John Smith" not "J. Smith" or "john@jumptrading.com"

### Email Format

- Use company email when possible (not Gmail/Yahoo unless necessary)
- Verify with tools: Hunter.io, Clearbit, Apollo

### Lead Scoring

Update lead score based on:

| Signal | Score Change |
|--------|--------------|
| Opened email | +2 |
| Clicked link | +5 |
| Replied to email | +10 |
| Booked demo | +15 |
| Attended demo | +20 |
| Started pilot | +25 |
| No response after 7 days | -5 |
| Explicitly not interested | -50 |

### Next Step Field

**ALWAYS populate when updating deal:**

```
Format: [Action] with [Who] on [When]
Examples:
- "Send pilot proposal to John by Fri"
- "Follow up call with Sarah on 3/25"
- "Wait for budget approval (review 4/1)"
```

---

## CRM Integrations

### Essential Integrations

| Tool | Purpose | Setup |
|------|---------|-------|
| Gmail/Outlook | Email sync | Settings → Sales → Email |
| LinkedIn Sales Nav | Lead research | Marketplace → Install |
| Calendly | Meeting scheduling | Marketplace → Install |
| Slack | Deal notifications | Marketplace → Install |
| DocuSign | Contract signing | Marketplace → Install |

### Optional Integrations (Later)

| Tool | Purpose | When to Add |
|------|---------|-------------|
| Apollo | Lead enrichment | >100 leads/month |
| Clearbit | Data enrichment | >500 leads/month |
| Salesloft | Sequence automation | >3 SDRs |
| Outreach | Sequence automation | >5 SDRs |
| Gong | Call recording | >$50K MRR |
| Clari | Forecasting | >$100K MRR |

---

## Weekly CRM Hygiene

### Monday Morning (30 min)

- [ ] Review deals closing this week
- [ ] Check aging deals (overdue next step)
- [ ] Update pipeline forecast

### Daily (15 min)

- [ ] Log all calls/emails from previous day
- [ ] Update deal stages
- [ ] Set next steps for all active deals

### Friday Afternoon (30 min)

- [ ] Review weekly activity metrics
- [ ] Clean up duplicate contacts
- [ ] Archive lost deals with loss reason
- [ ] Plan next week's priorities

### Monthly (2 hours)

- [ ] Review conversion rates by stage
- [ ] Update lead scoring based on wins/losses
- [ ] Clean stale leads (90+ days no activity)
- [ ] Review sequence performance

---

## Reporting Cadence

### Weekly Sales Report

**Navigate:** Reports → Analytics → Create Report

**Metrics:**

| Metric | This Week | Last Week | WoW Change |
|--------|-----------|-----------|------------|
| New Leads | — | — | — |
| Discovery Calls | — | — | — |
| Demos Completed | — | — | — |
| Pilots Started | — | — | — |
| Deals Closed Won | — | — | — |
| MRR Added | — | — | — |
| Pipeline Created | — | — | — |

### Monthly Pipeline Review

| Segment | Leads | Conv Rate | Avg Deal | MRR Added |
|---------|-------|-----------|----------|-----------|
| Prop Shop | — | —% | $— | $— |
| Family Office | — | —% | $— | $— |
| HNW Trader | — | —% | $— | $— |
| Enterprise | — | —% | $— | $— |
| Partnership | — | —% | $— | $— |

---

## Unresolved Questions

1. Should we use HubSpot free tier or start with paid Sales Hub?
2. What's the right lead scoring threshold for "sales ready"?
3. How do we track multi-touch attribution (which channel drove the deal)?
4. Should we integrate with accounting (Stripe/QuickBooks) for revenue tracking?

---

**Next Steps:**

- [ ] Create HubSpot account
- [ ] Configure pipeline stages
- [ ] Import 50 leads from lead-list.md
- [ ] Set up email templates and sequences
- [ ] Connect Gmail/Outlook
- [ ] Create meeting links
- [ ] Set up weekly reporting cadence
