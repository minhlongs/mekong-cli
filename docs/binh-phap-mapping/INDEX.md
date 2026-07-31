# Binh Pháp Deep Mapping — Mekong-CLI Restructuring

> Solo dev | Generated: 2026-07-25 | Status: COMPLETE (Phase 1-5)

## Execution Summary

| Phase | Status | Key Change |
|-------|--------|-----------|
| 1 Routing | DONE | Fable 5 + Opus 4.8 dual-path, local removed |
| 2 Structure | DONE | topology.py → src/core/binh_phap/, 6 domain dirs created |
| 3 Commands | DONE | cfo, cmo, cso wired + execute_for_topic() |
| 4 Docs | DONE | 9 plan files, INDEX + usage guide |
| 5 Domain | DONE | Real logic in commercial/*, research/*, observability/* |
| 6 Testing | DONE | 8 integration tests pass, dispatcher exec verified |

## Architecture: Sun Tzu / Kongming Ready

```
User invokes:  cfo "Q3 budget review" --prompt "deep dive"
                    |
                    v
            build_mk_app() loads mk Typer
                    |
                    v
    cfo_cmd() → BinhPhapDispatcher(company_json)
                    |
          +---------+---------+
          v                   v
    next_action()        execute_for_topic()
    → topology           → _execute_domain()
    → dimension/chapter      → LLM via execute_llm()
    → Fable 5 / Opus         → resolve_llm_provider()
                               → ZuneF or Anthropic
                    |
                    v
            JSON output: { domain, llm, meta }
```

## C-Suite Command Reference

| Command | Chapter | Domain | LLM Model | Use Case |
|---------|---------|--------|-----------|----------|
| `cfo` | Ch2 + Ch5 | budget, pricing | Fable 5 | Finance, pricing, cost structure |
| `cmo` | Ch11 + Ch12 | campaign, growth | Fable 5 | Marketing, outreach, growth |
| `cso` | Ch1 + Ch6 | terrain, competitive | Fable 5 | Market intel, positioning |

Usage:
```
cfo "Q3 budget" --prompt "deep dive on burn rate"
cmo "product launch" --prompt "Go-to-market strategy"
cso "competitors" --prompt "market landscape analysis"
```

All commands accept `--company` flag to override context file (default: `.mekong/company.json`).

## Dual-Path LLM Auth

| Tier | Model | Purpose | Credential Scope |
|------|-------|---------|------------------|
| Strategic (Fable 5) | claude-fable-5 | Commercial chapters 1/2/5/11/12 | ZuneF team gateway |
| Default (Opus 4.8) | claude-opus-4-8 | All other chapters | Anthropic direct or ZuneF |

Environment Variables (priority order):
- Strategic: `ZUNEF_FABLE_BASE_URL` → `FABLE_BASE_URL` → `ANTHROPIC_BASE_URL`
- Default: `ZUNEF_OPUS_BASE_URL` → `OPUS_BASE_URL` → `ANTHROPIC_BASE_URL`
- API Key: `ZUNEF_API_KEY` > `ANTHROPIC_API_KEY`

## Key Decisions
- Fable-only for strategic (Ch1/2/5/11/12), Opus 4.8 for everything else
- ZuneF gateway primary, Anthropic fallback for dev
- Jidoka hooks at cook/test/deploy
- No local LLM execution
- CLI help runs clean

## Completed Files
- `src/core/binh_phap/topology.py` — 3D dispatch engine
- `src/core/binh_phap/escalation.py` — dual-path auth resolver
- `src/core/binh_phap_dispatcher.py` — integration layer with execute_llm()
- `src/cli/csuite_commands.py` — C-suite command definitions (cfo/cmo/cso on root)
- `src/commercial/` — terrain, situation, finance, marketing, growth
- `src/research/` — competitive, scout
- `src/observability/` — health monitor
- `tests/core/test_binh_phap_vertical_integration.py` — 8 passing tests
- `.claude/commands/cfo.md` — command documentation (if exists)
- `.claude/commands/cmo.md` — command documentation (if exists)
- `.claude/commands/cso.md` — command documentation (if exists)
