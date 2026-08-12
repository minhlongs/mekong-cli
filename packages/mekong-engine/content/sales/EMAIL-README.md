# OpenClaw RaaS Gateway — Email Sending Guide

**Generated:** 2026-03-20
**Goal:** Send 50 personalized outreach emails for OpenClaw beta program

---

## Files Created

| File | Purpose |
|------|---------|
| `prospect-list-100.csv` | 50 AI startup prospects with contact info |
| `email-1-personalized.md` | 50 personalized Email 1 templates |
| `email-tracking.csv` | Track sent/opened/replied status |
| `send-emails.py` | Python script for automated sending |
| `EMAIL-README.md` | This guide |

---

## Option A: Manual Sending (Recommended for first batch)

### Step 1: Prepare Your Sender Info
Replace `[Your Name]` with your actual name in all emails.

### Step 2: Send via Gmail

**Method 1: Copy-Paste (10 at a time)**

1. Open `email-1-personalized.md`
2. Copy Email 1-10
3. Open Gmail → Compose
4. Paste subject + body
5. Add recipient from prospect list
6. Send

**Method 2: Gmail Mail Merge**

1. Install free mail merge extension:
   - [Mailtrack](https://mailtrack.io/)
   - [GMass](https://www.gmass.co/)
   - [Yet Another Mail Merge](https://yetanothermailmerge.com/)

2. Create Google Sheet with columns:
   - Email, Name, Company, Product, Milestone

3. Compose email with variables:
   ```
   Hi {{Name}},

   I noticed {{Company}} is building {{Product}}...
   ```

4. Send as mail merge

### Step 3: Update Tracking

After sending each email, update `email-tracking.csv`:
- Change `Status` from "Draft" to "Sent"
- Add send date
- Note any bounces

---

## Option B: Automated Sending (Python Script)

### Prerequisites

```bash
# Gmail App Password (required for SMTP)
# 1. Go to: https://myaccount.google.com/apppasswords
# 2. Create app password for "Mail"
# 3. Copy the 16-character password
```

### Usage

```bash
# Dry run (test without sending)
python3 send-emails.py --mode smtp --dry-run --sender "Your Name"

# Actually send (requires Gmail credentials)
python3 send-emails.py --mode smtp \
  --email "your-email@gmail.com" \
  --password "your-app-password" \
  --sender "Your Name"
```

### Rate Limiting

- Script sends 1 email every 2 seconds
- Gmail daily limit: 500 emails (free), 2000 (Workspace)
- Recommended: Send in batches of 50/day

---

## Email Sequence Timeline

| Email | Day | Date | Purpose |
|-------|-----|------|---------|
| Email 1 | Day 1 | 2026-03-20 | Intro + Value Prop |
| Email 2 | Day 3 | 2026-03-23 | Social Proof |
| Email 3 | Day 6 | 2026-03-26 | Demo Offer |
| Email 4 | Day 10 | 2026-03-30 | Follow-up |
| Email 5 | Day 14 | 2026-04-03 | Breakup |

---

## Expected Metrics (Industry Benchmarks)

| Metric | Target | Expected Count |
|--------|--------|----------------|
| Sent | 50 | 50 |
| Opened | 40% | 20 |
| Replied | 20% | 10 |
| Demo Scheduled | 10% | 5 |
| Trial Started | 6% | 3 |
| Paid Converted | 2-4% | 1-2 |

---

## Follow-up Actions

### When prospect replies:

**Positive reply ("Yes, interested"):**
1. Respond within 2 hours
2. Send Calendly link: `https://calendly.com/yourname/15min`
3. Update tracking CSV: Status = "Demo"

**Curious ("Tell me more"):**
1. Send demo URL: `https://mekong-engine.agencyos-openclaw.workers.dev`
2. Offer 15-min onboarding call
3. Update tracking CSV: Status = "Trial"

**Not now ("Maybe later"):**
1. Add to 30-day follow-up list
2. Send Email 2 (Social Proof) on schedule
3. Update tracking CSV: Status = "Follow-up"

**Not interested:**
1. Thank them politely
2. Update tracking CSV: Status = "Not Interested"
3. Remove from future sequences

---

## Tips for Success

1. **Personalize the milestone** - Research each company briefly
2. **Send from personal email** - Higher deliverability than domain
3. **Warm up your inbox** - Send 10/day for first 5 days
4. **Track opens** - Use Gmail read receipts or Mailtrack
5. **Follow up consistently** - 80% of replies come from Email 2-5
6. **A/B test subject lines** - Try variations for next batch

---

## Quick Commands

```bash
# Check Python script
python3 send-emails.py --help

# Generate manual CSV export
python3 send-emails.py --mode manual --sender "Your Name"

# View tracking status
cat email-tracking.csv | grep "Sent"
```

---

## Demo URL

Share this with interested prospects:
**https://mekong-engine.agencyos-openclaw.workers.dev**

---

## Support

Questions about the outreach sequence?
- Docs: `content/sales/outreach-emails.md`
- Product info: `../docs/README.md`
- Demo: `https://mekong-engine.agencyos-openclaw.workers.dev`

---

**Good luck with the outreach!** 🚀
