# Contract Review — March 2026
**Generated:** 2026-03-12 | **Entity:** Mekong CLI / OpenClaw | **Status:** Templates Ready

---

## Executive Summary

No active contracts. Pre-revenue stage. This document establishes the contract
framework for SaaS credit sales, enterprise agreements, and data processing.
All templates are ready for first customer. Legal review by counsel recommended
before first enterprise deal over $10,000.

---

## 1. SaaS Terms of Service (Standard — Credit Sales)

### Scope
Governs all Starter, Pro, and Enterprise subscription tiers sold via Polar.sh.

### Key Terms

**1.1 Service Description**
Mekong CLI ("Service") provides AI-powered task orchestration via the RaaS (Recipe-as-a-Service)
API. Credits (MCU) are consumed per successful task delivery.

**1.2 Payment Terms**
- Subscriptions billed monthly in advance via Polar.sh
- Credits are prepaid and non-refundable once consumed
- Unused credits carry forward 30 days post-billing cycle
- Failed payment → 7-day grace period → account suspension

**1.3 Acceptable Use**
Customer shall not:
- Use Service to generate illegal, harmful, or deceptive content
- Reverse-engineer the Recipe system or extract proprietary contracts
- Resell API access without written permission (Enterprise tier only with addendum)
- Exceed rate limits (defined in API documentation)

**1.4 Service Level Agreement**
- Uptime target: 99.5% monthly (Cloudflare Workers SLA basis)
- Scheduled maintenance: 2-hour window, 48-hour notice
- Support response: 48 hours (Starter), 24 hours (Pro), 4 hours (Enterprise)
- Credits refunded for outages exceeding 4 hours in any 30-day period

**1.5 Data and Privacy**
- No customer content stored beyond MCU ledger balance
- Customer retains all rights to inputs and outputs
- LLM processing via customer's own API keys (BYOK) — no data retention by Mekong
- See Privacy Policy [link] for full data handling details

**1.6 Intellectual Property**
- Mekong CLI codebase: MIT license (open source)
- Recipe system (388 contracts): Proprietary trade secret
- Customer outputs: Owned by customer
- Customer inputs: Customer retains all rights

**1.7 Limitation of Liability**
- Maximum liability: 3 months of fees paid
- No liability for indirect, incidental, or consequential damages
- No warranty of fitness for particular purpose (AI outputs are probabilistic)

**1.8 Termination**
- Customer may cancel anytime via Polar.sh dashboard
- Mekong may terminate for AUP violation with 5-day notice
- Data export available 30 days post-termination

---

## 2. Enterprise Agreement Framework

### When to Use
- Annual contract value > $5,000
- Custom integrations required
- SLA stronger than standard tier
- Data processing agreement required

### Enterprise-Specific Terms

**2.1 Custom Pricing**
- Annual prepay discount: 15%
- Volume commitment: Minimum 10,000 MCU/mo
- Dedicated support: Named CSM assigned
- Custom SLA: 99.9% uptime, 1-hour response

**2.2 White-Label Rights** (Enterprise Add-on)
- Customer may brand CLI output with their own name
- No resale without signed Reseller Addendum
- Revenue share: 20% of downstream revenue

**2.3 Security Addendum**
- Penetration test results available on NDA
- SOC 2 Type II: Target Q4 2026 (post-revenue)
- GDPR DPA: See Section 3 below

**2.4 Enterprise Negotiation Checklist**
- [ ] Payment terms (Net-30 vs. prepaid)
- [ ] Custom SLA thresholds
- [ ] Data residency requirements
- [ ] Audit rights
- [ ] Subprocessor list approval
- [ ] Exit/migration assistance clause
- [ ] Auto-renewal notice period (60 days)

---

## 3. Data Processing Addendum (DPA) Template

For EU customers or any customer requiring GDPR compliance documentation.

```
DATA PROCESSING ADDENDUM

This DPA is entered into between:
  Controller: [Customer Name] ("Customer")
  Processor: Mekong CLI / OpenClaw ("Provider")

1. SUBJECT MATTER
   Provider processes personal data on behalf of Customer solely to provide
   the Service as described in the Agreement.

2. NATURE AND PURPOSE
   Processing activities: API request routing, MCU credit ledger management
   Duration: Term of subscription agreement
   Type of data: Email (via Polar.sh, not Provider), usage metadata
   Data subjects: Customer's authorized users

3. CUSTOMER OBLIGATIONS
   Customer warrants it has legal basis to share any personal data with Provider.

4. PROVIDER OBLIGATIONS
   4.1 Process data only on Customer's documented instructions
   4.2 Ensure personnel are bound by confidentiality
   4.3 Implement appropriate technical/organizational security measures
   4.4 Assist with data subject rights requests within 72 hours
   4.5 Delete or return data upon termination

5. SUBPROCESSORS
   Approved subprocessors:
   - Cloudflare, Inc. (infrastructure, US/EU)
   - Polar.sh (payment processing, EU)
   [Full list at: mekongcli.com/subprocessors]

6. INTERNATIONAL TRANSFERS
   Data may be transferred to US-based Cloudflare infrastructure.
   Safeguard: Cloudflare EU-US Data Privacy Framework certification.

7. SECURITY MEASURES
   - Encryption at rest (Cloudflare D1 AES-256)
   - Encryption in transit (TLS 1.3)
   - Access controls (API key authentication)
   - Incident notification: 72 hours per GDPR Art. 33
```

---

## 4. Open Source Contributor Agreement

Supplementing the MIT license for significant contributions (>500 lines):

**Inbound = Outbound:** All contributions licensed under MIT.
**Patent grant:** Contributors grant patent license for their contributions.
**No CLAs for small fixes:** DCO sign-off (`git commit -s`) sufficient for minor PRs.

---

## 5. Contract Risk Register

| Contract Type      | Risk                         | Mitigation                        |
|--------------------|------------------------------|-----------------------------------|
| SaaS ToS           | AI output liability          | Disclaimer + liability cap        |
| Enterprise         | SLA breach penalty           | Credit-only remedy (no cash)      |
| DPA                | GDPR non-compliance          | No PII architecture               |
| White-label        | IP leakage                   | Recipe system stays server-side   |
| Contributor CLA    | Patent troll via contrib     | Patent grant in CLA               |

---

## 6. Action Items

| Item                              | Priority | Due        |
|-----------------------------------|----------|------------|
| Legal counsel review of ToS       | High     | Before $10K deal |
| Privacy policy (public-facing)    | High     | Apr 2026   |
| DPA template finalized            | Medium   | May 2026   |
| Enterprise agreement template     | Medium   | May 2026   |
| CLA bot (cla-assistant.io)        | Low      | 10th contributor |

---

*Next review: Upon first enterprise inquiry or $5K MRR, whichever comes first.*
