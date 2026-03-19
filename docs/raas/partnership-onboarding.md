# RaaS Partner Onboarding Guide

> **Operational Playbook** — Step-by-step guide for onboarding new RaaS partners

**Version:** 1.0.0 | **Last Updated:** 2026-03-19 | **Audience:** Partner Operations Team

---

## Quick Reference

| Phase | Duration | Owner | Key Milestone |
|-------|----------|-------|---------------|
| 1. Application | 3-5 days | Partner Ops | Signed agreement |
| 2. Onboarding | 5-7 days | Success Manager | Training complete |
| 3. Go-Live | 2-3 days | Technical Lead | First mission submitted |
| 4. Growth | Ongoing | Account Manager | 3+ active clients |

---

## Phase 1: Application (Week 1)

### Step 1.1: Receive Application

**Source:** `https://agencyos.network/partners/apply`

**Application Data Schema:**
```json
{
  "company": {
    "name": "string (required)",
    "website": "URL (required)",
    "size": "1-10|11-50|51-200|200+",
    "founded": "YYYY",
    "headquarters": "string",
    "vertical": "string[]",
    "services": "string[]"
  },
  "contact": {
    "name": "string",
    "title": "string",
    "email": "email",
    "phone": "string",
    "linkedin": "URL"
  },
  "projection": {
    "month_3": "number (expected clients)",
    "month_6": "number",
    "month_12": "number",
    "averageDealSize": "number (USD)"
  },
  "tier_interest": "Registered|Certified|Strategic|Enterprise",
  "why_raas": "string (min 100 words)"
}
```

**Action Items:**
- [ ] CRM: Create partner record in HubSpot/Salesforce
- [ ] Email: Send auto-acknowledgment within 1 hour
- [ ] Slack: Notify #partner-applications channel
- [ ] Assign: Partner Operations Manager (POM) as owner

---

### Step 1.2: Qualification Call (30 minutes)

**Attendees:**
- Partner: CEO/Founder + Head of Partnerships
- AgencyOS: Partner Operations Manager

**Agenda:**
```
0-5 min:   Introductions & rapport building
5-15 min:  Partner background (ask, don't tell)
  - Current business model
  - Why interested in RaaS?
  - Target client profile
15-25 min: RaaS overview (tailored to their vertical)
  - 6-way revenue split
  - Quadratic funding opportunity
  - Tier benefits
25-30 min: Next steps & timeline
```

**Qualification Criteria (MEDDIC):**
| Criteria | Questions | Pass Signals |
|----------|-----------|--------------|
| **Metrics** | "What's your target partner revenue?" | $5K+/mo realistic |
| **Economic Buyer** | "Who decides on partnerships?" | Decision-maker on call |
| **Decision Criteria** | "What matters most: revenue, features, support?" | Aligned with RaaS strengths |
| **Decision Process** | "What's your evaluation timeline?" | 2-4 weeks (not 6+ months) |
| **Identify Pain** | "What's broken with current model?" | Hourly billing fatigue |
| **Champion** | "Who internally will drive this?" | Named champion |

**Scoring:**
```
Score ≥ 8/10 → Fast-track to Certified/Strategic
Score 6-7/10 → Standard Registered onboarding
Score < 6/10 → Nurture track (revisit in 90 days)
```

---

### Step 1.3: Partner Agreement

**Document:** `legal/partner-agreement-v1.0.pdf`

**Key Terms by Tier:**

| Clause | Registered | Certified | Strategic | Enterprise |
|--------|------------|-----------|-----------|------------|
| Revenue Share | 15% | 25% | 30% | 35-50% |
| Term | 12 months | 24 months | 36 months | Custom |
| Termination | 30 days | 60 days | 90 days | Custom |
| Non-compete | None | Vertical-exclusive | Region-exclusive | Negotiated |
| Marketing Fund | 0% | 2% | 5% | 10% |
| SLA | Best effort | 24h | 4h | Custom |

**Workflow:**
```
1. POM generates agreement via DocuSign template
2. Partner receives email for e-signature
3. Partner reviews/signs (3-5 days typical)
4. Counter-sign by AgencyOS VP Partnerships
5. Fully executed → Move to Phase 2
```

**Red Flags (Legal Review Required):**
- Request for exclusivity (Registered/Certified only)
- Revenue share > 30% for non-Enterprise
- Termination < 30 days
- Liability cap > $100K

---

## Phase 2: Onboarding (Week 2)

### Step 2.1: Partner Portal Setup

**System:** `partners.agencyos.network`

**Automated Workflow:**
```
Trigger: Agreement fully executed
  ↓
1. Create partner account in Auth0
2. Generate partner_id (e.g., ptnr_abc123)
3. Provision partner subdomain: {company}.agencyos.network
4. Send welcome email with:
   - Login credentials (temporary password)
   - Portal URL
   - Onboarding checklist link
  ↓
Slack: Notify #partner-success "New partner: {company}"
```

**Welcome Email Template:**
```
Subject: Welcome to AgencyOS RaaS, {Company}!

Hi {Partner Name},

Congratulations on joining the AgencyOS RaaS ecosystem!

Your Partner Portal credentials:
- URL: {company}.agencyos.network
- Username: {email}
- Temporary Password: {auto-generated}

Next Steps (complete within 7 days):
□ Complete your profile
□ Upload company logo
□ Enroll in product training
□ Schedule technical setup call

Your Partner Success Manager: {PSM name}
Slack: #{company}-slack-channel (we'll invite you)

Let's build something great together!

— The AgencyOS Team
```

---

### Step 2.2: Product Training

**Platform:** `learn.agencyos.network`

#### Registered Partner (2 hours)
```
Module 1: RaaS Fundamentals (30 min)
  - Video: What is RaaS? (15 min)
  - Quiz: 6-way split model (10 min)
  - Resource: Revenue distribution guide (5 min)

Module 2: Partner Portal (30 min)
  - Video: Dashboard walkthrough (15 min)
  - Hands-on: Submit test mission (15 min)

Module 3: Sales Basics (60 min)
  - Video: RaaS pitch deck (20 min)
  - Role-play: Objection handling (20 min)
  - Quiz: Product knowledge (20 min)

Completion: Certificate of Completion (auto-generated)
```

#### Certified Partner (8 hours)
```
Module 1-3: (Same as Registered)

Module 4: Advanced RaaS (2 hours)
  - Deep dive: Quadratic funding mechanics
  - Case study: Community fund matching
  - Assignment: Calculate client ROI

Module 5: Technical Integration (2 hours)
  - API authentication
  - Webhook configuration
  - Debugging common errors
  - Hands-on: Build integration

Module 6: Certification Exam (2 hours)
  - 50 multiple choice questions
  - 2 practical scenarios
  - Pass mark: 80%

Completion: Certified RaaS Partner badge + LinkedIn certificate
```

#### Strategic Partner (16 hours)
```
Module 1-6: (Same as Certified)

Module 7: White-Label Configuration (4 hours)
  - Brand customization
  - Custom domain setup
  - CSS theming
  -hands-on: Deploy branded dashboard

Module 8: Enterprise Sales (4 hours)
  - Negotiation tactics
  - Contract customization
  - Executive relationship building
  - Role-play: Enterprise deal

Module 9: Community Fund Strategy (2 hours)
  - Grant writing workshop
  - Quadratic funding optimization
  - Case studies: Funded projects

Completion: Strategic Partner badge + press release
```

---

### Step 2.3: Technical Setup

**Attendees:**
- Partner: CTO/Technical Lead
- AgencyOS: Solutions Engineer

**Agenda (90 minutes):**

```
0-15 min: Environment Setup
  - Create API keys (production + sandbox)
  - Configure webhook endpoints
  - Test connectivity

15-45 min: API Integration
  - POST /v1/missions endpoint
  - Authentication: Bearer token
  - Request/response walkthrough
  - Error handling

45-60 min: Webhook Configuration
  - mission.completed payload
  - mission.failed payload
  - payment.settled payload
  - Signature verification

60-75 min: Test Mission Submission
  - Submit sample mission
  - Verify 6-way split calculation
  - Check ledger entries

75-90 min: Q&A + Next Steps
```

**Pre-Call Checklist (Partner):**
- [ ] Development environment ready
- [ ] Webhook endpoint deployed (HTTPS required)
- [ ] API client library installed (`npm install @agencyos/raas-sdk`)
- [ ] Test credentials received

**Test Mission Script:**
```bash
# 1. Get access token
curl -X POST https://api.agencyos.network/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"client_id":"...","client_secret":"..."}'

# 2. Submit test mission
curl -X POST https://api.agencyos.network/v1/missions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Build landing page for e-commerce client",
    "budget": 1000,
    "priority": "high"
  }'

# 3. Verify webhook received
# Expected payload:
{
  "event": "mission.completed",
  "data": {
    "mission_id": "msn_abc123",
    "status": "completed",
    "revenue_split": {
      "platform": 200,
      "expert": 300,
      "ai_compute": 150,
      "developer": 150,
      "community_fund": 100,
      "customer_reward": 100
    }
  }
}
```

---

### Step 2.4: Sales Enablement

**Deliverables (Partner Downloads from Portal):**

| Asset | Format | Use Case |
|-------|--------|----------|
| RaaS Pitch Deck | PPTX + PDF | First client meeting |
| ROI Calculator | Google Sheets | Quantify value prop |
| One-Pager | PDF | Email attachment |
| Case Studies | PDF (3-pack) | Social proof |
| Demo Script | PDF | Live demo delivery |
| Objection Handling | PDF | Sales prep |
| Email Templates | Google Doc | Outreach sequences |
| Proposal Template | Google Doc | Client proposals |

**ROI Calculator Inputs:**
```
Current Model:
  - Avg hourly rate: $150
  - Hours/month: 160
  - Revenue: $24,000/mo

RaaS Model:
  - Avg client subscription: $2,000/mo
  - Clients managed: 15
  - Revenue share (30%): $9,000/mo
  - Community fund grants: $3,000/mo
  - Total: $12,000/mo (50% revenue, 80% margin)

Savings:
  - No delivery team overhead: -$8,000/mo
  - No software licensing: -$2,000/mo
  - Net margin improvement: +$6,000/mo
```

---

## Phase 3: Go-Live (Week 3)

### Step 3.1: First Client Onboarding

**Checklist:**
- [ ] Client signed (Partner closes deal)
- [ ] Client account created in RaaS
- [ ] Client billing configured (Polar.sh webhook)
- [ ] First mission brief submitted
- [ ] Partner Success Manager notified

**First Mission Support:**
```
Slack Channel: #{partner}-support
Response Time: < 2 hours (Certified+), < 24 hours (Registered)

Include:
  - Mission goal clarity
  - Success criteria
  - Budget confirmation
  - Timeline expectations
```

---

### Step 3.2: First Revenue Split Verification

**Process:**
```
1. Mission completed → webhook fired
2. Payment settled via Polar.sh
3. Revenue split executed (POST /revenue/split)
4. Journal entry created
5. Partner receives email: "Revenue earned: $XXX"
6. Partner dashboard updated
```

**Verification Query (Partner Portal):**
```sql
SELECT
  journal_entry_id,
  description,
  created_at,
  split->>'expert' as partner_share,
  split->>'total' as total_revenue
FROM journal_entries
WHERE partner_id = 'ptnr_{id}'
ORDER BY created_at DESC
LIMIT 1;
```

---

### Step 3.3: 30-Day Check-In

**Attendees:**
- Partner: CEO + Operations Lead
- AgencyOS: Partner Success Manager

**Agenda (45 minutes):**
```
0-10 min:  Review first month metrics
  - Clients onboarded
  - Missions submitted
  - Revenue earned

10-25 min: Identify friction points
  - What's working well?
  - What's blocked?
  - What support needed?

25-40 min: Growth planning
  - Next 30-day goals
  - Pipeline review
  - Upsell opportunities (tier upgrade?)

40-45 min: Action items + next meeting
```

**Success Metrics (30 days):**
| Metric | Registered | Certified | Strategic |
|--------|------------|-----------|-----------|
| Clients | 1-2 | 3-5 | 5-10 |
| Revenue | $500-1K | $2-5K | $5-15K |
| CSAT | ≥ 4/5 | ≥ 4.5/5 | ≥ 4.8/5 |
| Tier Upgrade Interest | 20% | 30% | N/A |

---

## Phase 4: Growth (Ongoing)

### Step 4.1: Quarterly Business Review (QBR)

**For:** Certified+ Partners

**Preparation (AgencyOS):**
- [ ] Revenue trend analysis (last 90 days)
- [ ] Community fund participation report
- [ ] Benchmark vs. peer partners
- [ ] Tier upgrade ROI analysis

**QBR Deck Structure:**
```
Slide 1-3: Performance Review
  - Revenue: Actual vs. Target
  - Growth rate: QoQ, YoY
  - Client retention rate

Slide 4-6: Community Fund
  - Grants received: $X
  - Projects funded: N
  - Quadratic matching efficiency

Slide 7-9: Growth Opportunities
  - Upsell pipeline
  - New vertical expansion
  - Tier upgrade recommendation

Slide 10-12: Joint Action Plan
  - 90-day goals
  - Resource requirements
  - Success metrics
```

---

### Step 4.2: Tier Upgrade Path

**Registered → Certified (Typical: 60-90 days)**

**Prerequisites:**
- 3+ active clients
- $1K+ monthly revenue through platform
- Completed certification exam

**Upgrade Incentives:**
- First month Certified fee waived
- Bonus: $500 community fund credits
- Priority lead: 3 warm intros

**Process:**
```
1. PSM identifies ready partner
2. Send upgrade proposal email
3. Schedule upgrade call (30 min)
4. Sign tier amendment
5. Provision Certified benefits
6. Announce in #partners Slack
```

---

### Step 4.3: Community Fund Strategy

**For:** Active partners (Certified+)

**Best Practices:**
```
1. Identify high-impact projects
  - Client success stories
  - Industry-first implementations
  - Open source contributions

2. Write winning applications
  - Clear problem statement
  - Measurable outcomes
  - Community benefit (not just partner)

3. Leverage quadratic funding
  - Mobilize small contributors
  - Many small donations > few large
  - Use Slack/Twitter to rally support

4. Report outcomes publicly
  - Progress updates in #community-fund
  - Final report with metrics
  - Thank contributors
```

**Example Application:**
```markdown
Project: AI-Powered Accessibility Audit for Nonprofits

Problem: 80% of nonprofit websites fail WCAG 2.1 compliance

Solution: Build automated accessibility auditor using RaaS

Budget: 5,000 MCU (≈$500)

Community Impact:
  - 100+ nonprofits served pro-bono
  - Open source code for all
  - Training materials for developers

Quadratic Funding Ask: 2,000 MCU matching

Individual Contributions Secured:
  - 45 contributors × 50 MCU = 2,250 MCU
  - Quadratic match: ~8,000 MCU
  - Total: ~10,000 MCU (2x leverage)
```

---

## Appendices

### A: Contact Directory

| Role | Name | Email | Slack |
|------|------|-------|-------|
| VP Partnerships | TBD | partnerships@agencyos.network | @vp-partnerships |
| Partner Success | TBD | success@agencyos.network | @partner-success |
| Technical Lead | TBD | integrations@agencyos.network | @solutions-eng |
| Legal | TBD | legal@agencyos.network | @legal-team |

---

### B: Email Templates

#### Application Acknowledgment
```
Subject: We've received your RaaS partnership application

Hi {Name},

Thanks for applying to join the AgencyOS RaaS ecosystem!

We've received your application and will review within 2-3 business days.

Next steps:
1. Partner Operations Manager will reach out to schedule a 30-min intro call
2. We'll discuss your goals and answer any questions
3. If it's a fit, we'll send the partner agreement for signature

In the meantime:
- Check out our partner portal: partners.agencyos.network
- Read the RaaS overview: agencyos.network/raas

Questions? Reply to this email anytime.

Welcome aboard!

— Partner Operations Team
```

#### Agreement Sent
```
Subject: Your AgencyOS RaaS Partner Agreement is ready

Hi {Name},

Great news — your partnership agreement is ready for review!

Please review and sign via DocuSign:
{docusign_link}

Agreement Summary:
- Tier: {tier}
- Revenue Share: {share}%
- Term: {term}
- Effective Date: {date}

Questions? Your Partner Operations Manager ({POM name}) is standing by.

Let's get you onboarded!

— Legal & Partnerships
```

#### Welcome Email (Post-Signature)
```
Subject: Welcome to AgencyOS RaaS, {Company}! 🎉

Hi {Name},

Congratulations! Your partnership is official!

Your Partner Portal:
- URL: {company}.agencyos.network
- Username: {email}
- Temp Password: {password}

Your First 7 Days:
□ Day 1-2: Complete profile, upload logo
□ Day 3-4: Product training (2-16 hours based on tier)
□ Day 5-6: Technical setup call with Solutions Engineering
□ Day 7: Submit your first test mission

Your Team:
- Partner Success Manager: {PSM name} ({email})
- Solutions Engineer: {SE name} ({email})
- Slack: Join #{company}-support channel

We're here to help you succeed. Let's build something great!

— The AgencyOS Team
```

---

### C: Troubleshooting Guide

| Issue | Symptoms | Resolution |
|-------|----------|------------|
| API 401 | Unauthorized errors | Regenerate API key in portal |
| Webhook fails | 500 errors, no payload | Verify HTTPS + signature verification |
| Revenue not showing | Dashboard $0 | Check Polar.sh webhook status |
| Training stuck | Module won't advance | Clear browser cache, try incognito |
| Mission pending | > 24 hours no progress | Check Slack #mission-status |

---

### D: Related Documents

- [RaaS Partnership Process](../raas-partnership-process.md) — Partner tiers, benefits, responsibilities
- [Revenue Distribution Model](raas/revenue-distribution.md) — 6-way split calculations
- [Bookkeeping Examples](raas/bookkeeping-data.csv) — Double-entry journal entries
- [Technical Integration Spec](technical/raas-integration-spec.md) — API endpoints, webhooks

---

**Document Owner:** Partner Operations Team
**Review Cycle:** Quarterly
**Next Review:** 2026-06-19
