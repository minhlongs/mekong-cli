---
title: "Harvest OpenClaw Skills"
description: "Systematic harvesting of top skills from OpenClaw ecosystem to Mekong CLI"
status: in-progress
priority: P1
effort: 2h
branch: master
tags: [skills, openclaw, harvest]
created: 2026-02-18
---

# Harvest OpenClaw Skills Plan

## Context
We are upgrading Mekong CLI capabilities by harvesting top skills from the OpenClaw ecosystem.
Sources:
1. Official: github.com/openclaw/skills
2. Awesome: github.com/VoltAgent/awesome-openclaw-skills
3. UI: open-claw-skills-library.vercel.app

## Strategy (Binh Phap: 法)
- **Source**: ClawHub 5,705 raw → Awesome 3,002 curated → Official 164 hand-picked.
- **Quality Gate**: 始計 (Initial Calculations) - Inspect before adoption.
- **Destination**: `.claude/skills/`

## Phase 1: Setup & Discovery
- [x] Verify ClawHub CLI
- [x] Search and Identify Target Skills
  - [x] P0: `cc-godmode` (Found & Installed)
  - [x] P1: `smart-model-switching` (Found & Installed)
  - [x] P1: `memory` (Found & Installed)
  - [x] P1: `deep-research-pro` (Found & Installed)
  - [x] P1: `agent-browser` (Found & Installed)
  - [ ] P1: `ec-task-orchestrator` (Not found, searching alternatives)

## Phase 2: Installation (The Harvest)
- [x] Install P0: `cc-godmode`
- [x] Install P1 Batch (smart-model-switching, memory, deep-research-pro, agent-browser)
- [ ] Install Specialized Skills (Marketing, Finance, etc.) - Deferred to next batch

## Phase 3: Integration & Testing
- [ ] Map to CỬU ĐỊA matrix
- [ ] Test top 5 skills with real tasks
- [ ] Document in knowledge/openclaw-skills-harvest-report.md

## Phase 4: Reporting
- [ ] Create `knowledge/openclaw-skills-harvest-report.md`

## Current Status
- Installed 5/6 top skills.
- `ec-task-orchestrator` not found. Will document as missing.
- Proceeding to Matrix Mapping and Reporting.
