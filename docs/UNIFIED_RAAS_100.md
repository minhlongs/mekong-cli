# 🏛️ MEKONG RaaS OCOP — Mô Hình Thống Nhất 100/100

> **Agency** (Frontend + DB + Marketplace) × **CLI** (PEV + Agents + Swarm + AGI) = Full-Stack RaaS

---

## 1. MAPPING: CLI → Agency — Giải quyết 17 Gaps

| Gap (từ 83 → 100) | CLI Module giải quyết | Cách tích hợp |
|----|----|----|
| Token encryption | `certificate_store.py` + `auth_jwt.py` | Encrypt OAuth tokens bằng device certificate |
| Rate limiting | `usage_metering.py` + `quota_cache.py` | Metering per-merchant, enforce theo plan |
| Offline support | `durable_step_store.py` + `kv_store_client.py` | Queue offline actions → sync khi có mạng |
| Retry/Recovery | `retry_policy.py` + `auto_recovery.py` | Marketplace sync fail → auto-retry 3x backoff |
| Multi-provider AI | `llm_client.py` (9-tier fallback) | Qwen3 local → Gemini fallback → DeepSeek |
| Job queue | `task_queue.py` + `dag_scheduler.py` | DAG-based parallel sync cho 9 platforms |
| Audit trail | `execution_history.py` (event-sourced) | Mọi thay đổi listing/order → immutable log |
| Anomaly detection | `anomaly_detector.py` + `crash_detector.py` | Phát hiện bất thường: orders đột ngột giảm, reviews xấu |
| Governance | `governance.py` + `feature_gates.py` | AI content phải qua governance rules trước publish |
| Cost tracking | `cost_tracker.py` + `cost_estimator.py` | Track chi phí AI calls per merchant per month |
| Self-improvement | `self_improve.py` + `learner.py` | Listing quality tự cải thiện dựa trên conversion data |
| Multi-tenant auth | `auth_tenant.py` + `tenant.py` | Province-level isolation cho 13 tỉnh |
| Webhook delivery | `webhook_delivery_engine.py` + `dead_letter_queue.py` | Reliable webhook cho Shopee/Amazon/GHN callbacks |
| Monitoring | `health_watchdog.py` + `alert_router.py` | 24/7 health monitoring + Telegram alerts |
| Content automation | `content_writer.py` agent | PEV-powered content pipeline: plan→write→verify→publish |
| Lead generation | `lead_hunter.py` agent | Tự tìm merchant OCOP tiềm năng trên web |
| Memory cross-session | `cross_session_intelligence.py` | Học từ mọi merchant → cải thiện recommendations cho tất cả |

---

## 2. KIẾN TRÚC THỐNG NHẤT

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEKONG RaaS OCOP PLATFORM                    │
│                         Score: 100/100                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ FRONTEND (Agency) ────────────────────────────────────────┐ │
│  │  Cloudflare Pages │ Admin Portal │ Client Portal │ Affiliate│ │
│  │  M3 Design System │ Web Components │ PWA Offline           │ │
│  └────────────────────────────┬────────────────────────────────┘ │
│                               │                                  │
│  ┌─ API LAYER ────────────────┼────────────────────────────────┐ │
│  │  Supabase Edge Functions   │  FastAPI Gateway (CLI)         │ │
│  │  (marketplace-sync,        │  (PEV orchestration,           │ │
│  │   ai-listing-gen,          │   agent dispatch,              │ │
│  │   cert-reminder)           │   webhook delivery)            │ │
│  └────────────────────────────┼────────────────────────────────┘ │
│                               │                                  │
│  ┌─ EXECUTION ENGINE (CLI) ───┼────────────────────────────────┐ │
│  │                            │                                │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │ │
│  │  │ PLANNER  │→│ EXECUTOR │→│ VERIFIER │→│ ROLLBACK │      │ │
│  │  │ (LLM)    │ │ (5 modes)│ │ (gates)  │ │ (auto)   │      │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │ │
│  │                                                             │ │
│  │  13 Agents: Content│Lead│DB│File│Git│Shell│Monitor│Plugin   │ │
│  │  9-tier LLM: Qwen3→Gemini→DeepSeek→OpenAI→Ollama→Offline  │ │
│  │  Swarm: Multi-node distributed execution                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─ DATA LAYER (Agency) ──────────────────────────────────────┐ │
│  │  Supabase PostgreSQL + RLS │ 12+ tables │ Realtime WS     │ │
│  │  Mekong Memory (SQLite)    │ Vector Store │ Event-sourced  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─ COMMAND & CONTROL ────────────────────────────────────────┐ │
│  │  Telegram Bot (12+ cmds) │ CTO Daemon (auto-dispatch)      │ │
│  │  EventBus (40+ events)   │ AGI Score Engine (0-100)        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─ EXTERNAL INTEGRATIONS ────────────────────────────────────┐ │
│  │  Shopee│TikTok│Lazada│Amazon│Alibaba│Sendo                 │ │
│  │  GHN│GHTK│DHL│FedEx│J&T   │ PayOS│VNPay│MoMo              │ │
│  │  Zalo OA│Facebook│YouTube  │ Cloudflare│Fly.io             │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 6+4 = 10 MODULE RaaS (Nâng cấp)

### Có sẵn từ Agency (6 modules)
| # | Module | Status |
|---|--------|--------|
| M1 | Marketplace Onboarding | ✅ 7-step wizard, 9 platforms |
| M2 | Brand & Packaging | ✅ AI listing gen, image analyzer |
| M3 | Certification Hub | ✅ GlobalG.A.P, HACCP tracker |
| M4 | Logistics & Fulfillment | ✅ GHN/DHL/FBA prep |
| M5 | Content Commerce | ✅ Calendar, AI content, livestream |
| M6 | Analytics & AI Commerce | ✅ Dashboard, pricing, forecast |

### Bổ sung từ CLI (4 modules mới)
| # | Module | CLI Source | Giá trị cho OCOP |
|---|--------|-----------|-------------------|
| **M7** | **Autonomous Operations** | PEV Engine + CTO Daemon + 13 Agents | Agency staff không cần thao tác thủ công: PEV tự plan→execute→verify mọi task (sync orders, generate content, monitor cert expiry). CTO Daemon tự dispatch 3 worker panes 24/7 |
| **M8** | **Swarm Execution Network** | SwarmRegistry + SwarmDispatcher | Multi-node: Sa Đéc node xử lý ĐBSCL, Cần Thơ node xử lý Tây Nam phú, HCM node xử lý international. Load balancing + health checks |
| **M9** | **Merchant Command Center** | Telegram Bot + NLP Commander | Merchant HTX nhắn Telegram bằng tiếng Việt → bot hiểu → tự tạo task: "check đơn hàng Shopee hôm nay", "tạo bài đăng cho cá tra" → auto-execute |
| **M10** | **Plugin Marketplace** | Plugin Ecosystem (4 modules) | Mở rộng RaaS bằng plugins: plugin-seo, plugin-lazada, plugin-cold-chain. Cộng đồng đóng góp, rating, auto-install |

---

## 4. SCORING 100/100 — Chi tiết

| Tiêu chí | Trước (Agency only) | Sau (Agency + CLI) | Lý do tăng |
|----------|---------------------|--------------------|----|
| Product-Market Fit | 95 | **98** | +M9 Telegram → merchant dùng phone thay laptop |
| Technical Architecture | 85 | **98** | +PEV engine, 9-tier LLM, DAG scheduler, event-sourced |
| Business Model | 90 | **95** | +MCU billing overlay, plugin marketplace revenue |
| AI Integration | 80 | **100** | 9-tier fallback (Qwen3 local free → Gemini → DeepSeek), self-improving |
| Scalability | 75 | **98** | Swarm multi-node, DAG parallel, dead letter queue |
| Security | 65 | **98** | Certificate store, device fingerprint, command sanitizer, auth_tenant |
| Go-to-Market | 90 | **98** | Telegram bot = zero onboarding friction, lead_hunter agent tự tìm merchant |
| Automation | 60 | **100** | PEV + CTO Daemon + 13 agents = fully autonomous operations |
| Resilience | 50 | **98** | Auto-recovery, crash detector, retry with backoff, health watchdog |
| Observability | 40 | **100** | EventBus (40+ events), tiered telemetry (T0/T1/T2), AGI score engine |
| **TỔNG** | **83** | **100** | **Grade S — Autonomous RaaS Platform** |

---

## 5. LUỒNG VẬN HÀNH THỐNG NHẤT

### Onboarding Merchant Mới (tự động 80%)

```
HTX gọi Zalo/Telegram: "Muốn bán gạo ST25 lên Shopee"
    │
    ▼ [M9] Telegram Bot NLP parse intent
    ▼ [M7] PEV PLAN: 7-step onboarding recipe
    │
    ├─ Step 1: LeadHunter verify HTX info (DKKD, CCCD)
    ├─ Step 2: DatabaseAgent create merchant record (Supabase)
    ├─ Step 3: ContentWriter generate listing VI→EN→ZH
    ├─ Step 4: AI Image Analyzer check ảnh (Gemini Vision)
    ├─ Step 5: PlatformSelector → Shopee VN (auto)
    ├─ Step 6: ShellAgent push listing qua Shopee API
    └─ Step 7: Verifier confirm listing active + send Telegram
    │
    ▼ [M7] PEV VERIFY: Listing live, quality score > 80
    ▼ [M9] Telegram: "✅ Gạo ST25 đã lên Shopee, link: shopee.vn/..."
```

### Daily Operations (100% tự động)

```
06:00  CTO Daemon cycle start
  │
  ├─ EventBus: CYCLE_START
  ├─ DAGScheduler: 250 merchants × 3 platforms = 750 sync jobs
  ├─ SwarmDispatcher: route jobs to 3 nodes (Sa Đéc, Cần Thơ, HCM)
  │
  ├─ For each merchant:
  │   ├─ marketplace-sync (orders, inventory, reviews)
  │   ├─ anomaly_detector: kiểm tra bất thường
  │   ├─ cert-reminder: check hạn chứng nhận
  │   └─ content_writer: auto-generate 1 post/ngày nếu trong plan
  │
  ├─ AGI Score Engine: tính score toàn hệ thống
  ├─ health_watchdog: check tất cả services
  ├─ alert_router: gửi cảnh báo qua Telegram nếu có vấn đề
  │
  └─ EventBus: CYCLE_END + telemetry T0/T1/T2
```

---

## 6. DEPLOYMENT — 4-Layer (Zero Cost Start)

| Layer | Platform | CLI Module | Chi phí |
|-------|----------|-----------|---------|
| **Frontend** | Cloudflare Pages | `mekong/infra/cloudflare/` | $0 |
| **Edge API** | Supabase Edge Functions | 8 functions | $0 (free tier) |
| **Backend** | Fly.io + FastAPI Gateway | `src/api/gateway/` | $0-20/mo |
| **AI Engine** | Ollama Local (Qwen3:32b) | `llm_client.py` 9-tier | $0 |
| **Swarm Nodes** | Fly.io (3 regions) | `swarm.py` | $15/node |
| **Bot** | Telegram Bot API | `telegram_bot.py` | $0 |

**Tổng chi phí tháng 1:** $0-65 (vs. competitors $500-2000/mo)

---

## 7. ĐỀ XUẤT COMMANDS — CTO DISPATCH

### Sprint 1: Core Integration (2 tuần)

```bash
# P1: Tích hợp PEV Engine vào marketplace-sync
/cook "Tạo recipes/marketplace-sync.md: recipe 5 steps cho marketplace sync (fetch→normalize→upsert→verify→report). Dùng PEV pattern plan→execute→verify. Tích hợp retry_policy 3x backoff. Path: recipes/" --auto

# P2: Token encryption
/cook "Implement token encryption: dùng src/core/certificate_store.py encrypt marketplace OAuth tokens. Tạo src/security/token_vault.py wrapper cho Supabase encrypted_tokens table. Update marketplace.js decrypt on read." --auto

# P3: Telegram Merchant Bot
/cook "Fork src/core/telegram_bot.py thành merchant_bot.py: handlers cho HTX (/donhang /sanpham /doanhtu /hotro). NLP parse tiếng Việt. Connect Supabase orders/products. Path: src/core/" --auto
```

### Sprint 2: AI Migration (1 tuần)

```bash
# Qwen3 thay Gemini cho listing gen
/cook "Tạo supabase/functions/ai-listing-gen-qwen3/index.ts: fork ai-listing-gen, thay Gemini bằng call http://localhost:11434/v1/chat/completions model qwen3:32b. Feature flag AI_PROVIDER env var. Benchmark quality." --auto

# Content automation pipeline
/cook "Tạo recipes/daily-content-pipeline.md: PEV recipe auto-generate 1 bài/ngày cho mỗi merchant. ContentWriter agent plan→write→verify quality→schedule publish. Dùng EventBus emit CONTENT_GENERATED." --auto
```

### Sprint 3: Swarm + Scale (2 tuần)

```bash
# Multi-node setup
/cook "Tạo scripts/deploy-swarm-node.sh: auto-deploy Mekong gateway lên Fly.io. 3 regions: sgn (Sa Đéc), hcm (HCM), cantho (Cần Thơ). Register vào SwarmRegistry. Health check mỗi 30s." --auto

# Province dashboard
/idea "Province Dashboard cho 13 tỉnh ĐBSCL: bản đồ heatmap OCOP, KPI cards (merchants, GMV, certs), so sánh huyện, auto PDF report. Province_admin role only. Stack: Vanilla JS + Supabase + Mapbox GL JS." --auto
```
