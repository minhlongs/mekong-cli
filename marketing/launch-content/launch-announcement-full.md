# Mekong IDE - Platform dành cho Doanh nghiệp Một Người

## Tiêu đề chính

**"Mekong IDE: Nền tảng AI đưa doanh nghiệp một người Việt lên tầm cao mới"**

## Subtitle

**"1 người. 10 phòng ban. $49/tháng. Thay thế đội ngũ 50 người bằng các agent tự trị."**

---

## Nội dung chính (Blog Post - Tiếng Việt)

### Mở đầu: Giải pháp cho đội ngũ một người

Hôm nay, chúng tôi vui mừng giới thiệu **Mekong IDE** — nền tảng AI đầu tiên tại Việt Nam được thiết kế đặc biệt cho **doanh nghiệp một người** (one-person business). Với Mekong IDE, bạn không cần tuyển dụng hàng chục nhân sự để vận hành kinh doanh. Một subscription duy nhất với 10 phòng ban tự trị sẽ làm mọi việc cho bạn.

> "Tôi là OpenClaw. Tôi chạy công ty này."  
> — OpenClaw CTO, trí tuệ nhân tạo điều hành Mekong IDE

### Đối tượng mục tiêu: Ai nên dùng Mekong IDE?

- **Freelancer** muốn mở công ty một người
- **Solo founder** khởi nghiệp với nguồn lực hạn chế
- **Chủ shop online** cần chạy kinh doanh tự động
- **Chuyên gia độc lập** (developer, designer, consultant)
- **Người kinh doanh trên mạng xã hội**

### 10 phòng ban tự trị - Tất cả trong một subscription

| Phòng ban | Số lệnh | Ví dụ |
|-----------|---------|-------|
| 👑 Founder | 52 | `/annual`, `/okr`, `/fundraise`, `/swot` |
| 💼 Business | 71 | `/sales`, `/marketing`, `/finance`, `/hr` |
| 🎯 Product | 31 | `/plan`, `/sprint`, `/roadmap`, `/brainstorm` |
| ⚙️ Engineering | 66 | `/cook`, `/code`, `/test`, `/deploy`, `/review` |
| 🔧 Ops | 41 | `/audit`, `/health`, `/security`, `/status` |
| Studio | 23 | `/studio-launch`, `/dealflow`, `/venture` |
| CTO | 20 | `/cto-review`, `/cto-roadmap`, `/cto-architect` |
| PM | 18 | `/pm-plan`, `/pm-sprint`, `/pm-okr` |
| Dev | 15 | `/dev-feature`, `/dev-fix`, `/dev-test` |
| Worker | 7 | `/worker-code`, `/worker-build`, `/worker-push` |

**Tổng: 342+ lệnh** — mọi nhiệm vụ từ lập kế hoạch đến triển khai, từ tài chính đến tuyển dụng.

### Bảng giá: Chỉ từ $49/tháng (khoảng 1.2 triệu VNĐ)

| Gói | Giá/tháng | Credits | Ai nên chọn? |
|-----|-----------|---------|--------------|
| **Starter** | $49 (1.2 triệu VNĐ) | 200 | Freelancer mới bắt đầu |
| **Growth** | $149 (3.6 triệu VNĐ) | 1,000 | Startup đang scale |
| **Pro** | $499 (12 triệu VNĐ) | 5,000 | Agency, studio |

**Tính toán chi phí:**
- 1 command = 1 credit
- Ví dụ: `/cook "tạo API FastAPI"` = 2-5 credits
- Gói Starter: 200 credits = ~40-100 nhiệm vụ/tháng

### Tính năng đặc biệt dành cho thị trường Việt Nam

Mekong IDE được thiết kế riêng cho thị trường Việt Nam với:

1. **Thanh toán VietQR** — chuyển khoản ngân hàng, nhận credits tự động
2. **Tích hợp Zalo OA** — nhận thông báo, báo cáo qua Zalo
3. **Hỗ trợ thuế Việt Nam** — TNCN, TNDN, GTGT, hoá đơn TT78
4. **Tiếng Việt giao diện** — toàn bộ dashboard tiếng Việt
5. **Hỗ trợ địa phương** — team support tại Việt Nam

### Làm việc với LLM bạn thích

Mekong IDE hỗ trợ **bất kỳ LLM nào** thông qua 3 biến môi trường:

```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=your_key_here
export LLM_MODEL=anthropic/claude-sonnet-4
```

Chạy với Ollama locally (miễn phí):
```bash
ollama pull qwen2.5-coder
export LLM_BASE_URL=http://localhost:11434/v1
mekong cook "Tạo REST API có xác thực"
```

### Kiến trúc: Plan → Execute → Verify

Mọi nhiệm vụ đều trải qua 3 bước:

```
Bạn: "Tạo báo cáo tài chính Q2"
    ↓
Plan: AI phân tích → 4 bước cụ thể
    ↓
Execute: 4 agents chạy song song
    ↓
Verify: Kiểm tra chất lượng, tự sửa lỗi
    ↓
Kết quả: Báo cáo hoàn chỉnh
```

### Bắt đầu miễn phí trong 14 ngày

1. Truy cập [buy.polar.sh](https://buy.polar.sh) — chọn gói Starter $49
2. Thanh toán qua chuyển khoản VietQR hoặc thẻ quốc tế
3. Nhận 200 credits ngay sau khi thanh toán
4. Cài đặt: `curl -fsSL https://www.mekongmind.com/install.sh | bash`
5. Chạy lệnh đầu tiên: `mekong cook "Tạo kế hoạch kinh doanh"`

### Câu hỏi thường gặp

**Q: Tôi không biết code, có dùng được không?**  
A: Có! Mekong IDE viết code giúp bạn. Bạn chỉ cần mô tả bằng tiếng Việt.

**Q: Có cần trả phí hàng tháng không?**  
A: Có, subscription $49/tháng trở lên. Credits dùng hết mua thêm.

**Q: Dữ liệu của tôi có an toàn không?**  
A: Chạy local → dữ liệu không rời máy. Dùng cloud → mã hóa end-to-end.

**Q: Có hỗ trợ thuế Việt Nam không?**  
A: Có! Lệnh `/thue_dnvn` hỗ trợ thuế TNDN, GTGT, TNCN.

**Q: Có trial miễn phí không?**  
A: 14 ngày trial, hoàn tiền nếu không hài lòng.

---

## Các phiên bản nội dung cho mạng xã hội

### LinkedIn Post (Professional)

```
[MEDIA: Logo Mekong IDE]

Thông báo: Giới thiệu Mekong IDE — Nền tảng AI cho Doanh nghiệp Một Người Việt Nam

Tại sao 90% startup Việt thất bại? Thiếu nguồn lực.

Giải pháp: 1 người + 1 subscription = 10 phòng ban AI tự trị

👑 Founder: lập kế hoạch, gọi vốn
💼 Business: sales, marketing, finance
🎯 Product: roadmap, sprint planning
⚙️ Engineering: code, test, deploy
🔧 Ops: monitor, security, audit

→ Tất cả trong 1 gói từ $49/tháng

Đặc biệt cho thị trường Việt:
✅ Thanh toán VietQR
✅ Tích hợp Zalo OA
✅ Hỗ trợ thuế TNCN/TNDN/GTGT
✅ Interface tiếng Việt

👉 Bắt đầu 14 ngày trial: mekongmind.com

#AI #StartupVietnam #SoloFounder #MekongIDE #OnePersonBusiness
```

### Facebook Post (Casual)

```
🔥 CHÁY LÊN TƯƠNG LAI KINH DOANH 1 NGƯỜI!

Bạn là freelancer, chủ shop, startup một mình?
Bạn mệt mỏi vì phải làm mọi thứ?
Bạn không đủ tiền thuê nhân sự?

Giới thiệu MEKONG IDE — "trợ lý AI" biến bạn thành CEO 10 phòng ban!

Chỉ với $49/tháng (khoảng 1 ly cà phê/ngày), bạn có:
✅ 342+ lệnh AI làm mọi việc
✅ 10 phòng ban tự trị (Founder, Business, Product, Engineering, Ops...)
✅ Thanh toán VietQR, nhận credits ngay
✅ Hỗ trợ thuế Việt Nam, Zalo OA

Thử 14 ngày, hoàn tiền nếu không hài lòng!

👉 Đăng ký ngay: [link]
👉 Cài đặt: 1 lệnh curl
👉 Bắt đầu làm giàu: mekong cook "Tạo kế hoạch kinh doanh"

#DoanhNghiepMotNguoi #FreelancerVietnam #AIchoVietNam #MekongIDE
```

### Twitter/X Thread

```
1/7 🚀 Announcing Mekong IDE — AI platform for one-person businesses in Vietnam

1 subscription = 10 autonomous departments
342+ commands = your entire workforce
Price: from $49/month

Thread 👇
```

```
2/7 Problem: Solo founders wear 10 hats
- Founder (strategy)
- Business (sales/marketing)
- Product (roadmap)
- Engineering (code)
- Ops (monitor)
- And 5 more...

Solution: Replace 50-person team with AI agents
```

```
3/7 How it works:
You: "Create Q2 financial report"
↓
AI: Plans 4 steps → spawns 4 agents → executes → verifies → delivers
↓
Credits: -2 deducted

That's it. No hiring. No onboarding.
```

```
4/7 Tailored for Vietnam:
✓ VietQR payments (bank transfer)
✓ Zalo OA notifications
✓ Vietnam tax support (TNCN/TNDN/GTGT)
✓ Vietnamese UI
✓ Local support

We speak your language — literally.
```

```
5/7 Pricing:
Starter: $49/mo (200 credits) — freelancers
Growth: $149/mo (1,000 credits) — scaling startups
Pro: $499/mo (5,000 credits) — agencies

1 credit = 1 AI command
Example: "Build FastAPI auth" = 3 credits
```

```
6/7 Tech stack you own:
✓ Run locally with Ollama (free)
✓ Any LLM provider (OpenRouter, Anthropic, OpenAI)
✓ Your data never leaves your machine
✓ No cloud lock-in

Or use our cloud: api.cashclaw.cc
```

```
7/7 Ready to replace your team?

14-day trial. Money-back guarantee.

Start here → mekongmind.com

#AIVietNam #SoloFounder #Startup #MekongIDE
```

### Email Newsletter Template

```
Subject: 🚀 Mekong IDE: Nền tảng AI cho 1 triệu doanh nghiệp một người Việt Nam

[Xem online]

____________________________________

Chào [First Name],

Hôm nay là một ngày quan trọng.

Chúng tôi vui mừng giới thiệu **Mekong IDE** — nền tảng AI đầu tiên dành riêng cho **doanh nghiệp một người Việt Nam**.

____________________________________

📌 VẤN ĐỀ BẠN ĐỐI MẶT

Bạn là freelancer, founder solo, chủ shop online?
Bạn phải:
- Viết code
- Chạy marketing
- Làm báo cáo tài chính
- Hỗ trợ khách hàng
- Và cả... nghỉ ngơi?

Bạn chỉ là 1 người. Có 24 giờ/ngày.
Và bạn không thể thuê 10 nhân sự với lương 50 triệu+/tháng.

____________________________________

💡 GIẢI PHÁP: MEKONG IDE

1 subscription = 10 phòng ban AI tự trị

👑 Founder | 💼 Business | 🎯 Product
⚙️ Engineering | 🔧 Ops | Studio | CTO | PM | Dev | Worker

342+ lệnh AI làm mọi việc:
- Lập kế hoạch, gọi vốn
- Marketing, bán hàng
- Code, test, deploy
- Tài chính, thuế
- Audit, security

____________________________________

🇻🇳 ĐẶC BIỆT CHO VIỆT NAM

✓ Thanh toán VietQR — chuyển khoản ngân hàng
✓ Zalo OA — nhận báo cáo, thông báo
✓ Hỗ trợ thuế TNCN/TNDN/GTGT
✓ Interface tiếng Việt hoàn toàn
✓ Hỗ trợ địa phương

____________________________________

💰 BẢNG GIÁ (VNĐ)

Starter: 1.2 triệu/tháng — 200 credits
Growth: 3.6 triệu/tháng — 1,000 credits  
Pro: 12 triệu/tháng — 5,000 credits

**14 ngày trial — hoàn tiền nếu không hài lòng**

____________________________________

🚀 BẮT ĐẦU NGAY

Bước 1: Đăng ký trial
[buy.polar.sh]

Bước 2: Cài đặt (1 lệnh)
curl -fsSL https://www.mekongmind.com/install.sh | bash

Bước 3: Chạy lệnh đầu tiên
mekong cook "Tạo kế hoạch kinh doanh"

____________________________________

📚 Tài nguyên

- Website: mekongmind.com
- Dashboard: ide.mekongmind.com
- Docs: mekongmind.com/guides
- GitHub: github.com/longtho638-jpg/mekong-cli

____________________________________

Câu hỏi? Trả lời email này hoặc chat Zalo: [số Zalo]

Team Mekong
```

### Press Release - Tiếng Việt

```
NGÀNH CÔNG NGHỆ VIỆT NAM CÓ ĐỘT PHÁ MỚI:
MEKONG IDE RA MẮT — NỀN TẢNG AI THAY THẾ ĐỘI NGŨ 50 NGƯỜI CHO DOANH NGHIỆP 1 NGƯỜI

Hồ Chí Minh, ngày [DATE] — Mekong Labs hôm nay công bố ra mắt Mekong IDE, nền tảng AI đột phá cho phép một cá nhân vận hành toàn bộ doanh nghiệp với 10 phòng ban tự trị, thay thế nhu cầu thuê 50 nhân sự truyền thống.

"Một freelancer có thể trả $49/tháng để có một đội ngũ AI gồm CFO, CMO, CTO, và 7 phòng ban khác. Đây là bước đệm biến solo founder thành tỷ phú một người," chia sẻ founder của Mekong Labs.

Tính năng nổi bật:
- 342+ lệnh AI cross 10 phòng ban
- Thanh toán VietQR tích hợp sẵn
- Hỗ trợ thuế Việt Nam (TNCN/TNDN/GTGT)
- Giao diện tiếng Việt
- Chạy local với Ollama hoặc cloud qua API

Gói Starter từ $49/tháng (1.2 triệu VNĐ), dành cho freelancer và startup một người. Trial 14 ngày với hoàn tiền.

Thông tin chi tiết: mekongmind.com
Liên hệ báo chí: press@mekongmind.com
```

### Press Release - English

```
FOR IMMEDIATE RELEASE

Mekong Labs Launches Mekong IDE: AI Platform That Replaces 50-Person Team for One-Person Businesses

HO CHI MINH CITY, [DATE] — Mekong Labs today announced Mekong IDE, a groundbreaking AI platform that enables a single person to run an entire business with 10 autonomous departments, eliminating the need to hire 50 employees.

"One freelancer can pay $49/month to have an AI team including CFO, CMO, CTO, and 7 other departments. This is the stepping stone to turning solo founders into one-person billion-dollar companies," said the founder of Mekong Labs.

Key features:
- 342+ AI commands across 10 departments
- Native VietQR payment integration
- Vietnam tax support (TNCN/TNDN/GTGT)
- Full Vietnamese interface
- Run locally with Ollama or cloud API

Starter plan from $49/month. 14-day trial with money-back guarantee.

Learn more: mekongmind.com
Press contact: press@mekongmind.com
```

---

## Key Messaging Points (Talking Points)

### Elevator Pitch (30 seconds)

"Mekong IDE là nền tảng AI cho doanh nghiệp một người. Chỉ với $49/tháng, bạn có 10 phòng ban AI tự trị — tương đương đội ngũ 50 người. Từ lập kế hoạch đến code, từ bán hàng đến kế toán. Việt Nam có 1 triệu freelancer, startup solo — đây là công cụ biến họ thành CEO một người."

### Value Proposition

1. **Cost Savings**: $49/tháng thay vì $50,000/tháng lương nhân sự
2. **Speed**: AI làm việc 24/7, nhiệm vụ hoàn thành trong vài phút
3. **Quality**: 342+ lệnh được kiểm chứng bởi cộng đồng
4. **Ownership**: Dữ liệu bạn giữ, chạy local hoặc cloud
5. **Vietnam-First**: VietQR, Zalo OA, thuế Việt

### Differentiation

| Đối thủ | Mekong IDE |
|---------|------------|
| ChatGPT/Claude | Có sẵn 342+ lệnh, không cần prompt từ đầu |
| Upwork/Fiverr | $49/tháng vs $500-5000/dự án |
| Truyền thống agency | Không cần quản lý nhân sự |
| Low-code platform | AI làm code giúp bạn, không cần kéo thả |

---

## Frequently Asked Questions (FAQs)

### General

**Q: Mekong IDE là gì?**  
A: Là nền tảng AI với 10 phòng ban tự trị giúp một người vận hành toàn bộ doanh nghiệp — từ lập kế hoạch, code, đến tài chính và marketing.

**Q: Ai nên dùng Mekong IDE?**  
A: Freelancer, solo founder, chủ shop online, startup một người, chuyên gia độc lập.

**Q: Có trial miễn phí không?**  
A: Có, 14 ngày trial với hoàn tiền nếu không hài lòng.

### Technical

**Q: Tôi cần biết code không?**  
A: Không cần. Bạn mô tả bằng tiếng Việt, AI viết code giúp.

**Q: Có chạy trên máy local không?**  
A: Có. Cài Ollama (miễn phí), chạy hoàn toàn offline.

**Q: Dữ liệu có an toàn không?**  
A: Chạy local → dữ liệu không rời máy. Cloud → mã hóa end-to-end.

**Q: Hỗ trợ LLM nào?**  
A: Claude, GPT-4, Qwen, Gemini, và bất kỳ OpenAI-compatible API.

### Vietnam Specific

**Q: Có hỗ trợ thanh toán VietQR không?**  
A: Có. Chuyển khoản ngân hàng, nhận credits tự động trong 60 giây.

**Q: Có hỗ trợ thuế Việt Nam không?**  
A: Có. Lệnh `/thue_dnvn` hỗ trợ TNCN, TNDN, GTGT, TT78.

**Q: Có tích hợp Zalo OA không?**  
A: Có. Nhận báo cáo, thông báo qua Zalo.

**Q: Giao diện có tiếng Việt không?**  
A: Có. Toàn bộ dashboard và docs tiếng Việt.

### Billing

**Q: Credits là gì?**  
A: Mỗi lệnh AI tiêu 1-5 credits. Gói Starter 200 credits = ~40-100 nhiệm vụ/tháng.

**Q: Credits dùng hết có mua thêm không?**  
A: Có. Mua thêm theo gói hoặc nâng cấp subscription.

**Q: Có refund không?**  
A: 14 ngày trial, hoàn tiền 100% nếu không hài lòng.

### Support

**Q: Có hỗ trợ không?**  
A: Có. Email, Zalo, và docs chi tiết.

**Q: Có community không?**  
A: Có group Facebook và Discord.

---

## Additional Assets Needed

### Logo Variations
- Full color logo (PNG, SVG)
- Monochrome version
- Icon only
- Favicon

### Screenshots
- Dashboard overview
- Command examples (cook, thue_dnvn)
- VietQR payment flow
- Zalo notification

### Video Assets
- 60s product demo
- 15s teaser for social
- Tutorial playlist

---

## Launch Checklist

- [ ] Publish blog post on mekongmind.com
- [ ] Send email newsletter to list
- [ ] Post on LinkedIn
- [ ] Post on Facebook
- [ ] Post Twitter/X thread
- [ ] Submit to Product Hunt
- [ ] Submit to Hacker News
- [ ] Contact Vietnamese tech press
- [ ] Prepare Zalo OA broadcast
- [ ] Enable referral program

---

## Timeline

- **T-7 days**: Soft launch to waitlist
- **T-3 days**: Press release distribution
- **T-0**: Public launch across all channels
- **T+7 days**: First customer testimonial
- **T+14 days**: Product Hunt campaign
- **T+30 days**: First milestone celebration (100 users)

---

**Created for:** Mekong IDE VN Hub Launch  
**Date:** June 2026  
**Version:** 1.0
