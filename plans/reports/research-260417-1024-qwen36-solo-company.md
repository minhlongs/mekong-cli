# Research — Qwen3.6-35B-A3B Solo Company on M1 Max 64GB

**Date:** 2026-04-17 10:35 | **Hardware target:** M1 Max 64GB RAM / 2TB SSD

## Qwen3.6-35B-A3B Facts (released 2026-04-16)

- MoE: 35B total / **3B active** / 256 experts (8 routed + 1 shared per token)
- Arch: Gated Delta Networks + sparse MoE
- Context: **262,144 tokens** (256K)
- Benchmarks vs Sonnet 4.5 / Gemma4-31B:
  - SWE-bench Verified: **73.4** (up from 3.5)
  - Terminal-Bench 2.0 (agentic coding): **51.5** (Gemma4-31B=42.9)
  - MMMU: 81.7 (Sonnet=79.6)
  - RealWorldQA: 85.3 (Sonnet=70.3)
  - MathVista-mini: 86.4 (Sonnet=79.8)
- Tokens/s on M1 Max: **~30 tok/s** (MLX + flash-paging)
- License: Apache 2.0 (open weights), MLX/GGUF available day-1

## M1 Max 64GB Feasibility

| Quant | RAM | Quality | Best for |
|-------|-----|---------|----------|
| Q4_K_M | ~19-20GB | Near-lossless | Daily driver |
| Q6_K | ~28GB | Lossless-ish | Quality-critical |
| Q8_0 | ~38GB | Full quality | Batch inference |
| bf16 | ~70GB | ❌ won't fit | N/A |

**Verdict:** Q4 is the sweet spot. ~45GB free for concurrent work (agent runtime, Tauri shell, Chrome, IDE).

## Competitive Landscape

- **walter-grace/mac-code** (github): "Claude Code but free on Mac, Qwen3.5 35B, $0/mo" → DIRECT competitor for pure code-agent repackaging
- **Ollama + Continue.dev**: commodity local-LLM setup, no IDE moat
- **LM Studio**: desktop app, no agent layer
- **mekong-cli (existing)**: has SDLC + gates + Polar $49/mo, cloud LLM bound
- **Sophia BYOK (existing)**: M1 Max runtime for client keys
- **OpenClaw (existing)**: M1 Max daemon host

## Moat Analysis

| Angle | Moat | Risk |
|-------|------|------|
| Pure "run Qwen locally" wrapper | 🔴 Low (mac-code exists) | Commodity |
| Qwen as Claude-API drop-in for CC CLI | 🟡 Medium (cost savings $200→$50/mo) | Claude API compat drift |
| Qwen-backed agent IDE w/ signals+gates | 🟢 High (Mekong SDLC stack) | Ship complexity |
| Qwen fine-tuned for Vietnamese SMB verticals | 🟢 High (language + vertical moat) | Training cost |

## Business Models vs a16z Solo Doctrine

**a16z rule:** agents do all work, human = strategy only, $1M ARR target, XONG = $ in bank.

Top-3 revenue paths:

1. **B2C: $29/mo "Qwen Unlimited"** — serve Qwen3.6 from M1 Max via CF Tunnel; customers pay for unmetered access. Break-even: 30 users. Risk: M1 Max = single point of failure.
2. **B2B-Solopreneur: $99 one-time setup** — package Qwen3.6 + Mekong skills + hooks as installer for solopreneur's own M1/M2/M3 Mac. High margin, zero infra. Risk: support burden.
3. **Platform wrapper: Claude API cost-saver** — `mekongd` intercepts CC CLI subagent calls → routes "cheap" work (explore/search/reformat) to local Qwen3.6, only "plan/opus" hits cloud. Cuts bills 4-10x. SaaS $19/mo or FOSS+donations.

## Recommended Direction

**Option C: `mekongd` Claude API cost-saver daemon** — highest-leverage because:
- Solves $200-500/mo Claude bill for every CC CLI heavy user (huge TAM)
- Leverages Qwen3.6 SWE-bench 73.4 → "good enough" for ~70% of agent subtasks
- Plugs into existing Mekong CLI ecosystem (not a me-too clone)
- Ship-ready in 2-3 weeks: MLX serve + OpenAI-compat proxy + routing policy

## Unresolved Questions

1. Should this be a NEW repo or a Mekong CLI subpackage?
2. Pricing: FOSS + Polar-paid cloud sync tier OR pure $19/mo SaaS?
3. M1 Max public exposure via CF Tunnel = security risk — accept or gate behind auth?
4. Qwen3.6 Apache 2.0 but commercial resale of access — any attribution needed?
