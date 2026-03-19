# RaaS Onboarding Email Sequence

**5-email automated sequence for new customer onboarding**
**Goal:** Activate → Engage → Convert POC to Annual

---

## Email 1: Welcome + Getting Started (Day 0)

**Send:** Immediately after signup
**Goal:** Reduce time-to-first-mission < 24 hours

---

**Subject:** Welcome to RaaS — Let's ship your first mission 🚀

**Preview text:** Your 15-minute getting started checklist inside

---

Hi {{first_name}},

Welcome to **Revenue-as-a-Service!**

I'm {{sender_name}}, your onboarding specialist. Over the next 14 days, I'll help you:

✅ Run your first mission (15 minutes vs. 4 hours)
✅ Train your team on best practices
✅ Measure real ROI from your client work

**Your 15-Minute Getting Started Checklist:**

| Step | Time | Status |
|------|------|--------|
| 1. Watch 3-min demo video | 3 min | ⬜ |
| 2. Run your first mission | 10 min | ⬜ |
| 3. Review deployed code | 2 min | ⬜ |

**📹 [Watch Demo: Your First Mission in 3 Minutes](#)**

**🚀 [Launch Dashboard: Run Your First Mission](#)**

---

**Pro Tip:** Start with a low-risk mission like:
- "Add password reset endpoint"
- "Create user profile API"
- "Build contact form with validation"

---

**Need Help?**

Reply to this email anytime or join our [Slack Community](#) for instant support.

Let's ship something great,

**{{sender_name}}**
Onboarding Specialist, AgencyOS

---

**P.S.** 85% of customers who run their first mission within 24 hours upgrade to annual. Don't wait!

---

## Email 2: First Mission Best Practices (Day 2)

**Send:** 48 hours after signup
**Goal:** Ensure first mission success, build confidence

---

**Subject:** How to write missions that get 10x better results

**Preview text:** 5 templates you can copy/paste

---

Hi {{first_name}},

Hope you've run at least one mission by now!

Here's what we learned from **5,000+ successful missions:**

### The 3-Part Mission Formula

```
[Action] + [Specific Feature] + [Tech Requirements]

Example:
"Create REST API endpoints for user CRUD operations
 with JWT authentication and input validation"
```

---

### 5 Copy/Paste Templates

**1. Authentication Flow**
```
"Add user authentication with OAuth2 (Google, GitHub)
 including login, logout, register, and password reset
 endpoints. Use JWT tokens with 7-day expiry."
```
**Credits:** 3 | **Time saved:** 6 hours

---

**2. CRUD API Module**
```
"Build complete CRUD API for {{resource_name}} with:
 - GET /api/{{resource}} (list with pagination)
 - GET /api/{{resource}}/:id (single item)
 - POST /api/{{resource}} (create with validation)
 - PUT /api/{{resource}}/:id (update)
 - DELETE /api/{{resource}}/:id (soft delete)
 Include TypeScript types and error handling."
```
**Credits:** 3 | **Time saved:** 4 hours

---

**3. UI Component**
```
"Create responsive {{component_name}} component with:
 - TypeScript props interface
 - Tailwind CSS styling
 - Loading and error states
 - Mobile-first design
 - Dark mode support"
```
**Credits:** 1 | **Time saved:** 2 hours

---

**4. Database Migration**
```
"Create database migration for {{table_name}} table:
 - Define schema with proper types
 - Add indexes for frequently queried columns
 - Include RLS (Row Level Security) policies
 - Write seed data script (10 sample records)
 - Add rollback migration"
```
**Credits:** 3 | **Time saved:** 5 hours

---

**5. Integration Setup**
```
"Integrate {{service_name}} API:
 - Set up authentication (API key/OAuth)
 - Create service class with TypeScript
 - Add error handling and retry logic
 - Write unit tests (80%+ coverage)
 - Document API methods in README"
```
**Credits:** 3 | **Time saved:** 4 hours

---

### What to Avoid ❌

| Bad Mission | Better Version |
|-------------|----------------|
| "Fix bugs" | "Fix TypeScript errors in auth.service.ts: missing return types, implicit any" |
| "Add features" | "Add rate limiting to /api/login endpoint: max 5 attempts per 15 minutes" |
| "Improve performance" | "Optimize database query in getUsers(): add index on email column, use SELECT instead of *" |

---

**🎯 [Try a Template Now](#)**

Questions? Hit reply — I read every response.

**{{sender_name}}**

---

## Email 3: Advanced Features (Day 5)

**Send:** 5 days after signup
**Goal:** Unlock advanced use cases, increase credit utilization

---

**Subject:** You're using 10% of RaaS. Here's the other 90%.

**Preview text:** 7 advanced features power users love

---

Hi {{first_name}},

By now you've probably run a few simple missions.

**Ready to unlock the full power?**

---

### Feature 1: White-Label Mode 🎭

**Perfect for:** Agencies delivering to clients

Your clients never need to know we exist. Enable white-label:

1. Go to Settings → Branding
2. Upload your logo
3. Customize email templates
4. Add custom domain (optional)

**Result:** Your brand, your code, your clients.

[→ Enable White-Label](#)

---

### Feature 2: Multi-LLM Support 🤖

**Perfect for:** Cost optimization, custom requirements

Don't like our default LLM? Bring your own:

- Anthropic Claude 4.6 (default)
- Google Gemini 1.5 Pro
- Alibaba Qwen 3.5+
- Your fine-tuned model (custom endpoint)

[→ Configure LLM Provider](#)

---

### Feature 3: Mission Templates 📋

**Perfect for:** Teams running similar missions

Save your common missions as templates:

1. Run a mission successfully
2. Click "Save as Template"
3. Name it (e.g., "Standard CRUD API")
4. Share with your team

[→ Create Your First Template](#)

---

### Feature 4: Team Permissions 👥

**Perfect for:** Agencies with 3+ developers

Control who can:
- Create missions (developers)
- Approve deployments (tech leads)
- View billing (managers)
- Manage settings (admins)

[→ Set Up Team Permissions](#)

---

### Feature 5: Webhook Integrations 🔗

**Perfect for:** Automated workflows

Get notified when missions complete:

- Slack: Post to #dev channel
- Discord: Webhook to dev-testing
- Custom: POST to your endpoint

[→ Configure Webhooks](#)

---

### Feature 6: API Access 🔌

**Perfect for:** Custom tooling, CI/CD integration

Everything you can do in the dashboard, you can do via API:

```bash
# Create mission via API
curl -X POST https://api.agencyos.network/v1/missions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"description": "Add user login endpoint"}'

# Check status
curl https://api.agencyos.network/v1/missions/{id}
```

[→ View API Documentation](#)

---

### Feature 7: ROI Dashboard 📊

**Perfect for:** Proving value to stakeholders

Track your real-time impact:

- Hours saved per mission
- Dollar value created
- Credit utilization rate
- Team productivity trends

[→ View Your ROI Dashboard](#)

---

### Power User Challenge 🏆

**This week's goal:** Run 5 missions using at least 3 advanced features.

Hit 5 missions? Reply to this email — I'll send you a **$50 credit bonus**.

**{{sender_name}}**

---

## Email 4: ROI Check-In (Day 10)

**Send:** 10 days after signup
**Goal:** Reinforce value, address concerns early

---

**Subject:** Quick question about your RaaS results

**Preview text:** How's it going? Let's optimize.

---

Hi {{first_name}},

We're 10 days in — I wanted to check on your progress.

**Quick Questions:**

| Question | Your Answer |
|----------|-------------|
| Missions completed? | {{missions_completed}} |
| Hours saved? | {{hours_saved}} (estimated) |
| Team adoption? | {{team_members_active}} active users |
| Any blockers? | [Reply and let me know](#) |

---

### Based on Your Usage...

**If you've run 0-2 missions:**

No judgment! Most customers get stuck on one of these:

❌ "Didn't have time" → Block 30 min tomorrow, I'll wait on Slack
❌ "Not sure what mission to run" → Reply, I'll suggest 3 tailored ideas
❌ "First mission didn't meet expectations" → Let me review it personally

**→ [Schedule 15-min Rescue Call](#)**

---

**If you've run 3-10 missions:**

Great start! Here's how to 2x your results:

✅ Try a **complex mission** (5 credits) — you're ready
✅ Enable **team permissions** — get everyone involved
✅ Set up **webhooks** — automate notifications

**→ [Watch: Advanced Mission Techniques (8 min)](#)**

---

**If you've run 10+ missions:**

🎉 **You're a power user!**

Your estimated ROI so far:
- Hours saved: ~{{hours_saved}} hours
- Value created: ${{value_created}} (at $75/hr)
- Investment: $49 (Starter tier)
- **Net return: ${{net_return}}**

**Ready to upgrade and lock in annual pricing?**

**→ [View Annual Plans (17% off)](#)**

---

### Common Questions at Day 10

**Q: "Can I upgrade mid-cycle?"**
A: Yes! Prorated credit for unused Starter days.

**Q: "What happens if I exceed my credits?"**
A: Overage at $1.50/credit (Starter) or auto-upgrade next tier.

**Q: "Can I get a custom plan for my team?"**
A: Absolutely. Reply and I'll connect you with enterprise sales.

---

**How's it really going?** Hit reply — I read every response.

**{{sender_name}}**

---

## Email 5: POC Complete → Upgrade (Day 14)

**Send:** 14 days after signup (POC end)
**Goal:** Convert to annual contract

---

**Subject:** Your 14-day POC is complete. Here's what's next.

**Preview text:** Time to decide. Special offer inside.

---

Hi {{first_name}},

**Your 14-day Proof of Concept is officially complete.**

Let's look at your results:

---

### Your POC Summary

| Metric | Your Result |
|--------|-------------|
| **Missions Completed** | {{missions_completed}} |
| **Hours Saved** | {{hours_saved}} hours |
| **Value Created** | ${{value_created}} |
| **Investment** | $49 (Starter tier) |
| **Net ROI** | **{{roi_percentage}}%** |

---

### What Customers Typically Decide

**Scenario A: "This is a no-brainer"** (85% of users)

You've seen the ROI. Your team is faster. Clients are happier.

**→ Upgrade to Annual Pro: $1,988/year (save $400)**

Includes:
- 200 credits/month (vs. 50)
- Priority support (4h response)
- Custom mission templates
- White-label ready
- **Bonus:** 200 bonus credits ($300 value)

[→ Upgrade to Annual Now](#)

---

**Scenario B: "I need more time"** (10% of users)

Fair enough. Let's extend your POC 7 more days — same terms.

**→ Extend POC 7 Days**

[→ Request Extension](#)

---

**Scenario C: "This isn't for us"** (5% of users)

No hard feelings. If RaaS isn't the right fit:

**→ Request Full Refund**

Your $49 refund will process within 3-5 business days.

That said — I'd love to understand what didn't work. [Hop on a 15-min exit call?](#)

---

### Why 85% Choose Annual

**The math is simple:**

```
Monthly Pro (month-to-month): $249 × 12 = $2,988/year
Annual Pro (prepaid):         $1,988 ÷ 12 = $165/month

You save: $1,000/year (33% discount)
Plus: 200 bonus credits ($300 value)
Total value: $1,300
```

---

### What You're Getting

| Feature | Starter | Pro Annual |
|---------|---------|------------|
| Credits/month | 50 | 200 |
| Cost/credit | $0.98 | $0.83 |
| Support SLA | 72h | 4h |
| Team members | 3 | Unlimited |
| White-label | ❌ | ✅ |
| Custom templates | ❌ | ✅ |
| Webhook integrations | 1 | Unlimited |
| ROI dashboard | Basic | Advanced |

---

### Special Offer (48 Hours Only)

**Upgrade in the next 48 hours and get:**

🎁 **Free onboarding workshop** ($2,500 value)
- 2-hour team training
- Custom use case discovery
- Private Slack channel setup

🎁 **200 bonus credits** ($300 value)

🎁 **Price lock guarantee**
- Your rate locked for life
- No increases, ever

---

### Still Have Questions?

**Technical questions?** → [Reply to this email](#)

**Billing questions?** → [Talk to finance specialist](#)

**Need executive buy-in?** → [Download executive one-pager](#)

**Want a live demo for your team?** → [Schedule team demo](#)

---

### What Happens Next

**If you upgrade:**
1. Your account instantly upgrades to Pro
2. 200 credits added immediately
3. Bonus credits added within 1 hour
4. Welcome call scheduled within 48 hours

**If you extend:**
1. POC extended 7 days
2. Same Starter tier pricing
3. Check-in call on Day 21

**If you refund:**
1. Full refund within 3-5 days
2. Account remains active (free tier available)
3. Welcome back anytime

---

**The question isn't "Can you afford to upgrade?"**

**It's "Can you afford NOT to?"**

Your competitors are already using RaaS to ship 3x faster.

What will you decide?

**{{sender_name}}**

---

**P.S.** This special offer (workshop + bonus credits) expires in 48 hours. After that, standard pricing applies. [→ Upgrade Now](#)

---

## Performance Benchmarks

| Email | Target Open Rate | Target CTR | Target Conversion |
|-------|------------------|------------|-------------------|
| Email 1 (Welcome) | 65%+ | 40%+ | — |
| Email 2 (Templates) | 55%+ | 25%+ | — |
| Email 3 (Advanced) | 50%+ | 20%+ | — |
| Email 4 (Check-in) | 60%+ | 15%+ | — |
| Email 5 (Upgrade) | 70%+ | 35%+ | 25%+ |

---

## A/B Test Ideas

| Element | Variant A | Variant B |
|---------|-----------|-----------|
| Subject line | Emoji vs. no emoji | Question vs. statement |
| Send time | 9am PT | 2pm PT |
| CTA button | Green vs. blue | "Upgrade" vs. "Get Started" |
| Social proof | Customer count | Revenue numbers |
| P.S. section | Urgency vs. bonus | Scarcity vs. guarantee |

---

*Email Sequence v1.0 | March 19, 2026 | agencyos.network*
