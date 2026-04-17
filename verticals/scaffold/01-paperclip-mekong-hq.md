# MekongHQ — Strategy Command Center

> **STATUS: SCAFFOLD ONLY — NOT STARTED. Not in-flight. Not built. Post-D-Day target.**
> Last updated: 2026-04-17

---

## Binh Pháp Mapping

| Field | Value |
|-------|-------|
| Chapter | 1 始計 (Initial Calculations) |
| Principle | Know your strengths before engaging — audit before acting |
| Giant | Paperclip (31K stars) — task automation, agent orchestration |
| Application | Before any business move, MekongHQ computes options, surfaces risks, recommends strategy |

**Sun Tzu quote:** "The general who wins the battle makes many calculations before the battle is fought."
Applied: MekongHQ is the calculation layer — OKRs, SWOT, scenario planning, board-level outputs.

---

## Mission

MekongHQ is the AI-powered **strategy command center** for solo founders and small executive teams.
Replace a Chief of Staff, strategic advisor, and board consultant with one subscription.
Output: weekly strategy briefs, OKR tracking, scenario modeling — all autonomous.

---

## Target Market

- Solo founders scaling from $0 to $1M ARR
- Micro-consulting firms (1-5 people) needing executive output
- VC-backed seed-stage teams with no ops hire yet

**ICP:** Solo technical founder, $0 MRR today, needs board-level documentation for fundraising.

---

## Tech Sketch

- Built ON TOP of Mekong IDE kernel (323 commands already exist)
- Domain wrapper activates: `/annual`, `/okr`, `/swot`, `/fundraise`, `/pitch` commands
- Paperclip integration: task automation pipelines for recurring strategy reviews
- Output: PDF-ready strategy decks via markdown → PDF pipeline
- No new backend needed — uses existing PEV engine + LLM router

---

## Revenue Model

- $199/mo per seat (Strategy tier)
- $499/mo white-label for consulting firms
- No free tier — positioning as premium executive tool

---

## Prerequisites

- Mekong IDE v6.0 core (shipped)
- `/annual`, `/okr` commands tested end-to-end
- PDF export pipeline (not yet built)

---

## Owner Placeholder

_Unassigned. Requires: 1 product owner + 1 design review._

---

## Notes for Polar.sh Listing

**WARNING:** Do NOT describe as "health", "wellness", or "clinical" — Polar will reject.
Use: "B2B SaaS strategy management platform" or "executive operations software."
