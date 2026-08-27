CONDITIONAL PASS
ROUND: 1

# Plan Verdict — SUPER COMMAND #3: Runtime v0.2 (Contracts Completed + Debt Closure)

**Plan evaluated:** `/Users/macbook/mekong-cli/.claude/worktrees/super-command-2/.orchestrate/latest/plan.md`
**Task:** `/Users/macbook/mekong-cli/.orchestrate/latest/task.md` (10 task đã duyệt "go")
**Base verified:** worktree @ `d71e13fa02` = `origin/main`, branch `feat/runtime-v02-contracts-and-debt`, tree clean (đúng plan).
**Evaluator:** Sun Tzu (plan gate, pre-execution) · 2026-08-26

> ⚠️ NOTE vị trí file: `.orchestrate/latest/plan.md` ở MAIN repo là plan SUPER COMMAND #2 cũ (stale). Plan SC#3 thật nằm trong WORKTREE. Verdict này đánh giá plan trong worktree so với task SC#3 ở main repo. Pipeline nên đồng bộ lại đường dẫn trước khi EXECUTE.

---

## Verdict

**CONDITIONAL PASS** — Plan chất lượng cao: mọi claim load-bearing đã verify đúng tại `d71e13fa02`, decomposition đủ 10 task, risks có mitigation + fallback, gates đo lường được, scope decisions (A1–A8) có lý do và đúng tinh thần task. KHÔNG có HIGH/blocking. Còn **2 MED findings** (E3 sót `observability/__init__.py` sẽ gãy import sau khi delete; E5 import-graph test tự mâu thuẫn với chính bước repoint) → chuyển thành escrow TODO gắn lane, không chặn pipeline.

---

## Evidence (evaluator tự kiểm chứng, không dựa vào summary của planner)

### Git state
- `git log -1` = `d71e13fa02 feat: autonomous runtime v0.1 (#8)`; `git rev-parse origin/main` = `d71e13fa02...` ✓ khớp base plan.
- `git status -sb` = `## feat/runtime-v02-contracts-and-debt...origin/main`, chỉ `M .orchestrate/latest/plan.md` (pipeline artifact, không stage) ✓.

### Claim load-bearing — spot-check từng cái tại HEAD

| Claim của plan | Evaluator verify | Kết quả |
|---|---|---|
| Eval suite **FAIL 4/6** | Chạy thật `run_solo_ceo_harness_evals()` → `passed_count:2, total:6`. EVAL-07/08 PASS; EVAL-09 (`missing:["src/binh_phap/"]`), EVAL-10 (5 file mất), EVAL-11 (manifest 128 vs current 56, missing 20 cmds), EVAL-12 FAIL | **ĐÚNG 4/6** |
| `dna/core-dna.json:85` có `harness-eval` trong free_commands | line 85 = `"harness-eval"` ✓; `command-surface.json:90` + `command-packs.json:18` cũng liệt kê | ĐÚNG |
| `src/core/world_model.py:334` rglob không prune | line 334 `root.rglob("*")`; exclusions :326 filter post-hoc :340; depth skip :337 không prune descent; cap 500 :344 chỉ giới hạn output; `__init__` :111 `working_dir or os.getcwd()` | ĐÚNG |
| `protocols.py:187-197` LLMRouter thiếu `tool_call` | Protocol có classify/select_model/estimate_cost/generate/stream/structured_output/health — **KHÔNG có tool_call** | ĐÚNG |
| 68 file references `llm_client` | `grep -rln llm_client src/ tests/` = **68** | ĐÚNG |
| `harness/observability/tracing.py` byte-identical orphan | `git show 3408f8905b^:src/core/tracing.py \| cmp -` → **exit 0 BYTE-IDENTICAL**; sole importer = `harness/__init__.py:15-18`; zero external symbol consumers (grep start_trace/TraceContext ngoài telemetry_collector = không liên quan) | ĐÚNG |
| `runtime_adapter.py:253-259` plan()/delegate() stub | :253-255 `plan()` 1 Step; :257-259 `delegate()` mọi step → cùng `self._agent_id`; dispatch :359; `_MAX_REPAIR_ATTEMPTS=3` :116 | ĐÚNG |
| `agent_registry.py:24-48` AgentMeta policy fields + validation | risk_level/max_budget/max_iterations/approval_policy/model_preference + `__post_init__` validate (CRITICAL+AUTO→ValueError) :24-48; `get_meta_obj` :183 | ĐÚNG |
| `exec_runtime/types.py` Protocol 8 method | execute/filesystem/process/network_policy/environment/preview/health/destroy, `@runtime_checkable` :66; LocalExecutionRuntime là impl duy nhất | ĐÚNG |
| `protocols.py:253-270` PaymentProvider 7 method | record_usage/check_quota/settle_payment/quote/request_payment/verify/refund | ĐÚNG |
| CI gọi `python3 -m src.main harness-eval --json` | `core-dna-gate.yml:60` đúng lệnh đó; `src/main.py` có `app = build_app()` | ĐÚNG |
| `run.py:100` `_NullDispatcher` | :85 `dispatcher = _NullDispatcher()`, class :113 | ĐÚNG |
| `test_core_boundary.py:27-52` allowlist có llm_client | line 35 entry `"src/core/llm_client.py"` (transitional) | ĐÚNG |
| `conftest.py:293,311` pre-import + patch | đúng tuple + `@patch("src.core.llm_client.get_client")` | ĐÚNG |
| `governance.py:79/171/209`, `capability.py:183-189` | RISK_LEVEL_MAP :79, request_approval :171, record_audit :209; bus.execute() chỉ check existence/expiry :183-189 | ĐÚNG |
| `register_doctor` pattern `app_setup.py:38,130` | đúng; `command_surface.py:54 current_root_commands()` tồn tại (56 cmds hiện tại) | ĐÚNG |
| 5 test file leak cwd tồn tại | test_build_cli, test_company_init_cli, test_plan_cli, test_run_command_wiring, test_zx_executor — đủ 5 | ĐÚNG |
| 2 agent stacks tồn tại | `src/core/agent_base.py` + `src/core/agent_registry.py` VÀ `src/harness/agents/` (registry/base/factory riêng) | ĐÚNG |
| EVAL-10 eval logic: `required_files` check exists + capability_count≥5 | `learning_loop.py:82-83` `(PROJECT_ROOT/raw_path).exists()`; manifest có đúng 5 capabilities | ĐÚNG — hướng fix E1 khả thi |

### Scope decisions — đánh giá đặc biệt

1. **A1 (Task #1 mở rộng sửa 4 manifest):** ĐÚNG tinh thần, KHÔNG scope creep. Bằng chứng: CI gate gọi `harness-eval --json` chạy cả 6 evals; chỉ đăng ký command mà 4 evals vẫn đỏ thì gate KHÔNG xanh — trái mục tiêu "đóng red cấu trúc". Eval suite thật chứng minh 4/6 đỏ vì manifest drift, nên sửa manifest là điều kiện CẦN. Plan ghi rõ mitigation (chạy 6/6 local trước commit). ✓
2. **A2 (Task #5 "keep one + shim" → DELETE):** HỢP LÝ, có bằng chứng. Verify byte-identical (cmp exit 0) + zero consumers. "Keep one" đã xảy ra ở Wave 3 (core/tracing.py đã xóa, harness copy thành orphan). Shim cho zero consumers = debt mới. Plan có fallback đúng (execute-time tìm thấy consumer mới → về keep+shim). ✓ **NHƯNG** xem Finding 1 — sót `observability/__init__.py`.
3. **A4 (DELEGATE qua core stack, không harness/agents):** HỢP LÝ. runtime_adapter cùng tầng core; AgentMeta policy fields (liên quan task #10) nằm ở agent_registry; reuse AgentBase.run() làm execution unit tránh framework thứ 2. Plan CẤM chạm harness/agents + escrow 2-stack convergence riêng. ✓ Đúng ABSOLUTE RULE "không framework thứ 2".
4. **A5 (unknown agent giữ behavior hiện tại):** CHẤP NHẬN ĐƯỢC, không vi phạm fail-closed. Lý do: hệ thống ĐÃ có capability-level governance ở Gate 2.5 (classify capability risk) — unknown agent vẫn đi qua capability gating + plan thêm audit log. Plan tăng enforcement cho agent ĐÃ đăng ký (strictly more, không less). Trade-off được document rõ kèm "điều gì đổi câu trả lời". Xem Observation 3.
5. **Parity mới nếu E2 bỏ --ignore (§4.1):** CÔNG BẰNG, không kẽ hở. Quy tắc "bỏ ignore chỉ chấp nhận nếu không test nào ĐANG pass trở thành fail" + fail-set mới ⊆ baseline-cũ ∪ {world_model nay PASS} chặn mất test. ✓ Xem Finding 3 (timeout cho baseline E0).
6. **Lane boundaries:** E6/E9 cùng chạm runtime_adapter.py → SEQUENTIAL (E6 trước E9) ĐÚNG. E5 sau E4 ĐÚNG (E4 thêm tool_call vào llm_router_adapter trước, để E5 repoint import llm_client của adapter đó trong một lượt script). ✓
7. **ABSOLUTE RULES + protected flows + §18 + không đụng .github/workflows:** TÔN TRỌNG. §4.2 anchored grep protected flows RỖNG; §4.3 anchored grep `.github/workflows/` RỖNG (plan làm command khớp signature CI, KHÔNG sửa workflow); §18 phủ qua E8 (fail-closed, no keys logged, no custody, no real money, injected transport). ✓
8. **Gates + ship plan + STOP:** ĐỦ. E0 re-baseline tại base SHA; parity normalized diff mỗi lane; protected-flow grep; anti-duplication grep sweep; ruff; CLI smoke; core-dna-gate local simulate. Ship: 10 commit buckets, PR, CI acceptance (GREEN giữ xanh + core-dna-gate dự kiến flip đỏ→xanh là cải thiện mong muốn), squash merge, rollback = revert single squash. STOP §7 đúng chỗ (scores 10 chiều, blockers, 10 next tasks, không tự chạy Phase 3). ✓

---

## Findings

1. **[MED] E3 sót `src/harness/observability/__init__.py` — sẽ thành file import gãy sau khi delete.** File-ownership E3 (plan line 81) chỉ kê: DELETE `tracing.py` + `metrics.py`, strip re-exports trong `src/harness/__init__.py`. NHƯNG chính `src/harness/observability/__init__.py:13,17` có `from .tracing import ...` và `from .metrics import ...`. Sau khi xóa 2 file đó mà KHÔNG xử lý `observability/__init__.py`, file này mang import gãy. Verify: không gì import `src.harness.observability` lúc runtime (grep = rỗng ngoài chính nó), và `import src.harness` không trigger subpackage `__init__` → KHÔNG gãy test ngay. NHƯNG (a) để lại file chết với import gãy đi ngược mục tiêu "xóa dead code" của wave, (b) gate E3 (`python3 -c "import src.harness"`) sẽ KHÔNG bắt được vì không import subpackage, (c) ruff không resolve missing module nên cũng lọt. → Lỗ hổng gate thật. **Condition 1.**

2. **[MED] E5 import-graph test tự mâu thuẫn với bước repoint.** Plan line 99: "import-graph test: assert `src/core/__init__.py` và core modules (trừ adapters) KHÔNG import adapters.llm ngược lại". NHƯNG E5 cũng nói "scripted repoint toàn bộ 68 file" — evaluator verify có **26 file trong `src/core/` (ngoài adapters)** import llm_client (planner, nlu, autonomous, agi_loop, executor, orchestrator/*, telegram_bot/bot, world_model, ...). Sau khi repoint, 26 file này SẼ import `src.core.adapters.llm.client` → import-graph test như mô tả sẽ FAIL trên chính 26 file đó. Mâu thuẫn nội tại. llm_client vốn là transitional exception (đã document trong boundary allowlist). **Condition 2** — phải làm rõ hướng test trước khi chạy E5.

3. **[LOW] E0 baseline "with world_model" có thể hang.** §4.1 nói chạy lệnh KHÔNG `--ignore` "1 lần duy nhất trong E0 song song" để lấy baseline mới. Nhưng tại E0, world_model CHƯA fix → full-suite không-ignore sẽ hang ở `_get_file_tree` (đúng lý do ignore tồn tại). Plan dự kiến "world_model FAIL/timeout trong baseline cũ" nhưng không nêu cơ chế timeout cho lần chạy này → E0 có thể treo. **Escrow:** thêm `timeout <N>` cho lần chạy baseline with-world_model, hoặc chấp nhận baseline đó = baseline-cũ + đánh dấu world_model timeout.

4. **[LOW] Line count llm_client lệch 1.** Plan bảng §2 ghi "616 dòng"; `wc -l` = **615**. Không ảnh hưởng gate (script repoint đếm theo file/reference, không theo dòng). Sửa wording khi ghi docs/ship-report.

---

## Conditions (escrow TODO — KHÔNG chặn pipeline, gắn lane, phải verify ở vòng re-evaluation sau EXECUTE)

1. **[E3] Xử lý `src/harness/observability/__init__.py`.** Chọn 1: (a) strip dòng `from .tracing import ...` (:13-16) và `from .metrics import ...` (:17), GIỮ re-export core telemetry/health, hoặc (b) xóa cả package `observability/` nếu sau khi xóa tracing/metrics nó chỉ còn `__init__.py` không ai dùng (evaluator grep = 0 importer). KHÔNG được để import gãy trong tree. Mở rộng prove-step E3: thêm `python3 -c "import src.harness.observability"` (nếu giữ package) HOẶC assert package đã xóa sạch.
2. **[E5] Làm rõ import-graph test TRƯỚC khi chạy.** Chọn 1 và ghi vào execution.md: (a) whitelist 26 transitional core importers của `adapters.llm` (documented transitional exception, cùng kiểu `HTTP_LIB_ALLOWLIST` trong test_core_boundary.py), hoặc (b) test chỉ assert hướng circular — `adapters.llm` KHÔNG import ngược vào core (không assert core không import adapters.llm). KHÔNG viết test fail trên chính repoint dự định.
3. **[E0] Thêm timeout cho lần chạy baseline with-world_model** (xem Finding 3) để E0 không treo.
4. **Sửa line count llm_client 616→615** (Finding 4).

---

## Out-of-scope observations (KHÔNG chặn, tham khảo)

- **Vị trí pipeline artifacts không đồng nhất:** main repo `.orchestrate/latest/plan.md` = SC#2 stale, worktree `.orchestrate/latest/task.md` + `plan-verdict.md` = Wave 3 stale. Chỉ worktree `plan.md` + main repo `task.md` là SC#3 thật. Pipeline nên chuẩn hóa đường dẫn trước EXECUTE để tránh agent đọc nhầm plan cũ.
- **26 core importers của llm_client** nhiều hơn con số plan ngầm định — củng cố rằng E5 cần whitelist (Condition 2) chứ không thể "core không import adapters" tuyệt đối.
- **A5 unknown-agent:** quyết định giữ behavior hiện tại + audit log là defensible (capability gating vẫn còn). Nếu wave sau muốn strict fail-closed toàn bộ, phải migrate mọi caller `_NullDispatcher` — đã ghi trong A5.

---

## Scope check

- Plan phủ đúng 10 task task.md, KHÔNG lan sang Phase 3 (STOP §7 rõ).
- Protected flows (nowpayments_*, billing_routes, license_gate, raas_gate/, gateway.py) — cấm đụng, anchored grep RỖNG (§4.2). Verified deletion/move set không giao protected set.
- `.github/workflows/*` — KHÔNG sửa (§4.3, PR #7 sở hữu); plan làm command khớp signature CI thay vì đổi workflow. ✓
- Không framework/registry/permission-system thứ 2 (E6 reuse AgentRegistry+AgentBase; E9 giữ Governance là decision path duy nhất).
- Không bước irreversible thiếu gate: mọi deletion/move nằm trong commit bucket có parity + rollback = revert single squash.
- `.orchestrate/` không stage vào commit (§6.2). Không secret/key trong code/tests (§18 phủ E8).

**Kết luận:** Pipeline tiếp tục với 4 escrow TODO trên (2 MED gắn E3/E5, 2 LOW gắn E0/docs). Verdict: **CONDITIONAL PASS**.
