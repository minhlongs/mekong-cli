# Camofox Anti-Detect Browser — Installation Report

**Date:** 2026-02-20 | **Binh Pháp:** 反間篇 — Phản Gián (Counter-Intelligence)

## Tổng Kết

Đã cài đặt thành công Camofox anti-detect browser cho hệ sinh thái mekong-cli.

## Thành Phần Đã Cài

| Component | Version | Location |
|-----------|---------|----------|
| `@askjo/camofox-browser` | npm latest | `~/.camofox-browser/node_modules/` + global |
| `camofox-mcp` | npm latest | global (MCP bridge) |
| `camofox-browser` skill | from yelban/camofox-browser-skills | `.claude/skills/camofox-browser/` |
| MCP config | camofox entry | `.claude/mcp.json` |

## Kiến Trúc

```
AI Agent → (MCP) → camofox-mcp → (REST :9377) → camofox-browser → Camoufox (Firefox fork)
                                                                       ↓
                                                              C++ fingerprint spoofing
```

## Kết Quả Test Bot Detection (bot.sannysoft.com)

| Test | Kết Quả |
|------|---------|
| WebDriver (New) | ✅ `missing (passed)` |
| WebDriver Advanced | ✅ `passed` |
| PHANTOM_UA | ✅ `ok` — Firefox/146.0 |
| PHANTOM_PROPERTIES | ✅ `ok` |
| PHANTOM_ETSL | ✅ `ok` |
| PHANTOM_LANGUAGE | ✅ `ok` |
| PHANTOM_WEBSOCKET | ✅ `ok` |
| PHANTOM_WINDOW_HEIGHT | ✅ `ok` |
| SELENIUM_DRIVER | ✅ `ok` — 17/17 = false |
| navigator.webdriver | ✅ `false` (C++ patch) |
| Platform | ✅ `MacIntel` |
| Chrome (New) | ⚠️ `missing (failed)` — expected vì dùng Firefox |

**Verdict:** 11/12 passed — chỉ Chrome object missing (correct behavior cho Firefox-based browser).

## Cách Sử Dụng

### CLI (camofox.sh)
```bash
camofox start                     # Khởi động server port 9377
camofox open https://example.com  # Mở URL stealth
camofox snapshot                  # Lấy accessibility tree
camofox click @e1                 # Click element
camofox screenshot                # Chụp screenshot
camofox stop                      # Dừng server
```

### REST API (curl)
```bash
curl -X POST http://localhost:9377/tabs \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","userId":"agent","sessionKey":"s1"}'

curl "http://localhost:9377/tabs/{tabId}/snapshot?userId=agent"
```

### MCP (tự động qua Claude Code)
Đã cấu hình trong `.claude/mcp.json` — 35 tools available qua MCP protocol.

## Use Cases — Binh Pháp 反間

| Tình huống | Giải pháp |
|-----------|-----------|
| Site chặn Cloudflare/Akamai | Camofox bypass bot detection |
| Scrape X/Twitter, Amazon, LinkedIn | Camofox + session isolation |
| reCAPTCHA challenge | Camofox anti-fingerprint |
| Playwright bị block | Camofox thay thế (Firefox-based) |
| Multi-account browsing | Session isolation per userId |

## Cấu Hình

| Variable | Giá trị | Mô tả |
|----------|---------|-------|
| `CAMOFOX_PORT` | `9377` | Server port |
| `CAMOFOX_HEADLESS` | `true` | Headless mode |
| `MAX_SESSIONS` | `50` | Max concurrent sessions |
| `BROWSER_IDLE_TIMEOUT_MS` | `300000` | Auto-kill sau 5 phút idle |

## Bug Fix

- Fix `setup.sh`: `npm init -y` fail vì tên dir `.camofox-browser` không hợp lệ cho npm → thay bằng explicit `package.json` với tên `camofox-server`.

## Files Modified

- `.claude/mcp.json` — thêm camofox MCP entry
- `.claude/skills/camofox-browser/scripts/setup.sh` — fix npm init bug
- `.claude/skills/camofox-browser/` — installed from yelban/camofox-browser-skills
