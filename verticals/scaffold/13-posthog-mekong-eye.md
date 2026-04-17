# MekongEye — Competitive Intelligence Platform

> **STATUS: PARTIAL — PostHog integration started but not production-ready. Post-D-Day target.**
> Last updated: 2026-04-17

---

## Binh Pháp Mapping

| Field | Value |
|-------|-------|
| Chapter | 13 用間 (Use of Intelligence / Spies) |
| Principle | Intelligence is the foundation of all victory — know what others do not |
| Giant | PostHog (32K stars) — open-source product analytics, session replay, feature flags |
| Application | MekongEye turns PostHog's product analytics into competitive intelligence: understand user behavior patterns across markets, not just your own product |

**Sun Tzu quote:** "Hence it is that with none in the whole army are more intimate relations to be maintained than with spies."
Applied: In modern SaaS, intelligence = product analytics + competitive signals. MekongEye makes PostHog the foundation of a continuous market observation system.

---

## Mission

MekongEye is an **AI competitive intelligence platform** built on PostHog that goes beyond
internal product analytics. It monitors your own funnel deeply, benchmarks against market
signals, and surfaces actionable competitive insights — so a solo founder always knows
what customers want before competitors do.

---

## Target Market

- Product-led SaaS teams needing deep funnel analytics without a data science hire
- Founders who want competitive benchmarking beyond Similarweb surface data
- B2B SaaS operators tracking feature adoption vs. competitor feature releases

**ICP:** Solo PM at 500-user SaaS who can see their metrics but not understand WHY users churn.

---

## Current State (Partial)

- PostHog OSS self-hosted: tested locally, not deployed to production
- Basic event tracking schema: defined but not instrumented in Mekong IDE
- Feature flags: evaluated but not integrated with MCU billing gates
- Session replay: configured in PostHog dashboard, not wired to user sessions

**Next step:** Instrument Mekong IDE API with PostHog events → validate 30-day retention funnel.

---

## Tech Sketch

- PostHog OSS: self-hosted on Cloudflare Workers or customer VPS
- Commands activated: `/audit`, `/health`, `/status` — enriched with PostHog event data
- AI layer: `/analytics` command (new) — summarizes PostHog cohort data in plain English
- Competitive layer: scrape competitor changelogs, job postings → correlate with user behavior shifts
- Feature flags: gate Mekong IDE features per MCU tier via PostHog flags

---

## Revenue Model

- $499/mo Starter (PostHog managed instance + AI analytics briefings)
- $999/mo Growth (competitive intelligence layer, weekly briefings)
- $1,999/mo Enterprise (custom event taxonomy, dedicated analysis, API access)

---

## Prerequisites

- Mekong IDE v6.0 core (shipped)
- PostHog self-hosted deployment (not production-ready)
- `/analytics` command (not yet defined)
- Event instrumentation in Mekong IDE API (not done)

---

## Owner Placeholder

_Unassigned. Requires: 1 analytics engineer, PostHog self-hosting expertise._

---

## Notes for Polar.sh Listing

**WARNING:** Do NOT use "spy", "surveillance", "tracking users" in Polar product description.
Use: "product analytics SaaS", "business intelligence platform", "user behavior analytics."
