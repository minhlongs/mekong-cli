---
title: "Restore Critical Knowledge Items: Ethics, Self-Correction, Meta-Learning"
description: "Restoration of missing Knowledge Base domains by extracting logic from Mekong CLI core modules."
status: completed
priority: P1
effort: 1h
branch: main
tags: [knowledge-base, ethics, self-correction, meta-learning]
created: 2026-02-12
---

# Plan: Restore Critical Knowledge Items

## Context
The Knowledge Base is missing specific entries for Ethics, Self-Correction, and Meta-Learning. These concepts are implemented in the `mekong-cli` codebase but lack representation in the persistent Knowledge Store. This plan details the extraction and restoration process.

## Phases

### Phase 1: Ethics & Governance Restoration
**Source:** `src/core/governance.py`
**Target:** `~/.gemini/antigravity/knowledge/agencyos_ethics_safety_governance/`
- Create directory structure.
- Generate `metadata.json` defining the Ethics domain.
- Create artifact `governance_protocols.md` detailing:
    - Forbidden Patterns (Destructive commands).
    - Review Protocols (Production changes).
    - Audit Trail mechanisms.

### Phase 2: Self-Correction & Evolution Restoration
**Source:** `src/core/self_improve.py`
**Target:** `~/.gemini/antigravity/knowledge/agencyos_self_correction_evolution/`
- Create directory structure.
- Generate `metadata.json`.
- Create artifact `evolution_mechanics.md` detailing:
    - Recipe deprecation logic (Threshold < 20%).
    - Auto-generation of recipes from manual success.
    - Journaling format.

### Phase 3: Meta-Learning & Pattern Recognition Restoration
**Source:** `src/core/learner.py`
**Target:** `~/.gemini/antigravity/knowledge/agencyos_meta_learning_patterns/`
- Create directory structure.
- Generate `metadata.json`.
- Create artifact `learning_algorithms.md` detailing:
    - Failure streak detection.
    - Time-of-day success correlation.
    - Recipe effectiveness tracking.

## Execution
- **Method:** Use `Write` tool to create directories and files directly.
- **Verification:** Verify file existence and content validity.

## Todo List
- [x] Create `agencyos_ethics_safety_governance`
- [x] Create `agencyos_self_correction_evolution`
- [x] Create `agencyos_meta_learning_patterns`
- [x] Verify all Knowledge Items
