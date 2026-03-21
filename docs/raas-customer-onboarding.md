# RaaS Customer Onboarding Guide

Getting started with Mekong CLI RaaS (Robot-as-a-Service) in under 15 minutes.

---

## Prerequisites

- Node.js 18+ or Python 3.11+
- npm or pip installed
- Active internet connection
- Valid email address

---

## Step 1: Install Mekong CLI

### Via npm (TypeScript/JavaScript projects)

```bash
npm install -g @mekong/mekong-cli-core
```

### Via pip (Python projects)

```bash
pip install mekong-cli
```

### Verify Installation

```bash
mekong version
# Expected: Mekong CLI v5.0.0+
```

---

## Step 2: Create Your Account

### Option A: Web Signup (Recommended)

1. Visit [agencyos.network](https://agencyos.network)
2. Click **Sign Up** in the top right corner
3. Enter your email and create a password
4. Verify your email via the confirmation link
5. Log in to your dashboard

### Option B: CLI Signup

```bash
mekong cloud signup
```

Follow the prompts to create your account and organization.

---

## Step 3: Log In

### Web Dashboard

Visit [agencyos.network/dashboard](https://agencyos.network/dashboard) and enter your credentials.

### CLI Authentication

```bash
mekong cloud login
```

This stores your session token securely for subsequent commands.

---

## Step 4: Check Your Account Balance

```bash
mekong cloud whoami
```

Expected output:

```
User: your-email@example.com
Organization: Your Organization
Account Tier: Starter
Credits: 200
Trial Ends: 2026-04-21
```

---

## Step 5: Purchase Credits

### Pricing Tiers

| Tier | Credits | Price | Best For |
|------|---------|-------|----------|
| Starter | 200 | $49/month | Teams learning RaaS |
| Pro | 1,000 | $149/month | Growing agencies |
| Enterprise | Unlimited | $499/month | Large organizations |

### Buy Credits via CLI

```bash
mekong cloud billing checkout --tier starter
```

This opens Polar.sh checkout in your browser.

### Buy via Dashboard

1. Log in to [agencyos.network/dashboard](https://agencyos.network/dashboard)
2. Navigate to **Billing → Upgrade**
3. Select your tier and complete payment via Polar.sh
4. Credits appear instantly in your account

---

## Step 6: Submit Your First Mission

A **mission** is a self-contained task executed by Mekong's AI agents.

### Basic Mission

```bash
mekong cloud mission submit "build a landing page for my SaaS"
```

Output:

```
Mission Created!
ID: mission_123456...
Status: queued
Credits: 5
Estimated Time: 2-5 minutes

View Status: mekong cloud mission status mission_123456...
```

### Mission Credit Cost

| Complexity | Example | Credits |
|-----------|---------|---------|
| Simple | "Fix typo in README" | 1 |
| Standard | "Add dark mode to dashboard" | 3 |
| Complex | "Build complete payment system with Stripe" | 5 |

---

## Step 7: Check Mission Status

### Real-Time Status

```bash
mekong cloud mission status <mission-id>
```

Output:

```
Status: running
Progress: Step 2 of 4 (Planning)
Started: 2026-03-21 14:32:00 UTC
Estimated Completion: 2026-03-21 14:37:00 UTC
```

### View Mission History

```bash
mekong cloud mission list --limit 10
```

Lists your 10 most recent missions with status and credit cost.

### Stream Live Logs

```bash
mekong cloud mission logs <mission-id> --follow
```

Shows real-time execution logs as the mission runs.

---

## Step 8: View Billing History

```bash
mekong cloud billing history
```

Output:

```
Date              | Type      | Credits | Amount | Status
2026-03-21 14:35 | Mission   | -5      | N/A    | completed
2026-03-20 10:12 | Purchase  | +200    | $49    | completed
2026-03-19 08:45 | Mission   | -3      | N/A    | completed
```

### Export as CSV

```bash
mekong cloud billing history --format csv > billing.csv
```

---

## FAQ: Common Questions

### Q1: How long does a mission take?

**A:** Most missions complete in 2-10 minutes depending on complexity. Simple tasks (typo fixes) take ~30 seconds. Complex tasks (full feature implementation) may take up to 30 minutes for large codebases.

### Q2: What if a mission fails?

**A:** Credits are only charged upon successful completion. If a mission fails, you pay nothing and can retry immediately.

### Q3: Can I cancel a running mission?

**A:** Yes, but only queued missions are fully refunded. Running/completed missions are charged as-is.

```bash
mekong cloud mission cancel <mission-id>
```

### Q4: How do I get a refund?

**A:** Contact support@agencyos.network with your mission ID. We process refunds within 24 hours for legitimate issues.

### Q5: Can I use RaaS for multiple projects?

**A:** Yes. Each organization has a shared credit pool. All team members submit missions under the same account and share the same credits.

### Q6: What if I exceed my monthly credit limit?

**A:** Missions are queued until you purchase more credits. No overage charges—you control your spending.

### Q7: Is there an API?

**A:** Yes. See [RaaS API Documentation](./raas-api.md) for REST and SDK examples.

### Q8: Can I downgrade my tier?

**A:** Yes. Changes take effect at the start of your next billing cycle. No refunds for partial months.

### Q9: What payment methods do you accept?

**A:** Polar.sh handles payments. We accept all major credit cards, Apple Pay, and Google Pay.

### Q10: Where do I get support?

**A:** Email support@agencyos.network for technical issues. Response time: 24 hours (4 hours for Enterprise customers).

---

## Next Steps

1. **Join the Community**: Discord at [mekong-cli.io/discord](https://mekong-cli.io/discord)
2. **Explore Recipes**: Pre-built automation templates in [docs/raas](./raas/)
3. **Read Full API Docs**: [RaaS API Reference](./raas-api.md)
4. **Contact Sales**: Enterprise customers reach out to sales@agencyos.network

---

**Version:** 1.0.0 | **Last Updated:** 2026-03-21 | **Audience:** All RaaS Customers

© 2026 Binh Phap Venture Studio. *"The supreme art of war is to subdue the enemy without fighting."*
