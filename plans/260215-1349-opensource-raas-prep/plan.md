---
title: "Mekong-CLI Open-Source & RaaS Readiness Plan"
description: "Prepare mekong-cli monorepo for world-class open-source publication and establish RaaS foundation."
status: pending
priority: P1
effort: 8h
branch: master
tags: [opensource, raas, audit, documentation]
created: 2026-02-15
---

# Mekong-CLI Open-Source & RaaS Readiness Plan

## Context
Prepare the mekong-cli monorepo for open-source publication. This involves making the documentation world-class, ensuring security (no internal secrets), and laying the foundation for the Revenue-as-a-Service (RaaS) model.

## Phase 1: Documentation & DX (Developer Experience)
**Goal**: Make the project attractive and easy to use for external developers.

1. **README.md Overhaul**:
   - Create a high-impact, English-first README.md.
   - Include clear value proposition: "Autonomous AI Agent Swarm for RaaS".
   - Add architecture diagrams (Mermaid).
   - Detailed Quick Start (< 5 min to first mission).
   - Move detailed Vietnamese content to `README.vi.md`.

2. **Contributing & Community**:
   - Translate `CONTRIBUTING.md` to English.
   - Standardize `CODE_OF_CONDUCT.md` to English.
   - Add `SECURITY.md` with vulnerability reporting instructions.
   - Create `tasks/examples/` with diverse mission samples (bugfix, feature, refactor).

## Phase 2: Security & Privacy Audit
**Goal**: Ensure no sensitive data or internal-only logic is exposed.

1. **Secret Scanning**:
   - Verify `.env.example` contains only placeholders.
   - Use `grep` to scan for any hardcoded keys (sk-, AIza, etc.).
   - Check all `scripts/` for hardcoded internal URLs or credentials.

2. **Internal File Redaction/Relocation**:
   - Audit `apps/openclaw-worker/` for files like `BINH_PHAP_MASTER.md`, `QUAN_LUAT.md`, `DOANH_TRAI.md`.
   - Redact sensitive business logic or move to `plans/internal/` (which is gitignored).
   - Ensure brain logs and proxy logs are not tracked (check `.gitignore`).

## Phase 3: Package Metadata & Open-Source Foundation
**Goal**: Technical readiness for npm/git publication.

1. **package.json Standardization**:
   - Update root `package.json` with correct description, keywords, and repository info.
   - Decide on `private: true` status (Keep for monorepo root, but ensure subpackages are publishable).
   - Ensure `LICENSE` (MIT) is present and correctly referenced.

2. **Build & Install Verification**:
   - Verify `pnpm install` and `pip install -r requirements.txt` work on a fresh clone.
   - Ensure `mekong cook` command is functional after installation.

## Phase 4: RaaS Foundation & Monetization
**Goal**: Define the commercial boundary.

1. **Antigravity Proxy Documentation**:
   - Create `docs/raas-foundation.md` explaining the Proxy layer.
   - Define the "Revenue-as-a-Service" model: How developers can use Mekong to build revenue-generating agents.
   - Document the commercial tiers (Community vs. Enterprise).

## Tasks & Assignments

### Mission 1: README & Contributing Standard (5 files)
- Modify `/README.md` (Overhaul)
- Modify `/CONTRIBUTING.md` (English translation)
- Modify `/CODE_OF_CONDUCT.md` (English translation)
- Create `/docs/raas-foundation.md`
- Create `/README.vi.md` (Sync current content)

### Mission 2: Security Sweep & Internal Redaction (5 files)
- Audit `apps/openclaw-worker/BINH_PHAP_MASTER.md`
- Audit `apps/openclaw-worker/QUAN_LUAT.md`
- Update `.gitignore` if needed
- Check `.env.example`
- Redact/Move internal docs

### Mission 3: Examples & DX (5 files)
- Create `tasks/examples/mission_example_bugfix.txt`
- Create `tasks/examples/mission_example_feature.txt`
- Create `tasks/examples/mission_example_refactor.txt`
- Update `package.json` metadata
- Verify installation flow

## Success Criteria
- [ ] README.md is English-first, professional, and includes diagrams.
- [ ] Zero hardcoded secrets found in codebase.
- [ ] fresh `pnpm install` works without errors.
- [ ] RaaS monetization hooks are documented.
- [ ] Contributing guide is clear for external developers.
