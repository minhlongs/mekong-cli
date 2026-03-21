# Mekong CLI — Pricing & Billing

**MCU (Mekong Credit Unit) consumption-based + subscription tiers**

> Transparent, usage-based pricing. 1 MCU = 1 command execution (average).

---

## Subscription Tiers

### **Free** — Try it out
- **$0/month**
- 10 MCU/month (3 commands/day)
- Perfect for: Learning, evaluating, hobby projects
- No credit card required

### **Starter** — For indie developers
- **$79/month** (was $49, revised March 2026)
- 150 MCU/month (5 commands/day average)
- 24-hour support
- Best for: Solo founders, indie developers

### **Pro** — For power users
- **$249/month** (was $99, revised March 2026)
- 750 MCU/month (25 commands/day average)
- Priority support (4-hour response)
- Email + Slack support
- Best for: Small teams, growing agencies

### **Enterprise** — For high-volume teams
- **$599/month** (custom pricing available)
- Unlimited MCU* (fair use: 2,000/mo average)
- Overage: $0.20/MCU beyond 3,000/month
- Dedicated support + SLA
- Custom agents + integrations
- Best for: Agencies, enterprises, consulting firms

\* Fair use policy enforced. Contact sales for exemptions.

---

## What is 1 MCU?

**1 MCU = 1 command execution (average)**

| Command | MCU Cost | Examples |
|---------|----------|----------|
| **Simple** (0-1) | 0-1 | `/help`, `/status`, `/health` |
| **Standard** (1-2) | 1-2 | `/code`, `/fix`, `/test`, `/quote` |
| **Complex** (2-5) | 2-5 | `/cook`, `/plan`, `/deploy`, `/audit` |
| **Parallel** (3-8) | 3-8 | `/fundraise`, `/pitch` (5+ agents) |

**Complexity Multipliers** (applied per command):
- Simple task: ×1 (example: `/code "hello world"`)
- Medium task: ×2 (example: `/plan "new feature"`)
- Complex task: ×3 (example: `/cook "full-stack REST API"`)

**Examples:**
```bash
mekong code "reverse array" → 1 MCU
mekong plan "Q2 roadmap" → 2 MCU
mekong cook "Build auth system" → 3-5 MCU (scope-based)
mekong fundraise "Series A" → 5-8 MCU (8 agents parallel)
```

---

## Billing Details

### How It Works

1. **Plan Selection:** Choose your tier (Free, Starter, Pro, Enterprise)
2. **Monthly Charge:** Subscription auto-renewed monthly
3. **Command Execution:** Each command deducts MCU from balance
4. **Zero Balance:** HTTP 402 (Payment Required) if out of MCU
5. **Overage:** Only Enterprise allows overage at $0.20/MCU

### Payment Methods

- **Polar.sh:** Primary payment processor
  - Credit/debit card (Visa, Mastercard, Amex)
  - Apple Pay, Google Pay
  - Automatic monthly renewal

### Billing Cycle

- **Monthly:** Charges on day of signup each month
- **Annual Discount:** Pay 10 months, get 2 months free (17% off)
- **Usage Tracking:** Real-time dashboard at `/account/usage`

### Usage Dashboard

View your MCU consumption:
```bash
mekong account:usage
# Output: { "tier": "pro", "mcus_remaining": 250, "reset_date": "2026-04-21" }
```

---

## Refund & Credit Policy

**7-Day Money Back Guarantee**
- Full refund if you cancel within 7 days of signup
- No questions asked

**Partial Refunds**
- Unused MCU credited to next month
- Prorated refund if downgrading mid-month

**Failed Charges**
- Retry up to 3 times (24h intervals)
- Account suspended if payment fails after 3 retries
- Auto-reactivate on successful payment

---

## Discounts & Promotions

### Annual Prepay
- Pay 10 months upfront, get 2 months free
- Available for Starter and Pro tiers
- Best offer: Save $600/year on Pro

### Volume Discounts
- 10+ Enterprise licenses: 15% off
- Contact: sales@agencyos.network

### Open Source Project Discount
- 50% off all tiers for qualified open-source projects
- Apply at: agencyos.network/open-source

### Startup Program
- Y Combinator, Techstars: $2,000 free credits
- Other accelerators: Custom terms
- Apply at: agencyos.network/startups

---

## Unit Economics (Transparent)

### Cost Breakdown (per MCU)

| Component | Cost | % of Total |
|-----------|------|-----------|
| LLM API (80% Sonnet, 20% Opus) | $0.09 | 60% |
| Infrastructure (Cloudflare) | $0.03 | 20% |
| Support & Success | $0.02 | 13% |
| Payment Processing | $0.01 | 7% |
| **Total COGS** | **$0.15** | **100%** |

### Pricing by Tier (Gross Margin)

| Tier | Price/MCU | COGS | Margin |
|------|-----------|------|--------|
| **Free** | $0.00 | $0.15 | -100% (loss leader) |
| **Starter** | $0.53 | $0.15 | 72% |
| **Pro** | $0.33 | $0.15 | 55% |
| **Enterprise** | $0.20-0.30 | $0.15 | 33-50% |

### Profitability Scenarios

| Scenario | Customers | MRR | Gross Profit | Status |
|----------|-----------|-----|--------------|--------|
| Conservative | 200 | $45,000 | $22,500 | -$25K (losing) |
| Break-even | 400 | $90,000 | $45,000 | $0 (neutral) |
| Target | 1,000 | $250,000 | $137,500 | +$72.5K (healthy) |
| Moon | 5,000 | $1.2M | $600K | +$545K (profitable) |

---

## FAQ

**Q: Can I upgrade/downgrade mid-month?**
A: Yes. Changes take effect on the next billing cycle. Unused MCU from Pro → Starter transition credited to account.

**Q: What if I run out of MCU mid-month?**
A: Execution halts with HTTP 402. Buy additional credits or wait for next month's reset.

**Q: Is there a way to buy one-off credits?**
A: Not yet. Contact sales@agencyos.network for custom credit packs.

**Q: Can I cancel anytime?**
A: Yes. Cancel anytime, no lock-in contracts. Refund up to 7 days.

**Q: Do credits carry over?**
A: No. MCU resets monthly. Unused credits expire at month end.

**Q: Is there a volume commitment?**
A: No. Month-to-month billing. No commitment required.

**Q: Do you offer SLA?**
A: Yes, Enterprise customers get 99.5% uptime SLA + dedicated support.

---

## Competitive Comparison

| Product | Price/mo | Credits | $/Credit | Type |
|---------|----------|---------|----------|------|
| **Mekong CLI** | $79-599 | 150-∞ | $0.20-0.53 | Workflow automation |
| Cursor Pro | $20 | Unlimited* | ~$0.10 | Code completion |
| GitHub Copilot | $10 | Unlimited | ~$0.05 | Code completion |
| ChatGPT Plus | $20 | Unlimited | $0.002 | Chat only |

*Limited daily requests

**Why Mekong CLI?**
- Full workflow automation (not just code)
- Multi-agent orchestration (8 AI roles)
- Self-healing execution (auto-retry)
- RaaS marketplace integration
- Enterprise governance (SOC2)

---

## Next Steps

1. **Sign up:** Visit [agencyos.network](https://agencyos.network)
2. **Choose tier:** Select Free/Starter/Pro/Enterprise
3. **Start building:** `mekong cook "your goal"`
4. **Monitor usage:** `mekong account:usage`
5. **Upgrade anytime:** No penalties, instant activation

---

## Need Help?

- **Email:** support@agencyos.network
- **Slack:** Join our community Slack (Pro/Enterprise)
- **Docs:** `/docs/getting-started.md`
- **Status:** [status.agencyos.network](https://status.agencyos.network)
