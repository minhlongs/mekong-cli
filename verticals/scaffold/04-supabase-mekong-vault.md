# MekongVault — Compliance & Data Governance SaaS

> **STATUS: SCAFFOLD ONLY — NOT STARTED. Not in-flight. Not built. Post-D-Day target.**
> Last updated: 2026-04-17

---

## Binh Pháp Mapping

| Field | Value |
|-------|-------|
| Chapter | 4 軍形 (Military Disposition) |
| Principle | Establish an invincible position before seeking victory — secure data before scaling |
| Giant | Supabase (100K stars) — open-source Postgres + auth + RLS |
| Application | MekongVault builds compliance posture (SOC2-ready, GDPR, RLS policies) so startups can sell to enterprise |

**Sun Tzu quote:** "First make yourself invincible, then wait for an opportunity to defeat the enemy."
Applied: MekongVault makes your data stack enterprise-grade before you need it — compliance as a moat.

---

## Mission

MekongVault is an **AI-powered compliance and data governance platform** built on Supabase.
It auto-generates RLS policies, audit trails, GDPR workflows, and SOC2 evidence packs —
so a solo founder can pass enterprise security reviews without a dedicated security team.

---

## Target Market

- B2B SaaS startups needing SOC2 Type I/II to close enterprise deals
- Healthcare-adjacent SaaS requiring HIPAA-grade data handling (data layer only, not medical advice)
- EU-market startups navigating GDPR compliance

**ICP:** Series A B2B SaaS, just lost a $200K deal because they failed security review.

---

## Tech Sketch

- Supabase integration: auto-generate RLS policies from schema analysis
- Commands activated: `/audit`, `/security`, `/health`
- Output: compliance evidence pack (PDF), RLS migration scripts, audit log dashboards
- Agent layer: monitors Supabase project → alerts on policy drift
- Backend: Supabase (naturally) + Cloudflare Workers for webhooks

---

## Revenue Model

- $299/mo Starter (1 Supabase project, SOC2 evidence pack)
- $999/mo Growth (5 projects, GDPR workflows, HIPAA checklist)
- $2,999 one-time SOC2 audit prep package

---

## Prerequisites

- Mekong IDE v6.0 core (shipped)
- Supabase MCP integration
- `/security` command production-grade

---

## Owner Placeholder

_Unassigned. Requires: 1 security-focused engineer, Supabase partnership discussion._

---

## Notes for Polar.sh Listing

**WARNING:** Do NOT use "HIPAA", "medical", "health data" in Polar product description.
Use: "B2B data governance SaaS", "compliance automation platform."
