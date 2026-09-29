---
name: consulting
description: >-
  Mekong Consulting — AI agent building service, pricing, outreach
---

# /consulting — AI Agent Building & Enterprise Advisory Suite

Client engagement, commercial proposal synthesis, dynamic multi-currency service pricing (USD/VND), and B2B outreach for the Mekong RaaS Agency OS.

---

## Service Offerings & Pricing

| Service | Price (USD) | Price (VND) | Delivery Timeline |
|---|---|---|---|
| **AI Agent Audit (`audit`)** | $500 | ~12,700,000 VND | 3 business days |
| **Custom Agent Build (`custom_agent`)** | $2,000 | ~50,800,000 VND | 1 week |
| **Full Stack Setup (`full_stack`)** | $5,000 | ~127,000,000 VND | 2 weeks |
| **Monthly Retainer (`retainer`)** | $2,000/mo | ~50,800,000 VND/mo | Ongoing |

---

## Typer CLI Commands

```bash
# Consulting operations & pipeline overview
mekong consulting [--json]

# Show service catalog, pricing, and deliverables
mekong consulting pricing [--currency USD|VND] [--json]

# Generate commercial proposal for client / prospect
mekong consulting proposal "Acme Corp" --service custom_agent --industry "Fintech" [--budget 2500] [--save] [--output-dir <path>] [--json]

# Generate personalized multi-channel B2B outreach copy
mekong consulting outreach "TechCorp" --service audit --role "VP of Engineering" [--json]

# Manage client engagement contracts
mekong consulting engagement create "Fintech Asia" --service full_stack --price 5000 [--start-date 2026-10-01] [--notes "Trading bot"] [--json]
mekong consulting engagement list [--status PROPOSED|ACTIVE|DELIVERED|COMPLETED|ALL] [--json]
mekong consulting engagement update <ENG-ID> --status DELIVERED --notes "Deployment completed and verified" [--json]
```

---

## Native MCP Tools

| MCP Tool | Description | Arguments |
|---|---|---|
| `mekong_consulting_pricing` | Show service packages and dynamic pricing | `currency: str = "USD"` |
| `mekong_consulting_proposal` | Synthesize customized consulting proposal | `prospect_name: str, service_tier: str = "custom_agent", requirements: str = ""` |
| `mekong_consulting_outreach` | Generate multi-channel outreach templates | `prospect_name: str, service_tier: str = "custom_agent", role: str = "CTO"` |
