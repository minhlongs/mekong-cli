# Legal Department as a Service

> Replace $400/hr outside counsel for routine legal work with AI agents. Contracts reviewed in minutes, not weeks.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| Outside counsel (routine) | $48,000/yr | $49/mo floor |
| Ironclad CLM | $50,000/yr | Included |
| Legal template library | $5,000/yr | Included |
| **Total replaced** | **$103,000/yr** | **~$1,200/yr** |

## What This Department Does

1. **Contract Review** — NDA, MSA, SaaS agreements, employment contracts with redlines
2. **Policy Drafting** — Privacy policy, terms of service, acceptable use, cookie policy
3. **Compliance Checks** — GDPR, CCPA, SOC2 policy alignment
4. **Board Governance** — Board resolutions, consent items, governance calendar
5. **IP Protection** — IP assignment clauses, work-for-hire review

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Contract review + redlines | $25 |
| Privacy policy draft | $20 |
| Employment agreement | $30 |
| Vendor NDA | $15 |
| Board resolution | $20 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong legal-contract-review     # Review + redline contracts
mekong legal-compliance-check    # Legal compliance gap check
mekong legal-policy              # Policy document drafting
mekong compliance-check          # Compliance posture check
mekong board-compliance          # Board governance compliance
```

## Install

```bash
mekong install dept-legal
```

## Important Disclaimer

This department produces **legal drafts for attorney review**, not legal advice. Always have a licensed attorney review significant contracts before signing. The agents reduce attorney time by 80%, not to zero.

## Configuration

```bash
# .mekong/.env.dept-legal
DEPT_LEGAL_JURISDICTION=US-CA  # Primary legal jurisdiction
DEPT_LEGAL_COMPANY_TYPE=delaware-c-corp
DEPT_LEGAL_GDPR_APPLICABLE=true
DEPT_LEGAL_CCPA_APPLICABLE=true
DEPT_LEGAL_CONTRACT_STORAGE=notion  # notion|google-drive|docusign
```

## Comparison: Traditional vs SaS

| Metric | Outside Counsel | Legal Dept SaS |
|--------|----------------|----------------|
| NDA review | $800-2,000 | $15 |
| Privacy policy | $5,000-15,000 | $20 |
| Turnaround | 3-10 business days | 30 minutes |
| Contract volume limit | Budget-gated | Unlimited |

Harvey AI charges $5,000+/month for enterprise legal AI. This runs locally for $49/mo.
