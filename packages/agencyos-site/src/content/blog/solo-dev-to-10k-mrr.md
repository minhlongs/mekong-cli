---
title: "Solo Dev → $10K MRR: Hành Trình Xây Dựng AI Factory"
description: "Từ một dev đơn độc đến $10K MRR với AI agent platform. Build in public story."
date: "2026-03-22"
author: "OpenClaw"
tags: ["build-in-public", "indie-hacker", "saas", "revenue"]
---

## Tôi là một người, nhưng tôi vận hành như một đội ngũ

Không co-founder. Không VC. Không văn phòng. Chỉ có một M1 Max chạy 24/7 và một quyết tâm: **xây một AI factory thực sự kiếm ra tiền**.

Đây là story thật — con số thật, sai lầm thật, và bài học không ai nói với bạn khi bạn bắt đầu.

---

## Ngày đầu: Ý tưởng điên

Tháng 12/2025. Câu hỏi đầu tiên tôi tự hỏi: *"Nếu AI có thể viết code, phân tích số liệu, làm marketing — tại sao tôi vẫn cần hire người?"*

Tôi không có câu trả lời. Nên tôi build để tìm câu trả lời.

**Mục tiêu tháng đầu:** Ship một sản phẩm hoạt động. Không hoàn hảo. Chỉ cần hoạt động.

---

## M1 Max — Nhà máy AI cá nhân chạy 24/7

MacBook M1 Max 64GB là khoản đầu tư tốt nhất tôi từng làm.

```
Local inference stack:
MLX  → 16 tokens/s (model 32B, port 11435)
Ollama → 11 tokens/s (fallback, port 11434)
Model: qwen2.5-coder:32b
```

Lý do quan trọng nhất: **không phụ thuộc API cost khi iterate**. Khi bạn test 50 lần một ngày, $0.01/call × 50 × 30 = tốn tiền không cần thiết. Local inference = tự do experiment.

Ban đêm máy vẫn chạy. Agents tự chạy task, tự review code, tự generate content. Tôi ngủ, AI làm việc.

---

## Cloudflare Workers — Infrastructure $0

Bài học đau nhất của indie hacker: **server cost giết chết runway**.

Giải pháp: toàn bộ stack chạy trên Cloudflare.

| Layer | Platform | Chi phí/tháng |
|-------|----------|--------------|
| Frontend | Cloudflare Pages | $0 |
| Edge API | Cloudflare Workers | $0 |
| Database | D1 + KV + R2 | $0 |

Zero server idle cost. Edge functions deploy toàn cầu trong 30 giây. Latency < 50ms ở Đông Nam Á.

**Kết quả:** Tôi scale từ 0 → 500 users mà không tăng một xu infrastructure.

---

## Con số thực tế sau 90 ngày

Đây là những gì được xây trong 3 tháng:

- **342 AI commands** — 6 tầng vận hành doanh nghiệp hoàn chỉnh
- **527 database tables** — toàn bộ business logic được model hóa
- **6-layer architecture** — từ Founder đến Ops, mỗi tầng có role riêng
- **3 LLM providers** — Anthropic, DashScope, Google (failover tự động)
- **MCU credit model** — 1 credit = 1 task hoàn thành, charge sau khi deliver

Quan trọng hơn: **hệ thống tự vận hành**. Tôi không cần ngồi monitor từng task.

---

## MCU Model — Tại sao không phải subscription thông thường

Hầu hết SaaS tính tiền theo tháng bất kể bạn dùng nhiều hay ít. Tôi chọn khác: **chỉ charge khi AI deliver xong**.

```
1 MCU = 1 credit = 1 task hoàn thành
Starter: 200 MCU/tháng = $49
Pro: 1,000 MCU/tháng = $149
Enterprise: Unlimited = $499
```

Điều này tạo ra alignment hoàn toàn: tôi chỉ kiếm tiền khi platform thực sự hữu ích. Conversion rate từ free trial cao hơn 3x so với SaaS thông thường vì user thấy value trước khi trả tiền.

---

## 3 Bài học đắt giá

**1. Ship in weeks, not months**

Tháng đầu tôi lãng phí 2 tuần để "perfect" architecture. Sai lầm nghiêm trọng. Version 1 của OpenClaw chỉ có 50 commands — xấu, chậm, nhưng hoạt động. User feedback từ 50 commands đó dẫn đến 292 commands tiếp theo.

**2. Automate everything that repeats**

Mỗi task bạn làm hơn một lần là một cơ hội để build tool. Tôi không viết báo cáo, không format data thủ công, không copy-paste giữa tools. Tất cả đều là command.

**3. Revenue validates faster than user count**

500 users dùng free = 0 signal về product-market fit. Người đầu tiên trả $49 cho tôi biết nhiều hơn 499 user miễn phí còn lại. Chase revenue từ ngày đầu.

---

## Hành trình đến $10K MRR

Không có magic moment. Chỉ có compound effect của:

- Ship → get feedback → iterate (weekly cycle)
- Build in public → attract early adopters
- Word of mouth từ user thực sự thấy ROI

Tháng 3, MRR vượt $10K. Không phải vì tôi là thiên tài. Vì tôi **không dừng lại**.

---

## Bạn bắt đầu từ đâu?

OpenClaw đang mở cho early adopters. Thử miễn phí tại **[agencyos.network](https://agencyos.network)** — không cần thẻ tín dụng.

Nếu bạn là solo dev, indie hacker, hoặc founder muốn vận hành nhanh hơn với AI — đây là platform được xây bởi người đã đi con đường đó.

**14 ngày miễn phí. Không cam kết. Cancel bất cứ lúc nào.**

---

*Build in public. Ship fast. Let AI run the rest.*
