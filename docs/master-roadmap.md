# Mekong CLI — Master Execution Roadmap

**Version:** 1.0 | **Created:** 2026-07-04
**Context:** Post Military Camp Overhaul + Revenue Execution

---

## Completed ✅

| Track | Files | Status |
|-------|-------|--------|
| /project-idea 25-file blueprint | `plans/company-blueprint/` | ✅ |
| Military Camp Overhaul | Quân luật, pre-commit, patrol, audit | ✅ |
| Revenue Execution | Stripe, trial, CRM, signup | ✅ |

---

## Track D: Binh Phap Automation Chain (1-2 tuần)

**Mục tiêu:** Auto-execute 13 chapter Binh Phap commands chain sau /project-idea, không cần WIN-WIN-WIN manual.

**Phase D1:** Chain Definition
- Map 13 chapters → commands → execution DAG
- Tự động detect layer transition

**Phase D2:** Auto-executor
- Script chạy chain tự động, spawn subagent per chapter
- Status tracking (chapter nào done, chapter nào fail)

**Phase D3:** Recovery
- Chapter 8 (Nine Variations) — tự động retry khi fail
- Fallback strategies cho từng chapter

---

## Track E: Plugin Ecosystem (4-8 tuần)

**Mục tiêu:** Mở mekong-cli cho 3rd party build skill + command plugin.

**Phase E1:** Plugin API
- `mekong plugin init` — scaffold plugin
- Registry schema (.plugin.json)
- Hooks system (pre/post command)

**Phase E2:** Registry
- Local plugin registry (`.claude/plugins/`)
- `mekong plugin install <url>`
- Dependency resolution

**Phase E3:** Marketplace
- `clipmart/` — public plugin directory
- Versioning + update channel
- Plugin sandbox (security)

---

## Track F: ZenOS Governance (3-6 tuần)

**Mục tiêu:** Governance layer cho mekong-cli ecosystem.

**Phase F1:** Commons Foundation
- Draft ZenOS Commons charter
- Member registration
- Proposal system

**Phase F2:** Voting & Treasury
- Contribution-weighted voting
- Multi-sig treasury
- Grant distribution

**Phase F3:** Anti-Capture
- Term limits
- Right to fork
- Constitutional review cycle

---

## Recommended Build Order

```
D (Binh Phap) → E (Plugin) → F (Governance)
  2 weeks         6 weeks       4 weeks
```

**Total:** ~12 weeks (Q3-Q4 2026)
