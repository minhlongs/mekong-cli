# 🧠 /brainstorm — Phân Tích MEKONG RaaS Platform Docs

**File:** `MEKONG_RAAS_DOCS.md` (2676 dòng, 89KB)
**Version:** AgencyOS 2026 v1.0
**Phân tích:** 2026-03-27

---

## 1. ĐÁNH GIÁ TỔNG QUAN

### ✅ Điểm mạnh

| Hạng mục | Đánh giá | Chi tiết |
|----------|----------|----------|
| **Tầm nhìn sản phẩm** | ⭐⭐⭐⭐⭐ | RaaS cho OCOP — giải bài toán thực tế 3,900 sản phẩm ĐBSCL chưa vào thị trường quốc tế |
| **DB Schema** | ⭐⭐⭐⭐⭐ | 12+ tables, RLS policies, foreign keys, check constraints — rất chặt chẽ |
| **RBAC** | ⭐⭐⭐⭐ | 6 roles, permission matrix rõ ràng, `auth.js` centralized |
| **AI Layer** | ⭐⭐⭐⭐ | 6 AI features qua Gemini, Edge Functions kiến trúc sạch |
| **No-Build Philosophy** | ⭐⭐⭐⭐ | Zero bundler = deploy = upload files, dễ maintain |
| **Business Model** | ⭐⭐⭐⭐⭐ | Setup fees + retainer + commission — 3 nguồn thu rõ ràng, target 1.17 tỷ/tháng |
| **Marketplace Coverage** | ⭐⭐⭐⭐ | 9 platforms (Shopee, TikTok, Lazada, Amazon US/JP/SG, Alibaba, Sendo) |
| **Certification Hub** | ⭐⭐⭐⭐⭐ | GlobalG.A.P, HACCP, OCOP upgrade — roadmap chi tiết, auto-reminder |

### ⚠️ Gaps & Risks

| Gap | Severity | Đề xuất |
|-----|----------|---------|
| **Không có offline support** | 🔴 HIGH | HTX vùng sâu ĐBSCL internet yếu — cần PWA + IndexedDB cache |
| **Token encryption chưa có** | 🔴 CRITICAL | Marketplace creds (OAuth tokens) chưa encrypted — P0 security |
| **Rate limiting Edge Functions** | 🔴 HIGH | Cost overrun risk — mỗi Gemini call tốn tiền |
| **Không có error recovery** | 🟡 MED | Sync engine fail → status stuck "syncing" mãi |
| **Single-region Supabase** | 🟡 MED | Latency cho merchant ở các tỉnh xa |
| **Chưa có bulk import** | 🟡 MED | 250+ merchants × 20 products = 5000 SKUs bằng tay? |
| **Không có versioning cho listings** | 🟢 LOW | Cần audit trail khi AI modify content |
| **Chưa có dashboard mobile** | 🟡 MED | Merchant HTX dùng phone nhiều hơn laptop |

---

## 2. BRAINSTORM — CƠ HỘI CHIẾN LƯỢC

### 🚀 Opportunity 1: Qwen3 Local thay Gemini → Giảm chi phí AI 100%

**Hiện tại:** Gemini API mỗi call tốn tiền, 6 features × 500 merchants = hàng ngàn calls/ngày.

**Đề xuất:** Thay Gemini bằng Qwen3 32B local (đã config Ollama) cho các task:
- Listing generation (Qwen3 output quality tương đương Flash)
- Content creation (caption, hashtags)
- Translation VI→EN/ZH/JA
- Giữ Gemini Vision cho image analysis (Qwen3 chưa mạnh vision)

**ROI:** ~$500-2000/tháng savings, tốc độ nhanh hơn (local), không dependency Google.

### 🚀 Opportunity 2: B2G Contract Engine — Sở NN&PTNT

**Hiện tại:** Gói Province 15M/tháng / tỉnh, 13 tỉnh ĐBSCL.

**Đề xuất:** Xây dashboard riêng cho Sở NN&PTNT:
- Bản đồ OCOP heatmap
- KPI report auto-generated (PDF)
- So sánh performance giữa các huyện
- Integration với Hệ thống quản lý OCOP quốc gia

**ROI:** 13 tỉnh × 15M = 195M MRR, + upgrade contracts 30-50M/tỉnh.

### 🚀 Opportunity 3: LiveCommerce-as-a-Service

**Hiện tại:** Chỉ có checklist livestream, chưa có tool hỗ trợ.

**Đề xuất:**
- **Pre-live:** AI auto-generate script từ sản phẩm list
- **In-live:** Real-time order tracker overlay → KDS sync
- **Post-live:** Auto-cut highlights → Reels/TikTok
- **Analytics:** View, conversion, GMV /session

**ROI:** Livestream tăng GMV 3-5x, commission tăng theo.

### 🚀 Opportunity 4: Cold Chain Tracking (IoT)

**Hiện tại:** Logistics chỉ track vị trí, không track nhiệt độ.

**Đề xuất:** Tích hợp IoT sensor (nhiệt độ, độ ẩm) cho hàng tươi/hải sản ĐBSCL:
- Webhook từ sensor device → Supabase
- Alert khi nhiệt độ vượt ngưỡng
- Blockchain hash cho certificate of origin

**ROI:** Mở cung đường EU/Nhật yêu cầu cold chain proof. Premium pricing.

### 🚀 Opportunity 5: Affiliate → KOC Network

**Hiện tại:** Affiliate module theo hoa hồng cố định.

**Đề xuất:**
- Xây KOC marketplace: content creator đăng ký → nhận sản phẩm → review
- AI match: KOC profile → loại sản phẩm OCOP phù hợp
- Tracking ROI per KOC, auto-payment

**ROI:** GMV tăng 2-3x qua referral, organic content miễn phí.

---

## 3. PHÂN TÍCH KỸ THUẬT CHI TIẾT

### Database Schema — Recommendations

```diff
# Thêm bảng audit trail
+ CREATE TABLE listing_versions (
+   id UUID PRIMARY KEY,
+   listing_id UUID REFERENCES marketplace_listings(id),
+   version INT,
+   changes JSONB,
+   changed_by UUID,
+   created_at TIMESTAMPTZ
+ );

# Thêm token encryption
+ CREATE TABLE encrypted_tokens (
+   id UUID PRIMARY KEY,
+   account_id UUID REFERENCES marketplace_accounts(id),
+   encrypted_access_token BYTEA,
+   encrypted_refresh_token BYTEA,
+   encryption_key_id TEXT
+ );

# Thêm sync job queue
+ CREATE TABLE sync_jobs (
+   id UUID PRIMARY KEY,
+   account_id UUID,
+   job_type TEXT,
+   status TEXT DEFAULT 'pending',
+   attempts INT DEFAULT 0,
+   max_attempts INT DEFAULT 3,
+   error_message TEXT,
+   scheduled_at TIMESTAMPTZ,
+   started_at TIMESTAMPTZ,
+   completed_at TIMESTAMPTZ
+ );
```

### AI Layer — Qwen3 Migration Path

| Feature | Gemini | Qwen3 Local | Action |
|---------|--------|-------------|--------|
| Listing Gen | Flash | ✅ qwen3:32b | Migrate |
| Image Analysis | Vision | ❌ Not ready | Keep Gemini |
| Content Creation | Flash | ✅ qwen3:32b | Migrate |
| Pricing Engine | Pro | ⚠️ Test needed | Pilot |
| Translation | Flash | ✅ qwen3:32b | Migrate |
| Demand Forecast | Flash | ✅ qwen3:32b | Migrate |

### Architecture Improvement Suggestions

1. **Job Queue cho Sync:** Thay direct Edge Function → queue-based (Supabase pg_cron enqueue)
2. **Retry with backoff:** Marketplace API fail → retry 3x với exponential backoff
3. **Cache Layer:** Supabase Edge Functions cache Gemini/Qwen responses → giảm duplicate calls
4. **Feature Flags:** Đã có trong `MekongEnv.FEATURES` — extend cho A/B testing
5. **Multi-tenant isolation:** Khi scale 13 tỉnh → schema-based hoặc RLS-based isolation

---

## 4. SCORING

| Tiêu chí | Score | Notes |
|----------|-------|-------|
| Product-Market Fit | 95/100 | OCOP ĐBSCL là pain point thực, giải pháp rất cụ thể |
| Technical Architecture | 85/100 | No-build + Supabase + CF Pages solid, thiếu offline + security |
| Business Model | 90/100 | 3 nguồn thu, unit economics rõ, B2G premium |
| AI Integration | 80/100 | Gemini only → cần multi-provider (Qwen3 fallback) |
| Scalability | 75/100 | OK cho 500 merchants, cần re-architect cho 5000+ |
| Security | 65/100 | Token encryption chưa có, RLS chưa cover hết |
| Go-to-Market | 90/100 | Pilot Sa Đéc → 13 tỉnh ĐBSCL = clear expansion path |
| **TỔNG** | **83/100** | **Grade A — Production-ready MVP, cần harden security** |

---

## 5. ĐỀ XUẤT COMMANDS — GIAO CTO

### Immediate (Sprint hiện tại)

```bash
# P1 — TIÊN PHONG: Security hardening
/cook "Implement token encryption cho marketplace_accounts: tạo encrypted_tokens table, dùng pgcrypto pgp_sym_encrypt/decrypt cho access_token và refresh_token. Update marketplace.js để encrypt trước khi save, decrypt khi dùng." --auto

# P2 — CÔNG BINH: Offline support
/cook "Tạo service-worker.js cho PWA support: cache static assets, IndexedDB queue cho offline orders/products. Thêm manifest.json, install prompt, offline-first cho portal/" --auto

# P3 — HIẾN BINH: Rate limiting
/cook "Tạo supabase/functions/rate-limiter/index.ts: track AI API calls per merchant per day, enforce limit dựa trên plan (Starter=50, Growth=200, Export=500 calls/day). Return 429 khi exceed." --auto
```

### Next Sprint — AI Migration

```bash
# Migrate Listing Gen to Qwen3
/cook "Fork supabase/functions/ai-listing-gen sang dùng Qwen3 32B qua Ollama API http://localhost:11434/v1. Giữ fallback Gemini nếu Ollama down. Feature flag: AI_PROVIDER=qwen3|gemini." --auto

# Migrate Content Gen to Qwen3
/cook "Fork supabase/functions/ai-content-gen sang dùng Qwen3 32B. Prompt format giữ nguyên, chỉ đổi endpoint. Benchmark quality vs Gemini Flash, log both results cho A/B testing." --auto
```

### Strategic — B2G Dashboard

```bash
# Province Dashboard
/idea "Province Dashboard cho Sở NN&PTNT: bản đồ OCOP heatmap theo huyện, KPI cards (merchants, GMV, certifications, new products), auto PDF report generator, so sánh huyện vs huyện. Stack: Vanilla JS + Supabase + Mapbox GL JS. Path: admin/province-dashboard.html" --auto
```
