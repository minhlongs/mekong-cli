# MekongMap — Market Intelligence SaaS

> **STATUS: SCAFFOLD ONLY — NOT STARTED. Not in-flight. Not built. Post-D-Day target.**
> Last updated: 2026-04-17

---

## Binh Pháp Mapping

| Field | Value |
|-------|-------|
| Chapter | 10 地形 (Terrain / Ground Types) |
| Principle | Know your terrain before advancing — map the competitive landscape |
| Giant | LangChain (132K stars) — LLM orchestration, RAG pipelines, agent chains |
| Application | MekongMap uses LangChain RAG pipelines to continuously index markets, competitors, and signals — giving founders a live intelligence advantage |

**Sun Tzu quote:** "Know the ground, know the weather; your victory will then be total."
Applied: Market terrain changes constantly. MekongMap tracks competitors, pricing shifts, job postings, and regulatory changes — terrain knowledge as competitive advantage.

---

## Mission

MekongMap is an **AI market intelligence platform** that continuously monitors competitors,
industry trends, and market signals using LangChain-powered RAG pipelines. It delivers
weekly intelligence briefings so a solo founder knows the battlefield without a research team.

---

## Target Market

- B2B SaaS founders tracking 5-20 competitors manually
- PE/VC-backed operators needing market diligence on ongoing basis
- Consultants and analysts who sell market intelligence to clients

**ICP:** Solo SaaS founder who lost 3 deals this quarter because competitors shipped a feature first.

---

## Tech Sketch

- LangChain RAG pipeline: ingest competitor websites, job boards, GitHub, Product Hunt, HN
- Vector store: Supabase pgvector or Cloudflare Vectorize
- Commands activated: `/scout`, `/research`, `/competitive` (new command needed)
- Output: weekly briefing PDF + real-time Slack alerts on signal spikes
- Agent chain: crawl → chunk → embed → rank → synthesize → deliver

---

## Revenue Model

- $299/mo Starter (10 competitors tracked, weekly briefing)
- $799/mo Growth (unlimited competitors, daily briefings, API access)
- $1,499/mo Enterprise (custom signal sources, dedicated RAG pipeline)

---

## Prerequisites

- Mekong IDE v6.0 core (shipped)
- LangChain integration / RAG pipeline (not built)
- Vector store setup (Supabase pgvector or CF Vectorize)
- `/competitive` command (not yet defined)

---

## Owner Placeholder

_Unassigned. Requires: 1 ML/RAG engineer, LangChain expertise, vector DB ops._
