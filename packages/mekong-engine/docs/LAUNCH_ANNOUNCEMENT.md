# Mekong Engine RaaS Gateway MVP — Launch Announcement

**Release Date:** March 20, 2026 | **Version:** 3.2.0 | **Status:** Production Ready

---

## Executive Summary

Mekong Engine is now live as a **Robotics-as-a-Service (RaaS) Gateway** — enabling businesses to deploy AI agents via simple API calls with pay-per-use credit billing.

**Production URL:** https://mekong-engine.agencyos-openclaw.workers.dev

---

## What is Mekong Engine?

Mekong Engine is a serverless PEV (Plan-Execute-Verify) platform running on Cloudflare Workers that provides:

| Feature | Description |
|---------|-------------|
| **Mission-Based API** | Submit goals → AI plans → executes → verifies → refunds failures |
| **Multi-Tenant Billing** | Credit ledger with NOWPayments integration |
| **BYOK LLM Support** | Bring Your Own Key (OpenAI, Google, Anthropic) or use Workers AI |
| **21 Route Groups** | Tasks, Agents, CRM, Governance, Ledger, Equity, and more |
| **Enterprise Ready** | RBAC, audit logging, rate limiting, quadratic voting |

---

## MVP Features (v3.2.0)

### Core Capabilities

1. **Task Management** (`/v1/tasks`)
   - Create missions with automatic credit deduction
   - Real-time SSE streaming
   - Cancel + refund support
   - Complexity-based pricing (1-5 credits)

2. **Agent Execution** (`/v1/agents`)
   - Git, File, Shell agents
   - Lead Hunter, Content Writer
   - Recipe Crawler

3. **Billing System** (`/billing`)
   - Tenant creation with API key generation
   - Credit ledger with double-entry accounting
   - NOWPayments webhook integration
   - Tier-based rate limiting (Free/Pro/Enterprise)

4. **BYOK LLM** (`/v1/settings/llm`)
   - AES-256-GCM encrypted storage
   - Provider presets (OpenAI, Google, Anthropic)
   - Masked key retrieval
   - Secure key rotation

5. **Governance** (`/v1/governance`)
   - Stakeholder management
   - Proposal creation & voting
   - Quadratic voting formula

6. **Extended Modules**
   - CRM (`/v1/crm`) — Contacts, companies, campaigns
   - Ledger (`/v1/ledger`) — Double-entry accounting
   - Equity (`/v1/equity`) — Cap table, SAFE notes
   - Revenue (`/v1/revenue`) — MRR/ARR tracking
   - Funding (`/v1/funding`) — Quadratic funding rounds

---

## Pricing Tiers

| Tier | Credits/Month | Price | BYOK | Rate Limit |
|------|--------------|-------|------|------------|
| **Free** | 100 MCU | $0 | Workers AI only | 50/hr, 500/day |
| **Starter** | 200 MCU | $49/mo | All providers | 500/hr, 5,000/day |
| **Pro** | 1,000 MCU | $149/mo | All providers | 2,000/hr, 20,000/day |
| **Enterprise** | Unlimited | $499/mo | Custom models | Custom limits |

**MCU = Mekong Credit Unit**
- Simple task (single command): 1 MCU
- Standard task (multi-step): 3 MCU
- Complex task (orchestrated agents): 5 MCU

---

## Quick Start

### 1. Create Tenant

```bash
curl -X POST https://mekong-engine.agencyos-openclaw.workers.dev/billing/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"my-company"}'
```

**Response:**
```json
{
  "tenant_id": "tnt_abc123",
  "name": "my-company",
  "api_key": "mk_xxx_secret_key",
  "tier": "free",
  "credits": 100
}
```

### 2. Run First Mission

```bash
curl -X POST https://mekong-engine.agencyos-openclaw.workers.dev/v1/tasks \
  -H "Authorization: Bearer mk_xxx" \
  -H "Content-Type: application/json" \
  -d '{"goal":"Analyze Q1 sales data and generate summary","params":{"complexity":"standard"}}'
```

### 3. Check Mission Status

```bash
curl https://mekong-engine.agencyos-openclaw.workers.dev/v1/tasks \
  -H "Authorization: Bearer mk_xxx"
```

---

## Design Partner Onboarding

### Benefits for Design Partners

- **Free Pro Tier** for 3 months (valued at $447)
- **Priority Support** via dedicated Slack channel
- **Direct Input** on roadmap priorities
- **Early Access** to beta features

### Onboarding Steps

1. **Sign Up** — Create tenant at `/billing/tenants`
2. **Configure LLM** — Set up BYOK or use Workers AI
3. **Run Test Mission** — Verify end-to-end flow
4. **Join Slack** — Get invited to #design-partners channel
5. **Schedule Kickoff** — 30-min onboarding call

### Design Partner Commitments

- Run at least 5 missions/week
- Provide feedback on bugs/UX within 48 hours
- Participate in monthly review calls

---

## API Documentation

**Full API Reference:** [docs/README.md](./README.md)

### Key Endpoints

| Category | Endpoint | Purpose |
|----------|----------|---------|
| **Health** | `GET /health` | System status |
| **Tasks** | `POST /v1/tasks` | Create mission |
| **Agents** | `POST /v1/agents/:name/run` | Run agent |
| **Settings** | `POST /v1/settings/llm` | Configure LLM |
| **Billing** | `GET /billing/credits` | Check balance |
| **CRM** | `POST /v1/crm/contacts` | Create contact |
| **Governance** | `POST /v1/governance/proposals` | Create proposal |

---

## Technical Specifications

### Infrastructure

| Component | Technology |
|-----------|------------|
| **Runtime** | Cloudflare Workers |
| **Framework** | Hono.js |
| **Database** | Cloudflare D1 (SQLite) |
| **Cache** | Cloudflare KV |
| **AI** | Workers AI (Llama 3.1 8B) + BYOK |
| **Deployment** | Git push → Cloudflare auto-deploy |

### Security

- API key authentication (SHA-256 hashed)
- AES-256-GCM encryption for BYOK keys
- HMAC-SHA256 webhook signatures
- Rate limiting per tenant tier
- Replay attack prevention

### Reliability

- **Uptime SLA:** 99.9% (Pro+ tiers)
- **RPO:** < 24 hours (daily backups)
- **RTO:** < 4 hours
- **Global Edge:** 200+ Cloudflare locations

---

## Verification Report

| Check | Status |
|-------|--------|
| **Type Check** | PASS (0 errors) |
| **Unit Tests** | PASS (129/129) |
| **Integration Tests** | PASS (11/11) |
| **CI/CD Pipeline** | Ready (GitHub Actions configured) |
| **Production Deploy** | Ready (Cloudflare Workers) |
| **Documentation** | Complete |
| **Support Runbook** | Complete |

---

## Roadmap (Post-Launch)

### Q2 2026

- [ ] Multi-region D1 replication
- [ ] Advanced analytics dashboard
- [ ] Plugin marketplace
- [ ] Mobile SDK (iOS/Android)

### Q3 2026

- [ ] Progressive decentralization (DAO governance)
- [ ] Token-based quadratic funding
- [ ] Cross-tenant collaboration
- [ ] Enterprise SSO (SAML/OAuth)

---

## Contact & Support

| Channel | Contact |
|---------|---------|
| **Production URL** | https://mekong-engine.agencyos-openclaw.workers.dev |
| **Documentation** | [docs/README.md](./README.md) |
| **Support Runbook** | [docs/SUPPORT_RUNBOOK.md](./SUPPORT_RUNBOOK.md) |
| **Email** | support@agencyos.network |
| **Slack** | #mekong-engine channel |
| **GitHub** | https://github.com/longtho638-jpg/mekong-cli |

---

## Demo Environment

A sandbox environment is available for testing:

```bash
# Sandbox URL (Free tier, rate limited)
SANDBOX_URL="https://mekong-engine.agencyos-openclaw.workers.dev"

# Create test tenant
curl -X POST $SANDBOX_URL/billing/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"demo-tenant"}'
```

---

## About AgencyOS

Mekong Engine is part of the **AgencyOS** ecosystem — a comprehensive platform for AI-powered business operations.

**Other AgencyOS Products:**
- **OpenClaw Engine** — PEV orchestration framework
- **RaaS Dashboard** — Tenant management UI
- **Solo OS** — Personal operating system

---

**Release:** v3.2.0 | **Date:** 2026-03-20 | **License:** MIT

---

## Appendix: Command Reference

### Health Check
```bash
curl https://mekong-engine.agencyos-openclaw.workers.dev/health
```

### Create Tenant
```bash
curl -X POST https://mekong-engine.agencyos-openclaw.workers.dev/billing/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"company-name"}'
```

### Configure LLM
```bash
curl -X POST https://mekong-engine.agencyos-openclaw.workers.dev/v1/settings/llm \
  -H "Authorization: Bearer mk_xxx" \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","api_key":"sk-..."}'
```

### Run Mission
```bash
curl -X POST https://mekong-engine.agencyos-openclaw.workers.dev/v1/tasks \
  -H "Authorization: Bearer mk_xxx" \
  -H "Content-Type: application/json" \
  -d '{"goal":"Your mission goal here","params":{"complexity":"standard"}}'
```

### Check Credits
```bash
curl https://mekong-engine.agencyos-openclaw.workers.dev/billing/credits \
  -H "Authorization: Bearer mk_xxx"
```

---

*Mekong Engine RaaS Gateway MVP — Built with Cloudflare Workers, Hono.js, and AI-powered PEV orchestration.*
