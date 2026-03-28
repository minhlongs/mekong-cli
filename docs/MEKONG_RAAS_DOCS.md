# Mekong Agency — RaaS Platform
## Full Product Documentation v1.0

> **Codename:** AgencyOS 2026  
> **Stack:** Vanilla JS · Supabase · Cloudflare Pages · Google Gemini AI  
> **Phạm vi:** Hệ thống Retail-as-a-Service cho sản phẩm OCOP vùng Đồng bằng sông Cửu Long  
> **Last updated:** March 2026

---

## Mục lục

1. [Tổng quan sản phẩm](#1-tổng-quan-sản-phẩm)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Database Schema](#3-database-schema)
4. [Authentication & RBAC](#4-authentication--rbac)
5. [Module 1 — Marketplace Onboarding](#5-module-1--marketplace-onboarding-as-a-service)
6. [Module 2 — Brand & Packaging](#6-module-2--brand--packaging-as-a-service)
7. [Module 3 — Certification Hub](#7-module-3--certification-as-a-service)
8. [Module 4 — Logistics & Fulfillment](#8-module-4--logistics--fulfillment-as-a-service)
9. [Module 5 — Content Commerce](#9-module-5--content-commerce-as-a-service)
10. [Module 6 — Analytics & AI Commerce](#10-module-6--analytics--ai-commerce-as-a-service)
11. [AI Layer — Gemini Integration](#11-ai-layer--gemini-integration)
12. [API Reference](#12-api-reference)
13. [Frontend Architecture](#13-frontend-architecture)
14. [Deployment & DevOps](#14-deployment--devops)
15. [Business Model & Pricing](#15-business-model--pricing)
16. [Lộ trình phát triển](#16-lộ-trình-phát-triển)
17. [Glossary](#17-glossary)

---

## 1. Tổng quan sản phẩm

### 1.1 Vision

Mekong Agency là nền tảng **Retail-as-a-Service (RaaS)** đầu tiên tại Đồng bằng sông Cửu Long, được thiết kế để giải quyết toàn bộ chuỗi rào cản khiến hơn **3,900 sản phẩm OCOP** của vùng chưa tiếp cận được thị trường quốc tế.

Thay vì bán công cụ (tool), Mekong Agency bán **kết quả** (result): merchant OCOP không cần biết Amazon, không cần có designer, không cần hiểu logistics quốc tế — agency làm tất cả và thu phí theo doanh thu.

### 1.2 Problem Statement

| Rào cản | Tỷ lệ ảnh hưởng | Hậu quả |
|---------|----------------|---------|
| Chi phí logistics 30% giá thành | 100% merchant | Mất cạnh tranh vs Thái Lan, Trung Quốc |
| Không có chứng nhận quốc tế (GlobalG.A.P., HACCP) | ~85% HTX nhỏ | Không xuất được EU, Nhật, Mỹ |
| Bao bì không đạt chuẩn sàn quốc tế | ~90% OCOP 3 sao | Bị từ chối listing Amazon/Alibaba |
| Không biết tạo/vận hành store online | ~95% HTX | Bỏ qua kênh e-commerce |
| Sản xuất nhỏ lẻ, không đủ volume | ~70% | Không đàm phán được logistics tốt |
| Thiếu content số (ảnh, video, mô tả EN/ZH) | ~98% OCOP | Listing nghèo nàn, không ra đơn |

### 1.3 Solution — 6 RaaS Modules

```
┌─────────────────────────────────────────────────────────────┐
│                    MEKONG AGENCY RAAS PLATFORM              │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │  M1           │  │  M2           │  │  M3           │  │
│  │  Marketplace  │  │  Brand &      │  │  Certification│  │
│  │  Onboarding   │  │  Packaging    │  │  Hub          │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │  M4           │  │  M5           │  │  M6           │  │
│  │  Logistics &  │  │  Content      │  │  Analytics &  │  │
│  │  Fulfillment  │  │  Commerce     │  │  AI Commerce  │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  │
│                                                             │
│  ════════════════ AgencyOS Core Platform ═════════════════  │
│   CRM · Campaign Manager · Finance · Client Portal · AI    │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 Target Users

| Role | Mô tả | Nhu cầu chính |
|------|--------|---------------|
| **Agency Admin** | Team Mekong Agency | Quản lý toàn bộ merchants, campaigns, finance |
| **Province Manager** | Sở NN&PTNT tỉnh (B2G) | Theo dõi portfolio OCOP tỉnh, báo cáo KPI |
| **Merchant** | HTX / cơ sở OCOP | Theo dõi store, đơn hàng, doanh thu |
| **Content Creator** | Nội dung viên trong agency | Tạo content, schedule posts, quản lý asset |
| **Affiliate** | CTV giới thiệu merchant mới | Theo dõi hoa hồng, referral links |

### 1.5 Key Metrics (Target Year 1)

| Metric | Q2 2026 | Q3 2026 | Q4 2026 | Q1 2027 |
|--------|---------|---------|---------|---------|
| Active merchants | 50 | 150 | 250 | 500 |
| Provinces covered | 2 | 5 | 9 | 13 |
| SKUs listed trên sàn | 200 | 800 | 1,500 | 3,500 |
| GMV qua platform | 500M VND | 2B VND | 5B VND | 15B VND |
| Monthly recurring revenue | 100M VND | 350M VND | 700M VND | 1.5B VND |

---

## 2. Kiến trúc hệ thống

### 2.1 High-Level Architecture

```
                        ┌─────────────────────┐
                        │   Cloudflare Pages  │
                        │   (Static Hosting)  │
                        └──────────┬──────────┘
                                   │  HTTPS
                    ┌──────────────┼──────────────┐
                    │              │              │
             ┌──────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
             │ Admin Portal│ │  Client  │ │  Affiliate │
             │ /admin/*    │ │  Portal  │ │  Portal    │
             │             │ │ /portal/ │ │ /affiliate/│
             └──────┬──────┘ └────┬─────┘ └─────┬──────┘
                    │              │              │
                    └──────────────┼──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │         Supabase             │
                    │  ┌──────────────────────┐    │
                    │  │  PostgreSQL Database  │    │
                    │  └──────────────────────┘    │
                    │  ┌──────────────────────┐    │
                    │  │  Auth (JWT + RLS)     │    │
                    │  └──────────────────────┘    │
                    │  ┌──────────────────────┐    │
                    │  │  Edge Functions       │    │
                    │  │  (Deno / TypeScript)  │    │
                    │  └──────────────────────┘    │
                    │  ┌──────────────────────┐    │
                    │  │  Realtime (WS)        │    │
                    │  └──────────────────────┘    │
                    │  ┌──────────────────────┐    │
                    │  │  Storage (S3-compat.) │    │
                    │  └──────────────────────┘    │
                    └──────────────┬───────────────┘
                                   │
              ┌────────────────────┼───────────────────┐
              │                    │                   │
     ┌────────▼────────┐  ┌────────▼───────┐  ┌───────▼───────┐
     │  Google Gemini  │  │ Marketplace    │  │   Logistics   │
     │  API (AI Layer) │  │ APIs           │  │   Partners    │
     │                 │  │ Shopee/Amazon/ │  │   (Webhooks)  │
     │                 │  │ Alibaba/TikTok │  │               │
     └─────────────────┘  └────────────────┘  └───────────────┘
```

### 2.2 Tech Stack chi tiết

#### Frontend
```
/src
├── assets/
│   ├── css/
│   │   ├── m3-agency.css          # Material Design 3 tokens + components
│   │   ├── admin-unified.css      # Admin layout system
│   │   └── portal.css             # Client portal styles
│   └── js/
│       ├── auth.js                # Auth client + RBAC helper
│       ├── utils.js               # MekongUtils (format, i18n, helpers)
│       ├── api.js                 # Supabase client wrapper
│       ├── marketplace.js         # Marketplace API connectors
│       ├── ai.js                  # Gemini API wrapper
│       └── components/            # Web Components
│           ├── sadec-sidebar.js
│           ├── merchant-card.js
│           ├── platform-badge.js
│           └── ocop-star-rating.js
```

#### Backend (Supabase Edge Functions)
```
/supabase/functions/
├── marketplace-sync/              # Đồng bộ đơn hàng từ sàn về DB
├── ai-listing-gen/                # Gemini: tạo listing description
├── ai-image-analyze/              # Gemini: phân tích ảnh sản phẩm
├── certification-check/           # Tự động check status cert
├── logistics-webhook/             # Nhận webhook từ logistics partners
├── affiliate-commission/          # Tính hoa hồng affiliate
├── report-generator/              # Tạo báo cáo PDF/Excel
└── notification-push/             # Push notification (Zalo/Email)
```

#### Database
- **Supabase PostgreSQL** — primary datastore
- **Row Level Security (RLS)** — phân quyền ở tầng database
- **Realtime subscriptions** — sync UI không cần polling

#### External Integrations

| Service | Mục đích | Auth method |
|---------|----------|-------------|
| Shopee Open Platform | Listing, orders, inventory | OAuth 2.0 + HMAC |
| Amazon SP-API | Marketplace US/JP/SG | OAuth 2.0 + LWA |
| Alibaba ICBU API | B2B international | App Key + Secret |
| Lazada Open Platform | SEA marketplaces | OAuth 2.0 |
| TikTok Shop API | Social commerce | OAuth 2.0 |
| Google Gemini API | AI content generation | API Key |
| Giao Hang Nhanh | Domestic logistics | API Key |
| DHL Express API | International shipping | API Key + Account |
| Zalo OA API | Notification / mini app | OAuth 2.0 |

### 2.3 No-Build Philosophy

Dự án tuân theo nguyên tắc **zero bundler**:
- HTML + ES Modules trực tiếp, không qua Webpack/Vite
- CSS Variables thay thế preprocessors
- Web Components cho reusability
- Ưu điểm: deployment chỉ cần upload file, không có build step, dễ maintain

```html
<!-- Cách import đúng — ES Module trực tiếp -->
<script type="module">
  import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
  import { MekongAuth } from '/assets/js/auth.js';
  import { MekongUtils } from '/assets/js/utils.js';
</script>
```

---

## 3. Database Schema

### 3.1 Core Tables

#### `profiles` — Người dùng hệ thống
```sql
CREATE TABLE profiles (
  id            UUID PRIMARY KEY REFERENCES auth.users(id),
  role          TEXT NOT NULL CHECK (role IN (
                  'super_admin', 'manager', 'content_creator',
                  'client', 'affiliate', 'province_admin'
                )),
  full_name     TEXT,
  phone         TEXT,
  province_id   UUID REFERENCES provinces(id),
  avatar_url    TEXT,
  is_active     BOOLEAN DEFAULT TRUE,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);
```

#### `provinces` — Tỉnh/thành ĐBSCL
```sql
CREATE TABLE provinces (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,              -- "Đồng Tháp"
  code          TEXT NOT NULL UNIQUE,       -- "DTP"
  region        TEXT DEFAULT 'mekong',
  theme_color   TEXT DEFAULT '#1D9E75',     -- White-label màu tỉnh
  logo_url      TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Seed 13 tỉnh ĐBSCL
INSERT INTO provinces (name, code, theme_color) VALUES
  ('Long An', 'LA', '#1D9E75'),
  ('Tiền Giang', 'TG', '#0F6E56'),
  ('Bến Tre', 'BT', '#5DCAA5'),
  ('Trà Vinh', 'TV', '#1D9E75'),
  ('Vĩnh Long', 'VL', '#BA7517'),
  ('Đồng Tháp', 'DTP', '#EF9F27'),
  ('An Giang', 'AG', '#D85A30'),
  ('Kiên Giang', 'KG', '#178BD4'),
  ('Cần Thơ', 'CT', '#7F77DD'),
  ('Hậu Giang', 'HG', '#D4537E'),
  ('Sóc Trăng', 'ST', '#639922'),
  ('Bạc Liêu', 'BL', '#1D9E75'),
  ('Cà Mau', 'CM', '#0F6E56');
```

#### `merchants` — Hợp tác xã / Cơ sở OCOP
```sql
CREATE TABLE merchants (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  province_id     UUID REFERENCES provinces(id),
  owner_id        UUID REFERENCES profiles(id),
  business_name   TEXT NOT NULL,
  business_type   TEXT CHECK (business_type IN (
                    'cooperative', 'household', 'company', 'individual'
                  )),
  tax_id          TEXT,
  phone           TEXT,
  email           TEXT,
  address         TEXT,
  ward            TEXT,
  district        TEXT,

  -- OCOP info
  ocop_star       INT CHECK (ocop_star BETWEEN 1 AND 5),
  ocop_certified_at DATE,
  ocop_expires_at   DATE,

  -- Onboarding status
  onboarding_status TEXT DEFAULT 'pending' CHECK (onboarding_status IN (
                      'pending', 'in_progress', 'active', 'suspended'
                    )),
  onboarding_step   INT DEFAULT 0,

  -- RaaS subscription
  plan_id         UUID REFERENCES plans(id),
  plan_started_at TIMESTAMPTZ,
  plan_expires_at TIMESTAMPTZ,

  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `products` — Sản phẩm OCOP
```sql
CREATE TABLE products (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id     UUID REFERENCES merchants(id) ON DELETE CASCADE,
  sku_internal    TEXT,                     -- SKU nội bộ agency

  -- Thông tin cơ bản
  name_vi         TEXT NOT NULL,            -- Tên tiếng Việt
  name_en         TEXT,                     -- AI-generated
  name_zh         TEXT,                     -- AI-generated
  name_ja         TEXT,                     -- AI-generated

  category        TEXT,                     -- 'food', 'beverage', 'handicraft', ...
  sub_category    TEXT,
  description_vi  TEXT,
  description_en  TEXT,                     -- AI-generated
  description_zh  TEXT,                     -- AI-generated

  -- Vật lý
  weight_gram     INT,
  length_cm       NUMERIC,
  width_cm        NUMERIC,
  height_cm       NUMERIC,

  -- Giá
  cost_price      NUMERIC,                  -- Giá vốn
  base_price      NUMERIC,                  -- Giá bán cơ bản (VND)

  -- Media
  images          JSONB DEFAULT '[]',       -- [{url, alt_vi, alt_en, is_main}]
  videos          JSONB DEFAULT '[]',

  -- Certifications
  certifications  JSONB DEFAULT '[]',       -- ['OCOP_4_STAR', 'HACCP', 'ORGANIC']

  -- AI metadata
  ai_keywords_en  TEXT[],
  ai_keywords_zh  TEXT[],
  ai_quality_score NUMERIC,                 -- 0-100

  status          TEXT DEFAULT 'draft' CHECK (status IN (
                    'draft', 'review', 'approved', 'rejected', 'archived'
                  )),
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 Marketplace Tables

#### `marketplace_accounts` — Tài khoản sàn của merchant
```sql
CREATE TABLE marketplace_accounts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id     UUID REFERENCES merchants(id) ON DELETE CASCADE,
  platform        TEXT NOT NULL CHECK (platform IN (
                    'shopee_vn', 'shopee_sg', 'lazada_vn',
                    'tiktok_shop_vn', 'amazon_us', 'amazon_jp',
                    'amazon_sg', 'alibaba_icbu', 'sendo'
                  )),
  platform_shop_id   TEXT,                  -- Shop ID trên sàn
  platform_shop_name TEXT,
  access_token       TEXT,                  -- Encrypted
  refresh_token      TEXT,                  -- Encrypted
  token_expires_at   TIMESTAMPTZ,
  is_active          BOOLEAN DEFAULT TRUE,
  last_synced_at     TIMESTAMPTZ,
  sync_status        TEXT DEFAULT 'idle',   -- 'idle','syncing','error'
  sync_error         TEXT,
  created_at         TIMESTAMPTZ DEFAULT NOW()
);
```

#### `marketplace_listings` — Listing sản phẩm trên từng sàn
```sql
CREATE TABLE marketplace_listings (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id          UUID REFERENCES products(id),
  marketplace_account_id UUID REFERENCES marketplace_accounts(id),

  platform_item_id    TEXT,                 -- Item ID trên sàn
  platform_sku        TEXT,                 -- SKU trên sàn
  platform_url        TEXT,

  -- Giá sàn (có thể khác giá gốc)
  listing_price       NUMERIC,
  discount_price      NUMERIC,
  currency            TEXT DEFAULT 'VND',

  -- Tồn kho
  stock_quantity      INT DEFAULT 0,
  stock_warning_at    INT DEFAULT 10,       -- Cảnh báo khi còn ít hơn n

  -- Status
  listing_status      TEXT DEFAULT 'draft' CHECK (listing_status IN (
                        'draft', 'pending', 'active', 'inactive',
                        'delisted', 'banned'
                      )),
  rejection_reason    TEXT,

  -- Hiệu suất (updated by sync)
  total_sales         INT DEFAULT 0,
  total_revenue       NUMERIC DEFAULT 0,
  rating              NUMERIC,
  review_count        INT DEFAULT 0,
  views_30d           INT DEFAULT 0,

  last_synced_at      TIMESTAMPTZ,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

#### `orders` — Đơn hàng tổng hợp từ mọi sàn
```sql
CREATE TABLE orders (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id         UUID REFERENCES merchants(id),
  marketplace_account_id UUID REFERENCES marketplace_accounts(id),

  platform_order_id   TEXT NOT NULL,
  platform            TEXT NOT NULL,
  order_status        TEXT,                 -- Status theo platform
  normalized_status   TEXT CHECK (normalized_status IN (
                        'pending', 'confirmed', 'processing',
                        'shipped', 'delivered', 'cancelled', 'returned'
                      )),

  -- Giá trị đơn
  subtotal            NUMERIC,
  shipping_fee        NUMERIC,
  discount_amount     NUMERIC,
  platform_fee        NUMERIC,
  agency_commission   NUMERIC,              -- Hoa hồng agency
  net_to_merchant     NUMERIC,
  currency            TEXT DEFAULT 'VND',

  -- Khách hàng (anonymized theo policy sàn)
  buyer_name          TEXT,
  buyer_phone_masked  TEXT,                 -- "090****123"
  shipping_address    TEXT,
  shipping_province   TEXT,
  shipping_country    TEXT DEFAULT 'VN',

  -- Shipping
  tracking_number     TEXT,
  shipping_carrier    TEXT,
  shipped_at          TIMESTAMPTZ,
  delivered_at        TIMESTAMPTZ,

  platform_created_at TIMESTAMPTZ,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

#### `order_items` — Chi tiết sản phẩm trong đơn
```sql
CREATE TABLE order_items (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id        UUID REFERENCES orders(id) ON DELETE CASCADE,
  listing_id      UUID REFERENCES marketplace_listings(id),
  product_id      UUID REFERENCES products(id),
  platform_sku    TEXT,
  product_name    TEXT,
  quantity        INT,
  unit_price      NUMERIC,
  total_price     NUMERIC
);
```

### 3.3 Content & Media Tables

#### `media_assets` — Kho ảnh/video sản phẩm
```sql
CREATE TABLE media_assets (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id     UUID REFERENCES merchants(id),
  product_id      UUID REFERENCES products(id),
  asset_type      TEXT CHECK (asset_type IN (
                    'product_photo', 'lifestyle_photo', 'packaging',
                    'video_demo', 'video_ad', 'logo', 'banner'
                  )),
  storage_path    TEXT NOT NULL,            -- Supabase Storage path
  public_url      TEXT NOT NULL,
  file_size_kb    INT,
  width_px        INT,
  height_px       INT,
  format          TEXT,                     -- 'jpg', 'png', 'mp4', 'webp'

  -- AI analysis (Gemini Vision)
  ai_description  TEXT,
  ai_tags         TEXT[],
  ai_quality_score NUMERIC,                 -- 0-100
  meets_shopee_standard BOOLEAN,
  meets_amazon_standard BOOLEAN,

  is_approved     BOOLEAN DEFAULT FALSE,
  approved_by     UUID REFERENCES profiles(id),
  approved_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `content_posts` — Bài đăng social / content lịch
```sql
CREATE TABLE content_posts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id     UUID REFERENCES merchants(id),
  created_by      UUID REFERENCES profiles(id),

  platform        TEXT CHECK (platform IN (
                    'facebook', 'zalo', 'tiktok', 'instagram',
                    'youtube', 'shopee_feed', 'lazada_feed'
                  )),
  post_type       TEXT CHECK (post_type IN (
                    'product_post', 'promotional', 'educational',
                    'livestream', 'story', 'reel'
                  )),

  title           TEXT,
  content         TEXT,
  hashtags        TEXT[],
  media_asset_ids UUID[],

  scheduled_at    TIMESTAMPTZ,
  published_at    TIMESTAMPTZ,
  status          TEXT DEFAULT 'draft' CHECK (status IN (
                    'draft', 'scheduled', 'published', 'failed'
                  )),

  -- Metrics (updated post-publish)
  reach           INT,
  impressions     INT,
  engagements     INT,
  clicks          INT,
  conversions     INT,

  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.4 Certification Tables

#### `certifications` — Danh sách chứng nhận
```sql
CREATE TABLE certifications (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id     UUID REFERENCES merchants(id),
  cert_type       TEXT NOT NULL CHECK (cert_type IN (
                    'OCOP_3_STAR', 'OCOP_4_STAR', 'OCOP_5_STAR',
                    'GLOBAL_GAP', 'HACCP', 'ISO_22000', 'ORGANIC_VN',
                    'ORGANIC_EU', 'ORGANIC_USDA', 'VietGAP',
                    'HALAL', 'KOSHER', 'VFQI', 'AREA_CODE'
                  )),
  cert_number     TEXT,
  issued_by       TEXT,
  issued_at       DATE,
  expires_at      DATE,
  scope           TEXT,                     -- Sản phẩm/quy trình được chứng nhận

  document_url    TEXT,                     -- Supabase Storage
  status          TEXT DEFAULT 'pending' CHECK (status IN (
                    'pending', 'active', 'expiring_soon', 'expired', 'revoked'
                  )),

  -- Reminder
  reminder_sent_30d  BOOLEAN DEFAULT FALSE,
  reminder_sent_7d   BOOLEAN DEFAULT FALSE,

  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `certification_tasks` — Công việc để đạt chứng nhận
```sql
CREATE TABLE certification_tasks (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id     UUID REFERENCES merchants(id),
  cert_type       TEXT NOT NULL,
  task_name       TEXT NOT NULL,
  description     TEXT,
  required_docs   TEXT[],
  status          TEXT DEFAULT 'todo' CHECK (status IN (
                    'todo', 'in_progress', 'review', 'done', 'blocked'
                  )),
  assigned_to     UUID REFERENCES profiles(id),
  due_date        DATE,
  completed_at    TIMESTAMPTZ,
  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.5 Logistics Tables

#### `logistics_shipments` — Lô hàng / shipment
```sql
CREATE TABLE logistics_shipments (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id       UUID REFERENCES merchants(id),
  order_id          UUID REFERENCES orders(id),

  shipment_type     TEXT CHECK (shipment_type IN (
                      'domestic', 'cross_border', 'fba_inbound'
                    )),
  carrier           TEXT,                   -- 'GHN', 'GHTK', 'DHL', 'FedEx'
  tracking_number   TEXT,
  carrier_tracking_url TEXT,

  origin_address    TEXT,
  origin_province   TEXT,
  destination_address TEXT,
  destination_country TEXT DEFAULT 'VN',

  weight_kg         NUMERIC,
  declared_value    NUMERIC,
  currency          TEXT DEFAULT 'VND',

  shipping_cost     NUMERIC,
  agency_markup     NUMERIC,               -- Markup của agency
  total_charged     NUMERIC,

  status            TEXT DEFAULT 'pending' CHECK (status IN (
                      'pending', 'picked_up', 'in_transit',
                      'customs', 'out_for_delivery',
                      'delivered', 'failed', 'returned'
                    )),

  shipped_at        TIMESTAMPTZ,
  estimated_delivery TIMESTAMPTZ,
  delivered_at      TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT NOW(),
  updated_at        TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.6 Finance Tables

#### `invoices` — Hóa đơn agency → merchant
```sql
CREATE TABLE invoices (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id     UUID REFERENCES merchants(id),
  invoice_number  TEXT NOT NULL UNIQUE,
  invoice_date    DATE NOT NULL,
  due_date        DATE,

  -- Line items
  items           JSONB NOT NULL,
  -- [{ type: 'setup_fee'|'retainer'|'commission'|'addon',
  --    description: TEXT, quantity: INT, unit_price: NUMERIC, amount: NUMERIC }]

  subtotal        NUMERIC,
  vat_rate        NUMERIC DEFAULT 0.08,
  vat_amount      NUMERIC,
  total           NUMERIC,

  currency        TEXT DEFAULT 'VND',
  status          TEXT DEFAULT 'draft' CHECK (status IN (
                    'draft', 'sent', 'paid', 'overdue', 'cancelled'
                  )),
  paid_at         TIMESTAMPTZ,
  payment_method  TEXT,
  notes           TEXT,
  created_by      UUID REFERENCES profiles(id),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `commissions` — Hoa hồng theo GMV
```sql
CREATE TABLE commissions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  merchant_id     UUID REFERENCES merchants(id),
  order_id        UUID REFERENCES orders(id),
  period_month    TEXT,                     -- '2026-04'
  platform        TEXT,
  gmv             NUMERIC,
  commission_rate NUMERIC,
  commission_amount NUMERIC,
  status          TEXT DEFAULT 'pending' CHECK (status IN (
                    'pending', 'invoiced', 'paid'
                  )),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.7 Row Level Security Policies

```sql
-- Merchants chỉ thấy data của mình
CREATE POLICY "merchants_own_data" ON products
  FOR ALL USING (
    merchant_id IN (
      SELECT id FROM merchants WHERE owner_id = auth.uid()
    )
  );

-- Province admin thấy merchant trong tỉnh
CREATE POLICY "province_admin_access" ON merchants
  FOR SELECT USING (
    province_id IN (
      SELECT province_id FROM profiles WHERE id = auth.uid()
    )
    AND
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid()
      AND role = 'province_admin'
    )
  );

-- Agency staff thấy tất cả
CREATE POLICY "agency_full_access" ON merchants
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid()
      AND role IN ('super_admin', 'manager', 'content_creator')
    )
  );
```

---

## 4. Authentication & RBAC

### 4.1 Auth Flow

```
User truy cập trang bảo vệ
         │
         ▼
auth.js: checkSession()
         │
    Có session? ──No──► Redirect /login.html
         │ Yes
         ▼
    Lấy profile + role
         │
    Đúng role? ──No──► Redirect /403.html
         │ Yes
         ▼
    Inject user context vào trang
```

### 4.2 auth.js — Centralized Auth Module

```javascript
// /assets/js/auth.js

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { MekongEnv } from '/mekong-env.js';

const supabase = createClient(MekongEnv.SUPABASE_URL, MekongEnv.SUPABASE_ANON_KEY);

export class MekongAuth {

  /** Kiểm tra session + role, redirect nếu không đủ quyền */
  static async requireAuth(allowedRoles = []) {
    const { data: { session }, error } = await supabase.auth.getSession();

    if (!session) {
      const returnUrl = encodeURIComponent(window.location.pathname);
      window.location.href = `/login.html?return=${returnUrl}`;
      return null;
    }

    const { data: profile } = await supabase
      .from('profiles')
      .select('*, province:provinces(*)')
      .eq('id', session.user.id)
      .single();

    if (allowedRoles.length > 0 && !allowedRoles.includes(profile.role)) {
      window.location.href = '/403.html';
      return null;
    }

    // Inject vào global context
    window.MekongUser = { session, profile };
    return { session, profile };
  }

  /** Login với email/password */
  static async login(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    return data;
  }

  /** Logout */
  static async logout() {
    await supabase.auth.signOut();
    window.location.href = '/login.html';
  }

  /** Check permission cho action cụ thể */
  static can(action) {
    const role = window.MekongUser?.profile?.role;
    const permissions = {
      'super_admin':    ['*'],
      'manager':        ['read:all', 'write:campaigns', 'write:leads', 'write:invoices'],
      'content_creator':['read:campaigns', 'write:content', 'read:merchants'],
      'province_admin': ['read:province_merchants', 'read:province_reports'],
      'client':         ['read:own_projects', 'read:own_invoices'],
      'affiliate':      ['read:own_commissions', 'write:referrals'],
    };

    const userPerms = permissions[role] || [];
    return userPerms.includes('*') || userPerms.includes(action);
  }
}
```

### 4.3 Usage trên từng trang

```javascript
// Ví dụ: admin/marketplace.html
<script type="module">
  import { MekongAuth } from '/assets/js/auth.js';

  const { profile } = await MekongAuth.requireAuth([
    'super_admin', 'manager', 'content_creator'
  ]);

  // Render UI dựa theo role
  if (MekongAuth.can('write:campaigns')) {
    document.getElementById('btn-create-campaign').style.display = 'flex';
  }
</script>
```

### 4.4 Role Matrix

| Action | super_admin | manager | content_creator | province_admin | client | affiliate |
|--------|:-----------:|:-------:|:---------------:|:--------------:|:------:|:---------:|
| Xem tất cả merchant | ✅ | ✅ | ✅ | Tỉnh mình | ❌ | ❌ |
| Tạo/sửa merchant | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Quản lý marketplace | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Tạo content | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Xem báo cáo tỉnh | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Xem đơn hàng riêng | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| Xem hoa hồng riêng | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Quản lý finance | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Tạo invoice | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Xem invoice riêng | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |

---

## 5. Module 1 — Marketplace Onboarding as a Service

### 5.1 Overview

Module giúp merchant OCOP **từ 0 → có store đang bán** trên các sàn thương mại điện tử. Agency đóng vai người cầm tay, merchant chỉ cần cung cấp thông tin và sản phẩm.

**Luồng chính:**
```
Merchant đăng ký
      │
      ▼
Wizard: Thu thập thông tin cơ bản
      │
      ▼
Agency review + xác minh (KYC-lite)
      │
      ▼
Chọn platform phù hợp (dựa trên sản phẩm + cert)
      │
      ▼
Agency tạo account sàn (hoặc kết nối account có sẵn)
      │
      ▼
Upload sản phẩm + listing optimization
      │
      ▼
Go live + training cơ bản cho merchant
      │
      ▼
Ongoing management (retainer hàng tháng)
```

### 5.2 Platform Selection Engine

```javascript
// /assets/js/marketplace.js

export class PlatformSelector {

  /**
   * Tư vấn sàn phù hợp dựa trên profile merchant
   * @param {Object} merchantProfile
   * @returns {Array} ranked platforms với reasoning
   */
  static recommend(merchantProfile) {
    const { province, certifications, productCategories,
            monthlyCapacity, targetMarket } = merchantProfile;

    const platforms = [];

    // Shopee VN — luôn là điểm bắt đầu
    platforms.push({
      platform: 'shopee_vn',
      priority: 1,
      reason: 'Thị trường nội địa lớn nhất VN, rào cản thấp nhất',
      requirements: ['Chứng minh nhân dân', 'Tài khoản ngân hàng'],
      setup_days: 3,
      fee_setup: 2000000,
      fee_monthly: 2000000,
    });

    // TikTok Shop — nếu có khả năng làm video
    platforms.push({
      platform: 'tiktok_shop_vn',
      priority: 2,
      reason: 'Tăng trưởng nhanh nhất 2025-2026, phù hợp thực phẩm + OCOP storytelling',
      requirements: ['Giấy phép KD hoặc CCCD', 'Tài khoản TikTok'],
      setup_days: 5,
      fee_setup: 3000000,
      fee_monthly: 2500000,
    });

    // Amazon — chỉ khi có cert quốc tế
    if (certifications.some(c => ['HACCP', 'ORGANIC_USDA', 'ORGANIC_EU'].includes(c))) {
      platforms.push({
        platform: 'amazon_us',
        priority: 3,
        reason: 'Thị trường Mỹ cao cấp, đòi hỏi cert quốc tế nhưng biên lợi nhuận cao',
        requirements: ['HACCP hoặc Organic cert', 'Bao bì tiếng Anh', 'UPC barcode', 'USD account'],
        setup_days: 21,
        fee_setup: 8000000,
        fee_monthly: 5000000,
      });
    }

    // Alibaba ICBU — B2B, phù hợp volume lớn
    if (monthlyCapacity > 1000) {
      platforms.push({
        platform: 'alibaba_icbu',
        priority: targetMarket === 'china' ? 2 : 4,
        reason: 'B2B với buyer Trung Quốc, volume lớn, phù hợp gạo/hải sản/trái cây',
        requirements: ['Business license', 'Export license', 'Mã vùng trồng'],
        setup_days: 14,
        fee_setup: 5000000,
        fee_monthly: 4000000,
      });
    }

    return platforms.sort((a, b) => a.priority - b.priority);
  }
}
```

### 5.3 Onboarding Wizard Steps

```javascript
// Wizard state machine — 7 bước
const ONBOARDING_STEPS = [
  {
    step: 1,
    id: 'basic_info',
    title: 'Thông tin cơ bản',
    fields: ['business_name', 'business_type', 'province', 'phone', 'email', 'tax_id'],
    required: ['business_name', 'province', 'phone'],
  },
  {
    step: 2,
    id: 'ocop_profile',
    title: 'Thông tin OCOP',
    fields: ['ocop_star', 'ocop_certified_at', 'ocop_expires_at', 'product_categories'],
    required: [],
  },
  {
    step: 3,
    id: 'product_upload',
    title: 'Upload sản phẩm',
    description: 'Tải lên ít nhất 1 sản phẩm để bắt đầu. Agency sẽ hoàn thiện thông tin.',
    action: 'product_form',
  },
  {
    step: 4,
    id: 'media_upload',
    title: 'Ảnh & Video sản phẩm',
    description: 'Ảnh sẽ được phân tích tự động. Nếu không đạt chuẩn sàn, agency sẽ sắp xếp chụp lại.',
    action: 'media_upload',
  },
  {
    step: 5,
    id: 'platform_select',
    title: 'Chọn sàn kinh doanh',
    description: 'Dựa trên profile của bạn, hệ thống đề xuất các sàn phù hợp nhất.',
    action: 'platform_recommend',
  },
  {
    step: 6,
    id: 'plan_select',
    title: 'Chọn gói dịch vụ',
    action: 'plan_selection',
  },
  {
    step: 7,
    id: 'review_submit',
    title: 'Xác nhận & Gửi',
    description: 'Agency sẽ liên hệ trong vòng 24 giờ để tiếp tục onboarding.',
  },
];
```

### 5.4 Marketplace Sync Engine (Edge Function)

```typescript
// /supabase/functions/marketplace-sync/index.ts

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

interface SyncJob {
  merchantId: string;
  platform: string;
  syncType: 'orders' | 'inventory' | 'listings' | 'full';
}

async function syncShopeeOrders(shopeeClient: any, supabase: any, merchantId: string) {
  const orders = await shopeeClient.getOrderList({
    time_range_field: 'update_time',
    time_from: Math.floor(Date.now() / 1000) - 3600, // Last 1 hour
    time_to: Math.floor(Date.now() / 1000),
    page_size: 50,
  });

  for (const order of orders.response.order_list) {
    const detail = await shopeeClient.getOrderDetail({ order_sn_list: [order.order_sn] });

    // Normalize Shopee order → our schema
    const normalized = {
      merchant_id: merchantId,
      platform: 'shopee_vn',
      platform_order_id: order.order_sn,
      normalized_status: mapShopeeStatus(order.order_status),
      subtotal: detail.item_list.reduce((sum, item) => sum + item.model_discounted_price * item.model_quantity_purchased, 0),
      shipping_fee: detail.actual_shipping_fee,
      buyer_name: detail.recipient_address.name,
      shipping_address: `${detail.recipient_address.full_address}`,
      platform_created_at: new Date(order.create_time * 1000).toISOString(),
    };

    await supabase.from('orders').upsert(normalized, {
      onConflict: 'platform_order_id,platform',
    });
  }
}

function mapShopeeStatus(shopeeStatus: string): string {
  const map: Record<string, string> = {
    'UNPAID': 'pending',
    'READY_TO_SHIP': 'confirmed',
    'PROCESSED': 'processing',
    'SHIPPED': 'shipped',
    'COMPLETED': 'delivered',
    'CANCELLED': 'cancelled',
    'IN_CANCEL': 'cancelled',
    'TO_RETURN': 'returned',
  };
  return map[shopeeStatus] ?? 'pending';
}

Deno.serve(async (req) => {
  const { merchantId, platform, syncType }: SyncJob = await req.json();
  const supabase = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!);

  try {
    await supabase.from('marketplace_accounts')
      .update({ sync_status: 'syncing' })
      .eq('merchant_id', merchantId)
      .eq('platform', platform);

    // Dispatch to platform-specific handler
    if (platform === 'shopee_vn') {
      const account = await getShopeeAccount(supabase, merchantId);
      const shopeeClient = createShopeeClient(account);
      if (syncType === 'orders' || syncType === 'full') {
        await syncShopeeOrders(shopeeClient, supabase, merchantId);
      }
    }

    await supabase.from('marketplace_accounts')
      .update({ sync_status: 'idle', last_synced_at: new Date().toISOString() })
      .eq('merchant_id', merchantId)
      .eq('platform', platform);

    return new Response(JSON.stringify({ success: true }), { status: 200 });

  } catch (error) {
    await supabase.from('marketplace_accounts')
      .update({ sync_status: 'error', sync_error: error.message })
      .eq('merchant_id', merchantId)
      .eq('platform', platform);

    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
});
```

### 5.5 Platform API Credentials Configuration

```javascript
// /assets/js/platforms/shopee.js

export const SHOPEE_CONFIG = {
  partner_id: Deno.env.get('SHOPEE_PARTNER_ID'),
  partner_key: Deno.env.get('SHOPEE_PARTNER_KEY'),
  redirect_url: 'https://sadec-marketing-hub.pages.dev/admin/marketplace/callback/shopee',
  base_url: 'https://partner.shopeemobile.com',
};

export function generateShopeeAuthUrl(shopId) {
  const timestamp = Math.floor(Date.now() / 1000);
  const path = '/api/v2/shop/auth_partner';
  const baseString = `${SHOPEE_CONFIG.partner_id}${path}${timestamp}`;
  const sign = crypto.createHmac('sha256', SHOPEE_CONFIG.partner_key)
                     .update(baseString).digest('hex');

  return `${SHOPEE_CONFIG.base_url}${path}?partner_id=${SHOPEE_CONFIG.partner_id}`
       + `&timestamp=${timestamp}&sign=${sign}&redirect=${SHOPEE_CONFIG.redirect_url}`;
}
```

---

## 6. Module 2 — Brand & Packaging as a Service

### 6.1 Overview

Giải quyết rào cản bao bì / branding — xây dựng identity sản phẩm OCOP đạt chuẩn quốc tế, tích hợp AI để tạo content đa ngôn ngữ tự động.

### 6.2 AI Listing Generator (Edge Function)

```typescript
// /supabase/functions/ai-listing-gen/index.ts

import { GoogleGenerativeAI } from 'https://esm.sh/@google/generative-ai';

const genAI = new GoogleGenerativeAI(Deno.env.get('GEMINI_API_KEY')!);

interface ListingRequest {
  product: {
    name_vi: string;
    description_vi: string;
    category: string;
    certifications: string[];
    weight_gram: number;
    province: string;
  };
  platforms: string[];           // ['shopee_vn', 'amazon_us', 'alibaba_icbu']
  target_languages: string[];    // ['en', 'zh', 'ja']
}

interface PlatformListing {
  platform: string;
  title: string;
  description: string;
  bullet_points: string[];
  keywords: string[];
  hashtags: string[];
}

const PLATFORM_CONSTRAINTS = {
  shopee_vn: {
    title_max: 120,
    description_max: 3000,
    bullet_count: 5,
  },
  amazon_us: {
    title_max: 200,
    description_max: 2000,
    bullet_count: 5,
    bullet_max: 500,
  },
  alibaba_icbu: {
    title_max: 128,
    description_max: 5000,
    bullet_count: 8,
  },
  tiktok_shop_vn: {
    title_max: 255,
    description_max: 1000,
    hashtag_count: 10,
  },
};

async function generateListingForPlatform(
  model: any,
  product: ListingRequest['product'],
  platform: string,
  language: string
): Promise<PlatformListing> {

  const constraints = PLATFORM_CONSTRAINTS[platform];
  const certBadges = product.certifications.join(', ');

  const prompt = `
Bạn là chuyên gia marketing nông sản Việt Nam xuất khẩu.
Tạo listing sản phẩm cho platform ${platform} bằng ngôn ngữ ${language}.

Thông tin sản phẩm:
- Tên: ${product.name_vi}
- Mô tả gốc: ${product.description_vi}
- Danh mục: ${product.category}
- Chứng nhận: ${certBadges || 'OCOP ' + product.province}
- Xuất xứ: ${product.province}, Đồng bằng sông Cửu Long, Việt Nam
- Trọng lượng: ${product.weight_gram}g

Yêu cầu output (JSON):
{
  "title": "Tiêu đề tối đa ${constraints.title_max} ký tự, bao gồm từ khóa chính",
  "description": "Mô tả tối đa ${constraints.description_max} ký tự",
  "bullet_points": ["${constraints.bullet_count} điểm nổi bật ngắn gọn"],
  "keywords": ["10 từ khóa SEO phù hợp ${platform}"],
  "hashtags": ["hashtag nếu là social platform"]
}

Lưu ý:
- Nhấn mạnh xuất xứ Mekong Delta, chứng nhận OCOP
- Ngôn ngữ ${language}: tự nhiên, phù hợp văn hóa ${language === 'zh' ? 'Trung Quốc' : language === 'ja' ? 'Nhật Bản' : 'Anh/Mỹ'}
- Tránh claims về sức khỏe chưa được kiểm chứng
- Chỉ output JSON, không có text thừa
`;

  const result = await model.generateContent(prompt);
  const text = result.response.text().replace(/```json|```/g, '').trim();
  const parsed = JSON.parse(text);

  return { platform, ...parsed };
}

Deno.serve(async (req) => {
  const { product, platforms, target_languages }: ListingRequest = await req.json();

  const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
  const results: PlatformListing[] = [];

  for (const platform of platforms) {
    const lang = platform.endsWith('_vn') ? 'vi'
                : platform.includes('alibaba') ? 'zh'
                : platform.includes('amazon_jp') ? 'ja'
                : 'en';

    const listing = await generateListingForPlatform(model, product, platform, lang);
    results.push(listing);

    // Generate additional language versions if requested
    for (const extraLang of target_languages) {
      if (extraLang !== lang) {
        const extraListing = await generateListingForPlatform(model, product, platform, extraLang);
        results.push({ ...extraListing, platform: `${platform}_${extraLang}` });
      }
    }
  }

  return new Response(JSON.stringify({ listings: results }), {
    headers: { 'Content-Type': 'application/json' },
  });
});
```

### 6.3 Image Quality Analyzer (Edge Function)

```typescript
// /supabase/functions/ai-image-analyze/index.ts

async function analyzeProductImage(model: any, imageBase64: string, mimeType: string) {
  const prompt = `
Phân tích ảnh sản phẩm thực phẩm/nông sản Việt Nam này cho mục đích đăng bán trên sàn thương mại điện tử.

Đánh giá theo tiêu chuẩn:
1. Shopee VN: Nền trắng, sản phẩm chiếm >70% frame, rõ nét
2. Amazon: Nền trắng #FFFFFF thuần, không watermark, không text, 1000x1000px minimum
3. Alibaba: Chấp nhận lifestyle, nhưng cần rõ sản phẩm

Output JSON:
{
  "overall_score": 0-100,
  "meets_shopee": boolean,
  "meets_amazon": boolean,
  "meets_alibaba": boolean,
  "issues": ["Danh sách vấn đề cụ thể"],
  "suggestions": ["Gợi ý cải thiện cụ thể"],
  "product_detected": "Mô tả sản phẩm phát hiện được",
  "auto_tags": ["tag tự động"]
}
`;

  const result = await model.generateContent([
    { inlineData: { data: imageBase64, mimeType } },
    prompt,
  ]);

  return JSON.parse(result.response.text().replace(/```json|```/g, '').trim());
}
```

### 6.4 Brand Guidelines Template

```markdown
## Brand Package cho Merchant OCOP

### Tài liệu bắt buộc
- [ ] Logo chính (SVG + PNG 1000px)
- [ ] Logo phụ (horizontal + stacked)
- [ ] Màu thương hiệu (HEX + CMYK + Pantone)
- [ ] Font chữ (2 fonts tối đa)

### Bao bì tối thiểu (checklist)
- [ ] Tên sản phẩm tiếng Việt + Anh
- [ ] Thành phần / Ingredients (EN)
- [ ] Hướng dẫn sử dụng
- [ ] Thông tin dinh dưỡng (bắt buộc cho Amazon US)
- [ ] Ngày sản xuất / Hạn sử dụng
- [ ] Trọng lượng tịnh (gram + oz)
- [ ] Xuất xứ: "Product of Vietnam — Mekong Delta"
- [ ] Barcode EAN-13 hoặc UPC-A
- [ ] QR code truy xuất nguồn gốc
- [ ] Logo OCOP sao
- [ ] Logo chứng nhận (HACCP, GlobalGAP,...)

### Tiêu chuẩn ảnh sản phẩm theo sàn
| Sàn | Background | Kích thước tối thiểu | Số ảnh tối thiểu |
|-----|------------|---------------------|------------------|
| Shopee VN | Trắng | 500×500 | 3 |
| TikTok Shop | Trắng | 800×800 | 3 |
| Amazon US | Trắng thuần #FFF | 1000×1000 | 7 |
| Alibaba ICBU | Linh hoạt | 800×800 | 6 |
| Lazada VN | Trắng | 500×500 | 3 |
```

---

## 7. Module 3 — Certification as a Service

### 7.1 Certification Roadmap Engine

```javascript
// /assets/js/certification.js

export const CERT_ROADMAPS = {

  GLOBAL_GAP: {
    name: 'GlobalG.A.P.',
    description: 'Chứng nhận sản xuất nông nghiệp tốt toàn cầu — bắt buộc để xuất EU, Nhật, Hàn',
    timeline_months: 6,
    cost_estimate_vnd: '50,000,000 – 80,000,000',
    target_markets: ['EU', 'Japan', 'Korea', 'Australia'],
    tasks: [
      { name: 'Đánh giá ban đầu (gap assessment)', duration_weeks: 2, docs: ['Hồ sơ đất', 'Hồ sơ nước', 'QT sản xuất hiện tại'] },
      { name: 'Đào tạo tiêu chuẩn GlobalG.A.P.', duration_weeks: 1, docs: ['Danh sách nhân sự cần đào tạo'] },
      { name: 'Xây dựng hệ thống hồ sơ', duration_weeks: 4, docs: ['Farm map', 'Risk assessment', 'IPM plan', 'Worker health records'] },
      { name: 'Triển khai và ghi chép', duration_weeks: 8, docs: ['Nhật ký sản xuất', 'Nhật ký phun thuốc', 'Kiểm tra nội bộ'] },
      { name: 'Đánh giá nội bộ (internal audit)', duration_weeks: 1, docs: ['Checklist tự đánh giá', 'Corrective actions'] },
      { name: 'Đánh giá bên ngoài (CB audit)', duration_weeks: 2, docs: ['Liên hệ CB được GlobalG.A.P. chấp nhận'] },
      { name: 'Cấp chứng chỉ', duration_weeks: 2, docs: ['Nộp hồ sơ chính thức'] },
    ],
  },

  HACCP: {
    name: 'HACCP',
    description: 'Hazard Analysis Critical Control Points — bắt buộc cho thực phẩm xuất Mỹ',
    timeline_months: 4,
    cost_estimate_vnd: '30,000,000 – 50,000,000',
    target_markets: ['USA', 'Canada', 'EU'],
    tasks: [
      { name: 'Thành lập HACCP team', duration_weeks: 1, docs: ['Sơ đồ nhân sự', 'Job description'] },
      { name: 'Mô tả sản phẩm và quy trình', duration_weeks: 2, docs: ['Product description', 'Flow diagram'] },
      { name: 'Phân tích mối nguy (Hazard Analysis)', duration_weeks: 3, docs: ['Hazard analysis worksheet'] },
      { name: 'Xác định CCPs', duration_weeks: 1, docs: ['CCP decision tree', 'CCP list'] },
      { name: 'Xây dựng critical limits + monitoring', duration_weeks: 2, docs: ['Monitoring procedures', 'Corrective actions'] },
      { name: 'Xây dựng HACCP plan + records', duration_weeks: 3, docs: ['HACCP plan document', 'Record forms'] },
      { name: 'Đào tạo và vận hành thử', duration_weeks: 4, docs: ['Training records', 'Verification records'] },
      { name: 'Audit và cấp chứng chỉ', duration_weeks: 2, docs: ['Third-party audit report'] },
    ],
  },

  OCOP_UPGRADE: {
    name: 'Nâng hạng OCOP (3→4 hoặc 4→5 sao)',
    description: 'Nâng hạng OCOP để đủ điều kiện xuất khẩu chính ngạch',
    timeline_months: 3,
    cost_estimate_vnd: '10,000,000 – 20,000,000',
    target_markets: ['Domestic premium', 'Export B2C'],
    tasks: [
      { name: 'Đánh giá hiện trạng và khoảng cách', duration_weeks: 1 },
      { name: 'Cải thiện chất lượng sản phẩm', duration_weeks: 4 },
      { name: 'Nâng cấp bao bì và nhãn hiệu', duration_weeks: 3 },
      { name: 'Hoàn thiện hồ sơ đăng ký', duration_weeks: 2 },
      { name: 'Nộp hồ sơ và chờ thẩm định', duration_weeks: 4 },
    ],
  },
};
```

### 7.2 Certification Tracking UI Component

```javascript
// /assets/js/components/cert-tracker.js

class CertTracker extends HTMLElement {
  connectedCallback() {
    this.render();
  }

  async loadData() {
    const { data: certs } = await supabase
      .from('certifications')
      .select('*')
      .eq('merchant_id', this.merchantId)
      .order('expires_at', { ascending: true });

    return certs;
  }

  getStatusColor(cert) {
    if (cert.status === 'active') {
      const daysLeft = Math.floor((new Date(cert.expires_at) - Date.now()) / 86400000);
      if (daysLeft < 30) return 'warning';
      return 'success';
    }
    if (cert.status === 'expired') return 'danger';
    return 'info';
  }

  render() {
    // Web Component template
    this.innerHTML = `
      <div class="cert-tracker-container">
        <!-- Rendered by JS -->
      </div>
    `;
  }
}

customElements.define('cert-tracker', CertTracker);
```

### 7.3 Auto-Reminder Edge Function

```typescript
// /supabase/functions/cert-reminder/index.ts
// Chạy hàng ngày bằng pg_cron hoặc Supabase cron

Deno.serve(async () => {
  const supabase = createAdminClient();

  // Tìm cert sắp hết hạn 30 ngày
  const thirtyDaysFromNow = new Date();
  thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);

  const { data: expiring } = await supabase
    .from('certifications')
    .select('*, merchant:merchants(business_name, phone, owner:profiles(*))')
    .eq('status', 'active')
    .lte('expires_at', thirtyDaysFromNow.toISOString())
    .eq('reminder_sent_30d', false);

  for (const cert of expiring ?? []) {
    // Gửi notification qua Zalo OA
    await sendZaloNotification({
      phone: cert.merchant.phone,
      template: 'cert_expiry_30d',
      params: {
        business_name: cert.merchant.business_name,
        cert_type: cert.cert_type,
        expires_at: cert.expires_at,
      },
    });

    await supabase.from('certifications')
      .update({ reminder_sent_30d: true })
      .eq('id', cert.id);
  }

  return new Response(JSON.stringify({ processed: expiring?.length }));
});
```

---

## 8. Module 4 — Logistics & Fulfillment as a Service

### 8.1 Logistics Partner Network

| Partner | Loại | Phủ sóng | Ưu điểm | Tích hợp |
|---------|------|----------|---------|----------|
| Giao Hàng Nhanh (GHN) | Domestic | 63 tỉnh | Phổ biến nhất VN, giá rẻ | REST API |
| Giao Hàng Tiết Kiệm (GHTK) | Domestic | 63 tỉnh | Thấp nhất cho gói nhỏ | REST API |
| J&T Express | Domestic | 63 tỉnh | Nhanh, nhiều điểm lấy hàng | REST API |
| DHL Express | International | Toàn cầu | Fastest cross-border | REST API |
| FedEx | International | Toàn cầu | Reliable, thực phẩm tươi | REST API |
| Hau Giang Logistics Hub | Cold chain ĐBSCL | Mekong | Kho lạnh 150K tấn | Direct partner |

### 8.2 Shipment Creator

```javascript
// /assets/js/logistics.js

export class LogisticsManager {

  /**
   * Tạo shipment và lấy giá từ nhiều carrier
   * @param {Object} shipmentRequest
   * @returns {Array} quotes từ các carrier
   */
  static async getQuotes(shipmentRequest) {
    const { origin, destination, weight_kg, dimensions, service_type } = shipmentRequest;

    const promises = [];

    // GHN quote
    promises.push(this.getGHNQuote(origin, destination, weight_kg, dimensions));

    // GHTK quote
    promises.push(this.getGHTKQuote(origin, destination, weight_kg));

    // DHL nếu international
    if (destination.country !== 'VN') {
      promises.push(this.getDHLQuote(origin, destination, weight_kg, dimensions));
    }

    const results = await Promise.allSettled(promises);

    return results
      .filter(r => r.status === 'fulfilled')
      .map(r => r.value)
      .sort((a, b) => a.total_fee - b.total_fee);
  }

  static async getGHNQuote(origin, destination, weight_gram, dimensions) {
    const response = await fetch('https://dev-online-gateway.ghn.vn/shiip/public-api/v2/shipping-order/fee', {
      method: 'POST',
      headers: {
        'Token': Deno.env.get('GHN_API_TOKEN'),
        'ShopId': Deno.env.get('GHN_SHOP_ID'),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from_district_id: origin.district_id,
        service_type_id: 2,
        to_district_id: destination.district_id,
        to_ward_code: destination.ward_code,
        weight: weight_gram,
        length: dimensions?.length ?? 20,
        width: dimensions?.width ?? 15,
        height: dimensions?.height ?? 10,
      }),
    });

    const data = await response.json();
    return {
      carrier: 'GHN',
      service: 'Standard',
      total_fee: data.data.total,
      estimated_days: data.data.expected_delivery_time,
    };
  }
}
```

### 8.3 FBA Inbound Preparation Checklist

```markdown
## Amazon FBA Inbound — OCOP Food Products

### Yêu cầu bắt buộc
- [ ] FNSKU label (Fulfillment Network SKU) trên từng đơn vị sản phẩm
- [ ] Barcode scan test (100% scan rate)
- [ ] Bao bì kín, chịu được vận chuyển dài ngày
- [ ] Không có mùi mạnh (Amazon có quy định về thực phẩm có mùi)
- [ ] Best-before date: tối thiểu còn 90 ngày khi nhận vào kho FBA
- [ ] Nhãn tiếng Anh đầy đủ (ingredients, nutrition facts, allergens)
- [ ] Nhãn country of origin: "Product of Vietnam"
- [ ] Carton label: AMZN, shipment ID, PO number

### Thực phẩm đặc biệt (ĐBSCL)
| Sản phẩm | Yêu cầu thêm |
|----------|-------------|
| Mắm, nước mắm | Leak-proof + outer bag, cảnh báo mùi |
| Gạo | Bag phải < 50 lbs, resealable zip preferred |
| Trái cây sấy | FDA registration nếu bán tại Mỹ |
| Hải sản khô | FDA Prior Notice + import alert check |
| Bánh kẹo | Ingredient list đầy đủ, allergen statement |
```

---

## 9. Module 5 — Content Commerce as a Service

### 9.1 Content Calendar (đã có trong repo — mở rộng)

```javascript
// Mở rộng content_posts với marketplace integration

export const CONTENT_TYPES = {
  product_launch: {
    label: 'Ra mắt sản phẩm',
    templates: ['launch_announcement', 'product_story', 'behind_the_scenes'],
    platforms: ['facebook', 'tiktok', 'zalo', 'shopee_feed'],
    best_times: ['19:00', '20:00', '21:00'],
  },
  flash_sale: {
    label: 'Flash Sale',
    templates: ['countdown_timer', 'discount_announcement'],
    platforms: ['facebook', 'tiktok', 'shopee_feed', 'lazada_feed'],
    best_times: ['12:00', '20:00'],
  },
  ocop_story: {
    label: 'Câu chuyện OCOP',
    templates: ['farmer_story', 'production_process', 'terroir'],
    platforms: ['facebook', 'youtube', 'tiktok'],
    best_times: ['07:00', '12:00', '18:00'],
  },
  livestream: {
    label: 'Livestream bán hàng',
    templates: ['pre_live_announcement', 'live_replay'],
    platforms: ['tiktok', 'facebook', 'shopee_live'],
    best_times: ['19:00', '20:00', '21:00'],
  },
};
```

### 9.2 AI Content Generator

```typescript
// /supabase/functions/ai-content-gen/index.ts

async function generateSocialContent(product: any, contentType: string, platform: string) {
  const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });

  const platformGuide = {
    tiktok: 'Ngắn, hook mạnh trong 3 giây đầu, call-to-action rõ ràng, 3-5 hashtag viral',
    facebook: 'Kể chuyện, cảm xúc, tối đa 300 từ, 1-2 hashtag',
    zalo: 'Ngắn gọn, thân mật, link mua hàng, emoji vừa phải',
    shopee_feed: 'Tập trung vào giá và ưu đãi, 150-200 ký tự',
  };

  const prompt = `
Tạo nội dung ${contentType} cho sản phẩm OCOP trên ${platform}.

Sản phẩm: ${product.name_vi}
Mô tả: ${product.description_vi}
Xuất xứ: ${product.province}, Mekong Delta
Chứng nhận: ${product.certifications?.join(', ') || 'OCOP'}

Hướng dẫn ${platform}: ${platformGuide[platform]}

Output JSON:
{
  "caption": "Nội dung đăng",
  "hashtags": ["list hashtag"],
  "cta": "Call-to-action",
  "best_time": "Giờ đăng tốt nhất"
}
`;

  const result = await model.generateContent(prompt);
  return JSON.parse(result.response.text().replace(/```json|```/g, '').trim());
}
```

### 9.3 Livestream Management

```markdown
## Livestream Checklist cho HTX

### Trước buổi live (24h)
- [ ] Post thông báo lịch live lên Facebook + Zalo
- [ ] Chuẩn bị sản phẩm demo (số lượng đủ cho live)
- [ ] Test setup: mic, camera, lighting, kết nối internet
- [ ] Chuẩn bị script/outline bán hàng
- [ ] Setup mã giảm giá riêng cho live
- [ ] Kết nối TikTok Shop / Shopee Live với store

### Trong buổi live
- [ ] Bắt đầu với hook: giới thiệu sản phẩm trong 30 giây
- [ ] Demo thực tế: mở gói, nếm thử, giải thích quy trình
- [ ] Kể câu chuyện: nông dân, vùng đất, truyền thống
- [ ] Nhắc nhở pin sản phẩm mỗi 5-10 phút
- [ ] Đọc comment và trả lời trực tiếp
- [ ] Flash deal trong 5 phút để tạo FOMO

### Sau buổi live
- [ ] Cắt highlight cho Reels/TikTok
- [ ] Update inventory (trừ số đã bán live)
- [ ] Báo cáo vào AgencyOS: doanh thu, đơn hàng, viewer
```

---

## 10. Module 6 — Analytics & AI Commerce as a Service

### 10.1 Unified Dashboard Architecture

```javascript
// /admin/analytics/index.html

// Aggregated metrics từ tất cả sàn + tất cả merchants
class MekongAnalytics {

  async getPortfolioMetrics(filters = {}) {
    const { province_id, period_days = 30, merchant_id } = filters;

    let query = supabase
      .from('orders')
      .select(`
        id,
        platform,
        normalized_status,
        subtotal,
        agency_commission,
        platform_created_at,
        merchant:merchants(id, business_name, province_id)
      `)
      .gte('platform_created_at', new Date(Date.now() - period_days * 86400000).toISOString())
      .eq('normalized_status', 'delivered');

    if (province_id) query = query.eq('merchant.province_id', province_id);
    if (merchant_id) query = query.eq('merchant_id', merchant_id);

    const { data: orders } = await query;

    // Aggregate
    const metrics = {
      total_gmv: orders.reduce((s, o) => s + (o.subtotal ?? 0), 0),
      total_commission: orders.reduce((s, o) => s + (o.agency_commission ?? 0), 0),
      order_count: orders.length,
      avg_order_value: 0,
      by_platform: {},
      by_province: {},
      daily_trend: {},
    };

    metrics.avg_order_value = metrics.total_gmv / (metrics.order_count || 1);

    // Group by platform
    for (const order of orders) {
      if (!metrics.by_platform[order.platform]) {
        metrics.by_platform[order.platform] = { gmv: 0, orders: 0 };
      }
      metrics.by_platform[order.platform].gmv += order.subtotal ?? 0;
      metrics.by_platform[order.platform].orders += 1;
    }

    return metrics;
  }
}
```

### 10.2 AI Pricing Engine

```typescript
// /supabase/functions/ai-pricing/index.ts

async function suggestOptimalPrice(
  product: any,
  competitorData: any[],
  salesHistory: any[]
): Promise<{ suggested_price: number; reasoning: string; confidence: number }> {

  const model = genAI.getGenerativeModel({ model: 'gemini-1.5-pro' });

  const prompt = `
Bạn là chuyên gia pricing cho nông sản OCOP Việt Nam.

Sản phẩm: ${product.name_vi}
Giá hiện tại: ${product.base_price} VND
Danh mục: ${product.category}

Dữ liệu đối thủ trên ${product.platform}:
${JSON.stringify(competitorData.slice(0, 10), null, 2)}

Lịch sử bán (30 ngày qua):
- Đơn hàng: ${salesHistory.length}
- Revenue: ${salesHistory.reduce((s, o) => s + o.subtotal, 0)} VND
- Avg order qty: ${(salesHistory.reduce((s, o) => s + o.quantity, 0) / salesHistory.length).toFixed(1)}

Đề xuất giá tối ưu. Output JSON:
{
  "suggested_price": số tiền VND,
  "min_price": số tiền VND tối thiểu,
  "max_price": số tiền VND tối đa,
  "reasoning": "giải thích 2-3 câu",
  "confidence": 0-100,
  "action": "increase" | "decrease" | "maintain"
}
`;

  const result = await model.generateContent(prompt);
  return JSON.parse(result.response.text().replace(/```json|```/g, '').trim());
}
```

### 10.3 Demand Forecasting

```javascript
// Simple moving average + Gemini insight

export async function forecastDemand(productId, weeks = 4) {
  const { data: history } = await supabase
    .from('order_items')
    .select('quantity, order:orders(platform_created_at)')
    .eq('product_id', productId)
    .gte('order.platform_created_at', new Date(Date.now() - 90 * 86400000).toISOString());

  // Group by week
  const weeklyData = {};
  for (const item of history ?? []) {
    const week = getWeekNumber(new Date(item.order.platform_created_at));
    weeklyData[week] = (weeklyData[week] ?? 0) + item.quantity;
  }

  const values = Object.values(weeklyData);
  const avg = values.reduce((s, v) => s + v, 0) / values.length;
  const trend = values.length >= 2
    ? (values[values.length - 1] - values[0]) / values.length
    : 0;

  // Forecast next N weeks
  const forecast = [];
  for (let i = 1; i <= weeks; i++) {
    forecast.push(Math.max(0, Math.round(avg + trend * i)));
  }

  return {
    weekly_avg: Math.round(avg),
    trend: trend > 0 ? 'increasing' : trend < 0 ? 'decreasing' : 'stable',
    forecast,
    recommended_stock: Math.round(forecast.reduce((s, v) => s + v, 0) * 1.2), // 20% buffer
  };
}
```

---

## 11. AI Layer — Gemini Integration

### 11.1 AI Module Architecture

```javascript
// /assets/js/ai.js

export class MekongAI {

  static async callEdgeFunction(functionName, payload) {
    const { data: { session } } = await supabase.auth.getSession();

    const response = await fetch(
      `${window.MekongEnv.SUPABASE_URL}/functions/v1/${functionName}`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message ?? `Edge function ${functionName} failed`);
    }

    return response.json();
  }

  /** Tạo listing description đa ngôn ngữ */
  static generateListings(product, platforms, languages) {
    return this.callEdgeFunction('ai-listing-gen', { product, platforms, target_languages: languages });
  }

  /** Phân tích chất lượng ảnh sản phẩm */
  static analyzeImage(imageBase64, mimeType) {
    return this.callEdgeFunction('ai-image-analyze', { imageBase64, mimeType });
  }

  /** Tạo content social media */
  static generateContent(product, contentType, platform) {
    return this.callEdgeFunction('ai-content-gen', { product, contentType, platform });
  }

  /** Gợi ý giá tối ưu */
  static suggestPrice(product, competitorData, salesHistory) {
    return this.callEdgeFunction('ai-pricing', { product, competitorData, salesHistory });
  }
}
```

### 11.2 AI Features Summary

| Feature | Model | Input | Output |
|---------|-------|-------|--------|
| Listing Generation | Gemini 1.5 Flash | Product info + platform | Title, description, keywords |
| Image Analysis | Gemini Vision | Product image base64 | Quality score, suggestions |
| Content Creation | Gemini 1.5 Flash | Product + platform + type | Caption, hashtags, CTA |
| Pricing Suggestion | Gemini 1.5 Pro | Product + competitors + history | Suggested price + reasoning |
| Demand Forecast | Gemini 1.5 Flash | Sales history + seasonality | Weekly forecast |
| Translation | Gemini 1.5 Flash | Vietnamese text | EN / ZH / JA |

---

## 12. API Reference

### 12.1 Supabase REST API

Base URL: `https://<project-id>.supabase.co/rest/v1/`

**Authentication**
```http
Authorization: Bearer <JWT_TOKEN>
apikey: <SUPABASE_ANON_KEY>
```

#### Merchants

```http
# Get merchants (agency staff — all; province_admin — own province)
GET /merchants?select=*,province:provinces(name,code)&order=created_at.desc

# Get single merchant
GET /merchants?id=eq.<UUID>&select=*

# Create merchant
POST /merchants
Content-Type: application/json
{
  "business_name": "HTX Lúa Gạo An Bình",
  "province_id": "<UUID>",
  "business_type": "cooperative",
  "phone": "0901234567",
  "ocop_star": 4
}

# Update onboarding step
PATCH /merchants?id=eq.<UUID>
{ "onboarding_step": 3, "onboarding_status": "in_progress" }
```

#### Products

```http
# List products của merchant
GET /products?merchant_id=eq.<UUID>&status=eq.approved&select=*

# Create product
POST /products
{
  "merchant_id": "<UUID>",
  "name_vi": "Gạo ST25 Sóc Trăng",
  "category": "food",
  "weight_gram": 1000,
  "base_price": 45000,
  "certifications": ["OCOP_5_STAR", "VietGAP"]
}
```

#### Marketplace Listings

```http
# Get listings với performance metrics
GET /marketplace_listings?product_id=eq.<UUID>&select=*,account:marketplace_accounts(platform,platform_shop_name)

# Sync trigger (POST to Edge Function)
POST /functions/v1/marketplace-sync
{
  "merchantId": "<UUID>",
  "platform": "shopee_vn",
  "syncType": "orders"
}
```

#### Orders

```http
# Orders của merchant trong khoảng thời gian
GET /orders?merchant_id=eq.<UUID>&platform_created_at=gte.2026-01-01&select=*,items:order_items(*)&order=platform_created_at.desc

# Orders by normalized status
GET /orders?normalized_status=eq.shipped&merchant_id=eq.<UUID>
```

### 12.2 Edge Functions

| Function | Method | Auth | Description |
|----------|--------|------|-------------|
| `marketplace-sync` | POST | Bearer JWT | Đồng bộ đơn hàng/inventory từ sàn |
| `ai-listing-gen` | POST | Bearer JWT | Tạo listing description bằng Gemini |
| `ai-image-analyze` | POST | Bearer JWT | Phân tích chất lượng ảnh |
| `ai-content-gen` | POST | Bearer JWT | Tạo social content |
| `ai-pricing` | POST | Bearer JWT | Gợi ý giá tối ưu |
| `cert-reminder` | POST | Service Key | Cron: gửi nhắc nhở cert (daily) |
| `report-generator` | POST | Bearer JWT | Tạo báo cáo PDF/Excel |
| `notification-push` | POST | Service Key | Gửi push qua Zalo/Email |

### 12.3 Webhook Receivers

```typescript
// Tất cả webhook nhận qua /supabase/functions/v1/webhook-receiver

// Verify Shopee signature
function verifyShopeeWebhook(req: Request): boolean {
  const timestamp = req.headers.get('X-Shopee-Timestamp');
  const signature = req.headers.get('X-Shopee-Signature');
  const body = req.rawBody;

  const expected = crypto
    .createHmac('sha256', SHOPEE_PARTNER_KEY)
    .update(`${timestamp}|${body}`)
    .digest('hex');

  return signature === expected;
}

// Verify Amazon signature (SQS message)
// Amazon dùng SNS → SQS → Supabase Edge Function

// Event types handled:
// Shopee: ORDER_STATUS_UPDATE, ITEM_STOCK_UPDATE, BANNED_ITEM
// Amazon: ORDER_STATUS_CHANGE, FBA_INVENTORY_AVAILABILITY_CHANGES
// Lazada: order.update, product.update
```

---

## 13. Frontend Architecture

### 13.1 Page Structure

```
/
├── index.html                      # Landing page (marketing)
├── login.html                      # Unified login
├── 403.html                        # Unauthorized
│
├── admin/                          # Agency Admin Portal
│   ├── index.html                  # Dashboard tổng quan
│   ├── merchants/
│   │   ├── index.html              # Danh sách merchants
│   │   ├── new.html                # Onboarding wizard
│   │   └── [id].html               # Chi tiết merchant
│   ├── marketplace/
│   │   ├── index.html              # Multi-platform dashboard
│   │   ├── listings.html           # Quản lý listings
│   │   └── orders.html             # Đơn hàng tổng hợp
│   ├── content/
│   │   ├── calendar.html           # Content calendar
│   │   ├── ai-generate.html        # AI content generator
│   │   └── media-library.html      # Kho media
│   ├── certifications/
│   │   └── index.html              # Cert tracking hub
│   ├── logistics/
│   │   └── index.html              # Shipment management
│   ├── analytics/
│   │   └── index.html              # AI-powered analytics
│   ├── finance/
│   │   ├── invoices.html
│   │   └── commissions.html
│   └── settings/
│       └── index.html
│
├── portal/                         # Client/Merchant Portal
│   ├── index.html                  # Merchant dashboard
│   ├── store/
│   │   └── index.html              # My stores overview
│   ├── orders/
│   │   └── index.html              # My orders
│   ├── products/
│   │   └── index.html              # My products
│   └── reports/
│       └── index.html              # My performance reports
│
└── affiliate/                      # Affiliate Portal
    ├── index.html                  # Affiliate dashboard
    └── referrals/
        └── index.html
```

### 13.2 Web Components

```javascript
// /assets/js/components/merchant-card.js

class MerchantCard extends HTMLElement {
  static get observedAttributes() {
    return ['merchant-id', 'show-stats'];
  }

  async connectedCallback() {
    const merchantId = this.getAttribute('merchant-id');

    const { data: merchant } = await supabase
      .from('merchants')
      .select(`
        *,
        province:provinces(name, theme_color),
        listings:marketplace_listings(count),
        orders:orders(count, subtotal.sum())
      `)
      .eq('id', merchantId)
      .single();

    this.render(merchant);
  }

  render(merchant) {
    const ocop_stars = '★'.repeat(merchant.ocop_star ?? 0) + '☆'.repeat(5 - (merchant.ocop_star ?? 0));

    this.innerHTML = `
      <div class="merchant-card" style="border-left: 3px solid ${merchant.province?.theme_color}">
        <div class="merchant-card__header">
          <span class="merchant-card__name">${merchant.business_name}</span>
          <span class="merchant-card__province">${merchant.province?.name}</span>
        </div>
        <div class="merchant-card__ocop">${ocop_stars}</div>
        <div class="merchant-card__stats">
          <span>${merchant.listings?.count ?? 0} listings</span>
          <span>${MekongUtils.formatCurrency(merchant.orders?.[0]?.sum ?? 0)}</span>
        </div>
        <div class="merchant-card__status status-${merchant.onboarding_status}">
          ${merchant.onboarding_status}
        </div>
      </div>
    `;
  }
}

customElements.define('merchant-card', MerchantCard);
```

### 13.3 MekongUtils — Helper Library

```javascript
// /assets/js/utils.js

export const MekongUtils = {

  /** Format tiền VND */
  formatCurrency(amount, currency = 'VND') {
    if (currency === 'VND') {
      return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND',
        maximumFractionDigits: 0,
      }).format(amount);
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(amount);
  },

  /** Format số lớn */
  formatNumber(num) {
    if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(1)}B`;
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
    return num.toString();
  },

  /** Format ngày tháng */
  formatDate(dateStr, format = 'dd/MM/yyyy') {
    const date = new Date(dateStr);
    if (format === 'dd/MM/yyyy') {
      return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth()+1).toString().padStart(2, '0')}/${date.getFullYear()}`;
    }
    return date.toLocaleDateString('vi-VN');
  },

  /** Debounce search */
  debounce(fn, delay = 300) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  },

  /** Normalize platform name */
  platformLabel(platform) {
    const labels = {
      shopee_vn: 'Shopee VN',
      shopee_sg: 'Shopee SG',
      lazada_vn: 'Lazada VN',
      tiktok_shop_vn: 'TikTok Shop',
      amazon_us: 'Amazon US',
      amazon_jp: 'Amazon JP',
      amazon_sg: 'Amazon SG',
      alibaba_icbu: 'Alibaba Global',
    };
    return labels[platform] ?? platform;
  },

  /** Màu theo platform */
  platformColor(platform) {
    const colors = {
      shopee_vn: '#EE4D2D',
      lazada_vn: '#0F146D',
      tiktok_shop_vn: '#000000',
      amazon_us: '#FF9900',
      alibaba_icbu: '#FF6A00',
    };
    return colors[platform] ?? '#888';
  },

  /** OCOP sao text */
  ocopStars(count) {
    return '★'.repeat(count) + '☆'.repeat(5 - count);
  },
};
```

### 13.4 Environment Configuration

```javascript
// /mekong-env.js — KHÔNG commit lên Git, add vào .gitignore

window.MekongEnv = {
  // Supabase
  SUPABASE_URL: 'https://<project-id>.supabase.co',
  SUPABASE_ANON_KEY: '<anon-key>',

  // Google AI
  GEMINI_API_KEY: '<gemini-api-key>',

  // App config
  APP_NAME: 'Mekong Agency',
  APP_VERSION: '5.10.0',
  DEFAULT_PROVINCE: 'DTP',           // Đồng Tháp default

  // Feature flags
  FEATURES: {
    AMAZON_INTEGRATION: false,       // Enable khi pilot Q4
    AI_PRICING: true,
    BLOCKCHAIN_TRACE: false,         // Enable Q1 2027
    MULTI_PROVINCE: false,           // Enable khi scale
  },
};
```

---

## 14. Deployment & DevOps

### 14.1 Cloudflare Pages Setup

```bash
# Build command: không cần (No-Build philosophy)
# Build output directory: / (root)
# Node.js version: N/A

# Environment variables trên Cloudflare Pages:
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
```

**`_headers` — Security headers:**
```
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=()
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://esm.sh; connect-src 'self' https://*.supabase.co https://generativelanguage.googleapis.com
```

**`_redirects`:**
```
/admin        /admin/index.html  200
/portal       /portal/index.html 200
/affiliate    /affiliate/index.html 200
/login        /login.html        200
```

### 14.2 Supabase Setup

```bash
# Cài supabase CLI
npm install -g supabase

# Init project
supabase init

# Kết nối project
supabase login
supabase link --project-ref <project-id>

# Apply migrations
supabase db push

# Deploy edge functions
supabase functions deploy marketplace-sync
supabase functions deploy ai-listing-gen
supabase functions deploy ai-image-analyze
supabase functions deploy ai-content-gen
supabase functions deploy ai-pricing
supabase functions deploy cert-reminder
supabase functions deploy report-generator
supabase functions deploy notification-push

# Set secrets
supabase secrets set GEMINI_API_KEY=<key>
supabase secrets set SHOPEE_PARTNER_ID=<id>
supabase secrets set SHOPEE_PARTNER_KEY=<key>
supabase secrets set AMAZON_CLIENT_ID=<id>
supabase secrets set AMAZON_CLIENT_SECRET=<secret>
supabase secrets set GHN_API_TOKEN=<token>
supabase secrets set DHL_API_KEY=<key>
supabase secrets set ZALO_OA_TOKEN=<token>
```

### 14.3 Cron Jobs (Supabase pg_cron)

```sql
-- Enable pg_cron
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Sync orders từ tất cả active accounts mỗi 30 phút
SELECT cron.schedule(
  'sync-marketplace-orders',
  '*/30 * * * *',
  $$
    SELECT net.http_post(
      url := current_setting('app.supabase_url') || '/functions/v1/marketplace-sync-all',
      headers := jsonb_build_object('Authorization', 'Bearer ' || current_setting('app.service_key'))
    );
  $$
);

-- Cert reminders mỗi sáng 8h
SELECT cron.schedule(
  'cert-reminders',
  '0 8 * * *',
  $$
    SELECT net.http_post(
      url := current_setting('app.supabase_url') || '/functions/v1/cert-reminder',
      headers := jsonb_build_object('Authorization', 'Bearer ' || current_setting('app.service_key'))
    );
  $$
);

-- Tính commissions cuối tháng
SELECT cron.schedule(
  'calculate-commissions',
  '0 1 1 * *',
  $$
    SELECT net.http_post(
      url := current_setting('app.supabase_url') || '/functions/v1/commission-calc',
      headers := jsonb_build_object('Authorization', 'Bearer ' || current_setting('app.service_key'))
    );
  $$
);
```

### 14.4 GitHub Actions CI

```yaml
# .github/workflows/deploy.yml

name: Deploy to Cloudflare Pages

on:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate HTML
        run: npx html-validate "**/*.html" --ignore "node_modules/**"
      - name: Check JS syntax
        run: node --input-type=module < /dev/null

  deploy:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: sadec-marketing-hub
          directory: .
          gitHubToken: ${{ secrets.GITHUB_TOKEN }}

  deploy-functions:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
      - run: supabase functions deploy --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

### 14.5 Monitoring

```javascript
// /assets/js/monitoring.js — Client-side error tracking

window.addEventListener('error', (event) => {
  // Log to Supabase for internal monitoring
  fetch('/functions/v1/log-error', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      user_id: window.MekongUser?.profile?.id,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    }),
  }).catch(() => {}); // Silent fail
});
```

---

## 15. Business Model & Pricing

### 15.1 Gói dịch vụ (Plans)

```sql
-- Seed plans
INSERT INTO plans (name, code, description, features, fee_setup, fee_monthly, commission_rate) VALUES

('Starter', 'STARTER',
 'Phù hợp HTX mới bắt đầu — 1-2 sàn nội địa',
 '{"platforms": ["shopee_vn", "tiktok_shop_vn"], "products_max": 20, "ai_listings": true, "content_posts_month": 8}',
 2000000, 2000000, 0.05),

('Growth', 'GROWTH',
 'Phù hợp HTX có OCOP 4 sao — đa sàn nội địa + Lazada',
 '{"platforms": ["shopee_vn", "tiktok_shop_vn", "lazada_vn"], "products_max": 100, "ai_listings": true, "content_posts_month": 20, "livestream_month": 2}',
 4000000, 4000000, 0.05),

('Export', 'EXPORT',
 'Phù hợp HTX có chứng nhận quốc tế — Amazon/Alibaba',
 '{"platforms": ["all"], "products_max": 500, "ai_listings": true, "content_posts_month": 40, "livestream_month": 4, "certification_support": true, "logistics_network": true}',
 8000000, 7000000, 0.06),

('Province', 'PROVINCE',
 'Dành cho Sở NN&PTNT — quản lý portfolio OCOP tỉnh',
 '{"merchants_max": 50, "province_dashboard": true, "b2g_reports": true, "all_modules": true}',
 20000000, 15000000, 0.04);
```

### 15.2 Revenue Model

| Nguồn thu | Tính toán | Target Q4 2026 |
|-----------|-----------|----------------|
| Setup fees | 250 merchants × avg 4M | 1 tỷ VND |
| Monthly retainer | 250 × avg 3.5M | 875M VND/tháng |
| Commission (5% GMV) | 5B GMV × 5% | 250M VND/tháng |
| B2G contracts (tỉnh) | 3 tỉnh × 15M | 45M VND/tháng |
| **Monthly Revenue** | | **~1.17 tỷ VND** |

### 15.3 Commission Calculation

```javascript
// Commission theo tầng GMV

function calculateCommission(gmv, plan_code) {
  const rates = {
    STARTER: [
      { threshold: 0,       rate: 0.05 },
    ],
    GROWTH: [
      { threshold: 0,       rate: 0.05 },
      { threshold: 50000000, rate: 0.045 }, // Discount khi GMV > 50M
    ],
    EXPORT: [
      { threshold: 0,       rate: 0.06 },
      { threshold: 100000000, rate: 0.055 },
      { threshold: 500000000, rate: 0.05 },
    ],
  };

  const tiers = rates[plan_code] ?? rates.STARTER;
  let rate = tiers[0].rate;

  for (const tier of tiers) {
    if (gmv >= tier.threshold) rate = tier.rate;
  }

  return {
    gmv,
    rate,
    commission: Math.round(gmv * rate),
  };
}
```

---

## 16. Lộ trình phát triển

### 16.1 Sprint Planning

#### Q2 2026 — MVP Launch (Shopee + TikTok Shop)
```
Sprint 1 (2 tuần):
  ✅ Merchant onboarding wizard (7 steps)
  ✅ Product CRUD + media upload
  ✅ Shopee OAuth integration
  ✅ Basic marketplace listings UI

Sprint 2 (2 tuần):
  ✅ Shopee order sync (Edge Function)
  ✅ AI listing generation (Gemini)
  ✅ TikTok Shop OAuth + listing
  ✅ Client portal (merchant view)

Sprint 3 (2 tuần):
  ✅ Finance dashboard (invoices)
  ✅ Affiliate module
  ✅ Zalo notification
  ✅ 50 merchant pilot (Sa Đéc + Đồng Tháp)
```

#### Q3 2026 — Brand & Content
```
Sprint 4-6:
  □ AI image analyzer (Gemini Vision)
  □ Content calendar + scheduler
  □ Media library + approval workflow
  □ Lazada integration
  □ Province admin role + dashboard
  □ 100 thêm merchants (5 tỉnh)
```

#### Q4 2026 — International
```
Sprint 7-9:
  □ Amazon SP-API integration (pilot 10 SKUs)
  □ Alibaba ICBU integration
  □ Certification Hub (HACCP, GlobalGAP tracker)
  □ Logistics integration (GHN, DHL)
  □ Multi-currency (USD, CNY)
  □ 100 thêm merchants (target 250 total)
```

#### Q1 2027 — Scale
```
Sprint 10-12:
  □ 13-province white-label deployment
  □ AI pricing engine
  □ Demand forecasting
  □ B2G dashboard (Sở NN&PTNT)
  □ Blockchain traceability (pilot)
  □ Scale to 500 merchants
```

### 16.2 Technical Debt Backlog

| Priority | Item | Effort | Notes |
|----------|------|--------|-------|
| P0 | Token encryption cho marketplace creds | 3 days | Security critical |
| P0 | Rate limiting cho Edge Functions | 2 days | Cost control |
| P1 | Offline support (PWA) cho portal | 5 days | Rural connectivity |
| P1 | Bulk product import (CSV/Excel) | 3 days | Onboarding acceleration |
| P2 | Mobile app (PWA wrapper) | 10 days | Field merchant use |
| P2 | Advanced search + filtering | 4 days | Scale requirement |
| P3 | A/B testing cho listings | 7 days | Optimization |

---

## 17. Glossary

| Term | Định nghĩa |
|------|-----------|
| **OCOP** | One Commune One Product — Chương trình "Mỗi xã một sản phẩm" của VN |
| **HTX** | Hợp tác xã |
| **ĐBSCL** | Đồng bằng sông Cửu Long (Mekong Delta) |
| **RaaS** | Retail-as-a-Service — Mô hình agency cung cấp toàn bộ hạ tầng bán lẻ dưới dạng dịch vụ |
| **GMV** | Gross Merchandise Value — Tổng giá trị hàng hóa giao dịch |
| **FBA** | Fulfillment by Amazon — Amazon tự lưu kho và giao hàng |
| **ICBU** | International Commerce Business Unit — Nhánh xuất khẩu của Alibaba |
| **SKU** | Stock Keeping Unit — Đơn vị quản lý tồn kho |
| **SP-API** | Selling Partner API của Amazon |
| **GlobalG.A.P.** | Chứng nhận thực hành nông nghiệp tốt toàn cầu |
| **HACCP** | Hazard Analysis Critical Control Points — Phân tích mối nguy và kiểm soát điểm tới hạn |
| **UPC/EAN** | Mã vạch sản phẩm quốc tế |
| **FNSKU** | Fulfillment Network SKU — Mã SKU của Amazon cho FBA |
| **KOC/KOL** | Key Opinion Consumer / Leader — Người ảnh hưởng trên mạng xã hội |
| **RLS** | Row Level Security — Bảo mật tầng dòng dữ liệu trong PostgreSQL |
| **Edge Function** | Serverless function chạy gần người dùng (Supabase/Cloudflare) |
| **CTP** | Cần Thơ — Trung tâm kinh tế ĐBSCL |
| **B2G** | Business to Government — Bán dịch vụ cho cơ quan nhà nước |
| **MRR** | Monthly Recurring Revenue — Doanh thu định kỳ hàng tháng |
| **Retainer** | Phí dịch vụ trả hàng tháng theo hợp đồng |

---

## Appendix A — Quick Start cho Developer

```bash
# 1. Clone repo
git clone https://github.com/huuthongdongthap/sadec-marketing-hub.git
cd sadec-marketing-hub

# 2. Tạo env file
cp mekong-env.js.example mekong-env.js
# Điền SUPABASE_URL, SUPABASE_ANON_KEY, GEMINI_API_KEY

# 3. Khởi động local server
npx serve .
# Hoặc: python3 -m http.server 3000

# 4. Apply database migrations
supabase db push

# 5. Deploy edge functions (dev)
supabase functions serve

# 6. Truy cập
# Admin: http://localhost:3000/admin
# Portal: http://localhost:3000/portal
# Login: admin@mekongmarketing.com / admin123
```

## Appendix B — Checklist Onboard Merchant Đầu tiên

```
Ngày 1:
  □ Tạo account trong hệ thống
  □ Điền thông tin cơ bản (business info, OCOP cert)
  □ Upload ít nhất 3 sản phẩm + ảnh
  □ AI analyze ảnh → check quality

Ngày 2:
  □ Agency review + approve products
  □ Tạo Shopee account (hoặc kết nối có sẵn)
  □ AI generate listing descriptions
  □ Agency check + chỉnh sửa nếu cần

Ngày 3:
  □ Push listings lên Shopee
  □ Setup TikTok Shop (nếu trong plan)
  □ Training merchant: cách xem orders, cách chat khách hàng
  □ Setup Zalo notification

Tuần 1-2:
  □ Monitor orders và support
  □ Content first posts (3-5 posts)
  □ Review sau 2 tuần, điều chỉnh strategy
```

---

*Tài liệu này được duy trì bởi team Mekong Agency.*  
*Mọi thay đổi phải được review bởi Tech Lead và cập nhật CHANGELOG.md.*  
*© 2026 Mekong Agency. All rights reserved.*
