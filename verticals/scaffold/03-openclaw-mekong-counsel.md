# MekongCounsel — AI Consulting Engine

> **STATUS: SCAFFOLD ONLY — NOT STARTED. Not in-flight. Not built. Post-D-Day target.**
> Last updated: 2026-04-17

---

## Binh Pháp Mapping

| Field | Value |
|-------|-------|
| Chapter | 3 謀攻 (Attack by Stratagem) |
| Principle | Win without direct confrontation — consult before competing |
| Giant | OpenClaw (347K stars) — universal agent orchestration |
| Application | MekongCounsel deploys AI agents to deliver consulting outputs without hiring consultants |

**Sun Tzu quote:** "Supreme excellence consists in breaking the enemy's resistance without fighting."
Applied: MekongCounsel delivers consulting-grade deliverables (market analysis, tech audits, strategy docs) via agents — no engagement needed.

---

## Mission

MekongCounsel is an **AI consulting delivery engine** for technical founders who need expert output
without retaining expensive consultants. Scope: due diligence reports, vendor evaluations,
architecture reviews, and go-to-market playbooks — all generated autonomously.

---

## Target Market

- Seed/Series A startups needing technical due diligence
- Solo founders preparing investor data rooms
- SMBs that need occasional consulting but can't afford retainers

**ICP:** Pre-Series A CTO who needs a vendor evaluation report in 24h, not 4 weeks.

---

## Tech Sketch

- OpenClaw agent orchestration: multi-step research → synthesis → deliverable generation
- Commands activated: `/audit`, `/review`, `/design`, `/brainstorm`, `/scout`
- Output formats: PDF, Notion export, Google Docs (via markdown pipeline)
- Delivery SLA: 24h turnaround per deliverable (async, not real-time chat)
- No new infrastructure — runs on existing Mekong IDE + OpenClaw daemon

---

## Revenue Model

- $500 per deliverable (project-based)
- $2,000/mo retainer (unlimited deliverables, 48h SLA)
- White-label API: $499/mo for agencies reselling under their brand

---

## Prerequisites

- OpenClaw daemon v6.1+ (autonomous dispatch — partially shipped)
- `/scout` + `/audit` commands production-grade
- Deliverable PDF pipeline

---

## Owner Placeholder

_Unassigned. Requires: 1 product owner, OpenClaw daemon stable._
