# OpenClaw Worker & Vibe Factory — Architecture Research
**Date:** 2026-03-01 | **Researcher:** researcher-260301-1946

---

## 1. Tổng Quan Kiến Trúc

OpenClaw Worker (`apps/openclaw-worker/`) là autonomous CTO daemon, viết bằng Node.js/CommonJS. Entrypoint: `task-watcher.js`. Kiến trúc "thin orchestrator" — boot, wire modules, không chứa logic.

**Triết lý:** Chạy FOREVER, self-healing, không exit khi queue rỗng.

---

## 2. Mission Lifecycle (Spawn → Dispatch → Complete → Archive)

```
tasks/*.txt (CRITICAL/HIGH/MEDIUM/LOW prefix)
    │
    ▼
task-queue.js (FIFO + priority sort)
    │  fs.watch + poll(100ms)
    ▼
mission-dispatcher.js
    │  detectProjectDir() → buildPrompt()
    │  Safety gate → Learning hints → Priority classify
    ▼
brain-mission-runner.js → runMission()
    │  findIdleWorker() → tmux pane routing (P0/P1/P2)
    │  tmux send-keys → CC CLI nhận prompt
    ▼
Polling state machine (DISPATCHED→BUSY→DONE)
    │  detect completion pattern / 8x IDLE polls
    ▼
post-mission-gate.js (build verify, auto-commit nếu GREEN)
mission-journal.js (telemetry ghi vào data/)
tasks/processed/ (archive)  hoặc  tasks/dead-letter/ (DLQ sau 5 retries)
```

---

## 3. Brain Process Management

**Dual-mode boot** (v2026.2.9+):
- **Tmux mode (default):** `brain-boot-sequence.js` tạo tmux session `tom_hum:brain`, 3 panes:
  - P0: `mekong-cli` — Opus PRO (direct Anthropic, no proxy)
  - P1: `apps/well` — API proxy (port 9191)
  - P2: `apps/algo-trader` — API proxy (port 9191)
- **Direct mode (legacy):** `claude -p` per mission, stdin=ignore

**Routing (虛實 Intent-Aware):**
- PRO intent → `CLAUDE_CONFIG_DIR=~/.claude_antigravity_pro`, unset proxy, Opus 4.6
- API intent → `ANTHROPIC_BASE_URL=http://127.0.0.1:9191`, proxy routing

**Reliability sub-modules:**
- `brain-heartbeat.js` — file-based liveness
- `brain-output-hash-stagnation-watchdog.js` — detect hung process
- `brain-respawn-controller.js` — max 5 respawns/hour
- `circuit-breaker.js` — CLOSED/OPEN/HALF_OPEN pattern
- `mission-recovery.js` — model failover (HTTP 400), context overflow truncation

---

## 4. Auto-CTO Pilot Loop

**3-Phase Binh Pháp cycle** (`auto-cto-pilot.js`):
1. **始計 SCAN** — chạy build/lint/test, detect lỗi thực (không hallucinate)
2. **謀攻 PLAN** — LLM assess ROI, chỉ dispatch critical/high severity
3. **軍形 VERIFY** — re-scan, GREEN → advance, RED → retry (max 3 cycles)

**Intervals:** SCAN=120s, FIX=15s. Dedup TTL=30min.

**17 BINH_PHAP_TASKS** trong `config.js` (frozen): từ `console_cleanup` đến `bmad_retrospective`.

**Cùng sử dụng:** `strategic-brain.js`, `revenue-health-scanner.js`, `clawwork-integration.js`.

---

## 5. File IPC Mechanism

**Lịch sử evolution:**
- v1: `MISSION_FILE=/tmp/tom_hum_next_mission.txt` → expect script đọc → inject vào CC CLI stdin
- v2: `runMission()` trực tiếp qua Node.js child_process
- **v3 (current):** tmux `send-keys -l` vào pane cụ thể, poll `capture-pane -p` để detect completion

**WAL (Write-Ahead Log):** `tasks/.wal.json` — mission survive khi task-watcher crash/restart.

---

## 6. Vibe Factory Monitor (`scripts/vibe-factory-monitor.js`)

**Thay thế `night-monitor.sh`** — AGI-level codebase-aware task generator.

**Flow mỗi pane (90s interval):**
1. `scanCodebase()` — git status, recent commits, TODO count, file count
2. LLM call qua AG Proxy (port 9191) → gen `/plan:hard` task chính xác
3. `tmuxSendBuffer()` — inject vào CC CLI (Ctrl+U để clear, send-keys -l, Enter)
4. Monitor tiến độ, auto-Enter khi kẹt

**4 panes cố định:** mekong-cli, well, algo-trader, apex-os.

**Score-Targeted Generation:** `generateScoreTargetedTask()` — sort dimensions by score (thấp nhất → pick đó), 12min cooldown per dim per pane. Dùng `project-score-calculator.js` để score 6 dimensions.

**BINH_PHAP_MAP:** Map 13 chapters → open-source repos (planning cho future open-source).

---

## 7. Prompt Building Logic

`mission-dispatcher.js::buildPrompt()` pipeline:
1. `stripPollution()` — remove WORKFLOW ORCHESTRATION + GOOGLE ULTRA INTEL blocks (save tokens)
2. Parse explicit `/command` trong task content
3. Intent detection: CI, BOOTSTRAP, TEST, MULTI_FIX, STRATEGIC, COMPLEX, FIX, REVIEW
4. Complexity routing: simple→`/plan:hard`, medium→`/debug`, complex→`/plan:parallel`
5. **Plan Infiltration:** nếu có `plan.md` → inject path vào prompt
6. PRO availability check → deep tasks → `claude-opus-4-6`

**Sanitization:** escape `()$\`!`, giới hạn 150 chars khi log.

---

## 8. Current Bottlenecks & Known Issues

Từ `knowledge/memory.md` (2026-03-01):
- **Repeat FAILED missions (today):** `HIGH_mission_mekong_cli_fix_bu*` — "Max retries exhausted" hàng loạt → success rate gần 0%
- **BUILD FAILED pattern:** Code worked nhưng TypeScript/lint fail → chưa check trước commit
- **Missing module imports:** Lỗi lặp lại `require()` không validate path trước
- **STALE LOCK BUG (fixed 2026-02-17):** `.mission-active.lock` không cleanup khi crash → missions blocked indefinitely. Fix: try-finally
- **all_workers_busy không retry (fixed 2026-02-22):** task bị archive ngay thay vì re-queue
- **tech debt hiện tại:** `well` có 536 TODOs, 1745 console.logs (health-report.json)

---

## 9. Giữ Lại / Thay Thế Cho Open-Source

**Giữ lại (core logic clean):**
- `task-queue.js` — FIFO + DLQ + WAL pattern, tốt
- `mission-dispatcher.js` — prompt building, routing, retry logic
- `auto-cto-pilot.js` — Binh Pháp 3-phase loop
- `brain-state-machine.js`, `circuit-breaker.js` — reliability patterns
- `vibe-factory-monitor.js` — score-targeted task gen (unique value)

**Thay thế / làm sạch cho open-source:**
- Xóa private routing: `apps/well`, `apps/algo-trader`, `apps/apex-os` hardcoded paths
- Xóa proprietary: `google-ultra.js`, `moltbook-integration.js`, `jules-agent.js`
- Xóa `ANTIGRAVITY_KEY: 'GOD_MODE_ACTIVE'` và proxy port hardcodes
- Externalize `config.PROJECTS` + `BINH_PHAP_TASKS` thành user config file
- `brain-boot-sequence.js` — PRO path (`~/.claude_antigravity_pro`) cần làm generic
- Loại bỏ 80+ lib modules không documented (nhiều dead code)

---

## Unresolved Questions

1. Tại sao `HIGH_mission_mekong_cli_fix_bu` FAILED liên tục hôm nay (2026-03-01)? Brain pane P0 bị stuck hay proxy issue?
2. Vibe Factory Monitor đang chạy như service độc lập hay được gọi từ `task-watcher.js`? (Boot sequence không gọi nó)
3. `post-mission-gate.js` auto-commit có đang hoạt động không? Health report cho thấy `gitStatus: DIRTY` cho cả algo-trader và well.
4. `mission-outcomes.json` toàn `failed_to_start` từ 2026-02-26 — well project có issue dai dẳng?
