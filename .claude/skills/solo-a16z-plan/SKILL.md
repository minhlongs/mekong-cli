# Solo a16z Plan

## Description

Guided business-plan workflow for solo founders, structured around the
Andreessen Horowitz (a16z) investing lens. Drives the founder through 14
sections / 61 prompt cards — from "Idea Maze" and "Why Now" through TAM/SAM/SOM,
distribution, unit economics, 7 Powers moat analysis, founder-market fit,
roadmap, risk, and the funding ask.

Replaces the AI-for-Work / GPT-for-Sheets business-plan template with a
ClaudeKit-native flow: prompts route through the LLM client (BYO model),
state persists to `.claude/solo-a16z/<project>.json`, and a dashboard
mirrors the same data so a founder can switch between CLI and IDE.

## When to Use

Trigger when the user asks to:
- "draft a business plan", "write a pitch deck outline", "validate my idea",
  "do a16z-style analysis", "find the Why Now / Contrarian Thesis",
  "size my market bottoms-up", "design a moat / 7 Powers analysis"
- run any of: `/plan-a16z`, `/founder-plan`, `claude plan-a16z ...`
- review a solo-founder idea before fundraising or before committing engineering effort

Do **not** trigger for tactical day-to-day commands (sprint planning, code
review, sales outreach) — those have dedicated commands.

## Implementation

CLI commands live in `cli/commands/plan_a16z.py` (Typer sub-app `plan-a16z`).

Framework data (sections, cards, prompts, input refs) is in
`.claude/skills/solo-a16z-plan/framework.json` — single source of truth shared
between the CLI and the dashboard.

State is per-project JSON at `.claude/solo-a16z/<slug>.json` with the shape
`{ seed, results: {key: text}, completed: {key: bool}, updated_at }`.

Dashboard route: `apps/dashboard/app/(founder)/solo-a16z/page.tsx`. The page
embeds the standalone HTML platform via iframe and proxies state to/from the
filesystem through `apps/dashboard/app/api/solo-a16z/route.ts`.

LLM calls go through `src.core.llm_client.get_client()` so the same 3 env vars
(`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`) used by the rest of the platform
also drive this skill.

## Dependencies

- `typer`, `rich` (already in `requirements.txt`)
- `src.core.llm_client` (in-tree)
- Next.js dashboard at `apps/dashboard` (optional — CLI works standalone)
