---
title: ZenOS Redesign
status: completed
priority: P0
effort: high
branch: zenos-redesign
tags: [zenos, constitutional-ai, particles]
created: 2026-06-18
---

# ZenOS Redesign

## Status
- [x] All 10 phases completed
- [x] 160 tests passing
- [x] Code-review completed
- [x] Docs updated
- [x] Journal written

## Overview
Redesigned mekong-cli into a ZenOS-aligned platform: Economic Particles, Constitutional AI, Founder Genome, Behavior Graph, ZenPay Money OS, Ostrom governance, and particle-first CLI. Vietnam features preserved.

## Phases
1. [x] Database Schema Redesign
2. [x] Constitutional AI Middleware
3. [x] Founder Genome Capture
4. [x] Behavior Graph Service
5. [x] ZenPay Money OS
6. [x] Ostrom Governance Framework
7. [x] CLI Particle-First Refactor
8. [x] Tenant-to-Particle Migration
9. [x] Test Suite
10. [x] Documentation & Onboarding

## Verification
- `python3 -m pytest tests/zenos/ -v --tb=short` → 160 passed
- Code-reviewer completed
- Journal written to `docs/journals/2025-06-18-zenos-redesign-complete.md`

## Unresolved Questions
- Graph DB choice: PostgreSQL JSONB vs Neo4j
- VND payout provider: Stripe vs Wise
- Founder Genome key rotation strategy
- Right to Exit data format
- Vietnam legal wrappers for OPC templates
