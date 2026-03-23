---
title: "Tôi xây 342 AI commands trong 3 tháng — Câu chuyện OpenClaw"
description: "Câu chuyện một developer solo xây dựng hệ thống 342 AI commands vận hành doanh nghiệp tự động trên M1 Max, Cloudflare Workers, và Claude Code CLI."
date: "2026-03-23"
author: "OpenClaw Founder"
tags: ["founder-story", "AI", "mekong-cli", "cloudflare", "devlog"]
---

## Bắt đầu từ một câu hỏi điên rồ

"AI có thể vận hành một công ty không?"

Tháng 12 năm 2025, tôi ngồi một mình với chiếc MacBook M1 Max 64GB và một ý tưởng mà nhiều người sẽ coi là không tưởng. Không team. Không investor. Chỉ có code, terminal, và một AI đối tác.

Ba tháng sau, **OpenClaw** ra đời — một hệ thống 342 AI commands có thể vận hành doanh nghiệp từ chiến lược đến kỹ thuật.

---

## Tại sao 342 commands?

Không phải ngẫu nhiên. Khi phân tích một doanh nghiệp thực sự, tôi nhận ra có **6 tầng vận hành**:

- **👑 Founder** — Chiến lược, gọi vốn, OKR, đàm phán
- **💼 Business** — Sales, marketing, tài chính, nhân sự
- **🎯 Product** — Lập kế hoạch, sprint, roadmap
- **⚙️ Engineering** — Code, test, deploy, review
- **🔧 Ops** — Health check, security, audit
- **🏯 Studio** — VC ops, dealflow, venture

Mỗi tầng cần một bộ lệnh riêng. Tổng cộng 342 commands — không thừa, không thiếu.

---

## Stack thực chiến trên M1 Max

Cỗ máy chính là M1 Max với 64GB RAM. Lý do? Local inference với **MLX** cho phép tôi chạy mô hình 32B parameters ngay trên máy, không phụ thuộc cloud, không lo cost khi iterate nhanh.

```
MLX (primary)  → 16 tokens/s @ port 11435
Ollama (backup) → 11 tokens/s @ port 11434
Model: qwen2.5-coder:32b
```

Nhưng để scale production, tôi cần infrastructure không tốn tiền. Câu trả lời: **Cloudflare Workers**.

---

## Cloudflare-first architecture

Toàn bộ hệ thống chạy trên 3 layer Cloudflare:

| Layer | Platform | Chi phí |
|-------|----------|---------|
| Frontend | Cloudflare Pages | $0 |
| Edge API | Cloudflare Workers | $0 |
| Backend + DB | Workers + D1 + KV + R2 | $0 |

Khi bạn là solo dev, mỗi đồng chi phí đều là máu. Cloudflare Workers cho phép tôi deploy edge functions toàn cầu ở latency <50ms mà không cần trả một xu cho server idle time.

---

## Vòng lặp phát triển: PEV Engine

Sau nhiều tuần thất bại với các kiến trúc phức tạp, tôi đúc kết về một vòng lặp đơn giản:

**Plan → Execute → Verify**

```
Planner → phân tích task, tạo subtasks
Executor → chạy shell/LLM/API calls
Verifier → kiểm tra chất lượng, rollback nếu fail
```

Đây là trái tim của OpenClaw. Mọi command đều đi qua PEV Engine. Nếu Verifier thất bại, hệ thống tự rollback và thử lại với strategy khác.

---

## Khoảnh khắc "aha"

Tuần thứ 6, tôi chạy thử lệnh `/annual` — tạo báo cáo thường niên cho một startup fictitious. Trong 4 phút, AI tạo ra:

- Phân tích thị trường 15 trang
- Financial projections 3 năm
- Risk assessment matrix
- Slide deck 20 trang

Tôi ngồi nhìn màn hình, không nói được gì trong 5 phút.

**Đây là khoảnh khắc tôi biết mình đang xây đúng thứ.**

---

## Bài học cho các solo founder

1. **YAGNI nghiêm túc** — Đừng build feature chưa cần. 342 commands được thêm vào từng bước, không phải một lúc.
2. **$0 infrastructure là có thể** — Cloudflare Workers + D1 đủ cho MVP production.
3. **AI là đồng đội, không phải công cụ** — Treat Claude Code CLI như một senior engineer trong team.
4. **Velocity > Perfection** — Ship, measure, iterate. Ba tháng thay vì ba năm.

---

## Tiếp theo là gì?

OpenClaw đang mở cửa cho **early adopters**. Nếu bạn là founder, CTO, hoặc solo dev đang muốn vận hành doanh nghiệp với sức mạnh của AI — đây là thời điểm.

**Starter plan $49/tháng, 200 credits, 14 ngày miễn phí.**

Không cần thẻ tín dụng để bắt đầu.

---

*Câu chuyện còn tiếp. Theo dõi blog để nhận cập nhật về hành trình xây dựng OpenClaw.*
