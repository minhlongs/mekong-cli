# 🌐 Agent Browser (Vercel Labs) — 虛實篇 93% Context Reduction

> Source: github.com/vercel-labs/agent-browser + vnrom.me/uzcuiwq
> Assessed: 2026-02-18 | Status: CRITICAL KEEP — P1 INSTALL NOW
> Action: npm install -g agent-browser → integrate vào Tôm Hùm

## What
- CLI tool browser automation DÀNH RIÊNG cho AI agents
- Vercel Labs official (14,000+ stars)
- Rust CLI + Node.js daemon + Playwright
- Snapshot + Refs: 93% LESS context than full DOM

## Core Innovation
Traditional: Send full DOM tree → huge context → waste tokens
Agent Browser: Snapshot → compact refs (@e1, @e2) → 93% savings

## Key Features
- Snapshot: accessibility tree + stable refs
- Actions: click, fill, type, hover, drag, select, screenshot, PDF, eval JS
- Session persistence: cookies, localStorage, AES-256 encryption
- Cloud: Browserbase, Kernel, iOS Safari
- JSON output: AI-friendly parse → act → resnapshot

## Install
```bash
npm install -g agent-browser
agent-browser install  # Downloads Chromium
```

## Workflow
```bash
agent-browser open https://docs.stripe.com/api
agent-browser snapshot -i --json > snapshot.json
agent-browser click @e5
agent-browser fill @e3 "search term"
agent-browser screenshot result.png
```

## Integration Plan
1. Install: npm install -g agent-browser
2. Tạo tool wrapper trong openclaw-worker/tools/browser-agent.js
3. HyperSkill Generator dùng agent-browser thay cheerio
4. scanner-hunter.js upgrade: dùng agent-browser thay puppeteer
5. Tôm Hùm CTO: new capability = web interaction

## Synergy Pipeline
Agent Browser (scrape, 93% less context)
  → HyperSkill (generate SKILL.md)
  → Tôm Hùm CTO (new skills)
  → Postiz MCP (auto-post)

## Binh Pháp
- 虛實篇: 93% context reduction = "avoid strength, attack weakness"
- 行軍篇: Stable refs > fragile CSS selectors
- 作戰篇: CLI calls = instant vs slow browser subagent
