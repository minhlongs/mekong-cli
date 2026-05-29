# Mekong CLI v6.0.0 — Project Overview & PDR

**Version:** 6.0.0 (Open Source)
**Status:** Production | Public MIT License
**Updated:** 2026-04-26
**Target:** Python 3.9+, TypeScript 18+, Cloudflare Workers
**Repository:** https://github.com/longtho638-jpg/mekong-cli

## 1. Project Overview

Mekong CLI is an **open-source AI agent framework** that transforms high-level goals into executable automation pipelines. It implements the **Plan-Execute-Verify (PEV)** pattern with:

- Type-safe agents extending a common protocol
- Orchestration engine with DAG-based parallel execution
- Pluggable LLM providers (OpenAI, Gemini, offline models)
- Built-in credit/billing system for monetizing agent work (RaaS)
- Multi-tenant isolation for platform providers

### Core Problem Solved
Developers building AI-powered platforms need a framework that:
1. Safely decomposes goals into steps (avoids hallucinations)
2. Executes steps with rollback on failure (reliability)
3. Validates results against quality gates (safety)
4. Tracks credits/billing per task (monetization)

### Target Users
- **Developers** building autonomous agent systems
- **Platform creators** implementing RaaS (Revenue-as-a-Service)
- **Enterprises** deploying AI agents with audit trails and cost controls
- **Researchers** experimenting with agent orchestration patterns

### v3.0.0 Deliverables
- **Agent Protocol** — Type-safe interface for pluggable agents
- **DAG Scheduler** — Parallel task execution with dependency management
- **LLM Provider Abstraction** — Swap providers (OpenAI/Gemini/offline)
- **Credit System** — SQLite-backed multi-tenant billing
- **Python SDK** — Client library for submitting missions
- **FastAPI Server** — REST API with WebSocket streaming

## 2. Product Requirements (PDR)

### Functional Requirements (FR)

| ID | Requirement | Status |
|----|------------|--------|
| FR-AGENT-01 | Agents implement AgentProtocol (plan/execute/verify) | ✅ v3.0 |
| FR-SCHEDULE-01 | DAG scheduler executes steps in topological order | ✅ v3.0 |
| FR-SCHEDULE-02 | Parallel execution of independent steps | ✅ v3.0 |
| FR-PROVIDER-01 | Pluggable LLM providers with auto-failover | ✅ v3.0 |
| FR-PLUGIN-01 | Community plugins (PyPI + local ~/.mekong/plugins/) | ✅ v3.0 |
| FR-CREDIT-01 | Multi-tenant credit store (SQLite) | ✅ v3.0 |
| FR-BILLING-01 | NOWPayments webhook integration for payments | ✅ v3.0 |
| FR-SDK-01 | Python SDK for submitting missions | ✅ v3.0 |
| FR-ROLLBACK-01 | Automatic rollback on verification failure | ✅ v3.0 |

### Non-Functional Requirements (NFR)

| Area | Requirement | Target |
|------|------------|--------|
| Performance | Plan < 2s, Execute < 30s, Verify < 5s | Measured |
| Reliability | No silent task failures, clear error reporting | 99.5% |
| Type Safety | Zero `any` types in production code | 100% |
| Test Coverage | Unit + integration tests for all modules | >80% |
| Security | No secrets in code, input validation (Pydantic) | Verified |
| Scalability | Parallel agent execution, pluggable providers | Proven |

### Success Criteria

1. **Stability**: Zero silent task failures
2. **Adoption**: Community contributions on PyPI
3. **Quality**: All merged code passes type safety + tests
4. **Performance**: CLI startup < 1s, typical task execution < 1 min

## 3. Architecture Summary

| Component | Technology | Location | Purpose |
|-----------|-----------|----------|---------|
| **CLI** | Python 3.9+ / Typer / Rich | `src/main.py` | Command-line interface |
| **Core Engine** | Pydantic / Python | `src/core/` | PEV orchestration |
| **Agents** | AgentProtocol | `src/agents/` + plugins | Task executors |
| **Providers** | LLMProvider abstraction | `src/core/providers.py` | LLM backends |
| **Billing** | SQLite + NOWPayments | `src/raas/` | Credit system |
| **API Server** | FastAPI + WebSocket | `src/core/gateway.py` | REST + streaming |
| **RaaS Plugin** | TypeScript / Cloudflare Workers | `plugins/mekong-raas/` | Auth, metering, billing |
| **Tasks DAG Plugin** | TypeScript / Cloudflare Workers | `plugins/mekong-tasks/` | Background scheduling |
| **Skills Catalog** | JSON manifest + SKILL.md | `skills/mekong/` | 22 departments, 348 commands |
| **Testing** | pytest | `tests/` | 62+ tests |
| **Package** | Poetry / PyPI | `pyproject.toml` | Distribution |

## 4. Key Features Breakdown

### PEV Pipeline (Plan-Execute-Verify)
Goal → Decomposed into steps with dependencies → Parallel execution → Quality validation → Credit deduction

### Agent System
Pluggable agents (Git, File, Shell) + community extensions via PyPI entry points or ~/.mekong/plugins/

### Company Templates (Clipmart)
Pre-built Paperclip AI company templates for different team structures:
- **mekong-saas-startup** — 22-agent full organization (solo founder with 5 departments)
- **mekong-dev-shop** — 8-agent engineering-focused solo operation
- **mekong-solo-founder** — 5-agent lean starter template
Each includes agent definitions, escalation matrices, Binh Pháp governance, and 300+ operational skills.

### Credit Billing
Per-tenant credit ledger: simple tasks cost 1 credit, complex tasks cost 5+ credits

### DAG Execution
Dependency-aware scheduling: runs independent steps in parallel, waits on dependencies, cancels downstream on failure

### Module 1: Nhịp Điệu Xanh Landing Page (Smart Landing & Ingestion Platform)
Newly bootstrapped Next.js project (`apps/nhipdieuxanh-landing`) serving as the primary capture layer for lead acquisition:
- **Dynamic Localization**: Auto-adjusts promotional banners, specific region perks, and investment copy based on the visitor's selected location (e.g. Cần Thơ, An Giang, Cà Mau, Sóc Trăng).
- **Interactive Mortgage Calculator**: Allows clients to customize property values, loan percentages, payment terms, and interest rates to calculate monthly payables dynamically.
- **Decree 13 Privacy Consent Checkbox**: Captures explicit user consent for PII processing. Submitting without checking invokes automated database-level masking.
- **Gated Blueprint Lock**: Restricts view of architectural blueprints until user provides verified email and phone.
- **Floating AI Chatbot Mockup**: Employs client-side keyword matching for common developer/investor inquiries (pricing, legal status, location, loan criteria).

## 5. Development Roadmap

| Version | Features | Timeline |
|---------|----------|----------|
| v3.0 (Current) | PEV engine, agents, DAG scheduler, credit billing | Shipped |
| v3.1 | Plugin marketplace, agent templates | Q2 2026 |
| v3.2 | Web dashboard (open-source), community recipes | Q3 2026 |
| v4.0 | Enterprise features: audit logs, RBAC, SLA tracking | Q4 2026 |

## 6. Licensing & Governance

- **License:** MIT
- **Governance:** Open source, community-driven
- **Contributing:** See CONTRIBUTING.md
- **Code of Conduct:** Included in repository
