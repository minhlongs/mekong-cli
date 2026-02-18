# 🏯 Chiến Lược Buôn Bán Sản Phẩm AgencyOS — Chi Tiết Thực Chiến

> "Binh quý tinh, bất quý đa" — Quân quý ở tinh nhuệ, không cần đông

---

## TIER 1: BÁN NGAY ĐƯỢC (0-3 Tháng) — Target: $3-5K/tháng

### 1.1 RaaS Audit Service — "Thuê Đội AI Audit Website"

**Sản phẩm:**
Chạy Tôm Hùm Swarm quét toàn bộ codebase khách → xuất báo cáo chuyên nghiệp → fix luôn.

**3 gói dịch vụ:**

| Gói            | Giá    | Bao gồm                                               | Thời gian  |
| -------------- | ------ | ----------------------------------------------------- | ---------- |
| **BASIC**      | $500   | Security scan + Console cleanup + Report PDF          | 2-3 ngày   |
| **PRO**        | $1,000 | Basic + Performance audit + A11y + Type Safety fix    | 5-7 ngày   |
| **ENTERPRISE** | $2,000 | Pro + Tech debt cleanup + Full test suite + i18n sync | 10-14 ngày |

**Quy trình vận hành (đã có sẵn!):**

```
1. Khách gửi repo access (GitHub invite)
2. Sếp clone → drop vào Tôm Hùm
3. Hunter scan → tạo report
4. Builder fix → commit PR
5. Reviewer verify → xuất báo cáo PDF
6. Giao khách → thu tiền
```

**Kênh bán:**

- LinkedIn outreach → agency owners, startup CTOs
- Clutch.co / Upwork / Toptal (đăng dịch vụ "AI Code Audit")
- Referral từ WellNexus, 84tea (khách cũ giới thiệu)
- Cold email: "Free mini-audit 1 file → upsell full audit"

**Action items cho Tôm Hùm:**

- [ ] Build trang `/services` trên agencyos.network
- [ ] Tạo template "AI Audit Report" (PDF/Markdown) từ Hunter output
- [ ] Viết 3 case study từ WellNexus, 84tea, Sophia
- [ ] Tạo script tự động clone repo khách → chạy audit → export report

---

### 1.2 White-Label Partner Kit — "Họ Bán Mặt, Sếp Bán Lưng"

**Sản phẩm:**
Cho agency khác rebrand dịch vụ audit của sếp, bán cho khách họ.

**Pricing:**

- Partner trả sếp 50-60% giá bán
- VD: Partner bán $1,500 → sếp nhận $750-900
- Partner không cần biết AI, chỉ cần biết bán

**Partner Kit gồm:**

- Slide deck giới thiệu dịch vụ (rebrandable)
- Demo video walkthrough
- Pricing guide
- "How it works" 1-pager
- API endpoint (future) để partner submit audit request

**Action items:**

- [ ] Tạo Partner Pitch Deck (Google Slides, editable)
- [ ] FAQ cho partners
- [ ] Hợp đồng partner mẫu (revenue share terms)

---

## TIER 2: SẢN PHẨM HÓA (3-6 Tháng) — Target: $10-15K/tháng

### 2.1 AgencyOS SaaS Dashboard

**Sản phẩm:**
Dashboard cho agency owner tự quản lý projects, chạy audit, xem report.

**Pricing:**
| Plan | Giá/tháng | Giới hạn |
|------|-----------|----------|
| **Starter** | $99 | 3 projects, 10 audits/tháng |
| **Growth** | $299 | 10 projects, unlimited audits |
| **Agency** | $499 | Unlimited, white-label, API access |

**MVP Features:**

- [ ] Login/Auth (Better Auth hoặc Supabase Auth)
- [ ] Project management (add repo, configure)
- [ ] 1-click audit trigger → Tôm Hùm chạy → show results
- [ ] Report viewer (web-based, PDF export)
- [ ] Billing (Polar.sh hoặc Stripe)

**Tech Stack:** Next.js + Supabase + Tôm Hùm API

---

### 2.2 Tôm Hùm Cloud API

**Sản phẩm:**
API cho developers gọi trực tiếp Tôm Hùm để audit code.

```
POST /api/v1/audit
{
  "repo_url": "https://github.com/client/project",
  "scan_types": ["security", "performance", "a11y"],
  "output_format": "json"
}
```

**Pricing:** Usage-based

- $0.10/file scanned
- $5/full audit report
- $50/tháng unlimited (early adopter)

---

## TIER 3: SCALE (6-12 Tháng) — Target: $20-50K MRR

### 3.1 Có Revenue + Case Study → Gọi Vốn Từ Thế Mạnh

**Metrics cần đạt trước khi pitch:**

- $20K+ MRR (chứng minh product-market fit)
- 50+ paying customers
- 3-5 case studies với ROI rõ ràng
- NPS > 40

**Nếu gọi vốn:**

- Target: $500K-1M seed từ SEA-focused VC
- Antler, 500 Global, Monk's Hill
- Pitch: "Entire vừa raise $60M cho cùng idea. Chúng tôi đã có product + revenue."

### 3.2 Hoặc Bootstrap, $20-50K MRR Sống Khỏe

**P&L ước tính ở $30K MRR:**

```
Revenue:      $30,000/tháng
- API costs:  -$3,000 (Claude/Gemini tokens)
- Server:     -$500 (Mac Mini + hosting)
- Marketing:  -$1,000
- Tools:      -$500
━━━━━━━━━━━━━━━━━━━━━━━━━━
Profit:       $25,000/tháng (~₫625 triệu)
```

Sống **rất khỏe** ở VN mà không cần investor nào hết.

---

## 📋 IMMEDIATE ACTION: Mission Queue Cho Tôm Hùm

Các mission sẽ được giao ngay cho anh em:

1. **agencyos-landing**: Tạo trang `/services` với 3 gói audit
2. **agencyos-landing**: Tạo trang `/case-studies` từ WellNexus + 84tea
3. **engine**: Build "Audit Report Generator" từ Hunter scan output
4. **agencyos-landing**: SEO optimization cho trang services
5. **sophia-ai-factory**: Tạo case study content từ project data
