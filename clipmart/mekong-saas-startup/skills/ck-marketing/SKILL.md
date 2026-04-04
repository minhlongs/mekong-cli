---
name: ck-marketing
description: "Marketing Constitution — universal marketing command for all projects"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# Marketing Constitution - Universal Marketing Command

> **HIẾN PHÁP MARKETING** - Áp dụng cho mọi dự án từ Antigravity IDE

## Cú Pháp

```
/marketing [task] [--location=LOCATION] [--business=BUSINESS_NAME]
```

## Tasks Chính

### 1. Bootstrap Marketing Plan

```
/marketing bootstrap --location="Sa Đéc, Đồng Tháp" --business="Cơm Ánh Dương"
```

Output:

- `plans/marketing/MARKETING_STRATEGY.md`
- `plans/marketing/SOCIAL_MEDIA_CONTENT_CALENDAR.md`
- `plans/marketing/PROMOTIONAL_CAMPAIGNS.md`
- `plans/marketing/MARKETING_ASSETS.md`
- `plans/marketing/SEO_LOCAL_MARKETING.md`
- `plans/marketing/METRICS_AND_KPIS.md`

### 2. Create Posts

```
/marketing posts [platform] [count]
```

Platforms: facebook, zalo, tiktok, instagram
Output: `marketing/content/posts/{platform}_posts.md`

### 3. Google My Business Setup

```
/marketing gmb --location="LOCATION"
```

Output: `marketing/gmb/business_profile.md`

### 4. Loyalty Program

```
/marketing loyalty
```

Output: `marketing/loyalty/discount_codes.md`

### 5. Print Materials

```
/marketing print [menu|flyer|banner]
```

Output: `marketing/print/{type}_text.md`

## Nguyên Tắc Cốt Lõi (ĐIỀU 50 MARKETING)

### 🎯 Mục Tiêu

- Tạo content **READY-TO-USE** (copy-paste ngay)
- Localize đúng **địa điểm cụ thể**
- **Hashtags** phù hợp địa phương
- **SEO keywords** cho local search

### 📍 Localization Rules

```yaml
# PHẢI thay đổi theo địa điểm:
- City/Province name
- Quận → Phường (nếu tỉnh nhỏ)
- Local landmarks
- Local Facebook groups
- TikTok hashtags
- SEO keywords
```

### 📊 KPIs Mặc Định

| Metric         | Month 1 | Month 3 | Month 6 |
| -------------- | ------- | ------- | ------- |
| Orders         | 50-100  | 150-200 | 300+    |
| FB Followers   | 500     | 2,000   | 5,000   |
| Google Reviews | 10      | 30      | 100     |
| Repeat Rate    | 15%     | 25%     | 3

[Full documentation at agencyos.network]

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
