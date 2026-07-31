
---
title: "Mekong Commercial Restructure — Open Core + Layer Split + Commands + Packaging"
description: "Split Mekong into PUBLIC/PROPRIETARY layers, restore slash commands, build standalone installer, and add license enforcement for commercial viability."
status: completed
priority: P1
effort: 6w
tags: [architecture, commercial, open-core, licensing, packaging]
blockedBy: []
blocks: []
created: 2026-07-30
createdBy: ak-plan
---

# Mekong Commercial Restructure — Open Core + Layer Split + Commands + Packaging

## Overview

Restructure Mekong CLI from an internal harness into a commercially shipable product using the Open Core model: PUBLIC MIT layer (skills, commands, adapters) + PROPRIETARY engine layer (license enforcement, billing, daemon). Four deliverables in sequence: (1) layer split, (2) command restoration, (3) packaging, (4) build phases with TDD.

## Goals

| # | Goal | Priority |
|---|------|----------|
| 1 | Split PUBLIC/PROPRIETARY layer boundaries | P1 |
| 2 | Restore .claude/commands/ to functional set | P1 |
| 3 | Build standalone installer (brew + DMG) | P1 |
| 4 | Add license enforcement runtime | P1 |
| 5 | Enterprise tier features (SSO, audit, support) | P2 |
| 6 | VN Hub marketing site + pricing | P2 |

## Phases

| Phase | Name | Status | Priority |
|-------|------|--------|----------|
| 1 | [Layer Split — PUBLIC vs PROPRIETARY](./phase-01-layer-split.md) | Completed | P1 |
| 2 | [Command Restoration — .claude/commands/](./phase-02-command-restoration.md) | Completed | P1 |
| 3 | [Packaging — Standalone Installer](./phase-03-packaging.md) | Completed | P1 |
| 4 | [License Enforcement Runtime](./phase-04-license-enforcement.md) | Completed | P1 |
| 5 | [Enterprise Tier Build](./phase-05-enterprise-tier.md) | Completed | P2 |
| 6 | [Marketing Site + Pricing](./phase-06-marketing.md) | Completed | P2 |

## Dependencies

- Phase 1 must complete before Phase 4 (license enforcement needs layer split)
- Phase 2 is independent (can run parallel)
- Phase 3 depends on Phase 1 (installer needs layer boundaries)
- Phase 5 depends on Phase 4
- Phase 6 depends on Phase 5

## Success Criteria

- [x] PUBLIC layer (MIT) and PROPRIETARY layer cleanly separated in repo
- [x] `.claude/commands/` has 300+ functional slash commands
- [x] Standalone installer available via `brew install mekong` and DMG download
- [x] License enforcement gates features by tier (BASIC/PRO/ENTERPRISE)
- [x] Enterprise tier has SSO, audit logs, priority support
- [x] Marketing site live with pricing page

## Non-Goals

- Do not rewrite PEV engine (keep Python backend functional)
- Do not touch `apps/` or `mekong/daemon/` (private layer stays untouched)
- Do not change `.claude/skills/` or `.claude/agents/` (already working)
- Do not migrate off Cloudflare deploy (CF-only policy stays)

## Constraints

- Must maintain backward compatibility for existing `mekong` CLI users
- Python 3.14+ required (already pinned)
- TypeScript strict mode for harness
- All tests must pass before phase completion
- No secrets committed (enforce via pre-commit hooks)
