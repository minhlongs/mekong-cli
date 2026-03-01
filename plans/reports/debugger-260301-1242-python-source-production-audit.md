# Python Source Production Audit — mekong-cli/src/

**Ngày:** 2026-03-01
**Scope:** `src/` — 88 files, 15,870 LOC
**Tool:** `python3 -m py_compile` + AST analysis

---

## Tóm Tắt Điều Hành

| Hạng Mục | Kết Quả | Trạng Thái |
|---|---|---|
| Syntax errors | 0/88 files | PASS |
| Circular imports | 0 | PASS |
| Hardcoded secrets | 0 | PASS |
| TODO/FIXME | 0 (thực) | PASS |
| Type hints | 730/747 (97%) | PASS |
| Class docstrings | 233/233 (100%) | PASS |
| Function docstrings | 697/747 (93%) | WARNING |
| Unused imports | 49 | WARNING |
| Files > 200 LOC | 27 files | FAIL |

---

## 1. Syntax Errors — PASS

Tất cả 88 file compile thành công với `python3 -m py_compile`. Không có syntax error.

---

## 2. Circular Imports — PASS

Không phát hiện circular imports trong dependency graph nội bộ (`src.*`).

Các module được import nhiều nhất:
- `src.core.llm_client` — 7 lần
- `src.core.event_bus` — 4 lần
- `src.core.swarm`, `src.core.scheduler`, `src.core.memory` — 3 lần mỗi

---

## 3. Hardcoded Secrets — PASS

Không có hardcoded passwords, API keys, tokens, hay credentials nào trong source code.

`gateway.py` dùng `os.environ.get("MEKONG_API_TOKEN")` — đúng cách.

---

## 4. Tech Debt (TODO/FIXME) — PASS

Không có TODO/FIXME thực sự. 3 kết quả grep đều nằm trong docstring của `verifier.py` (mô tả chức năng check, không phải debt).

---

## 5. Type Hints — WARNING (97%)

**730/747 functions** có type hints. 17 functions thiếu:

Tập trung ở `src/core/gateway.py` — các FastAPI route handlers (14 functions):
```
gateway.py:351  dashboard
gateway.py:359  list_presets
gateway.py:364  list_projects
gateway.py:369  health_check
gateway.py:497  recipes_auto_list
gateway.py:514  telegram_status
gateway.py:538  swarm_list_nodes
gateway.py:589  memory_stats
gateway.py:626  schedule_list_jobs
gateway.py:650  consciousness
gateway.py:717  agi_health
gateway.py:727  agi_metrics
gateway.py:415  progress_callback
gateway.py:432  run_goal
```

Các file khác:
```
main.py:979     run
telemetry.py:32 _get_facade
zx_executor.py:219 wrapper  (dynamic decorator — khó type)
```

**Fix:** Thêm `-> dict` hoặc `-> JSONResponse` cho các route handlers FastAPI.

---

## 6. Docstrings — WARNING (93%)

- Classes: **100%** (233/233) — xuất sắc
- Functions: **93%** (697/747) — 50 functions thiếu

Tập trung ở `src/core/hooks.py` (28 functions thiếu — phần lớn là `__init__`, `phase`, `execute` của các Hook subclasses nhỏ):
```
hooks.py:58,84,90,93,119,125,128,148,154,157,168,173,176,191,195,198,215...
```

File khác thiếu ít:
```
auto_updater.py:58    __init__
swarm.py:180          __init__
agent_execution_sandbox.py:69  _handler
```

**Fix:** Ưu tiên `hooks.py` — thêm docstring ngắn cho các method `phase()` và `execute()`.

---

## 7. Unused Imports — WARNING (49 items)

### Nhóm 1: `src/core/__init__.py` — 24 "unused" (FALSE POSITIVE)

Đây là public re-exports của package, không phải unused thực sự. AST static analysis không thể detect external consumers. **Không cần fix.**

### Nhóm 2: Thực sự unused — CẦN FIX

```
src/core/planner.py:11        LLMClient        (from llm_client import LLMClient)
src/core/orchestrator.py:11   LLMClient        (from llm_client import LLMClient)
src/core/orchestrator.py:30   LLM_RETRY        (from retry_policy import LLM_RETRY)
src/core/cost_tracker.py:17   EventType        (from event_bus import EventType)
src/core/collector_registry.py:13  Callable    (from typing import Callable)
src/core/webhook_delivery_engine.py:15  Optional (from typing import Optional)
src/core/telegram_bot.py:18   annotations      (from __future__ import annotations)
src/agents/recipe_crawler.py:56  _query        (noqa: F841 — local variable unused)
```

**Fix:** Xóa các import này. Tổng 8 items thực sự cần clean.

---

## 8. File Size — FAIL (27 files > 200 LOC)

Files vi phạm quy tắc < 200 LOC (từ nặng nhất):

| File | LOC | Vượt quá |
|---|---|---|
| `src/main.py` | 1,186 | **5.9x** |
| `src/core/gateway.py` | 774 | **3.9x** |
| `src/core/telegram_bot.py` | 742 | **3.7x** |
| `src/core/orchestrator.py` | 624 | **3.1x** |
| `src/core/agi_loop.py` | 505 | **2.5x** |
| `src/core/llm_client.py` | 504 | **2.5x** |
| `src/core/verifier.py` | 468 | **2.3x** |
| `src/core/planner.py` | 447 | **2.2x** |
| `src/core/gateway_dashboard.py` | 384 | **1.9x** |
| `src/core/nlp_commander.py` | 341 | **1.7x** |
| `src/core/routing_strategy.py` | 325 | 1.6x |
| `src/core/telemetry.py` | 323 | 1.6x |
| `src/core/provider_registry.py` | 307 | 1.5x |
| `src/core/zx_executor.py` | 306 | 1.5x |
| `src/core/hooks.py` | 304 | 1.5x |
| `src/core/executor.py` | 301 | 1.5x |
| `src/agents/file_agent.py` | 290 | 1.5x |
| `src/core/swarm.py` | 282 | 1.4x |
| `src/core/autonomous.py` | 268 | 1.3x |
| `src/core/llm_cache.py` | 252 | 1.3x |
| `src/core/cc_spawner.py` | 249 | 1.2x |
| `src/core/scheduler.py` | 247 | 1.2x |
| `src/core/cost_tracker.py` | 247 | 1.2x |
| `src/core/health_watchdog.py` | 236 | 1.2x |
| `src/core/vector_memory_store.py` | 214 | 1.1x |
| `src/agents/git_agent.py` | 206 | 1.0x |
| `src/core/task_queue.py` | 203 | 1.0x |

**Ưu tiên split ngay:**
- `main.py` (1186 LOC) → tách thành `cli/commands/*.py` theo nhóm lệnh
- `gateway.py` (774 LOC) → tách routes thành `gateway_routes_*.py`
- `telegram_bot.py` (742 LOC) → tách handlers thành modules riêng
- `orchestrator.py` (624 LOC) → tách rollback/self-healing logic

---

## 9. Type-Ignore Annotations

8 instances `# type: ignore[...]` trong codebase (không phải `@ts-ignore` nhưng tương đương):

```
src/core/swarm.py:137         type: ignore[import-untyped]  — yaml
src/core/gateway_config.py:62 type: ignore[import-untyped]  — yaml
src/core/scheduler.py:221     type: ignore[import-untyped]  — yaml
src/core/event_bus.py:165     type: ignore[assignment]
src/core/event_bus.py:181     type: ignore[return-value]
src/core/zx_executor.py:219   type: ignore[no-untyped-def]
src/core/zx_executor.py:234   type: ignore[misc]
src/agents/agi_bridge.py:24   type: ignore[type-arg]
```

3 cái đầu (yaml untyped) — acceptable, yaml không có stubs chính thức.
`event_bus.py` 2 items — nên fix bằng cách khai báo `Optional[EventBus]` thay `None`.

---

## Danh Sách Issues Cần Fix (Ưu Tiên)

### P1 — Ngay Lập Tức
1. **Xóa 8 unused imports thực sự** trong `planner.py`, `orchestrator.py`, `cost_tracker.py`, `collector_registry.py`, `webhook_delivery_engine.py`, `telegram_bot.py`
2. **Fix `event_bus.py` type ignore** — đổi `None` → `Optional[EventBus] = None`

### P2 — Sprint Tiếp Theo
3. **Thêm type hints** cho 14 FastAPI route handlers trong `gateway.py` (`-> dict` hoặc `-> JSONResponse`)
4. **Thêm docstrings** cho 28 Hook methods trong `hooks.py` (ngắn, 1 dòng là đủ)

### P3 — Refactor Dài Hạn
5. **Split `main.py`** (1186 LOC → nhiều file `cli/commands/`) — vi phạm nặng nhất
6. **Split `gateway.py`** (774 LOC → `gateway_routes_core.py`, `gateway_routes_agi.py`, etc.)
7. **Split `telegram_bot.py`** (742 LOC → handlers riêng)
8. **Split `orchestrator.py`** (624 LOC → tách rollback module)

---

## Điểm Tổng Thể

| Front (Binh Pháp) | Score |
|---|---|
| 始計 Tech Debt | 10/10 (0 TODO) |
| 作戰 Type Safety | 9/10 (97% hints) |
| 謀攻 Performance | 6/10 (27 files oversized) |
| 軍形 Security | 10/10 (no hardcoded secrets) |
| 兵勢 Code Quality | 8/10 (49 unused imports, 7% no docstrings) |
| 虛實 Maintainability | 5/10 (main.py 1186 LOC critical) |
| **TỔNG** | **48/60 (80%)** |

---

## Câu Hỏi Chưa Giải Quyết

- `src/core/__init__.py` re-exports 24 symbols không dùng nội bộ — có consumer nào bên ngoài `src/` không? Nếu không thì nên trim.
- `zx_executor.py:219 wrapper` dùng `type: ignore[no-untyped-def]` trong dynamic decorator — có thể dùng `ParamSpec` để type-safe không?
- `main.py` 1186 LOC — có kế hoạch refactor CLI commands chưa hay đang chờ feature stable?
