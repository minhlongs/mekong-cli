# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Identity

Mekong CLI v6.0 — AI-operated business platform for Vietnamese one-person companies. MIT licensed. Public repo.

Core funnels:
1. Zalo OA — customer communication automation
2. Tax & Accounting (thue_dnvn, ke_toan) — TNCN/TNDN/GTGT compliance + TT78 invoices
3. AI Video Factory (sophia) — AI video generation on CF Workers

## Commands

Run from repo root. 43 commands wired to executable Python.

- Design intelligence: `mekong ui {audit,study,redesign,build,approve,benchmark}`
  (see docs/design-intelligence.md)

- Python tests: python3 -m pytest tests/ -v
- Lint: python3 -m ruff check src/ tests/
- Single test file: python3 -m pytest tests/<path> -v

## Architecture

mekong (CLI) / api-gateway (FastAPI :8000)
  src/api/ — REST routes (raas, billing, vn_pilot, vn_pricing, gateway)
  src/core/ — MCU billing, orchestrator, LLM routing
  src/services/ — Polar client, org service
  src/commands/ — 43 wired command modules
  src/cli/ — vn_setup wizard
  src/middleware/ — license_gate (JWT + balance check)
  src/seed/ — foundational auth, DB, config, types
  src/tree/ — domain logic (byok, telegram)
  src/forest/ — infrastructure (inngest, quota)
  src/land/ — business workflows (billing, payouts)

## Billing

- MCU: 1 MCU = 1 credit (MCUBilling singleton)
- Polar.sh webhook → org activation
- Tier enum: BASIC | PREMIUM | ENTERPRISE | MASTER

## Quality

- Python: ruff, mypy
- No console statements in production
- Tests must pass before push

## Public Repo Boundary

- apps/ — private client projects
- .env* — never commit
- app/ — private client projects
- billing/ — internal workspace (dịch vụ, không public)
