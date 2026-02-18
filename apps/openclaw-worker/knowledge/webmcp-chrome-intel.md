# 🌐 WebMCP — Chrome Agentic Web Standard — 勢篇 Strategic Intel

> Source: Google Chrome (developer.chrome.com/blog/webmcp-epp)
> Published: 2026-02-10 | Status: Early Preview Program
> Assessed: 2026-02-18 | Action: WATCH — xu thế 6-12 tháng

## What
- Google Chrome đang chuẩn hóa cách AI agents tương tác với websites
- Websites expose **structured tools** (thay vì agents scrape DOM)
- 2 APIs: Declarative (HTML forms) + Imperative (JS execution)

## 2 New APIs
1. **Declarative API**: Standard actions via HTML forms (checkout, support tickets)
2. **Imperative API**: Complex JS interactions (search + filter + booking)

## Impact cho Tôm Hùm
- **Short term (now)**: Không ảnh hưởng — EPP chỉ cho prototyping
- **Medium term (6-12mo)**: Khi GA → HyperSkill sẽ không cần scrape
  - Thay cheerio/puppeteer bằng WebMCP tool calls
  - Structured data thay vì parsed markdown
- **Long term (1-2yr)**: Mọi website = MCP server
  - scanner-hunter.js gọi WebMCP thay vì scrape
  - RaaS clients' sites tự expose tools cho agent 

## Binh Pháp Mapping
- 勢篇 (Thế) — Xu thế không cưỡng được, phải thuận theo
- 地形篇 — Terrain web đang thay đổi từ DOM → Structured Tools
- 因糧於敵 nâng cấp: websites CHỦ ĐỘNG cung cấp intel

## Action Items
- [ ] Đăng ký Early Preview Program: https://developer.chrome.com/docs/ai/join-epp
- [ ] Khi GA: Update HyperSkill generator thêm WebMCP mode
- [ ] Khi GA: Update scanner-hunter.js thêm WebMCP discovery
