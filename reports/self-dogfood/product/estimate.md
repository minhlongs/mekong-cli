# Effort Estimation — Mekong CLI v5.1 Key Features

**Date:** March 2026 | **Method:** T-shirt sizing with breakdown
**Team assumption:** 1 full-stack engineer (solo or small team scaling factor applied)
**Sizing:** S = 1–2 days | M = 3–5 days | L = 1–2 weeks | XL = 3–6 weeks

---

## Summary Table

| Feature | T-shirt | Engineer-days | Risk | Priority |
|---------|---------|---------------|------|----------|
| Stripe Integration (Enterprise invoicing) | M | 4d | Low | P1 |
| Plugin Marketplace v0 | L | 9d | Medium | P1 |
| Recipe Editor UI | M | 4d | Low-Medium | P2 |
| White-Label API | XL | 22d | High | P3 |
| **Total** | — | **39d** | — | — |

Solo founder with 5d/week working capacity: ~8 weeks of focused work.
With 2 engineers (1 senior + 1 mid): ~4–5 weeks.

---

## Feature 1: Stripe Integration (Enterprise Invoicing)

**Size: M — 4 engineer-days**

### Scope
Polar.sh handles self-serve subscriptions (Starter/Pro). Stripe is needed only for Enterprise annual contracts: custom invoicing, Net-30 payment terms, purchase orders, multi-seat billing. Not a replacement for Polar — additive for Enterprise only.

### Breakdown

| Task | Days | Notes |
|------|------|-------|
| Stripe account setup + test mode | 0.25d | Minimal setup |
| FastAPI `/webhooks/stripe` endpoint | 0.5d | Extend existing webhook handler pattern from Polar |
| Stripe customer + invoice creation on Enterprise signup | 0.5d | Triggered after sales call, not self-serve |
| Stripe `invoice.paid` webhook → provision Enterprise credits | 0.5d | Same credit service as Polar integration |
| Annual contract amount → MCU balance calculation | 0.25d | Simple math, config-driven |
| Admin UI: create Stripe invoice manually | 0.75d | Basic form, not a full billing portal |
| Testing (unit + integration, Stripe test mode) | 0.75d | Stripe test webhooks are good |
| **Total** | **4d** | — |

### Risk: Low
Stripe's API is well-documented. We already have Polar webhook pattern to follow. The only risk is scope creep if "Enterprise invoicing" expands to full self-serve billing — keep it manual/sales-assisted for v5.1.

### Dependencies
- Polar.sh integration must be complete first (API key provisioning pattern established)
- Need at least 1 potential Enterprise customer to validate invoice flow before building

### What this unlocks
- Can close Enterprise deals at $499/mo or $5,000/year without manual wire transfers
- Annual contracts provide runway predictability
- Estimated first-month revenue impact if 1 Enterprise customer closes: +$499 MRR

---

## Feature 2: Plugin Marketplace v0

**Size: L — 9 engineer-days**

### Scope
A GitHub-based plugin marketplace where community contributors can publish `.claude/commands/*.md` files that extend Mekong CLI. v0 is curated + manual — no automated registry, no npm-style package manager. A discovered list in the repo and a marketplace page on the website.

### What "Plugin" means in Mekong context
A plugin is a `.md` file in `.claude/commands/` that defines a new command. Already works today — Mekong reads all `.md` files in that directory as commands. The marketplace just makes discovery and installation easier.

```bash
# After marketplace:
mekong plugin install github/some-user/mekong-shopify-plugin
mekong plugin list
mekong plugin update --all
```

### Breakdown

| Task | Days | Notes |
|------|------|-------|
| Plugin spec definition (`.mekong-plugin.json` schema) | 0.5d | Name, version, commands array, author, description |
| `mekong plugin install [github-url]` command | 1d | git clone → copy .md files to `.claude/commands/` |
| `mekong plugin list` command | 0.5d | Read installed plugins from `.mekong/plugins.json` |
| `mekong plugin update` command | 0.5d | git pull → re-copy .md files |
| `mekong plugin remove` command | 0.25d | Delete .md files, update plugins.json |
| Sandboxing: plugin commands run with MCU limit | 1d | Prevent runaway plugins from draining credits |
| Plugin validation: check for malicious shell injection in .md | 1d | Security review of plugin content before install |
| GitHub-based plugin registry (README + JSON index) | 0.5d | Seed with 10 community plugins |
| Marketplace page on agencyos.network/plugins | 1.5d | Cards, search, install button (links to CLI command) |
| Documentation: "How to publish a plugin" | 0.5d | Plugin author guide |
| Seed plugins: write 5 example plugins to seed the marketplace | 1d | Shopify, Notion, Slack, AWS, Linear integrations |
| Testing | 0.75d | Install/update/remove lifecycle tests |
| **Total** | **9d** | — |

### Risk: Medium

**Primary risk: Security.** Plugins are `.md` files that contain LLM instructions. A malicious plugin could instruct the LLM to exfiltrate files or run destructive shell commands. Mitigation: plugin content validation before install + community review process before marketplace listing.

**Secondary risk: Ecosystem chicken-and-egg.** Marketplace has no value if there are no plugins. We seed with 10 curated plugins from the core team, then launch to community. Target 25 community plugins within 90 days of launch.

### What this unlocks
- Community-driven command expansion (289 → potentially 500+ with community)
- Third-party integrations without core team building each one
- "Plugin Marketplace" is a strong marketing angle (vs. competitors who don't have this)
- Agency use case: build private company-specific plugins for internal workflows

---

## Feature 3: Recipe Editor UI

**Size: M — 4 engineer-days**

### Scope
A web-based visual editor at `agencyos.network/recipes/editor` that lets non-technical users create custom DAG workflow recipes without writing YAML. Click to add steps, connect them visually, configure inputs.

### Why this matters
85 built-in recipes cover common use cases. But agencies want custom recipes for their specific workflows ("our client onboarding flow has 12 steps"). Writing YAML is fine for engineers; it's a blocker for agency owners.

### Breakdown

| Task | Days | Notes |
|------|------|-------|
| Recipe YAML schema documentation (what the editor produces) | 0.25d | Already partially exists, needs formalization |
| React component: step cards with drag-to-reorder | 0.75d | react-beautiful-dnd or Framer Motion |
| Step configuration: command selector, input mapping, output naming | 0.75d | Dropdown of available commands + field mapping UI |
| DAG edge drawing: connect outputs of step N to inputs of step N+1 | 0.75d | Simple arrow connections, not full graph library needed for v0 |
| Recipe validation: detect cycles, missing connections | 0.25d | Client-side validation before save |
| Export to YAML: download or copy-paste | 0.25d | One-click export |
| Save to account: store custom recipes server-side | 0.5d | `POST /api/recipes` endpoint, tied to account |
| `mekong recipe run --custom [name]` CLI integration | 0.25d | Pull custom recipe from API, run in local PEV |
| Testing | 0.25d | Happy path + invalid recipe validation |
| **Total** | **4d** | — |

### Risk: Low-Medium

**Primary risk: Scope creep.** "Recipe editor" can become a full workflow automation builder (Zapier territory). Hard boundary: v0 only supports linear recipes with simple input/output mapping. No conditional branches, no loops, no external API calls. Those are v1 features.

**Secondary risk: YAML round-tripping.** If users import an existing YAML recipe into the editor and it doesn't render cleanly, that's a bad experience. Mitigation: editor only supports the subset of recipe YAML it can display. Complex hand-written recipes remain code-only.

---

## Feature 4: White-Label API

**Size: XL — 22 engineer-days**

### Scope
Agencies can deploy Mekong under their own brand: `mekong.youragency.com`, custom API keys (not `sk-mekong-*`), their own Polar.sh account for billing their clients, custom command sets (restrict which of the 289 commands their clients can access).

This is the highest-ACV feature — an agency charging $500/mo to 10 clients generates $5K MRR from a single Mekong Pro account.

### Why XL
Multi-tenancy is fundamentally different from single-tenant. Every layer of the stack needs tenant isolation: API keys, credit pools, recipe libraries, billing accounts, rate limits, and audit logs must be per-tenant, not global.

### Breakdown

| Task | Days | Notes |
|------|------|-------|
| **Architecture** | | |
| Tenant model design: `tenants` table, tenant_id on all resources | 1d | Schema + RLS policies |
| API key namespacing: `sk-[tenant-slug]-xxxx` format | 0.5d | Key generation + resolution |
| Tenant-scoped credit pools: each tenant has own balance | 1d | Separate from reseller's master account |
| **Billing** | | |
| Reseller → Tenant billing model: reseller buys wholesale, sells retail | 1.5d | Master account bills agency; agency bills clients |
| Polar.sh sub-account or separate Polar accounts per tenant | 1d | Polar.sh API research needed — may require separate accounts |
| **Custom Branding** | | |
| Custom domain support: CNAME `mekong.agency.com` → agencyos.network | 1d | Cloudflare proxy config + TLS cert provisioning |
| Tenant-specific landing page template | 1d | Configurable logo, colors, pricing page |
| Custom API key prefix per tenant | 0.25d | Config field |
| **Command Access Control** | | |
| Per-tenant command allowlist: restrict which commands clients can use | 1.5d | Middleware reads tenant config, blocks unlisted commands |
| Custom recipe library per tenant: private recipes | 1d | `recipes` table with tenant_id foreign key |
| **CLI Changes** | | |
| `mekong auth --endpoint [custom-url]` to point CLI at tenant API | 0.5d | Config file stores endpoint + key |
| Pass tenant header on every API request | 0.25d | `X-Mekong-Tenant: [tenant-id]` |
| **Admin** | | |
| Tenant management dashboard (create/manage/suspend tenants) | 2d | Admin-only, not customer-facing yet |
| Tenant usage reporting: credits used, commands run, per tenant | 1.5d | Aggregate from mcu_transactions by tenant |
| **Security** | | |
| Tenant isolation audit: confirm no cross-tenant data leakage | 1.5d | Critical — review every query for tenant_id filter |
| Rate limiting per tenant (not just per account) | 0.5d | Prevent one tenant from hammering the shared LLM router |
| **Testing** | | |
| Multi-tenant integration tests: 3 tenants, confirm isolation | 1.5d | Most important test suite for this feature |
| Load test: 5 concurrent tenants, 10 users each | 0.5d | Confirm no cross-contamination under load |
| **Documentation** | | |
| White-label setup guide for agency owners | 1d | DNS setup, branding, client onboarding |
| API reference for tenant management endpoints | 0.5d | Swagger/OpenAPI |
| **Total** | **22d** | — |

### Risk: High

**Primary risk: Polar.sh multi-account complexity.** If Polar.sh doesn't support sub-accounts with reseller relationships, the billing architecture needs a redesign. Mitigation: spike this first (2 days) before committing to the estimate.

**Secondary risk: Security — tenant isolation bugs.** A data leak where tenant A sees tenant B's missions would be fatal to the product. This needs a dedicated security review pass, not just developer testing.

**Gating criteria before starting:** Need at least 1 signed letter of intent from an agency willing to pay $499+/mo for white-label access. Building this speculatively at 22 engineer-days is a significant bet.

---

## Estimation Assumptions

1. Estimates assume one senior full-stack engineer familiar with the codebase
2. Does not include: product design time, documentation (except where listed), deployment, post-launch bug fixes
3. Assumes existing infrastructure: FastAPI, PostgreSQL, Polar.sh integration in place
4. Testing estimates are minimal — production-quality test suites would add 30–50% to each estimate
5. These are median estimates — P90 (accounting for unexpected complexity) would be ~1.5x

## Sequencing Recommendation

```
Week 1-2:  Stripe Integration (M) + RaaS Checkout (from scope.md)
Week 3-4:  Recipe Editor UI (M)
Week 5-7:  Plugin Marketplace v0 (L)
Week 8+:   White-Label API (XL) — only if LOI from agency customer in hand
```
