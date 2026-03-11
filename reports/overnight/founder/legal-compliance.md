# Legal Framework & Compliance — Mekong CLI

**Date:** March 2026
**Covers:** legal, contract, agreement, ip-patent

---

## Corporate Structure

### Current State
- No formal incorporation (bootstrap phase)
- MIT license published on GitHub
- Payments via Polar.sh (handles tax/KYC for subscriptions)

### Recommended Structure (Pre-Raise)

**Option A: Vietnam-only (simple, cheap)**
- Register as sole proprietorship or LLC in Vietnam
- Suitable for: bootstrap, VN-market-only revenue
- Risk: US/EU VCs cannot invest directly into Vietnamese entity

**Option B: Singapore HoldCo + Vietnam OpCo (recommended)**
- Singapore Private Limited Company (SGD 1,000 setup, ~$750)
- 100% owns Vietnam OpCo (for local operations)
- US/EU investors invest into Singapore entity
- Standard structure for SEA startups raising internationally
- Setup timeline: 4–6 weeks via Rikvin or Sleek

**Option C: Delaware C-Corp + Vietnam subsidiary (US-VC-ready)**
- Required if targeting YC or US-lead investors
- Delaware incorporation: ~$500 via Stripe Atlas or Clerky
- Enables US SAFE instruments natively
- Best for: YC application, US enterprise sales

**Recommendation:** Singapore HoldCo before Q3 2026 seed raise. Convert to Delaware if YC accepted.

---

## Intellectual Property

### MIT License Analysis

Current: MIT license on all source code.

**Implications:**
- Anyone can fork, commercialize, redistribute (with attribution)
- Competitors CAN build a competing SaaS on Mekong code
- We CANNOT add proprietary features to existing MIT codebase retroactively

**Dual-licensing strategy (recommended Q3 2026):**
- Core engine: MIT (community goodwill, contributions)
- Enterprise features: Commercial license (SSO, audit logs, on-prem, SLA)
- Model: HashiCorp BSL, MongoDB SSPL, GitLab CE/EE

**What to keep proprietary:**
- `src/raas/` billing engine (35+ modules) — do NOT open source
- Enterprise dashboard (agencyos.network)
- Tôm Hùm daemon (`apps/openclaw-worker/`) — defer OSS release
- LLM routing optimizations with benchmark data

### Trademark

Register "Mekong CLI" trademark in:
- Vietnam (NOIP registration, ~$50, 3–6 months)
- Singapore (IPOS, ~$240, 9 months)
- US (USPTO, ~$350/class, 12–18 months)

Classes to register: Class 9 (software), Class 42 (SaaS/cloud services)

**Priority:** File Vietnam + Singapore before seed round announcement.

### Domain & Brand IP

Secure immediately if not held:
- [ ] mekong.sh (primary)
- [ ] mekong.cli (if available)
- [ ] mekongcli.com
- [ ] agencyos.network (dashboard)
- [ ] @mekongcli on Twitter/X, GitHub, YouTube, ProductHunt

---

## Customer Contracts & Terms

### Terms of Service (Required before paid launch)

Key clauses to include:

**1. Service Definition**
- Mekong CLI is a tool, not a professional service
- No guarantee of output quality from LLM-generated content
- MCU credits are consumed per successful task delivery (HTTP 200)

**2. Payment Terms**
- Subscriptions renew monthly/annually via Polar.sh
- No refunds on consumed MCU credits
- Disputed charges: 30-day window to raise with support

**3. Acceptable Use Policy**
Prohibited:
- Using Mekong CLI to generate illegal content
- Reverse engineering the RaaS billing system
- Sharing Enterprise credentials across organizations
- Automated account creation to abuse free tiers

**4. Data Privacy**
- We do not store LLM prompt content by default
- Usage metadata (MCU counts, timestamps) stored for billing audit
- GDPR: right to deletion available, submit to legal@mekong.sh
- Data residency: Cloudflare (global edge, EU data stays in EU if configured)

**5. Limitation of Liability**
- Maximum liability capped at 3 months of subscription fees paid
- No liability for losses from AI-generated code/plans deployed to production
- Standard SaaS limitation — critical for avoiding runaway legal exposure

**6. Governing Law**
- Singapore law (if Singapore HoldCo)
- SIAC arbitration for disputes >$10K
- English language contracts

### Enterprise Agreement Template

For $499/mo Enterprise tier, add:
- SLA: 99.5% uptime (Cloudflare SLA backs this)
- Data Processing Agreement (DPA) for GDPR compliance
- Security questionnaire response (standard InfoSec doc)
- Custom LLM endpoint option (customer brings own keys)
- Dedicated support channel (Slack shared channel)
- 30-day notice for price changes

---

## Open Source Contribution Agreement

Before accepting community PRs to `.claude/commands/` or `src/agents/`:

**Contributor License Agreement (CLA):**
- Contributors grant Mekong CLI perpetual license to use contributions
- CLA-assistant.io automates this for GitHub PRs
- Required for: any PR touching core engine, new agents, billing code
- Not required for: docs fixes, README typos

**Why CLA matters:** Enables future dual-licensing without contributor consent issues (see HashiCorp case).

---

## Regulatory Compliance

### GDPR (EU users)
- Privacy policy required before collecting any data
- Cookie consent if web dashboard has analytics
- DPA template available from Cloudflare (processor agreement)
- Data deletion endpoint: `DELETE /api/v1/user` in RaaS API

### Vietnam Cybersecurity Law
- If storing Vietnamese user data, may require local data residency
- Cloudflare has edge nodes in Singapore (nearest to VN)
- Low risk at bootstrap scale; revisit at 1,000+ VN users

### AI Act (EU, 2026)
- Mekong CLI is a "general purpose AI tool" — lower risk category
- Not a "high-risk AI system" (not used in healthcare, finance, law)
- Disclosure requirement: outputs should note AI-generated when applicable
- Current `mekong cook` already runs verifier checks — partial compliance

### US Export Controls (EAR/ITAR)
- MIT open source software generally exempt from export controls
- LLM API keys are customer-provided — not our liability
- Review if adding encryption features to RaaS billing

---

## IP Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Competitor forks MIT code | High | Low | Dual-license enterprise features |
| Patent troll on PEV engine | Low | High | Document prior art (publish architecture paper) |
| Trademark conflict "Mekong" | Low | Medium | Register trademark before launch |
| CLA not signed by contributor | Medium | Medium | CLA-assistant.io automation |
| LLM provider ToS violation | Low | High | Review each provider's commercial use terms |
| GDPR breach | Low | High | Privacy policy + DPA before EU marketing |

---

## Legal Budget 2026

| Item | Cost | When |
|------|------|------|
| Singapore incorporation | $750 | Q2 2026 |
| TOS + Privacy Policy (template) | $500 | Q1 2026 |
| Vietnam trademark filing | $50 | Q2 2026 |
| Singapore trademark filing | $240 | Q2 2026 |
| CLA automation setup | $0 (open source) | Q1 2026 |
| Seed round legal (SAFE docs) | $5,000–$15,000 | Q4 2026 |
| Enterprise DPA template | $300 | Q3 2026 |
| **Total 2026** | **~$17,000** | |
