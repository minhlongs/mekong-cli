# Mekong IDE — Operations Kit for Claude Code

## Install

Add to your `.claude/settings.json`:

```json
{
  "skills": ["https://github.com/longtho638-jpg/mekong-cli/tree/main/skills/claudekit"]
}
```

Or copy `.claude/commands/` from the repo into your project.

## What this gives Claude Code

290 operational commands covering 22 business departments. When you tell Claude Code to "create an invoice" or "write a compliance report", these commands provide the structured pipeline and domain expertise.

### Example

```
You: /accounting-invoice-batch "Client ABC, web dev, $5000"
Claude Code: [loads accounting-invoice-batch.md → follows pipeline → generates invoice]
```

### Departments included

Finance, Marketing, Sales, Engineering, Legal, Compliance, HR,
Design, Data, Security, Growth, Venture, CTO, CFO, CMO, CRO,
Operations, Incident, Observability, ML/AI, Customer Success, Product

### Key commands

| Command | What it does |
|---------|-------------|
| accounting-invoice-batch | Generate invoices from specs |
| marketing-content-engine | SEO content, calendars, social posts |
| devops-deploy-pipeline | CI/CD with rollback |
| legal-contract-review | Red flag analysis on contracts |
| compliance-soc2-prep | SOC2 readiness checklist |
| sales-pipeline-build | CRM pipeline from scratch |
| hr-onboard | New hire onboarding flow |

### Full list

See `.claude/commands/` — 290 markdown files, each a complete operational pipeline.

## RaaS API (optional)

For programmatic access, subscribe to Mekong IDE:
- Starter $49/mo — 200 credits
- Growth $149/mo — 1,000 credits  
- Pro $499/mo — 5,000 credits

API: https://agencyos.network
