# OpenClaw RaaS Gateway: Zero→IPO Blueprint

This document outlines the complete tri-layer architecture (Business, Agentic, Governance) for OpenClaw RaaS Gateway, executing the 25-step Company Architecture Workflow.

---

## Tri-Layer Architecture Map

| Layer | Focus | Implementation |
|:---|:---|:---|
| **[Business]** | Monetization, GTM, Pricing | Metered billing (MCU compute credits), target SaaS founders, high margin. |
| **[Agentic]** | Automated Execution, AI Roles | Agent loops running code generation, automated SDR sales pipelines, and real-time SRE monitoring. |
| **[Governance]** | Legal, Compliance, Risk, Security | Multi-tenant isolation on Cloudflare Edge, SOC2 audit trails, and strict rate-limiting / runaway execution guards. |

---

## 25-Step Company Architecture

### Phase 1: Foundation (Steps 1-5)

#### 1. Master Framework
- **Business Layer**: RaaS (Robot-as-a-Service) metered gateway API. Charges founders per agent-second and LLM tokens.
- **Agentic Layer**: 5 core agent layers (Founder, Business, Product, Engineering, Ops) communicating via the Water Protocol.
- **Governance Layer**: Compliance with Cloudflare isolation rules and automatic circuit breakers for budget management.

#### 2. Refactor to 2026 Frame
- All CLI capabilities (e.g., `mekong cook/plan/ops`) are exposed via the edge gateway.
- Leverages Cloudflare Worker execution to run agent sandboxes with zero cold-start delay.

#### 3. Agentic OS Design
- **Autonomy Level**: 85% of standard operations (customer support, developer onboarding, billing alerts, code template generation) are fully automated.
- **Agent Orchestration**: Multi-tenant scheduler agent coordinates client workspace tasks on Cloudflare D1.

#### 4. IPO Readiness Score
- Target Jurisdiction: Singapore (ACRA) and Vietnam (for engineering ops).
- Security controls: Strict encryption at rest via Cloudflare R2, compliance with GDPR/PDPA for customer agent logs.

#### 5. Gap Report + Roadmap
- **Gap 1**: Edge isolation for Python-based agent runtimes (mitigated by using JS-based lightweight agents or calling external sandboxes).
- **Roadmap (6 months)**:
  - Month 1: API edge gateway MVP with basic MCU metering.
  - Month 2: Open-source CLI and SDK release for SaaS developers.
  - Month 3: Self-serve billing integration (Stripe/Creem).
  - Month 4-6: Launch partner program, scale to 500 active apps.

---

### Phase 2: Business Model (Steps 6-7)

#### 6. Business Model Patterns
- **Archetype**: B2B Developer SaaS with Metered Billing.
- **Unit Economics**:
  - ARPU: $150/month (blended startup plan).
  - LTV: $2,800.
  - CAC: $45 (highly content & organic driven).
  - Payback period: 3 months.
  - MCU (Micro-Cognitive Unit): 1 MCU = 100 API execution steps or 10k input/output tokens. Priced at $0.01 per MCU.

#### 7. Customer Psychology + Personas
- **ICP**: SaaS Founders who want to add AI features (e.g. auto-reply, automatic report writers, background data extractors) but don't want to build orchestration infrastructure or pay massive fixed monthly fees for idle agents.
- **Pain Point**: High setup costs, slow startup times (cold starts), and complex multi-tenant billing calculations.
- **Jobs-to-be-Done (JTBD)**: "Instantly run agent tasks in response to user webhooks without maintaining servers."

---

### Phase 3: Brand + Content (Steps 8-12)

#### 8. Brand Positioning
- **Core Message**: "The Stripe for AI Agent Execution."
- **Moat**: Sub-millisecond startup, serverless execution at 1/10th the cost of AWS-based sandboxes, built-in billing API.

#### 9. Content Pillars + TOF
- **Pillar 1**: Edge computing for AI agents (Latency & cost comparisons).
- **Pillar 2**: Multi-tenant AI billing (How to build billing models for LLMs).
- **Pillar 3**: Agentic automation case studies.

#### 10. Website/Landing Narrative
- **Hero**: "Run lightweight AI agents at the edge. Pay only for execution steps."
- **Interactive Console**: Live playground showing real-time MCU metered billing ticks as the agent executes a code task.

#### 11. Performance Ads + Creatives
- High-contrast visual graphics showing "AWS server billing ($500/mo)" vs "Cloudflare Edge MCU Billing ($12/mo)".
- Targets: YCombinator companies, tech stack subreddits, indie hackers.

#### 12. Advertorial + Storytelling
- "How we scaled an AI email writer to 10k users with $0 infrastructure costs using RaaS Gateway on Cloudflare Edge."

---

### Phase 4: Revenue Engine (Steps 13-15)

#### 13. Email + Lifecycle Sequences
- **Trigger**: Developer signs up and creates their first API key.
- **Drip 1**: Quick-start guide (5 minutes to run your first edge agent).
- **Drip 2**: Best practices on preventing agent infinite loops (circuit breakers).
- **Drip 3**: Case studies of scale & enterprise custom integrations.

#### 14. Sales Process + Channels
- Auto-outbound lead generation using LeadHunter to scan GitHub for projects using LangChain/LlamaIndex that are scaling fast.
- Semi-automated sales demo scheduling.

#### 15. GTM Experiments + Bullseye
- **Bullseye Channel**: Engineering blog posts detailing how to deploy custom models to Cloudflare Workers.
- **Secondary Channel**: Integration with popular agent frameworks (Agno, Autogen) as an execution target.

---

### Phase 5: Operations (Steps 16-21)

#### 16. AARRR + Lean Analytics
- **Acquisition**: Developer SDK downloads.
- **Activation**: Running at least 5 agent executions in 24 hours.
- **Retention**: API calls active week-over-week.
- **Referral**: "Powered by OpenClaw" branding in agent emails/outputs gives discounts.
- **Revenue**: Total MCUs billed.

#### 17. Fundraising + VC Narrative
- "The infrastructure layer for the next wave of agentic SaaS. The compute provider of AI actions."

#### 18. Risk + Scenario OS
- **Runaway Loop Risk**: Client writes a recursive loop. Mitigation: Hard execution limits and token budgets per API key.
- **Security Isolation Risk**: One agent hacking another client space. Mitigation: Standard Cloudflare Worker isolates.

#### 19. Talent + Org Design
- Ultra-lean team: 2 Founders, 1 Dev-Rel lead, and a fleet of OpenClaw-powered agent employees running code-review, QA, and content generation.

#### 20. Industry Patterns + IPO Archetypes
- Comparable IPO paths: Twilio (telephony APIs), Cloudflare (CDN/Workers), Stripe (payment gateway).

#### 21. Data Room + Investor Materials
- High-level pitch deck, technical architecture diagrams, cap table modeling, and sample contract terms (SLA).

---

### Phase 6: Execution (Steps 22-25)

#### 22. Agentic Execution + OKR
- **Q1 OKR**: Standardize edge API endpoints and onboard 10 beta test accounts.
- **Q2 OKR**: Introduce multi-tenant workspaces and Creem/Paddle metering.

#### 23. Board Governance
- Regular quarterly updates, automated financial reports sent to founders/investors.

#### 24. ESG + Impact
- Lowering overall carbon footprint by running compute on edge architectures rather than idle server VMs.

#### 25. Crisis + Reputation OS
- Status page monitoring showing edge routing and uptime, automated fallback to alternative LLM provider API routes when major provider outages occur.

---

## Execution Plan & Alignment

| Layer | Key Actions | Agent/Owner | Status |
|:---|:---|:---|:---|
| **Founder** | Oversee vision, GTM strategy, and fundraising metrics | CEO Agent | Planned |
| **Business** | Setup sales funnel, manage CRM integrations, and billing | Revenue Agent | Planned |
| **Product** | Design user console, manage developer docs, and feedback | Product Agent | Planned |
| **Engineering** | Build Worker API gateway, implement database schema on D1 | CTO / Dev Agent | Planned |
| **Ops** | Serverless health checks, billing compliance, SRE metrics | SRE / Ops Agent | Planned |

---

## Follow-up Action Items
Refer to [tasks.md](file:///Users/macbook/mekong-cli/plans/company-blueprint/tasks.md) for the immediate implementation schedule.
