---
name: gemini
description: "Control Gemini CLI with rate limiting and retry logic"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# Gemini Command

Điều khiển Gemini CLI thông qua Claude với rate limiting tự động.

## Quick Commands

```bash
# Hỏi Gemini
/gemini:ask "Explain async/await in JavaScript"

# Phân tích hình ảnh
/gemini:vision ./screenshot.png

# Code review
/gemini:code ./src/app.js

# Kiểm tra status
/gemini:status
```

## How It Works

Claude sẽ chạy Gemini CLI thay anh với:
- ✅ Rate limiting: 15 requests/minute
- ✅ Auto retry: Exponential backoff (2^n seconds)
- ✅ Error handling: Tự động xử lý lỗi 429

## Usage Examples

### Hỏi Câu Hỏi Text
// turbo
```bash
node .claude/scripts/gemini-bridge.cjs ask "What is the best practice for error handling in Node.js?"
```

### Phân Tích Hình Ảnh
// turbo
```bash
node .claude/scripts/gemini-bridge.cjs vision ./docs/architecture.png
```

### Code Review
// turbo
```bash
node .claude/scripts/gemini-bridge.cjs code ./src/api/auth.ts
```

### Kiểm Tra Rate Limit
// turbo
```bash
node .claude/scripts/gemini-bridge.cjs status
```

## Configuration

Có thể điều chỉnh trong `gemini-bridge.cjs`:

| Setting | Default | Mô tả |
|---------|---------|-------|
| `MAX_REQUESTS_PER_MINUTE` | 15 | Số request tối đa/phút |
| `MAX_RETRIES` | 3 | Số lần retry tối đa |
| `INITIAL_BACKOFF_MS` | 2000 | Delay ban đầu khi retry |

## 🏯 Binh Pháp

> **"Dụng Gián"** - Sử dụng Agent khác để mở rộng năng lực

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
