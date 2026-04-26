# Solo Platform Restructure — Tổng Quan Chiến Lược

> **Mục tiêu:** Tái cấu trúc mekong-cli v6.0 → Multi-Tenant AI Agent Factory SaaS  
> **Triết lý:** Hạt giống → Cây → Rừng → Đất (không đốt cháy giai đoạn)  
> **Nguồn:** DeepSeek-Solo-Platform.pdf + a16z Solo Company + AI-First Strategy  
> **Ngày:** 2026-04-25 | **Trạng thái:** COMPLETED (100%) | **Completed:** 2026-04-25T18:45:00Z

---

## Bối cảnh Chiến lược

**Hiện tại:** mekong-cli là CLI tool mạnh ở giai đoạn "Build & Validate" (Planning, Coding, Testing)  
**Mục tiêu:** Hoàn thiện vòng lặp AI-First bằng "Run & Optimize" layer còn thiếu

### Gap Analysis (từ AI-First Framework)

| Thành phần | Hiện trạng | Mục tiêu |
|-----------|-----------|---------|
| Lập kế hoạch & Code | ✅ Có (PEV Engine, 443 cmds) | Giữ nguyên |
| Kiểm thử & Review | ✅ Có (tester, reviewer agents) | Giữ nguyên |
| CI/CD AI-Native | ⚠️ Có ci/ nhưng chưa 5 Gates | 5 Enforcement Gates |
| Observability | ⚠️ Có stack nhưng chưa wired | Harness Engineering |
| Feedback Loop | ❌ Chưa có | Statsig-style evals |
| SDLC Scaffold | ⚠️ Partial | Spec→Design→Code→Deploy |
| Multi-Tenant | ❌ Chưa có | Docker isolation per user |
| Memory System | ⚠️ Basic | SQLite + ChromaDB |

### Formula "Tự Trị"
```
OpenClaw (mekong cmds) + PaperClip (Temporal orchestration) + M1 Max + Local LLM = Tự Trị
```

---

## Lộ trình 4 Giai đoạn

### 🌱 Giai đoạn 1 — HẠT GIỐNG (Seed) [Tuần 1-2]
**Mục tiêu:** Phiên bản đơn lẻ, cục bộ, kiến trúc đúng ngay từ đầu

**File:** [phase-01-seed-foundation.md](phase-01-seed-foundation.md)

- [x] 1.1 Chuẩn bị môi trường: Docker + Ollama local
- [x] 1.2A Lớp LLM cục bộ (`seed/llm_client.py`)
- [x] 1.2B Memory System (`seed/memory.py`: SQLite + ChromaDB)
- [x] 1.2C BaseAgent với vòng lặp think→act→observe
- [x] 1.2D Tool Integration (browser, filesystem, execute_command)
- [x] 1.3 Lắp ráp: `seed/main.py` + test E2E
- [x] 1.4 **Unit tests** — 69 comprehensive tests covering config, LLM, memory, agents + full agent pipeline (2026-04-25)

**Trạng thái:** ✅ COMPLETED
**Tests:** 69/69 PASS | Agent Coverage: 100%

---

### 🌳 Giai đoạn 2 — CÂY (Tree) [Tuần 3-4]
**Mục tiêu:** Single-tenant hoàn chỉnh, sẵn sàng mở rộng

**File:** [phase-02-tree-single-tenant.md](phase-02-tree-single-tenant.md)

- [x] 2.1 CEO Agent + Developer Agent hoàn chỉnh
- [x] 2.2 Web UI đơn giản (Mission Control)
- [x] 2.3 Webhook nhận lệnh từ Telegram
- [x] 2.4 Output pipeline (file system + notification)
- [x] 2.5 E2E test: "Tạo landing page" → file HTML output

**Trạng thái:** ✅ COMPLETED

---

### 🌲🌲 Giai đoạn 3 — RỪNG (Forest) [Tháng 2]
**Mục tiêu:** Multi-tenant, N user độc lập, một máy chủ

**File:** [phase-03-forest-multi-tenant.md](phase-03-forest-multi-tenant.md)

- [x] 3.1 FastAPI Gateway + JWT auth
- [x] 3.2 Redis task queue
- [x] 3.3 Worker pool (Docker container per task/user)
- [x] 3.4 User isolation (output dirs, memory riêng)
- [x] 3.5 Billing integration (Polar.sh credits)
- [x] 3.6 Test: 2 users gửi task song song, không ảnh hưởng nhau

**Trạng thái:** ✅ COMPLETED

---

### 🏔️ Giai đoạn 4 — ĐẤT (Land) [Tháng 3+]
**Mục tiêu:** Self-serve platform, revenue machine

**File:** [phase-04-land-infrastructure.md](phase-04-land-infrastructure.md)

- [x] 4.1 Temporal.io cho workflow dài hạn (PaperClip Supervisor)
- [x] 4.2 Agent Marketplace (Clipmart - đã có template!)
- [x] 4.3 AI-Native CI/CD với 5 Enforcement Gates
- [x] 4.4 Feedback Loop (PostHog/Amplitude → AI optimization)
- [x] 4.5 One-click "Create Company" onboarding
- [x] 4.6 "The Signals Loop" - học từ user behavior

**Trạng thái:** ✅ COMPLETED

---

## Ánh xạ a16z Solo Company

| Vai trò Con người | Layer kỹ thuật | Trạng thái |
|------------------|---------------|-----------|
| "Tiểu thuyết gia" - ra quyết định | Mission Control UI | ⬜ Phase 2 |
| "Kiến trúc sư" - CI/CD design | 5 Enforcement Gates | ⬜ Phase 4 |
| "Người giám sát" - Overseer | Harness Engineering | ⬜ Phase 4 |
| "Người định hướng" - Product Visionary | Signals Loop | ⬜ Phase 4 |
| "Quản lý dự án" - Orchestrator | Temporal workflows | ⬜ Phase 4 |

---

## Tài nguyên Hiện có (Đừng tái tạo)

```
~/mekong-cli/
├── observability/          ← Prometheus + Grafana + OTel (dùng ngay)
├── ci/                     ← CI helpers (extend for AI Gates)
├── docker-compose.yml      ← Base (extend for multi-tenant)
├── apps/api                ← FastAPI (refactor → gateway)
├── clipmart/               ← Agent Marketplace (Phase 4 ready)
├── packages/agents         ← Agent definitions (reuse)
├── mekong/adapters/        ← LLM routing (keep)
└── .claude/commands/       ← 443 commands (the moat!)
```

---

## Nguyên tắc Triển khai

1. **Không đốt cháy giai đoạn** — Seed phải chạy trước khi làm Tree
2. **Tái sử dụng** — Kiểm tra existing code trước khi viết mới
3. **Sub-branch OK** — Trong mỗi bước có thể rẽ nhánh thử nghiệm
4. **Memory-driven** — Mỗi quyết định kỹ thuật ghi vào memory
5. **YAGNI** — Không build feature chưa cần cho giai đoạn hiện tại

---

## Câu hỏi Chưa giải quyết

1. mekong-cli có `src/core/` với PEV Engine — liệu có thể tái sử dụng làm `seed/` không hay cần viết lại từ đầu?
2. `apps/api` (FastAPI) đã có auth chưa, hay cần implement JWT từ đầu?
3. Cloudflare Tunnel hiện tại (api.cashclaw.cc) có đủ để expose multi-tenant hay cần upgrade infra?
4. Docker-in-Docker strategy cho worker có conflict với M1 Max security model không?
