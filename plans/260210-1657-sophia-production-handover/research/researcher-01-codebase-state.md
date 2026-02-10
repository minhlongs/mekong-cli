# Sophia AI Video Factory — Codebase State Report

## Tech Stack
| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js 16.1.6 (App Router) | React 19.2.3 |
| Styling | Tailwind CSS 4 | PostCSS |
| Database | Supabase (SSR + JS) | v2.94.1 |
| Payments | Polar.sh (@polar-sh/sdk + nextjs) | v0.42.5 |
| Background | Inngest | v3.50.0 |
| Bot | Telegraf (Telegram) | v4.16.3 |
| Video | HeyGen | Custom |
| Voice | ElevenLabs | Custom |
| AI Router | OpenRouter | Custom |
| i18n | next-intl | v4.8.2 |
| Cache | Upstash Redis | v1.36.2 |
| Testing | Vitest 4.0.18 + Playwright 1.58.1 | |

## App Routes
- `/` — Landing page (hero, workflow, features, pricing, FAQ, ROI calc)
- `/login` — Supabase Magic Link auth
- `/pricing` — Plan comparison
- `/guide/*` — User guide (FAQ, getting-started)
- `/dashboard` — Main dashboard (stats, campaigns)
- `/dashboard/create` — Campaign creation
- `/dashboard/campaigns` — List + `/[id]` detail
- `/dashboard/analytics` — Charts (Recharts)
- `/dashboard/settings` — User settings
- `/dashboard/support` — Support page
- `/dashboard/system-health` — System health
- `/dashboard/api-docs` — API docs
- `/affiliate-discovery` — Product discovery
- `/admin` — Admin panel
- `/setup-wizard` — Onboarding (system check, API keys, DB, finish)

## Tier Pricing
| Tier | Display | Price | Type |
|------|---------|-------|------|
| BASIC | Starter | $199/mo | Subscription |
| PREMIUM | Growth | $399/mo | Subscription |
| ENTERPRISE | Premium | $799/mo | Subscription |
| MASTER | Master | $4,999 | One-time |

## Quality
- `:any` types: 0
- TODO/FIXME: 1 (Master tier "coming soon")
- Tests: 32 files (145+ tests)
- Tech debt: All resolved/accepted (2026-02-09)

## Open Issues
1. Master tier checkout returns "coming soon"
2. Smart Resume Engine uses in-memory storage
3. sophia-video-bot dir has only pyproject.toml (abandoned?)
4. 3 production URLs — canonical unclear
