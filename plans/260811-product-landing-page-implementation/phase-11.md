# Phase 11 — Phase 01.11: CTA Section & Newsletter Signup

**Date:** 260811 · **Status:** pending

## Task
Build final CTA section with email capture form. Server action for newsletter submission (API route). Zod validation, honeypot spam protection, toast notifications.

## Files

- src/components/sections/cta.tsx
- src/components/ui/form-field.tsx
- src/actions/newsletter.ts
- src/lib/validators.ts

## Acceptance criteria

Form submits without page reload. Valid email required. Honeypot catches bots. Success/error toasts appear. Rate limited (5 req/min/IP). Submissions logged.
