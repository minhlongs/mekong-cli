# 🖥️ Accomplish AI (ex-Openwork) — 上兵伐謀 Market Separation

> Source: github.com/accomplish-ai/accomplish
> Assessed: 2026-02-18 | Status: SKIP — different market segment

## What
- Open source Desktop AI Agent (Electron)
- File management + document creation + browser automation
- BYOK: 13+ model providers + Ollama local
- GUI wrapper around OpenCode CLI (by SST)

## Architecture
Electron → node-pty → OpenCode CLI → LLM APIs

## vs Tôm Hùm
- Accomplish = GUI for non-coders (end users)
- Tôm Hùm = Multi-daemon AGI engine for developers/agencies
- Different markets, no competition, no learnings needed

## Only Noteworthy Pattern
- Electron + node-pty for GUI wrapping CLI tools
- Could inspire future P4: "Tôm Hùm Desktop GUI" (Electron wrapper)
- Not actionable now

## Skip Reason
- Single agent vs Tôm Hùm 11 daemons
- Sequential vs /cook --parallel
- No orchestration, no planning pipeline
- 上兵伐謀: Different battlefield entirely
