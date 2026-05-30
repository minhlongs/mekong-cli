# Mekong CLI Roadmap

**Current Version:** v3.0.1 (Stable)
**Last Updated:** 2026-03-11
**Status:** Open Source, Community-Driven

## Vision

Mekong CLI is building the **de facto standard for AI-powered agent orchestration**. Our roadmap focuses on:

1. **Reliability** — Zero silent failures, comprehensive audit trails
2. **Extensibility** — Easy plugin ecosystem for agents & providers
3. **Monetization** — Credit-based billing for RaaS platforms
4. **Community** — Open governance, transparent development

---

## v3.0.1 (Current) — UI Restructure & Code Quality Complete

**Status:** ✅ Shipped | **Release Date:** 2026-03-11 | **Updated:** 2026-04-05

### Delivered

- ✅ Plan-Execute-Verify (PEV) orchestration engine
- ✅ AgentProtocol for pluggable agents
- ✅ DAG scheduler with parallel execution
- ✅ Parallel Task Concurrency Engine (`cook-auto-parallel` & `goal run-parallel`)
- ✅ SQLite WAL mode journaling, connection busy timeouts & RLock thread synchronization
- ✅ Built-in agents (Git, File, Shell, RecipeCrawler)
- ✅ LLM provider abstraction (OpenAI, Gemini, offline)
- ✅ Multi-tenant credit system (SQLite)
- ✅ Python SDK for mission submission
- ✅ FastAPI server with WebSocket streaming
- ✅ Automatic rollback on verification failure
- ✅ RaaS API Bootstrap (Phase 1-6)
- ✅ Landing page v5.0 UI restructure (17 fixes)
- ✅ Revenue Router idempotency & modularization (PR #31)
- ✅ 102+ unit tests (>85% coverage)

### v3.0 Milestones

**RaaS Bootstrap (Phase 1-6):** Production REST API, JWT auth, credit system, NOWPayments webhooks, rate limiting, audit trails ✅

**Landing Page v5.0 (17 fixes):**
- Stats updated to 319 commands, 89 super workflows, 463 skills, 127 agents
- Free tier added (4-column pricing layout)
- Hero, cascade demo, features grid rewritten for super command/DAG architecture
- New `/engineering` page showcasing infrastructure capabilities
- AgencyOS branding removed, replaced with Mekong CLI identity
- Vietnamese text removed from terms/privacy pages
- SEO metadata optimized in layout.tsx
- Stats consistency verified across all pages

### Quality Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Type Safety | 100% | 100% (zero `any` types) |
| Test Coverage | >80% | 84% |
| CLI Startup | <1s | 0.8s |
| Task Execution | <30s typical | ~15s avg |
| API Response | <500ms | ~200ms |

---

## v3.1 (Next) — Plugin Ecosystem & Templates

**Target:** Q2 2026 | **Status:** Planning

### Goals

- **Plugin Marketplace** — Curated list of community agents/providers
- **Recipe Templates** — Pre-built automation recipes (deployment, testing, CI/CD)
- **Agent Starter Kit** — Boilerplate for building custom agents
- **Better Error Messages** — Actionable debugging for failed tasks

### Features

- [ ] Plugin registry & discovery service
- [ ] Agent templates (web scraper, email, database, API client)
- [ ] Provider templates (custom LLM, local model, fallback chain)
- [ ] Interactive agent builder CLI (`mekong agent new`)
- [ ] Recipe marketplace (GitHub-based registry)

### Success Criteria

- 10+ community plugins published
- Plugin installation <1 minute
- Documentation with working examples

---

## v3.2 — Dashboard & Web UI

**Target:** Q3 2026 | **Status:** In Progress

### Goals

- **Open-source Dashboard** — Monitor missions, manage credits, view audit logs
- **Recipe Editor** — Visual workflow designer (DAG-based)
- **Admin Panel** — Tenant management, credit allocation, webhook logs
- **Mobile App** — Submit missions, check status (React Native)

### Features

- [x] **Onboarding Analytics** (Phase 5 - 2026-03-14) — Funnel chart, conversion metrics, drop-off analysis, time-to-complete, cohort table
- [ ] Mission monitoring dashboard
- [ ] Credit allocation interface
- [ ] Recipe Editor — Drag-and-drop workflow designer
- [ ] Real-time WebSocket updates
- [ ] Dark mode support
- [ ] Role-based access control (RBAC)

### Completed Phase (2026-03-14)

**Phase 5: Onboarding Analytics UI**
- Vite + React 19 app at `apps/dashboard/`
- Analytics page with 5 visualization components
- Type-safe API integration with backend
- Responsive Tailwind CSS v4 design
- Support for 30/60/90-day time periods

### Success Criteria

- Usable dashboard for non-technical users
- Zero JavaScript errors in production
- Mobile-responsive design

---

## v4.0 — Enterprise Features

**Target:** Q4 2026 | **Status:** Planning

### Goals

- **Audit Logging** — Complete action trail for compliance
- **RBAC** — Fine-grained permissions (admin, operator, viewer)
- **SLA Tracking** — Task SLO metrics and reporting
- **Advanced Analytics** — Cost optimization, success rates, latency patterns
- **Backup/DR** — Automated backups, disaster recovery plan

### Features

- [ ] Immutable audit log (no deletions)
- [ ] API rate limiting per role
- [ ] SLA violation alerts
- [ ] Cost optimization recommendations
- [ ] Multi-region deployment support
- [ ] High availability (load balancing)

### Success Criteria

- SOC 2 Type II compliance ready
- 99.99% uptime SLA achievable
- Recovery time < 5 minutes

---

## Nhịp Điệu Xanh (Module 1) — Smart Landing & Ingestion Platform

**Status:** ✅ Fully Completed & Verified | **Completion Date:** 2026-05-28

This module implements the Cần Thơ smart landing page and lead ingestion gateway with strict security and privacy features matching Decree 13.

### Phase 1: Core Landing UI & Dynamic Localization
- [x] Responsive layout using Tailwind CSS and Lucide icons.
- [x] Location dropdown selector.
- [x] Dynamic location-based promotion banners (Cần Thơ, An Giang, Cà Mau, Sóc Trăng).
- [x] Dark/Light theme switching system.

### Phase 2: Interactive Mortgage Calculator
- [x] Input fields for property value, down payment, loan percentage, term, and interest rate.
- [x] Real-time calculations of monthly payments.
- [x] Amortization schedule visualization.

### Phase 3: Gated Blueprint Lock
- [x] Floor plan selector and tabbed layout.
- [x] Architectural blueprint access gated behind contact collection.
- [x] Client-side email/phone validation.

### Phase 4: Floating FAQ Chatbot Mockup
- [x] Chatbot widget with open/close state.
- [x] Natural keyphrase-matching algorithm for local FAQs (pricing, location, legal status, loans).
- [x] Bot thinking simulations and typing indicator.

### Phase 5: Lead Ingestion API & Decree 13 Compliance Boundary
- [x] Next.js route handler (`POST /api/leads`) with input validator.
- [x] Uniqueness hashing (`leadHash`) using SHA-256 to prevent database duplicates.
- [x] Multi-dimensional lead scoring system (points for phone, email, location, budget, intent).
- [x] Automatic lead level categorization (`COLD`/`WARM`/`HOT`) and persona classification.
- [x] Decree 13 compliant PII masking logic (redacts Name, Phone, and Email inside PostgreSQL if consent is false).
- [x] Database query check verification scripts (`scripts/check-leads.ts`).

---

## Nhịp Điệu Xanh (Module 2) — Deep Next.js & Full Codebase Optimizations

**Status:** ✅ Fully Completed & Verified | **Completion Date:** 2026-05-30

This module implements deep Next.js performance tuning, client-side bundle size optimization, and static resource cache optimizations for the Nhịp Điệu Xanh application.

### Phase 1: API & CPU Optimization
- [x] Cache static normalized FAQ keywords at startup to prevent diacritics removal overhead.
- [x] Cache static normalized Mekong Delta province strings in leads ingestion route handler.
- [x] Centralize diacritics removal and string normalization logic in `lib/utils.ts`.

### Phase 2: Code Splitting & UI Optimization
- [x] Extract `PipelineBoard` interactive drag-and-drop Kanban interface into a separate chunk.
- [x] Lazy-load heavy drag-and-drop dependencies dynamically (`@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`) using `next/dynamic` (`ssr: false`) to minimize LCP bundle weight.
- [x] Eliminate flash-of-unpainted-content and hydration errors using client-side dynamic mounts, optimizing TTFB.
- [x] Memoize `KanbanCard` component using `React.memo` to prevent redundant column-to-column drag re-renders.

### Phase 3: Next.js Configuration Hardening & Linting Bypass
- [x] Enable strict mode and disable `X-Powered-By` header in `next.config.ts`.
- [x] Configure ESLint `eslint.config.mjs` to bypass raw require and unused expression checks on auto-generated Prisma files.
- [x] Clean linter compilation output with zero typescript/linter warnings.

### Phase 4: Quality & Tests Verification
- [x] Configure Vitest integration test suite covering leads ingestion, dynamic scoring, Decree 13 masking compliance, status updates, FAQ queries, and social posts.
- [x] Verify all Vitest integration tests pass (8/8) and the production build builds cleanly.

---

## Long-term Vision (v5.0+)

### Community & Ecosystem

- **Marketplace** — Monetize community-built agents/providers
- **Standards** — RFC process for new features
- **Governance** — Community steering committee
- **Certifications** — Partner program for verified plugins

### Research Track

- **Advanced Scheduling** — ML-based task prioritization
- **Self-Healing** — Automatic error recovery with ML feedback loops
- **Distributed Execution** — Multi-node agent orchestration
- **Cost Optimization** — Automatic provider selection based on cost/latency

---

## How to Contribute

We welcome contributions for:

1. **Plugins** — Build agents or providers, publish to PyPI
2. **Bug Fixes** — File issues, submit PRs
3. **Documentation** — Improve guides, add examples
4. **Testing** — Add test coverage, find edge cases
5. **Roadmap Feedback** — Comment on GitHub discussions

### Quick Start

```bash
# Clone repo
git clone https://github.com/yourusername/mekong-cli.git
cd mekong-cli

# Install dev dependencies
pip install poetry && poetry install

# Run tests
python3 -m pytest tests/ -v

# Build custom agent
cp -r examples/agent-template/ ~/.mekong/plugins/my_agent/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full workflow.

---

## Breaking Changes & Deprecations

| Version | Change | Migration |
|---------|--------|-----------|
| v3.1 | Recipe format updated (backward compatible) | Auto-conversion script provided |
| v4.0 | RBAC required for API access | Default "admin" role if unset |

---

## Feedback & Feature Requests

- **GitHub Issues**: Bug reports & feature requests
- **Discussions**: Ideas, questions, feedback
- **Discord**: Real-time community chat (coming Q2 2026)
- **RFC Process**: Major features require RFC approval

**Let's build the future of AI orchestration together!**
