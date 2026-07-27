---
description: "💡 Ask AI — trả lời câu hỏi kỹ thuật bằng phân tích chuyên sâu, lập kế hoạch, hoặc định tuyến ý định Tiếng Việt/Tiếng Anh sang đúng lệnh mekong. Supports natural language command routing in Vietnamese and English."
argument-hint: "[technical-question|vietnamese-intent|english-intent]"
allowed-tools: Bash, Read, Agent
---
# /ask — NL Ask Router / Bộ định tuyến hỏi đáp ngôn ngữ tự nhiên

Trả lời câu hỏi kỹ thuật, thiết kế giải pháp, lập kế hoạch, hoặc định tuyến ý định tự do sang lệnh mekong phù hợp.

## Mục đích / Purpose
- Trả lời câu hỏi kỹ thuật với phân tích chuyên sâu
- Định tuyến tự động ý định Tiếng Việt/Tiếng Anh sang command mekong phù hợp (theo bảng từ khóa)
- Nếu không khớp từ khóa, fallback sang LLM plan (hành vi cũ — backward-compatible)
- Trả lời câu hỏi liên quan đến codebase hoặc task

## Cách dùng / Usage

Tiếng Việt (Vietnamese):
```bash
/ask "tạo landing page cho sản phẩm X"       → chuyển đến /cook
/ask "phân tích tài chính tháng 6"           → chuyển đến finance/analytics
/ask "lập kế hoạch marketing Q3"             → chuyển đến /plan
/ask "sửa lỗi thanh toán"                    → chuyển đến /fix
/ask "báo cáo so sánh MicroPython và CircuitPython" → trả lời chuyên sâu (LLM)
```

English:
```bash
/ask "create landing page for product X"     → routed to matching command
/ask "analyze financial data for June"       → routed to analytics/finance
/ask "plan marketing strategy Q3"            → routed to /plan
/ask "fix payment error"                     → routed to /fix
/ask "compare MicroPython vs CircuitPython"  → expert LLM answer (plan mode)
```

## Quy tắc định tuyến / Routing Rules

**Quy tắc chính / Primary rules:**
1. **Đầu tiên — Keyword matching**: Kiểm tra bảng từ khóa VI+EN bên dưới. Nếu khớp, gọi đúng command tương ứng.
2. **Thứ hai — LLM routing fallback**: Nếu không khớp keyword, để routing layer thực hiện LLM classification (đã được xử lý sẵn trong code).
3. **Cuối cùng — Expert answer**: Nếu là câu hỏi kiến trúc/kỹ thuật thuần túy không liên quan command nào → trả lời với phân tích chuyên sâu.

**Không bao giờ:**
- Gọi command chưa biết/không tồn tại trong danh sách `.claude/commands/`
- Giới thiệu keyword không có trong bảng bên dưới nếu hệ thống không gán đúng routing
- Xóa/giấu lệnh cũ — backward compatibility là bắt buộc

## Bảng từ khóa định tuyến / Routing Keyword Table

| Mục đích / Goal | Từ khóa Tiếng Việt (VI) | Từ khóa Tiếng Anh (EN) | Command mục tiêu |
|---|---|---|---|
| Build / Code / Lập trình | code, lập trình, viết code, xây dựng, triển khai code | code, build, implement, develop, write code | /cook |
| Debug / Sửa lỗi | sửa lỗi, sửa bug, lỗi, hỏng, không chạy | fix, debug, bug, broken, error, issue | /fix |
| Test / Kiểm thử | viết test, viết unit test, chạy test | test, unit test, integration test, write test | /test |
| Plan / Lập kế hoạch | lập kế hoạch, lên kế hoạch, tạo kế hoạch, tạo bài | plan, create plan, build plan, roadmap | /plan |
| Brainstorm / Gợi ý | brainstorm, động não, gợi ý ý tưởng, ý tưởng | brainstorm, idea, ideate, brain dump | /brainstorm |
| Deploy / Triển khai | triển khai, đưa lên production, push | deploy, release, ship, push to prod | deploy |
| Docs / Tài liệu | tạo tài liệu, viết tài liệu | docs, document, doc, readme | /docs |
| Analytics / Phân tích | phân tích dữ liệu, phân tích data | analyze data, analytics, data analysis | analytics-report |
| Security scan | quét bảo mật, kiểm tra bảo mật | security scan, security audit, security review | /security-scan |
| Audit / Kiểm toán | kiểm toán, audit, compliance | audit, compliance, SOC2, internal audit | /audit-compliance |

**Ghi chú:**
- **Tiếng Việt ưu tiên trước**, sau đó Tiếng Anh (theo thứ tự trong bảng).
- **Rewrite for generic requests**: Nếu request KHÔNG nằm trong bảng (ví dụ: "so sánh X và Y"), trả lời bằng LLM với phân tích chuyên sâu.

## Quy trình thực thi / Execution Flow

```
User input
│
▼
🔍 Keyword matching (route_ask())
│
├── Match found ──▶ _exec_subcommand() ──▶ python3 -m src.main <command> [args]
│
└── No match ────▶ LLM planning (RecipePlanner) ──▶ Expert answer
```

## Lưu ý / Notes
- **Backward compatible**: Nếu không khớp từ khóa, /ask vẫn hoạt động như cũ (plan-only alias). Không thay đổi behavior cũ.
- **Keywords dùng fnmatch heuristics**: prefix `*` = hậu tố; prefix `*` = tiền tố; không có wildcard = chứa nguyên văn.
- Bilingual là bắt buộc — mọi output cho user phải có cả VI và EN.
