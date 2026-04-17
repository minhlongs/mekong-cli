# Binh Pháp Roadmap — 13 Verticals Master Index

> **Dated: 2026-04-17 — All items below are post-D-Day targets.**
> D-Day = first paying Mekong IDE customer. XONG = $ in bank, not PR merged.
> Initial estimates — subject to revision as each vertical is scoped.

---

## Strategy

**Master formula:** 13 Sun Tzu chapters × 13 open-source giants × 13 vertical products.
**Core principle:** 1 AI kernel (443 commands) × 13 domain wrappers = 13 revenue streams.
Giants provide distribution. Mekong provides the AI layer. Verticals provide the revenue.

---

## Status Overview

| Ch. | Vertical | Giant | Status | Effort est. | Revenue target |
|-----|----------|-------|--------|-------------|----------------|
| 1 始計 | [MekongHQ](../verticals/scaffold/01-paperclip-mekong-hq.md) | Paperclip | SCAFFOLD | 40h (med) | $199/mo/seat |
| 2 作戰 | **CashClaw** *(shipped)* | Coolify | **SHIPPED** | — | Trading profits |
| 3 謀攻 | [MekongCounsel](../verticals/scaffold/03-openclaw-mekong-counsel.md) | OpenClaw | SCAFFOLD | 80h+ (large) | $500–2K/project |
| 4 軍形 | [MekongVault](../verticals/scaffold/04-supabase-mekong-vault.md) | Supabase | SCAFFOLD | 80h+ (large) | $299–999/mo |
| 5 兵勢 | [MekongStudio](../verticals/scaffold/05-nextjs-mekong-studio.md) | Next.js | SCAFFOLD | 40h (med) | $49–199/mo |
| 6 虛實 | MekongPay | Polar.sh | PARTIAL | 20h (small) | Transaction fees |
| 7 軍爭 | [MekongBridge](../verticals/scaffold/07-n8n-mekong-bridge.md) | n8n | SCAFFOLD | 40h (med) | $99–499/mo |
| 8 九變 | MekongMind | Ollama | PARTIAL | 20h (small) | Usage-based |
| 9 行軍 | [MekongPulse](../verticals/scaffold/09-grafana-mekong-pulse.md) | Grafana | SCAFFOLD | 40h (med) | $149–599/mo |
| 10 地形 | [MekongMap](../verticals/scaffold/10-langchain-mekong-map.md) | LangChain | SCAFFOLD | 80h+ (large) | $299/mo |
| 11 九地 | [MekongForce](../verticals/scaffold/11-crewai-mekong-force.md) | CrewAI | SCAFFOLD | 80h+ (large) | $499–2999/mo |
| 12 火攻 | [MekongLaunch](../verticals/scaffold/12-opencode-mekong-launch.md) | OpenCode | SCAFFOLD | 40h (med) | $1999–4999 |
| 13 用間 | [MekongEye](../verticals/scaffold/13-posthog-mekong-eye.md) | PostHog | PARTIAL | 20h (small) | $499–1999/mo |

**Effort key:** small = 20h / med = 40h / large = 80h+. All estimates initial; revise at kickoff.

---

## Execution Sequence (recommended)

Build in order of lowest prerequisite depth and highest revenue/effort ratio:

1. **MekongPay** (Ch.6) — smallest effort, already partial, unblocks billing for other verticals
2. **MekongMind** (Ch.8) — already partial, enables local LLM routing across all verticals
3. **MekongEye** (Ch.13) — already partial, PostHog instrumentation needed for all verticals anyway
4. **MekongHQ** (Ch.1) — medium effort, strategy tooling reuses existing `/okr`/`/annual` commands
5. **MekongStudio** (Ch.5) — medium effort, high volume market, reuses `/content`/`/social`
6. **MekongBridge** (Ch.7) — medium effort, integration layer unlocks enterprise deals
7. **MekongPulse** (Ch.9) — medium effort, signals layer already partially shipped (Layer 2)
8. **MekongLaunch** (Ch.12) — medium effort, growth tooling, own dogfood use case
9. **MekongCounsel** (Ch.3) — large, requires OpenClaw daemon stable
10. **MekongVault** (Ch.4) — large, requires Supabase partnership + security expertise
11. **MekongMap** (Ch.10) — large, requires RAG pipeline + vector DB
12. **MekongForce** (Ch.11) — large, requires CrewAI + mission intake UI

---

## Scaffold Index

Scaffolds live at `verticals/scaffold/`. See [scaffold README](../verticals/scaffold/README.md).

Each scaffold file contains:
- Binh Pháp chapter mapping + Sun Tzu quote applied to business
- Mission, ICP, tech sketch, revenue model
- Prerequisites and effort estimate
- Owner placeholder

---

## What "SCAFFOLD" Means

- A markdown plan document exists
- Zero code, zero infrastructure, zero dependencies added
- Not in-flight — no engineer is working on it
- Safe to read without mistaking it for shipped work
- Will be promoted to a proper phase plan when execution begins

---

## Next Action

**Do not build more scaffolds.** Focus execution on:
1. First Mekong IDE paying customer (D-Day)
2. Then: MekongPay + MekongMind + MekongEye (complete the partials)
3. Then: sequence above based on market validation

> 虛實 (Ch.6): Know your strengths and weaknesses. This roadmap maps both.
> XONG = $ in bank. Everything else is preparation.
