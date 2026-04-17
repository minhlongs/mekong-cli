# MekongForce — AI Agency Delivery Platform

> **STATUS: SCAFFOLD ONLY — NOT STARTED. Not in-flight. Not built. Post-D-Day target.**
> Last updated: 2026-04-17

---

## Binh Pháp Mapping

| Field | Value |
|-------|-------|
| Chapter | 11 九地 (Nine Grounds / Terrain Types) |
| Principle | Adapt tactics to terrain — deploy the right agent team for each mission |
| Giant | CrewAI (48K stars) — multi-agent role-based orchestration |
| Application | MekongForce deploys specialized CrewAI crews (researcher, writer, reviewer, deployer) for client delivery missions — AI agency without human headcount |

**Sun Tzu quote:** "Throw your soldiers into positions from which there is no escape, and they will prefer death to flight."
Applied: Committed agent crews with clear roles and no fallback option — they complete the mission or escalate. No half-done deliverables.

---

## Mission

MekongForce is an **AI agency delivery engine** that uses CrewAI multi-agent crews to execute
client projects end-to-end: research, write, build, review, deliver. A solo founder runs a
full-service agency with zero human contractors — agents are the team.

---

## Target Market

- Solo consultants and freelancers wanting to scale delivery without hiring
- Digital agencies needing to 10x output without 10x headcount
- Founders building productized services (fixed-scope, fixed-price deliverables)

**ICP:** Solo consultant billing $10K/mo manually, ceiling is time — wants to deliver $100K/mo via agent crews.

---

## Tech Sketch

- CrewAI crew definitions per service type (content crew, dev crew, research crew, GTM crew)
- Commands activated: `/cook`, `/code`, `/review`, `/deploy` — wrapped as crew missions
- Mission intake: web form → JSON mission spec → CrewAI dispatch → deliverable output
- Human-in-the-loop: approval gate before final delivery (configurable)
- Billing: per-mission credits (MCU system already in place)

---

## Revenue Model

- $499/mo Base (10 missions/mo, standard crews)
- $1,499/mo Growth (unlimited missions, custom crew configs)
- $2,999/mo Enterprise (dedicated crews, SLA, white-label client portal)

---

## Prerequisites

- Mekong IDE v6.0 core (shipped)
- OpenClaw daemon v6.1 stable (partially shipped)
- CrewAI integration layer (not built)
- Mission intake UI (not built)

---

## Owner Placeholder

_Unassigned. Requires: 1 AI systems engineer, CrewAI expertise, UX for mission intake._
