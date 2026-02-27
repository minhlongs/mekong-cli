# 🧬 DUAL AGI TRACKER — mekong-cli × AgencyOS

> **始計 Ch.1:** 多算勝少算不勝 — Tính nhiều thì thắng
> Cập nhật: 2026-02-23 19:44

---

## ĐẠO — 道 — Tầm nhìn song song

| | mekong-cli | AgencyOS |
|:--|:-----------|:---------|
| **Bản chất** | RaaS Engine Core (HEART) | Agency-in-a-Box (FULL BODY) |
| **Mô hình** | Free / Open Source / Cộng đồng | Paid RaaS / No-tech users |
| **Revenue** | $0 — Community contribution | $1M — Subscription $5-$15/mo |
| **DNA** | ClaudeKit → Python CLI | ClaudeKit → Next.js + Workers |
| **Trinity** | HANDS (Executor) | BRAIN + HANDS + PULSE |
| **PRD** | `PRD_MEKONG_GENESIS.md` | `PRD_AGENCY_GENESIS.md` |

---

## 風林火山 × AGI LEVELS — Dual Track

### 📦 MEKONG-CLI — Cửu Địa: 重地 (Trọng Địa)

> `mekong cook <recipe>` → Plan-Execute-Verify autonomous

| AGI Level | Module | File | Binh Pháp | Status |
|:----------|:-------|:-----|:----------|:-------|
| L1 🌪️GIÓ | CLI Interface | `src/cli.py` (Typer+Rich) | 兵貴勝 Nhanh thắng | ⏳ AUDIT |
| L1 🌪️GIÓ | Recipe Parser | `src/core/parser.py` | 法令孰行 Kỷ luật | ⏳ AUDIT |
| L2 🌲RỪNG | PEV Pipeline | `src/core/orchestrator.py` | 多算勝 Tính nhiều | ⏳ AUDIT |
| L2 🌲RỪNG | LLM Planner | `src/core/planner.py` | 上兵伐謀 Mưu trước | ⏳ AUDIT |
| L2 🌲RỪNG | Multi-Executor | `src/core/executor.py` | 奇正相生 Chính+Kỳ | ⏳ AUDIT |
| L2 🌲RỪNG | Verifier | `src/core/verifier.py` | 軍形 CI Gate | ❓ |
| L3 🔥LỬA | Self-Healing | `src/core/executor.py` | 九變 Cửu Biến | ❓ |
| L3 🔥LỬA | NLU Intent | `src/core/nlu.py` | 始計 Kế Sách | ❓ |
| L4 🔥LỬA | Memory | `src/core/memory.py` | 用間 Tình Báo | ❓ |
| L4 ⛰️NÚI | Agent Orchestration | `src/agents/` | 兵勢 Agent Teams | ❓ |
| L5 ⛰️NÚI | Supervisor Loop | `supervisor.py` | 將者國之輔 Tướng | ❓ |
| L6 ⛰️NÚI | Self-Evolving | `src/core/evolution.py` | 善之善者 Giỏi nhất | ❓ |
| — | Test Suite | `tests/` | 先為不可勝 Bất bại | ⏳ PYTEST |
| — | Telemetry | `src/core/telemetry.py` | 近而靜者 Trinh sát | ❓ |

**Chiến lược Viral (từ PRD):** `mekong init` → `mekong run recipes/lead_gen.md` → Tự cào khách
**DNA Hook:** "Kế thừa từ ClaudeKit, tối ưu cho Developer Việt Nam"

---

### 💰 AGENCYOS — Cửu Địa: 衢地 (Cù Địa — Multi-platform)

> Agency-in-a-Box: BRAIN(ClaudeKit) → HANDS(CC CLI) → PULSE(Antigravity)

| AGI Level | Module | Location | Binh Pháp | Status |
|:----------|:-------|:---------|:----------|:-------|
| L1 🌪️GIÓ | Landing + Conversion | `apps/agencyos-landing` | 爭地 First mover | ❓ AUDIT |
| L2 🌲RỪNG | Dashboard Admin | `apps/agencyos-web` | 重地 Production | ❓ AUDIT |
| L2 🌲RỪNG | RaaS Gateway API | `apps/raas-gateway` | 交地 API contracts | ❓ AUDIT |
| L2 🌲RỪNG | Engine API | `packages/engine` | 衢地 Multi-platform | ❓ AUDIT |
| L3 🔥LỬA | AI Pipeline (Sophia) | `apps/sophia-ai-factory` | 圍地 Deadline | ✅ DONE |
| L3 🔥LỬA | Payment (Polar/PayOS) | Integrated | 因糧於敵 Dùng lương địch | ✅ DONE |
| L3 🔥LỬA | Telegram Bot | `apps/sophia-video-bot` | 生間 Gián điệp sống | ✅ DONE |
| L4 🔥LỬA | Security Perimeter | RBAC + Rate Limit | 善守者藏九地 | ✅ DONE |
| L4 ⛰️NÚI | CTO Tôm Hùm | `apps/openclaw-worker` | 將者 Tướng Lĩnh | ⏳ 7 BUG FIXED |
| L5 ⛰️NÚI | Evolution Engine | `lib/evolution-engine.js` | 善之善者 | 🔴 DISABLED |
| L5 ⛰️NÚI | Vibe Manifest | `vibe_manifest.yaml` | 法 Pháp chế | ❓ |
| L6 ⛰️NÚI | Genesis Loop | `genesis.py` | Autonomous Loop | ❓ |

**Revenue Streams:** Sophia ($1200/tier) + Agency-in-a-Box (high-ticket) + RaaS per-project

---

## 🤖 CTO TÔM HÙM — Orchestrator Chung

> 將者國之輔也 — Tướng phụ trợ quốc gia cho CẢ HAI dự án

| Metric | Value | Binh Pháp |
|:-------|:------|:----------|
| CC CLI State | 🟢 BUSY (2 parallel agents) | 奇正相生 Chính+Kỳ |
| Current Mission | AGI Audit mekong-cli | 始計 Kế Sách |
| Dispatch | 1x only ✅ (no duplicates) | 多算勝 |
| Prompt Size | 135 chars (was 2000+) | 兵貴勝 Nhanh thắng |
| Watchdog | ✅ com.tomhum.watchdog | 善守者 Phòng thủ |
| Monitor | ✅ lib/monitor-24-7.js | 用間 Tình báo |

### 7 Bug Fixed (2026-02-23)

| # | Bug | Binh Pháp Anti-Pattern |
|:--|:----|:----------------------|
| 1 | `queued messages` false-positive | 必生 Tham sống sợ chết (quá cautious) |
| 2 | Prompt 2000→135 chars | 日費千金 Tốn ngàn vàng (token waste) |
| 3 | Evolution Engine flooding | 忿速 Nóng nảy (auto-task spam) |
| 4 | Missing AGENT_TEAMS env | 法令不行 Kỷ luật không thi hành |
| 5 | Healer killing mid-mission | 愛民 過nhân từ → PHIỀN (false rescue) |
| 6 | Missing BUSY_PATTERNS | 不知彼 Không biết người |
| 7 | 4x dispatch stacking | 兵無常勢 Quân không thế cố định |

---

## ⏭️ NEXT ACTIONS — 謀攻 Attack Plan

### Immediate (sau AGI audit)
1. Đọc `plans/mekong-agi-roadmap.md` → map với tracker này
2. Dispatch AgencyOS audit: `HIGH_mission_agencyos_agi_audit.txt`
3. Cả 2 audit chạy song song (奇正相生)

### Phase 1: 🌪️GIÓ Quick Wins (1-2 ngày)
- mekong: Fix test suite, verify CLI `mekong cook` works
- agencyos: Audit dashboard + landing health

### Phase 2: 🌲RỪNG Core Pipeline (3-5 ngày)
- mekong: PEV pipeline hoàn chỉnh, recipe parser
- agencyos: RaaS gateway verification, engine API

### Phase 3: 🔥LỬA Agent Teams (1-2 tuần)
- mekong: Self-healing, NLU, Memory
- agencyos: Re-enable Evolution Engine, Vibe Manifest

### Phase 4: ⛰️NÚI AGI (2-4 tuần)
- mekong: Supervisor Loop, Self-Evolving recipes
- agencyos: Genesis Loop, Full autonomous delivery

---

> 不戰而屈人之兵，善之善者也
> Thắng mà không chiến, giỏi nhất trong giỏi.
> — Tôn Tử, Ch.3 謀攻
