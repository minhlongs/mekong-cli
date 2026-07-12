# Plan: {{feature_name}}

## Overview

This document describes the implementation plan for **{{feature_name}}**.

{{description}}

---

## Architecture

{{architecture}}

### Layer Assignment

| Concern | Layer | Rationale |
|---------|-------|-----------|
| Data models | `seed/` | Foundational, shared |
| Business logic | `tree/` | Reusable domain logic |
| Orchestration | `forest/` | Cross-module coordination |
| User workflows | `land/` | Business-facing flows |

---

## API Contracts

{{contracts}}

All routes must include Zod validation on input and structured error responses (`{ error: string, code: string }`).

---

## Data Model

{{data_model}}

Migrations live in `migrations/` and are applied via `npm run db:migrate`.

---

## Research

{{research}}

### Decisions

| Question | Decision | Reference |
|----------|----------|-----------|
| Database | D1 (Cloudflare) | CF-direct doctrine |
| Validation | Zod | Project standard |
| Auth | Better Auth | Existing infra |

---

## Quickstart

```bash
# 1. Install dependencies
cd apps/<app>
npm install

# 2. Apply migrations
npm run db:migrate

# 3. Start dev server
npm run dev        # → http://localhost:3000

# 4. Run tests
npm test

# 5. Type check
npm run type-check
```

---

*Generated: {{generated_at}}*

> Template: `.specify/templates/plan-template.md`
