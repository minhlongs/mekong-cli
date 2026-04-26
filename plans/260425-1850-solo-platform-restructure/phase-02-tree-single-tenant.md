# Phase 02: Cây (Tree — Single-Tenant Complete)

> **Ưu tiên:** HIGH — sau Phase 01  
> **Thời gian:** Tuần 3-4 | **Trạng thái:** ✅ COMPLETED  
> **Mục tiêu:** Single user có thể dùng toàn bộ platform
> **Completed:** 2026-04-25T18:45:00Z

## Điều kiện tiên quyết

- [x] Phase 01 hoàn chỉnh (seed/main.py E2E pass)
- [x] Ollama LIVE local

## Kiến trúc Tree

```
seed/ (Phase 01 giữ nguyên)     ← "Trái tim" 
  +
apps/api/                        ← FastAPI gateway (refactor từ existing)
  +
Telegram webhook                 ← Channel input
  +
outputs/ system                  ← Kết quả có cấu trúc
```

## Implementation Steps

### 2.1 CEO Agent Hoàn Chỉnh
- CEO có thể phân tích task phức tạp
- CEO tạo multi-step plan
- CEO giao việc cho nhiều agent con

### 2.2 Developer Agent + Tester Agent
- Developer viết code real (không mock)
- Tester verify output tự động
- Loop: Dev → Test fail → Dev fix → Test pass

### 2.3 Mission Control UI (minimal)
- Web page đơn giản: 1 input box + 1 output area
- Submit task → polling status → hiển thị kết quả
- Stack: simple HTML + htmx (không cần React)

### 2.4 Telegram Webhook
- Bot nhận lệnh từ Telegram
- Gọi `seed/main.py` → trả kết quả về chat
- Format: `/task Tạo landing page cho...`

### 2.5 E2E Test Scenarios
```
Test 1: "Viết script Python đọc CSV và tính tổng"
Test 2: "Tạo landing page cho dịch vụ AI coaching"
Test 3: "Tìm kiếm và tóm tắt 3 bài về RAG architecture"
```

## Files cần tạo/sửa

| File | Hành động |
|------|-----------|
| `apps/api/src/routes/task.py` | Sửa (add single-user task endpoint) |
| `apps/api/src/routes/status.py` | Sửa (polling endpoint) |
| `seed/agents/tester.py` | Tạo mới |
| `apps/web/simple-mission-control.html` | Tạo mới (static HTML) |
| `integrations/telegram_bot.py` | Tạo mới |

## Checklist

- [x] CEO Agent Hoàn Chỉnh
- [x] Developer Agent + Tester Agent
- [x] Mission Control UI (minimal)
- [x] Telegram Webhook
- [x] E2E Test Scenarios

## Success Criteria

```
1. User gõ Telegram: /task "Viết README cho dự án XYZ"
2. Bot reply: "Đang xử lý... job_id=abc"
3. Sau 30s: Bot gửi file README.md
4. File quality: CEO plan + Dev code + Tester verify
```

## Next Steps → Phase 03 (Forest/Multi-Tenant)
