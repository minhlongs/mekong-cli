# Dashboard Walkthrough Script — 10 Minute Tour

**Purpose:** Guided tour of the RaaS Dashboard for sales demos and customer onboarding
**Duration:** 10 minutes
**Audience:** C-Level executives, agency owners, technical decision makers

---

## Pre-Demo Setup (5 minutes before call)

### Browser Setup
- Open: `https://agencyos.network/dashboard`
- Logged in as: `demo@agencyos.network`
- Screen resolution: 1920x1080 (full screen)
- Close all other tabs

### Dashboard State
- Ensure demo project is selected: "Demo Client"
- Credits visible: 153 remaining
- Recent missions populated (5-10 completed)

---

## Tour Script

### Stop 1: Dashboard Overview (2 minutes)

**URL:** `https://agencyos.network/dashboard`

**Say:**
> "Welcome to the RaaS Command Center. This is where your entire development operation runs."

**Point out:**

```
┌─────────────────────────────────────────────────────────────┐
│  📊 CREDIT OVERVIEW                                         │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ Available    │ Used         │ Pending      │            │
│  │ 153          │ 47           │ 3            │            │
│  └──────────────┴──────────────┴──────────────┘            │
│                                                             │
│  📈 MISSION ACTIVITY (Last 30 days)                        │
│  [Chart: 67 missions completed, 99.8% success rate]        │
│                                                             │
│  ⚡ RECENT MISSIONS                                         │
│  • JWT Authentication     ✅ Complete   - 3 credits        │
│  • User CRUD API          ✅ Complete   - 3 credits        │
│  • Password Reset         ✅ Complete   - 1 credit         │
│  • Dashboard Widget       🔄 Running    - 3 credits        │
└─────────────────────────────────────────────────────────────┘
```

**Key Points:**
- Real-time credit tracking
- Mission success rate: 99.8%
- Average completion time: 12 minutes

---

### Stop 2: Mission Creation (2 minutes)

**URL:** `https://agencyos.network/dashboard/missions/new`

**Say:**
> "Creating a mission is as simple as describing what you want."

**Click:** "New Mission" button

**Type:** "Add user profile page with avatar upload"

**Point out:**

```
┌─────────────────────────────────────────────────────────────┐
│  📝 CREATE NEW MISSION                                      │
├─────────────────────────────────────────────────────────────┤
│  Description: [Add user profile page with avatar upload...] │
│                                                             │
│  AI Preview:                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Estimated Cost: 3 credits (Standard)                │   │
│  │ Estimated Time: 10-15 minutes                       │   │
│  │ Files: ~8 files                                     │   │
│  │ Endpoints: PUT /users/:id, POST /users/:id/avatar   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [ ] Use my own LLM key                                     │
│  [ ] White-label output (client-facing)                     │
│                                                             │
│  [CREATE MISSION]  [CANCEL]                                 │
└─────────────────────────────────────────────────────────────┘
```

**Key Points:**
- Natural language input (no technical specs needed)
- AI instantly estimates cost and time
- Optional: bring your own LLM keys
- Optional: white-label for client delivery

---

### Stop 3: Live Execution (2 minutes)

**URL:** `https://agencyos.network/dashboard/missions/[mission-id]`

**Say:**
> "Watch your AI team execute in real-time. This is where the magic happens."

**Point out:**

```
┌─────────────────────────────────────────────────────────────┐
│  🚀 MISSION: Add user profile page with avatar upload       │
│  Status: IN PROGRESS (8 minutes elapsed)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [████████████████░░] 80% Complete                          │
│                                                             │
│  AGENT PIPELINE:                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✅ PLANNER      (2 min)  Architecture designed      │   │
│  │ ✅ CODER        (4 min)  Code written               │   │
│  │ 🔄 TESTERRUNNING  Unit + integration tests        │   │
│  │ ⏳ REVIEWER     Pending  Security audit            │   │
│  │ ⏳ DEPLOY       Pending  Production deploy          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  LIVE LOG:                                                  │
│  [14:32:15] Tester: Running 12 unit tests...               │
│  [14:32:18] Tester: ✅ All tests passing                   │
│  [14:32:19] Tester: Running integration tests...           │
│                                                             │
│  FILES CREATED (6):                                         │
│  • src/pages/profile.tsx                                    │
│  • src/components/avatar-upload.tsx                         │
│  • src/api/users.ts                                         │
│  • src/types/profile.ts                                     │
│  • src/hooks/useProfile.ts                                  │
│  • tests/profile.test.tsx                                   │
└─────────────────────────────────────────────────────────────┘
```

**Key Points:**
- 4-agent pipeline: Planner → Coder → Tester → Reviewer
- Real-time logging
- Files created visible as they're written
- Typical mission: 10-15 minutes

---

### Stop 4: Code Review (2 minutes)

**URL:** `https://agencyos.network/dashboard/missions/[mission-id]/review`

**Say:**
> "Every mission passes through rigorous quality gates before deployment."

**Point out:**

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 CODE REVIEW REPORT                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  OVERALL SCORE: A (96/100) ✅                              │
│                                                             │
│  QUALITY GATES:                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✅ PLAN REVIEW      Architecture validated           │   │
│  │ ✅ CODE REVIEW      ESLint: 0 errors                │   │
│  │ ✅ TYPE CHECK       TypeScript: No errors           │   │
│  │ ✅ TEST COVERAGE    94% (target: 80%)               │   │
│  │ ✅ SECURITY AUDIT   npm audit: 0 vulnerabilities    │   │
│  │ ✅ BEST PRACTICES   React hooks: Correct            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  CODE DIFF:                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ + export function ProfilePage() {                    │   │
│  │ +   const { user, loading } = useProfile();         │   │
│  │ +   if (loading) return <LoadingSpinner />;         │   │
│  │ +   return (                                         │   │
│  │ +     <div className="profile-container">           │   │
│  │ +       <AvatarUpload userId={user.id} />           │   │
│  │ +       <ProfileForm user={user} />                 │   │
│  │ +     </div>                                         │   │
│  │ +   );                                               │   │
│  │ + }                                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [APPROVE & DEPLOY]  [REQUEST CHANGES]  [DOWNLOAD ZIP]     │
└─────────────────────────────────────────────────────────────┘
```

**Key Points:**
- 6 quality gates, all must pass
- Code review with diff viewer
- Security audit included
- One-click deploy or download

---

### Stop 5: Analytics & ROI (2 minutes)

**URL:** `https://agencyos.network/dashboard/analytics`

**Say:**
> "Track your ROI in real-time. See exactly how much time and money you're saving."

**Point out:**

```
┌─────────────────────────────────────────────────────────────┐
│  📊 ROI DASHBOARD (Last 30 Days)                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  KEY METRICS:                                               │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ Hours Saved  │ Money Saved  │ ROI          │            │
│  │ 47.5 hrs     │ $3,562       │ 1,687%       │            │
│  └──────────────┴──────────────┴──────────────┘            │
│                                                             │
│  MISSIONS BY TYPE:                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ API Endpoints    [████████░░░░] 45 missions         │   │
│  │ UI Components    [██████░░░░░░] 32 missions         │   │
│  │ Bug Fixes        [████░░░░░░░░] 18 missions         │   │
│  │ Tests            [██░░░░░░░░░░] 12 missions         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  TIME SAVINGS BREAKDOWN:                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Human Developer Time:    95 hours                   │   │
│  │ RaaS Time:               11.5 hours                 │   │
│  │ Time Saved:              83.5 hours (88%)           │   │
│  │                                                             │
│  │ At $75/hour blended rate:                               │   │
│  │ 83.5 hrs × $75 = $6,262 value created                  │   │
│  │ Subscription cost:       -$199                          │   │
│  │ NET SAVINGS:             $6,063                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Points:**
- Real-time ROI calculation
- Hours saved vs. human developer
- Cost breakdown
- Mission distribution by type

---

## Closing Pitch (1 minute)

**Say:**

> "In 10 minutes, you've seen:
> - How easy it is to create missions (natural language)
> - How AI agents execute autonomously (4-agent pipeline)
> - How quality is enforced (6-gate review)
> - How ROI is tracked (real-time analytics)
>
> **What took 4-6 hours → Done in 15 minutes.**
>
> Your competitors are already using this. The question is: will you lead or follow?
>
> Let's start your 14-day POC on Monday. Starter tier: $49. If you don't see 10x ROI, I refund personally."

---

## Common Questions During Demo

### Q: "What if I don't like the code?"
**A:** "You approve every deployment. If code doesn't meet standards, request changes or cancel—credits refunded instantly."

### Q: "Can this handle complex business logic?"
**A:** "Great question. The PEV Orchestrator breaks complex missions into steps, validates each before proceeding. 99.8% success rate across 5,000+ missions."

### Q: "What about our existing codebase?"
**A:** "Agents read your entire codebase, follow your patterns, use your conventions. It's like adding senior devs who instantly understand your architecture."

### Q: "How secure is this?"
**A:** "SOC2 Type II in progress. Zero security incidents. Every mission runs npm audit, Snyk, OWASP checks. Nothing deploys without passing."

### Q: "Can we white-label for clients?"
**A:** "Yes. Your clients see your brand. RaaS is your secret weapon. 40% of our agency customers white-label."

---

## Post-Demo Follow-Up

### Email Template

```
Subject: RaaS Demo Follow-Up — [Company Name]

Hi [Name],

Thanks for the demo today. As discussed:

**What You Saw:**
- Mission creation in natural language
- 4-agent autonomous execution (15 min vs 4-6 hours)
- 6-gate quality review
- Real-time ROI tracking

**Your ROI (based on your team of 8 devs):**
- Current: ~160 hours/month on feature dev
- With RaaS: ~40 hours/month (75% reduction)
- Savings: 120 hours × $75/hr = $9,000/month
- Pro tier: $199/month
- Net: $8,801/month | ROI: 4,322%

**Next Steps:**
1. Sign POC agreement (attached)
2. Monday 10am: Onboarding call
3. Week 1: Run 3-5 real client missions
4. Day 15: ROI review → decision

Questions before Monday? Reply anytime.

Best,
[Your Name]
```

---

*Dashboard Walkthrough v1.0 | March 19, 2026 | agencyos.network*
