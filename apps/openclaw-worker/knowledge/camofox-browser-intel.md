# 🦊 Camofox Browser — 用間篇 Ngụy Gián Anti-Detection

> Source: github.com/jo-inc/camofox-browser
> Assessed: 2026-02-18 | Status: KEEP — P2 Stealth Browser
> Action: Install sau Agent Browser (P1), dùng cho blocked sites

## What
- Anti-detection browser server cho AI agents
- Camoufox engine: Firefox C++ fork, fingerprint spoofing
- Bypasses Google, Cloudflare, most bot detection
- REST API server, ~40MB idle, MIT license

## vs Agent Browser (Dual Engine Strategy)
- Agent Browser (Vercel): Playwright/Chromium = fast, normal sites
- Camofox: Camoufox/Firefox = stealth, blocked sites
- BOTH use similar snapshot refs (e1, e2, e3)

## Key Features
- C++ anti-detection (not JS shims — undetectable)
- 14 search macros: @google_search, @twitter_search, @linkedin_search...
- Cookie import (authenticated browsing)
- Proxy + GeoIP (residential proxies)
- Session isolation per user
- Deploy: Docker, Fly.io, Railway, $5 VPS

## OpenClaw Plugin
```bash
openclaw plugins install @askjo/camofox-browser
```

## Install
```bash
npm install @askjo/camofox-browser
npm start  # downloads Camoufox ~300MB first run
```

## Binh Pháp
- 用間篇: Ngụy Gián — giả dạng user thật bypass detection
- 虛實篇: C++ level = invisible to JS detection
- Dual Engine: Agent Browser (công khai) + Camofox (ngụy trang)

## Priority: P2 (complement to Agent Browser P1)
