# ENV Audit Report — 2026-03-01

## Summary

17 .env files audited. **2 files contain real, high-severity secrets.** No .env files with real secrets are git-tracked. 3 non-secret files are git-tracked (safe).

---

## CRITICAL — Real Secrets Found (Untracked, Local Only)

### 1. `/Users/macbookprom1/mekong-cli/.env` — HIGH RISK
Real, non-placeholder secrets present:

| Key | Value (masked) | Risk |
|-----|---------------|------|
| `GUMROAD_ACCESS_TOKEN` | `6rzTtCiZ...nHgU` | LIVE token — revoke immediately |
| `PAYPAL_CLIENT_ID` | `BAA_307I...` | LIVE PayPal production credential |
| `PAYPAL_CLIENT_SECRET` | `EJlaGiw3...` | LIVE PayPal production credential |
| `SUPABASE_URL` | `https://jcbahdio....supabase.co` | Real project ref |
| `GEMINI_API_KEY` | `AIzaSyCr0q...` | Real Google AI key |
| `GUMROAD_EMAIL` | `billwill.mentor@gmail.com` | Plaintext credential |
| `GUMROAD_PASSWORD` | `FastSaaS2026@` | **PLAINTEXT PASSWORD — CRITICAL** |
| `POLAR_ACCESS_TOKEN` | `polar_oat_bVAp...` | LIVE Polar token |

> `STRIPE_SECRET_KEY=sk_test_dummy` and `STRIPE_WEBHOOK_SECRET=whsec_test_secret` are test/dummy — OK.

### 2. `/Users/macbookprom1/mekong-cli/scripts/.env` — HIGH RISK
Real API keys for LLM proxy:

| Key | Risk |
|-----|------|
| `OLLAMA_KEYS` (8 keys) | Real production API keys |
| `OPENROUTER_KEY` | Comment says "REVOKED" — verify |
| `NVIDIA_CONFIGS` (17 keys) | Real `nvapi-*` production keys |
| `DASHSCOPE_API_KEYS` | Real DashScope key |

---

## MEDIUM — Expirable Tokens (Local Only)

| File | Secret | Notes |
|------|--------|-------|
| `apps/well/.env.production.local` | `VERCEL_OIDC_TOKEN` (JWT) | Short-lived (exp: ~12h), already expired |
| `apps/agencyos-landing/.env.local` | `VERCEL_OIDC_TOKEN` (JWT) | Short-lived, already expired |
| `apps/agencyos-web/.env.local` | `VERCEL_OIDC_TOKEN` (JWT) | Short-lived, already expired |
| `apps/com-anh-duong-10x/.env.production` | `VERCEL_OIDC_TOKEN` (JWT) | Short-lived, already expired |

Vercel OIDC tokens expire in ~12 hours — low risk, but should not persist in files.

---

## LOW / SAFE

| File | Status |
|------|--------|
| `doanh-trai-tom-hum/.env` | Local DB creds only (`localhost`) — safe |
| `apps/api/.env` | Local DB (`localhost`) — safe |
| `apps/worker/.env` | Local file path only — safe |
| `apps/engine/.env` | Local file path only — safe |
| `apps/well/.env.local` | Supabase anon key (public-safe by design) + admin emails |
| `apps/84tea/.env.local` | Supabase anon key + PayOS keys — see note below |
| `apps/anima119/.env.local` | Same Supabase project as 84tea, anon key only — safe |
| `apps/apex-os/.env` | Only `CLOUD_BRAIN_URL` (serveo URL) — low risk |
| `apps/com-anh-duong-10x/.env` | PayOS keys present (real) |
| `apps/openclaw-worker/.env` | Only `CLOUD_BRAIN_URL` — safe |
| `apps/agencyos-web/.env.local` | Vercel OIDC token only (expired) |
| `apps/dashboard/.env.production` | All placeholder values — safe |

### PayOS Keys Note (`apps/84tea/.env.local`, `apps/anima119/.env.local`, `apps/com-anh-duong-10x/.env`)
`PAYOS_CLIENT_ID`, `PAYOS_API_KEY`, `PAYOS_CHECKSUM_KEY` are real. PayOS (Vietnamese payment) — not untracked via gitignore pattern for `.env.local`, but files are confirmed untracked.

---

## Git Tracking Status

| File | Tracked? | Content |
|------|----------|---------|
| `apps/dashboard/.env.production` | YES (intentional) | All placeholders — safe |
| `.env.domain` | YES | Domain names only — safe |
| `.env.unified` | YES | Domain names only — safe |

**No real secrets are in git history.** The `apps/dashboard/.env.production` was added in commit `9b87a32d` with placeholder values only.

`.gitignore` covers: `.env`, `.env.local`, `*.env`, `scripts/.env` — all critical files are excluded.

**Gap:** `.env.production.local`, `.env.production` (per-app) patterns not universally covered. The `apps/com-anh-duong-10x/.env.production` is untracked only by coincidence (no `*.env.production` rule).

---

## Actions Required

| Priority | Action |
|----------|--------|
| P0 | Revoke `GUMROAD_PASSWORD` (`FastSaaS2026@`) — plaintext password in file |
| P0 | Rotate `PAYPAL_CLIENT_SECRET` (live mode credential) |
| P0 | Rotate `POLAR_ACCESS_TOKEN` |
| P0 | Rotate `GUMROAD_ACCESS_TOKEN` |
| P1 | Rotate `GEMINI_API_KEY` |
| P1 | Audit all 17 NVIDIA NIM keys — rotate if shared beyond this machine |
| P1 | Add `*.env.production` and `*.env.production.local` to root `.gitignore` |
| P2 | Move `.env` to secrets manager (1Password, Doppler, etc.) |
| P2 | Remove stored Vercel OIDC tokens from files |

---

## Unresolved Questions

- Are NVIDIA NIM keys (`nvapi-*`) shared/used elsewhere? If yes, rotate urgently.
- Is the OpenRouter key actually revoked? Verify at https://openrouter.ai/keys.
- PayOS keys in `84tea`/`anima119`/`com-anh-duong-10x` — same project or different?
- Who else has access to this machine's filesystem?
