# MekongPulse — Business Signals & Monitoring SaaS

> **STATUS: SCAFFOLD ONLY — NOT STARTED. Not in-flight. Not built. Post-D-Day target.**
> Last updated: 2026-04-17

---

## Binh Pháp Mapping

| Field | Value |
|-------|-------|
| Chapter | 9 行軍 (Marching / Situational Awareness) |
| Principle | Read terrain and enemy movements at all times — know your battlefield |
| Giant | Grafana (73K stars) — observability, dashboards, alerting |
| Application | MekongPulse gives founders real-time situational awareness: revenue, churn, ops health, competitor signals — all in one dashboard |

**Sun Tzu quote:** "Move only when it is advantageous to do so... know the enemy, know yourself."
Applied: You cannot make good decisions without data. MekongPulse is the nervous system — signals from every layer of the business surface in one place.

---

## Mission

MekongPulse is an **AI-powered business signals platform** that aggregates metrics from every tool
a founder uses — Stripe, Supabase, Cloudflare, PostHog, GitHub — into a unified Grafana-powered
dashboard with AI-generated weekly briefings and anomaly alerts.

---

## Target Market

- Solo founders with 3+ data sources and no unified view
- Early-stage SaaS teams needing ops health monitoring without a DevOps hire
- Micro-agencies tracking client campaign performance in real time

**ICP:** Solo SaaS founder checking 6 dashboards every morning — wants one briefing instead.

---

## Tech Sketch

- Grafana OSS core: self-hosted or managed
- Data connectors: Stripe webhooks, Supabase Realtime, Cloudflare Analytics API, PostHog API
- AI layer: weekly briefing generation via `/status` + `/audit` commands
- Alerting: anomaly detection → Slack/email → suggested action (LLM-generated)
- Deploy: Cloudflare Workers (data aggregation) + Grafana Cloud (dashboards)

---

## Revenue Model

- $149/mo Starter (5 data sources, weekly AI briefing, email alerts)
- $399/mo Growth (unlimited sources, daily briefings, Slack integration)
- $599/mo Pro (custom dashboards, API access, white-label)

---

## Prerequisites

- Mekong IDE v6.0 core (shipped)
- Signals SQLite layer (shipped in Layer 2 PR #67)
- Grafana integration / data connector layer (not built)

---

## Owner Placeholder

_Unassigned. Requires: 1 data engineer, Grafana OSS expertise._
