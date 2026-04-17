# Mekong CLI — Department Services Marketplace

> **Services-as-Software**: 22 autonomous AI departments. Per-outcome pricing. One subscription.
> Based on the a16z thesis by Jennifer Li: *Labor markets worth $2T will be reshaped by AI agents that deliver services as software products.*

## Quick Install

```bash
mekong install --list        # Show all available departments
mekong install dept-sales    # Install specific department
mekong install --dry-run dept-sales  # Validate before installing
```

## Department Catalog

| ID | Department | Layer | Replaces | Monthly Floor | Per-Outcome Unit | Price | Commands | Skills |
|----|-----------|-------|---------|---------------|-----------------|-------|----------|--------|
| dept-strategy | Strategy | Founder | Chief of Staff + consultants | $49 | strategic_deliverable | $15 | 9 | 4 |
| dept-finance | Finance | Founder | CFO + bookkeeper | $49 | finance_deliverable | $10 | 6 | 3 |
| dept-legal | Legal | Founder | Outside counsel | $49 | legal_document | $12 | 5 | 5 |
| dept-fundraising | Fundraising | Founder | Fundraising advisor | $49 | investor_touchpoint | $5 | 6 | 3 |
| dept-sales | Sales | Business | SDR + AE team (5 people) | $49 | qualified_lead | $2 | 9 | 3 |
| dept-marketing | Marketing | Business | Agency + content team | $49 | marketing_asset | $3 | 7 | 5 |
| dept-customer-success | Customer Success | Business | CSM team | $49 | customer_action | $1.50 | 3 | 2 |
| dept-bizops | BizOps | Business | BizOps manager | $49 | ops_deliverable | $8 | 6 | 2 |
| dept-product-management | Product Management | Product | Senior PM | $49 | product_artifact | $10 | 5 | 3 |
| dept-ux-research | UX Research | Product | UX researcher | $49 | research_deliverable | $12 | 2 | 3 |
| dept-data-analytics | Data Analytics | Product | Data eng + analyst team | $49 | data_deliverable | $8 | 12 | 3 |
| dept-engineering-backend | Backend Engineering | Engineering | Backend team | $49 | engineering_task | $5 | 6 | 5 |
| dept-engineering-frontend | Frontend Engineering | Engineering | Frontend team | $49 | frontend_task | $5 | 5 | 5 |
| dept-engineering-qa | QA Engineering | Engineering | QA team | $49 | test_run | $3 | 6 | 2 |
| dept-devops | DevOps | Engineering | DevOps engineer | $49 | infra_operation | $4 | 8 | 4 |
| dept-hr | HR | People | HR manager | $49 | hr_action | $3 | 6 | 2 |
| dept-recruiting | Recruiting | People | Recruiter / agency | $49 | candidate_screened | $1.50 | 4 | 2 |
| dept-accounting | Accounting | People | Bookkeeper + CPA | $49 | accounting_transaction | $0.50 | 5 | 3 |
| dept-compliance | Compliance | People | Compliance officer | $49 | compliance_control | $5 | 11 | 4 |
| dept-it-security | IT Security | People | IT security team | $49 | security_action | $4 | 5 | 4 |
| dept-cx-support | CX Support | People | Support team | $49 | ticket_resolved | $0.75 | 2 | 2 |
| dept-communications | Communications | People | PR/comms manager | $49 | communication_piece | $6 | 3 | 3 |

**Total: 22 departments | 145+ commands | 76+ skills**

## Total Savings Calculator

If you deployed all 22 departments to replace their human equivalents:

| Layer | Traditional Annual Cost | SaS Annual Cost | Savings |
|-------|------------------------|-----------------|---------|
| Founder (4 depts) | $640,000/yr | $2,400/yr | $637,600 |
| Business (4 depts) | $710,000/yr | $9,600/yr | $700,400 |
| Product (3 depts) | $565,000/yr | $4,800/yr | $560,200 |
| Engineering (4 depts) | $745,000/yr | $9,600/yr | $735,400 |
| People/Ops (7 depts) | $780,000/yr | $14,400/yr | $765,600 |
| **Total** | **$3,440,000/yr** | **$40,800/yr** | **$3,399,200/yr** |

> Note: Traditional cost estimates based on actual market salaries + tool costs. SaS cost at max usage of $49/mo floor × 22 departments = $1,078/yr floor, scaling to ~$40,800/yr at high volume.

## Pricing Philosophy

Every department is priced on **outcomes**, not seats or time:

- **Per-outcome**: You pay for qualified leads, tickets resolved, documents reviewed — not "agent hours"
- **Monthly floor**: $49/mo per department covers baseline operations
- **No seat tax**: Unlimited agents running within a department; pricing tied to what they produce
- **Volume discounts**: Higher volumes unlock lower per-unit rates

This model is inspired by Jennifer Li's a16z thesis that AI agents should be priced like software products — per value delivered — not like staff augmentation.

## Layer Architecture

```
🏯 Founder Layer    — Strategy, Finance, Legal, Fundraising
💼 Business Layer   — Sales, Marketing, CX Success, BizOps
🎯 Product Layer    — Product Management, UX Research, Data Analytics
⚙️  Engineering Layer — Backend, Frontend, QA, DevOps
👥 People/Ops Layer  — HR, Recruiting, Accounting, Compliance, IT Security, CX Support, Communications
```

## Getting Started

1. **Browse:** `cat clipmart/departments/CATALOG.md`
2. **Pick a department:** Start with the one that costs you most today
3. **Install:** `mekong install dept-[name]`
4. **Configure:** Edit `.mekong/.env.dept-[name]` with credentials
5. **Run:** `mekong [first-command]`
6. **Track outcomes:** Check `.mekong/outcomes/[dept]/`

## Reference

- Jennifer Li, a16z: *"Services-as-Software: The Next $2T Opportunity"*
- Mekong CLI v6.0 OpenClaw Constitution
- Pricing benchmarks: HubSpot, ZoomInfo, Apollo, Clay, Harvey, Ironclad, Gusto, Bench, Vanta
