# MekongBridge — Workflow Integration SaaS

> **STATUS: SCAFFOLD ONLY — NOT STARTED. Not in-flight. Not built. Post-D-Day target.**
> Last updated: 2026-04-17

---

## Binh Pháp Mapping

| Field | Value |
|-------|-------|
| Chapter | 7 軍爭 (Maneuvering / Contending for Advantage) |
| Principle | Seize critical positions before the enemy — own the integration layer |
| Giant | n8n (182K stars) — open-source workflow automation |
| Application | MekongBridge claims the integration chokepoint: all SaaS tools route through it, creating lock-in via workflow ownership |

**Sun Tzu quote:** "Whoever is first in the field and awaits the coming of the enemy will be fresh for the fight."
Applied: Own the automation layer before competitors do. Integrations = moat. First to connect = first to retain.

---

## Mission

MekongBridge is an **AI-powered workflow integration platform** that connects any SaaS tool stack
via n8n workflows, enhanced with LLM-driven automation logic. It replaces Zapier/Make for
technical founders who want self-hosted, customizable, and autonomous workflow orchestration.

---

## Target Market

- Operations-heavy SMBs with 5-20 SaaS tools that don't talk to each other
- No-code/low-code builders wanting AI-enhanced workflow logic
- B2B SaaS companies needing customer onboarding automation

**ICP:** Ops manager at 20-person company, manually copy-pasting between 8 tools daily.

---

## Tech Sketch

- n8n self-hosted core: deploy on Cloudflare Workers or customer's own infra
- Commands activated: `/integrate`, `/automate`, `/webhook`, `/pipeline`
- Agent layer: auto-generates n8n workflow JSON from natural language description
- 400+ pre-built connectors (via n8n) + Mekong-specific AI nodes
- Revenue gate: hosted n8n instance management + AI workflow generation credits

---

## Revenue Model

- $99/mo Starter (hosted n8n, 1,000 executions/mo, 5 AI workflow generations)
- $299/mo Growth (unlimited executions, 50 AI generations, priority support)
- $499/mo Enterprise (SLA, custom nodes, white-label)

---

## Prerequisites

- Mekong IDE v6.0 core (shipped)
- n8n MCP integration or API wrapper
- `/integrate` command (not yet built)

---

## Owner Placeholder

_Unassigned. Requires: 1 integrations engineer, n8n self-hosting expertise._
