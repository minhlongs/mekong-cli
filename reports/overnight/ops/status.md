# Mekong CLI v5.0 — Full System Status
**Generated:** 2026-03-12 overnight | **Version:** 5.0.0

---

## Platform Overview

| Attribute | Value |
|-----------|-------|
| Version | 5.0.0 |
| Codename | OpenClaw |
| Language | Python 3.9.6 |
| CLI framework | Typer + Rich |
| Deploy target | Cloudflare-only (Pages + Workers + D1 + KV + R2) |
| Monthly infra cost | $0 |
| License | MIT |
| Primary language | Vietnamese (ĐIỀU 55) |

---

## 5-Layer Command Status

### Layer 1: Founder (👑)
| Command | Status | MCU |
|---------|--------|-----|
| annual | ACTIVE | 5 |
| okr | ACTIVE | 3 |
| swot | ACTIVE | 3 |
| fundraise | ACTIVE | 5 |
| pitch | ACTIVE | 5 |
| ipo/* | ACTIVE | 5 |
| vc/cap-table | ACTIVE | 5 |

### Layer 2: Business (🏢)
| Command | Status | MCU |
|---------|--------|-----|
| sales | ACTIVE | 3 |
| marketing | ACTIVE | 3 |
| finance | ACTIVE | 3 |
| hr | ACTIVE | 2 |
| pricing | ACTIVE | 2 |
| brand | ACTIVE | 2 |

### Layer 3: Product (📦)
| Command | Status | MCU |
|---------|--------|-----|
| plan | ACTIVE | 3 |
| sprint | ACTIVE | 2 |
| roadmap | ACTIVE | 3 |
| brainstorm | ACTIVE | 1 |
| scope | ACTIVE | 2 |

### Layer 4: Engineering (⚙️)
| Command | Status | MCU |
|---------|--------|-----|
| cook | ACTIVE | 5 |
| fix | ACTIVE | 3 |
| code | ACTIVE | 3 |
| test | ACTIVE | 2 |
| deploy | ACTIVE | 3 |
| review | ACTIVE | 2 |

### Layer 5: Ops (🔧)
| Command | Status | MCU |
|---------|--------|-----|
| audit | ACTIVE | 2 |
| health | ACTIVE | 0 |
| security | ACTIVE | 2 |
| status | ACTIVE | 0 |
| clean | ACTIVE | 1 |

---

## Command Registry

- Total commands registered: 273 (.claude/commands/)
- Legacy commands: available via register_legacy_commands()
- Core commands: init, list, search, run, cook, plan, ui, version
- Sub-apps: swarm, schedule, memory
- AGI commands: autonomous loop, world model, self-improve

---

## Skills Catalog

- Total skills: 542 (.claude/skills/)
- Auto-activated per command context
- Categories: engineer, marketing, finance, legal, product, ops, founder

---

## Agent Registry

| Agent | Type | Status |
|-------|------|--------|
| LeadHunter | Python | ACTIVE |
| ContentWriter | Python | ACTIVE |
| RecipeCrawler | Python | ACTIVE |
| GitAgent | Python | ACTIVE |
| FileAgent | Python | ACTIVE |
| ShellAgent | Python | ACTIVE |
| MonitorAgent | Python | ACTIVE |
| NetworkAgent | Python | ACTIVE |
| DatabaseAgent | Python | ACTIVE |
| WorkspaceAgent | Python | ACTIVE |
| PluginAgent | Python | ACTIVE |
| CTO | Markdown | ACTIVE |
| CMO | Markdown | ACTIVE |
| CFO | Markdown | ACTIVE |

---

## MCU Billing Tiers

| Tier | Credits/mo | Price | Status |
|------|-----------|-------|--------|
| Starter | 50 | $49 | ACTIVE |
| Growth | 200 | $149 | ACTIVE |
| Premium | 1000 | $499 | ACTIVE |

MCU costs: simple=1, standard=3, complex=5
Payment: Polar.sh webhooks (only source)
Zero balance → HTTP 402 enforced via mcu_gate.py

---

## Infrastructure Status

| Service | Platform | Status |
|---------|----------|--------|
| Frontend | CF Pages | GREEN |
| Edge API | CF Workers | GREEN |
| Database | CF D1 (SQLite) | GREEN |
| Cache | CF KV | GREEN |
| Storage | CF R2 | GREEN |
| raas-gateway | CF Worker | GREEN |

**ALL SYSTEMS OPERATIONAL**
