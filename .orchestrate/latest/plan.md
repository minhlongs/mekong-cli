# SUPER COMMAND #3 — Runtime v0.2: Contracts Completed + Debt Closure

**Ngày:** 2026-08-26
**Repo:** /Users/macbook/mekong-cli — worktree `/Users/macbook/mekong-cli/.claude/worktrees/super-command-2`
**Base:** `origin/main` = `d71e13fa02` (PR #8 squash: autonomous runtime v0.1)
**Branch:** `feat/runtime-v02-contracts-and-debt` (đã tạo, @ d71e13fa02, tree clean — verified)
**Nguồn:** `.orchestrate/latest/task.md` — 10 task user đã duyệt "go" (2026-08-26), KHÔNG mở rộng
**Tiền lệ:** `.orchestrate/archive-super-command-2/plan.md` + `execution.md` (lane pattern, parity convention, escrow discipline)

---

## 0. TL;DR

Wave này = **đóng nợ cơ khí + hoàn tất contracts** của runtime v0.1, không thêm feature mới ngoài 10 task đã duyệt. Trình tự: (E0) re-baseline parity tại d71e13fa02 → (E1–E3) debt cơ khí song song: harness-eval command + sửa 4 dna manifest, world_model bounded walk, tracing dedup → (E4–E5) contracts: `tool_call()` + conformance suite, MOVE `llm_client` scripted → (E6–E9) features: DELEGATE wiring, CF/Docker ExecutionRuntime, x402 fail-closed provider, Gate-2.5 agent-policy enforcement → (E10) Buzz live = **DEFER/escrow** (blocked-on-environment, không fake). Ship = 1 PR → CI (GREEN set giữ xanh, core-dna-gate dự kiến flip đỏ→xanh) → squash merge → STOP chờ review.

---

## 1. Reframed Problem

Vấn đề thực sự KHÔNG phải "làm 10 task cho xong checklist". Vấn đề là: runtime v0.1 (PR #8) đã ship **foundation đúng nhưng còn nợ** — (a) CI gate đỏ vì chính command nó gọi (`harness-eval`) chưa tồn tại, (b) 1 test file bị `--ignore` vì hang, (c) LLM abstraction thiếu `tool_call()` và provider chưa bị ép qua cùng interface, (d) `llm_client` vẫn nằm sai chỗ (core thay vì adapters), (e) DELEGATE là stub, (f) AgentMeta policy fields khai báo mà không enforce. Mỗi khoản nợ này nhỏ riêng lẻ nhưng gộp lại = "contracts trên giấy". Wave này biến contracts thành **enforced behavior có test**, đồng thời đóng 2 khoản nợ CI (harness-eval, world_model) để pipeline sau chạy trên nền xanh hơn.

**Non-goals (từ task.md, giữ nguyên):** không framework orchestration thứ 2, không network thật cho x402, không staging Buzz (escrow), không đụng `.github/workflows/*` (PR #7 sở hữu), không đụng protected flows.

**Kết quả scout bắt buộc phải ghi nhận (thay đổi scope task #1 so với task.md gốc):**

> Đăng ký command `harness-eval` KHÔNG đủ làm core-dna-gate xanh. Workflow gọi `python3 -m src.main harness-eval --json` (`.github/workflows/core-dna-gate.yml:60` — verified) và eval suite hiện **FAIL 4/6**: EVAL-09 (immutable_root stale `src/binh_phap/` — thực tế `src/core/binh_phap/`), EVAL-10 (hermes manifest trỏ 5 file không tồn tại), EVAL-11/EVAL-12 (command-surface + command-packs manifests drift so với 36-group surface hiện tại). Task #1 = đăng ký command **VÀ** sửa 4 manifest để 6/6 evals pass. Đây là mở rộng cần-thiết-trong-tinh-thần-task (đóng red cấu trúc của core-dna-gate), không phải scope creep.

---

## 2. Audit → Action Mapping (10 task, mọi claim đã verify tại worktree @ d71e13fa02)

| # | Audit finding (verified) | Action | Reason | Risk |
|---|---|---|---|---|
| 1 | `harness-eval` chưa phải command; `dna/core-dna.json:85` đã có tên trong free_commands; `dna/command-surface.json:90` + `dna/command-packs.json:18` đã liệt kê; nhưng 4/6 evals FAIL: EVAL-09 root stale `src/binh_phap/` (thực: `src/core/binh_phap/`), EVAL-10 `dna/hermes-learning-loop.json` trỏ 5 file mất (`src/core/memory.py`, `.claude/skills/README.md`, 3 file `.claude/commands/*`), EVAL-11/12 manifest drift; CI gọi `python3 -m src.main harness-eval --json` (core-dna-gate.yml:60) | **NEW** command + **REFACTOR** 4 dna manifests | Đóng red cấu trúc core-dna-gate; command phải root-level + nhận `--json` đúng signature CI gọi | Medium — sửa manifest sai có thể làm eval khác đỏ; mitigate: chạy `run_solo_ceo_harness_evals()` local 6/6 trước commit |
| 2 | `src/core/world_model.py:334` `root.rglob("*")` descend toàn bộ cây, exclusions (line 326) filter post-hoc (line 340), depth skip (337) không prune descent, cap 500 (344) chỉ giới hạn output không giới hạn walk; `WorldModel.__init__` default `working_dir=os.getcwd()` (line 111); `tests/test_world_model.py:129-153` khởi tạo KHÔNG working_dir → hang khi cwd leak từ test khác (5 test file leak cwd đã điểm danh: test_build_cli, test_company_init_cli, test_plan_cli, test_run_command_wiring, test_zx_executor) | **REFACTOR** `_get_file_tree()` thành bounded walk prune-before-descend + hardening test isolation | Bỏ `--ignore=tests/test_world_model.py` khỏi parity command; đóng escrow #2 từ Wave 3 | Medium — walk mới phải giữ semantics (exclusions, depth, cap); fallback nếu không fix được trong wave: GIỮ ignore + escrow lại (nói rõ trong execution.md) |
| 3 | `src/core/protocols.py:187-197` LLMRouter Protocol có generate/stream/structured_output/health nhưng **KHÔNG có tool_call()**; `src/core/llm_router_adapter.py` (158 dòng) wrap LLMClient, stream yield 1 chunk (documented), không tool_call | **REFACTOR** Protocol + adapter: thêm `tool_call()`; **NEW** conformance test suite ép ≥2 provider qua cùng interface | §5 mandate: 5 method cùng interface; tool_call là method cuối còn thiếu | Low — additive; risk chính là provider không hỗ trợ tool calling → define capability flag + skip có lý do, không fake pass |
| 4 | `src/core/llm_client.py` (616 dòng) là provider-specific HTTP client nằm trong core; 68 file reference (45 src + 23 tests), 41 import statements (styles: `from src.core.llm_client import`, `from .llm_client` relative lines 42-44 nội bộ, `@patch("src.core.llm_client.get_client")` strings); `tests/conftest.py:293,311` pre-import tuple + patch target; `tests/test_core_boundary.py:27-52` HTTP_LIB_ALLOWLIST có entry `"src/core/llm_client.py"` | **MOVE** → `src/core/adapters/llm/` (scripted repoint toàn bộ 68 file, giữ behavior) | §4 CORE/ADAPTER boundary: core không chứa provider-specific impl | Medium — move rộng; mitigate: script sed có whitelist patterns + verify count trước/sau + parity + import-graph test; KHÔNG để shim 2 đường (PEV precedent: repoint sạch + DEPRECATION.md note) |
| 5 | `src/harness/observability/tracing.py` (302 dòng) **BYTE-IDENTICAL** với `src/core/tracing.py` đã xóa ở Wave 3 (verified: `git show 3408f8905b^:src/core/tracing.py | cmp -` exit 0); sole importer = `src/harness/__init__.py:15-18` re-export; **ZERO external symbol consumers** toàn repo (start_trace/TraceContext không ai dùng ngoài telemetry_collector.start_trace không liên quan); `metrics.py` (75 dòng) cùng cảnh — chỉ harness/__init__ import | **DELETE** cả 2 file dead + strip re-exports trong `src/harness/__init__.py` | Task text nói "giữ 1 bản + shim" nhưng scout chứng minh bản harness là orphan byte-identical với bản core đã xóa — "keep one" đã xảy ra ở Wave 3 (giữ bản khác: telemetry); shim cho zero consumers = debt mới. Honest adaptation: delete dead stubs, ghi rõ trong commit + execution.md | Low — zero consumers verified; nếu execute-time grep tìm thấy consumer mới xuất hiện → fallback về keep+shim |
| 6 | `src/core/runtime_adapter.py`: `plan()` stub lines 253-255 (1 Step từ intent), `delegate()` stub lines 257-259 (mọi step → cùng `self._agent_id`); execute loop gọi `self._dispatcher.dispatch(task, task.agent)` line 359; production wiring `src/commands/run.py:100` dùng `_NullDispatcher` (raise NotImplementedError, runtime fallback graceful); TỒN TẠI 2 agent stacks: `src/core/agent_base.py:59` AgentBase (plan/execute/verify/run, importers: swarm, agent_registry, src/agents/*) + `src/core/agent_registry.py` AgentRegistry singleton (AgentMeta declarative, built-ins cto/cmo/coo/cfo/cso/planner) và `src/harness/agents/` (registry/base/factory riêng) | **WIRE** (không NEW framework): `plan()`/`delegate()` thật qua AgentRegistry + AgentBase HIỆN CÓ; định nghĩa payload contract delegate()→agent spawn | §3 canonical lifecycle: DELEGATE phải thật; cấm orchestrator thứ 2 = reuse registry + AgentBase.run() làm execution unit, dispatcher bridge resolve AgentId→AgentMeta→AgentBase instance | Medium — 2 agent stacks tồn tại; wave này CHỈ wire core stack (agent_registry + agent_base), KHÔNG chạm harness/agents (escrow convergence riêng); _NullDispatcher giữ làm fallback khi registry không resolve được agent |
| 7 | `src/core/exec_runtime/types.py`: ExecutionRuntime Protocol runtime_checkable (execute/filesystem/process/network_policy/environment/preview/health/destroy); `src/core/exec_runtime/local.py` LocalExecutionRuntime là impl duy nhất (sanitizer-first, Popen registry, SIGTERM→SIGKILL, confine-to-root) | **NEW** `CloudflareExecutionRuntime` + `DockerExecutionRuntime` implement Protocol hiện có | §9/§16: CF + Docker = first-class adapters, local-first giữ nguyên | Medium — hermetic bắt buộc: CF adapter test qua injected transport/fake API client (KHÔNG gọi CF API thật); Docker adapter skip-if-no-daemon cho integration path nhưng PHẢI có unit path (command construction, spec mapping, error handling) chạy được không cần daemon |
| 8 | `src/core/protocols.py:253-270` PaymentProvider đủ 7 method; `src/core/adapters/payment_mock.py` MockPaymentProvider full; `src/core/adapters/payment_x402_shape.py` có shape codec pure-data (encode/decode, X402_SCHEME="exact", `_reject_forbidden_fields` chặn key-like fields) nhưng CHƯA có settlement provider thật | **NEW** `X402SettlementProvider` implement PaymentProvider, wrap shape codec; policy-gated fail-closed | §12/§18: economic bus cần provider thật sau interface nhưng KHÔNG network nếu thiếu config tường minh | High nếu làm ẩu — mitigate bằng invariants: thiếu explicit config ⇒ raise/refuse (fail-closed); approval bắt buộc qua Governance; không log keys; tests hermetic 100% (injected fake transport); không real money |
| 9 | Buzz live integration smoke cần staging workspace — session này KHÔNG CÓ | **DEFER** — ghi escrow BLOCKED-ON-ENVIRONMENT, không fake | Task.md chỉ đạo tường minh | None nếu ghi escrow trung thực; risk chỉ khi ai đó fake pass — gate bằng rule: không commit nào claim Buzz live đã chạy |
| 10 | `src/core/runtime_adapter.py:306-337` Gate 2.5 chỉ classify capability risk_level; `src/core/agent_registry.py:24-48` AgentMeta có risk_level/max_budget/max_iterations/approval_policy + validation (CRITICAL+AUTO→ValueError) nhưng KHÔNG ai đọc lúc execute; `src/core/capability.py:183-189` InMemoryCapabilityBus.execute() chỉ check existence/expiry | **WIRE**: Gate 2.5 mở rộng merge agent policy (registry lookup theo task.agent.name) — effective risk = max(agent, capability); budget→cost guard; iterations→repair cap; approval_policy→approval requirement | §13: 1 decision path Mission→Capability→Risk→Policy; biến khai báo thành enforcement | Medium — phải giữ Governance là decision path DUY NHẤT (không thêm permission system); unknown agent → fail-closed hay fallback SAFE? Quyết định: unknown agent meta = enforce nothing thêm nhưng log audit (giữ behavior hiện tại cho agent không đăng ký), agent ĐÃ đăng ký = enforce đủ |

**Chú thích phân loại:** NEW=4 (#1 command, #3 conformance suite, #7 ×2 adapters, #8 provider — thực 5 items), REFACTOR=3 (#2, #3 protocol, #1 manifests), MOVE=1 (#4), WIRE=2 (#6, #10), DELETE=1 (#5), DEFER=1 (#9). KEEP: toàn bộ protected flows + LocalExecutionRuntime + MockPaymentProvider + AgentRegistry/AgentBase hiện trạng.

---

## 3. Work Checklist — LANES (1 subagent/lane, ranh giới file rõ)

**Spawn convention (bắt buộc):** bare spawn (KHÔNG worktree-isolation — bài học Phase 10); mọi prompt kèm: Work context `/Users/macbook/mekong-cli/.claude/worktrees/super-command-2`, Reports `.orchestrate/latest/reports/`, Plans `.orchestrate/latest/`.

### E0 — Re-baseline (orchestrator tự làm, trước mọi lane)

- [ ] Trong worktree: `python3 -m pytest tests/ -q --tb=no --ignore=tests/test_world_model.py --continue-on-collection-errors 2>&1 | tee .orchestrate/latest/baseline_d71e13fa02.txt`
- [ ] Extract fail-set: `grep "^FAILED " baseline_d71e13fa02.txt | sed 's/ - .*//' | sort -u > .orchestrate/latest/failset_baseline.txt`; ghi tổng passed/failed/skipped vào execution.md
- [ ] Chụp CI baseline tại d71e13fa02 (đã scout: GREEN set = Check Documentation, Backend Python 3.11+, Command Injection Scan, Dependency Security Audit, Gate 1/2/4, Generate Security Attestation, Secret Scanning, Security Gate Enforcement, Security Headers Check, Security Scan; KNOWN-RED = command-fabric-release-gate, G1 Validation, G3 Quality, G4 Dep Audit, Gate 3 Quality Check, Lint & Unit Test, test, TypeScript Packages, validate; SKIPPED = Build&Push, Deploy×2, G5, Merge Gate, OWASP ZAP) — verify lại bằng `gh api repos/minhlongs/mekong-cli/commits/d71e13fa02.../check-runs`

### Wave A — Debt cơ khí (3 lane SONG SONG, không chung file)

**Lane E1 — harness-eval command + dna manifests** (fullstack-developer → tester)
- Files SỞ HỮU: `src/cli/commands/harness_eval_command.py` (NEW), `src/cli/app_setup.py` (register), `dna/core-dna.json`, `dna/command-surface.json`, `dna/command-packs.json`, `dna/hermes-learning-loop.json`, `tests/test_harness_eval_command.py` (NEW)
- [ ] Command root-level `harness-eval` theo pattern `register_doctor` (`src/cli/app_setup.py:38,130` — verified): wrap `run_solo_ceo_harness_evals()` từ `src/harness/evals/solo_ceo.py`; flag `--json` (CI gọi đúng `python3 -m src.main harness-eval --json`); exit code 0 khi passed==total, 1 khi có fail
- [ ] Verify `"harness-eval"` đã có trong `dna/core-dna.json:85` free_commands (verified — KHÔNG cần thêm; nếu execute-time thấy khác, ghi vào execution.md)
- [ ] Fix EVAL-09: `dna/core-dna.json` immutable_roots `src/binh_phap/` → `src/core/binh_phap/`
- [ ] Fix EVAL-10: `dna/hermes-learning-loop.json` required_files repoint về file thật trong repo: `src/core/memory.py` → `src/core/memory_client.py` (+`memory_scope.py`, `vector_memory_store.py` nếu eval chấp nhận list); 4 file `.claude/*` (ngoài repo public) → repoint về `src/core/mcp_server.py`/`mcp_task_store.py`/`mcp_plan_store.py` hoặc bỏ entry nếu schema cho phép — quyết định khi đọc eval logic trong solo_ceo.py
- [ ] Fix EVAL-11/12: regenerate `dna/command-surface.json` + `dna/command-packs.json` cơ khí từ `current_root_commands()` (`src/core/command_surface.py:54` — verified); xóa stale entries (accounting-*, 4-project...), thêm missing (agent, billing, company, doctor, founder...); giữ harness-eval trong core-runtime pack
- [ ] Prove: `python3 -c "from src.harness.evals.solo_ceo import run_solo_ceo_harness_evals as f; r=f(); print(r['passed'], r['total'])"` → 6/6; `python3 -m src.main harness-eval --json` exit 0
- [ ] DNA rule: mọi thay đổi feature surface (src/cli/) + dna/*.json trong CÙNG commit
- [ ] Test mới: command chạy, --json parse được, exit code đúng, 6/6 evals pass

**Lane E2 — world_model bounded walk** (debugger chẩn đoán → fullstack-developer fix → tester)
- Files SỞ HỮU: `src/core/world_model.py`, `tests/test_world_model.py`, (nếu cần) 5 test file leak cwd CHỈ để thêm cleanup fixture
- [ ] CHẨN ĐOÁN TRƯỚC: đo collect time có/không `--ignore` (`timeout 120 python3 -m pytest tests/test_world_model.py --collect-only -q` vs full-suite collect); xác nhận stack hang đúng `_get_file_tree` line 334 (faulthandler dump từ Wave 3: test_get_latest_snapshot→snapshot()→_get_file_tree); ghi số liệu vào report
- [ ] Fix `_get_file_tree()` (lines 324-348): bounded iterative walk — check exclusions + depth TRƯỚC khi descend (prune-before-descend), giữ cap 500 entries output + thêm hard visited-entry cap (vd 50k) để không bao giờ walk 300k entries dù exclusion sót; giữ nguyên output shape
- [ ] Test isolation: tests/test_world_model.py:129-153 phải khởi tạo WorldModel với working_dir tường minh (tmp_path fixture); thêm guard test: WorldModel trong tmp tree có excluded dir lớn → không descend vào
- [ ] Prove: `python3 -m pytest tests/test_world_model.py -q` pass standalone VÀ pass trong full-suite (không hang, <60s); sau đó parity command MỚI (bỏ --ignore) phải cho fail-set ⊆ baseline
- [ ] FALLBACK (nếu walk mới đổi semantics không cứu được trong wave): GIỮ `--ignore`, escrow lại với số liệu chẩn đoán — không block ship

**Lane E3 — tracing dedup** (fullstack-developer, lane nhỏ nhất)
- Files SỞ HỮU: `src/harness/observability/tracing.py` (DELETE), `src/harness/observability/metrics.py` (DELETE), `src/harness/__init__.py` (strip re-exports lines 15-18 + metrics tương đương), test files nếu có (verify: zero consumers đã scout)
- [ ] Verify lại zero consumers tại HEAD hiện tại (grep `from src.harness.observability import|from src.harness import.*start_trace|TraceContext` toàn src+tests) — nếu xuất hiện consumer mới → fallback keep+shim theo task text gốc
- [ ] Delete + strip; prove: `python3 -m pytest tests/ -q --tb=no` parity giữ nguyên; `python3 -c "import src.harness"` OK
- [ ] Commit message ghi rõ: bản harness là byte-identical orphan của bản core đã xóa Wave 3 (kèm bằng chứng cmp)

### Wave B — Contracts (2 lane, E5 phụ thuộc E4 hoàn thành interface)

**Lane E4 — tool_call() + conformance suite** (fullstack-developer → tester)
- Files SỞ HỮU: `src/core/protocols.py` (LLMRouter Protocol), `src/core/llm_router_adapter.py`, `tests/test_llm_router_conformance.py` (NEW)
- [ ] Thêm `tool_call()` vào LLMRouter Protocol (`src/core/protocols.py:187-197`) — signature nhận messages + tool schemas, trả về structured tool-call result; implement trong adapter wrap LLMClient (provider nào chưa hỗ trợ tool calling → capability flag + raise rõ ràng, KHÔNG silent fake)
- [ ] Conformance suite: parametrize ≥2 provider paths (vd OpenRouter-compatible + Claude-Fable-shaped fake transports — injected, không network) chạy CÙNG 5 method: generate/stream/structured_output/tool_call/health; assert contract invariants (return types, error semantics, health shape)
- [ ] Prove: suite pass; Protocol runtime_checkable isinstance check cho adapter

**Lane E5 — MOVE llm_client → adapters/llm** (fullstack-developer chạy script → tester)
- Files SỞ HỮU: `src/core/llm_client.py` → `src/core/adapters/llm/client.py` (hoặc package `src/core/adapters/llm/`), 68 file references, `tests/conftest.py:293,311`, `tests/test_core_boundary.py:27-52`, `DEPRECATION.md`
- [ ] Pre-verify count: `grep -rln "llm_client" src/ tests/ --include="*.py" | grep -v __pycache__ | wc -l` phải = 68 (baseline đã scout; nếu khác, cập nhật script trước khi chạy)
- [ ] Scripted repoint (sed với whitelist patterns, KHÔNG edit tay): `from src.core.llm_client import` → `from src.core.adapters.llm.client import`; `from .llm_client` (relative trong core) → absolute mới; `@patch("src.core.llm_client.get_client")` strings → path mới; conftest pre-import tuple + patch target; boundary allowlist entry `"src/core/llm_client.py"` → path mới (giữ nguyên transitional note)
- [ ] Post-verify: `grep -rn "core\.llm_client\|from \.llm_client" src/ tests/ --include="*.py"` = RỖNG (trừ DEPRECATION.md text); `python3 -c "from src.core.adapters.llm.client import get_client"` OK
- [ ] KHÔNG shim 2 đường (PEV precedent): repoint sạch + 1 dòng DEPRECATION.md note; import-graph test: assert `src/core/__init__.py` và core modules (trừ adapters) không import adapters.llm ngược lại
- [ ] Prove behavior: full parity fail-set = baseline; ruff clean

### Wave C — Features (4 lane; E6+E9 cùng chạm runtime_adapter → chạy SEQUENTIAL hoặc tách file region; E7, E8 độc lập song song)

**Lane E6 — DELEGATE wiring thật** (fullstack-developer → tester) — chạy TRƯỚC E9
- Files SỞ HỮU: `src/core/runtime_adapter.py` (plan/delegate region lines 253-259), `src/commands/run.py` (dispatcher wiring), `tests/test_runtime_delegate.py` (NEW)
- [ ] `plan()`: giữ Step generation nhưng thêm agent assignment thật — intent classification đơn giản qua AgentRegistry built-ins (cto/cmo/coo/cfo/cso/planner đã có); KHÔNG thêm LLM dependency mới
- [ ] `delegate()` payload contract (định nghĩa tường minh): `Task(step, agent=AgentId(name), params)` hiện có + mới: registry lookup `get_meta_obj(agent.name)` → resolve AgentBase subclass → dispatcher.dispatch spawn qua `AgentBase.run()` làm execution unit; unknown agent → fallback `_NullDispatcher` behavior hiện tại (graceful) + audit log
- [ ] `src/commands/run.py`: thay `_NullDispatcher` bằng registry-backed dispatcher (AgentRegistry + AgentBase bridge); giữ failure-tolerant init pattern hiện có
- [ ] CẤM: không class orchestrator mới, không scheduler mới, không chạm `src/harness/agents/` (2-stack convergence = escrow riêng)
- [ ] Tests: delegate() sinh tasks với agents khác nhau theo intent; dispatch thật qua AgentBase subclass fake; unknown agent fallback; cancel seam `_is_cancelled()` vẫn hoạt động giữa delegation

**Lane E7 — CF + Docker ExecutionRuntime** (fullstack-developer → tester) — song song E6
- Files SỞ HỮU: `src/core/exec_runtime/cloudflare.py` (NEW), `src/core/exec_runtime/docker.py` (NEW), `tests/test_exec_runtime_cloudflare.py` (NEW), `tests/test_exec_runtime_docker.py` (NEW)
- [ ] Cả hai implement đủ 8 method Protocol `src/core/exec_runtime/types.py`; reuse `SandboxSpec.resolve_in_root` + `CommandSanitizer(strict_mode=True)` như LocalExecutionRuntime làm chuẩn
- [ ] CF adapter: injected transport/fake API client — KHÔNG gọi CF API thật; test: command mapping, spec→worker config translation, error/timeout paths, health/destroy lifecycle
- [ ] Docker adapter: unit path (docker CLI command construction, spec→container config, network policy mapping, error handling) chạy KHÔNG cần daemon; integration path (`docker info` probe) skip-if-no-daemon với `pytest.mark.skipif`
- [ ] Prove: `isinstance(adapter, ExecutionRuntime)` runtime_checkable pass; unit tests pass hermetic

**Lane E8 — x402 settlement provider fail-closed** (fullstack-developer → tester) — song song E6
- Files SỞ HỮU: `src/core/adapters/payment_x402.py` (NEW), `tests/test_payment_x402_provider.py` (NEW)
- [ ] `X402SettlementProvider` implement PaymentProvider 7 method (`src/core/protocols.py:253-270`), wrap shape codec `payment_x402_shape.py` cho quote/request payload
- [ ] FAIL-CLOSED invariants (test từng cái): (1) thiếu explicit config (endpoint/asset/network/recipient) ⇒ raise ConfigError, không bao giờ default-allow; (2) settle/request bắt buộc qua Governance approval path; (3) không log key/seed — reuse `_reject_forbidden_fields` discipline, test assert secret không xuất hiện trong log capture; (4) network ONLY qua injected transport — test dùng fake transport, assert 0 socket call thật; (5) replay/wrong-asset/wrong-network reject theo §18 test list
- [ ] KHÔNG: wallet creation, custody, key storage, real money

**Lane E9 — Gate 2.5 agent-policy enforcement** (fullstack-developer → tester) — chạy SAU E6 (cùng file runtime_adapter.py)
- Files SỞ HỮU: `src/core/runtime_adapter.py` (Gate 2.5 region lines 306-337), `tests/test_policy_decision_path.py` (extend) hoặc `tests/test_agent_policy_enforcement.py` (NEW)
- [ ] Tại Gate 2.5: lookup `AgentRegistry.get_meta_obj(task.agent.name)`; nếu có meta: effective_risk = max(agent.risk_level, capability.risk_level) qua RISK_LEVEL_MAP (`src/core/governance.py:79`); max_budget → cost guard trước execute; max_iterations → cap `_MAX_REPAIR_ATTEMPTS` (line 116); approval_policy → request_approval (`src/core/governance.py:171`) khi HIGH
- [ ] Governance là decision path DUY NHẤT — không thêm permission check song song; audit event per decision (`record_audit` governance.py:209)
- [ ] Unknown/unregistered agent: giữ behavior hiện tại (capability-only classification) + audit log ghi nhận — không fail-closed toàn bộ để tránh break run.py flow hiện có
- [ ] Tests: agent CRITICAL + capability LOW → vẫn REVIEW_REQUIRED/deny theo policy; budget exceeded → refuse; iterations cap respected; approval_policy HIGH → approval requested; GOVERNANCE_AUTO_APPROVE bypass vẫn loud

**Lane E10 — Buzz live: DEFER** (orchestrator ghi, không spawn)
- [ ] Ghi escrow BLOCKED-ON-ENVIRONMENT vào execution.md + ship-report: không staging Buzz workspace trong session này; BuzzRuntimeAdapter (INTERFACE_VERSION v0.1) đã ship Wave trước với injectable transport — live smoke là việc của wave sau khi có workspace; KHÔNG fake pass

### Wave D — Docs + final gates (docs-manager → tester → orchestrator)

- [ ] docs-manager: cập nhật docs chịu ảnh hưởng — `docs/core-contract.md` (tool_call thêm vào LLM abstraction), `docs/runtime-adapters.md` (CF/Docker), `docs/economic-bus.md` (x402 provider + fail-closed policy), `docs/autonomy-model.md` (agent policy enforcement), `DEPRECATION.md` (llm_client move note); README/CLAUDE.md nếu command count đổi (36 → 37 với harness-eval)
- [ ] Final gate sweep (orchestrator + tester):
  - Parity: lệnh so sánh bên dưới §4
  - Protected flows anchored grep trên `git diff --name-only origin/main...HEAD`: `^src/(raas/nowpayments_|api/billing_routes\.py$|middleware/license_gate\.py$|lib/raas_gate/|gateway\.py$)` → RỖNG
  - §1.4-style anti-duplication grep sweep: không orchestrator class mới (`grep -rn "class.*Orchestrator\|class.*Scheduler" src/core/` diff vs baseline), không registry thứ 2, provider-specific imports trong core (boundary test tự chạy), payment secrets (`grep -rn "private_key\|seed_phrase" src/core/adapters/payment_x402.py` → chỉ rejection logic)
  - `python3 -m ruff check src/ tests/` clean
  - CLI smoke: `python3 -c "from src.cli.app_setup import build_app; print(len(build_app().registered_groups))"` ≥ 36 (37 nếu harness-eval là group mới — verify pattern register flat command có thể không tăng group count; ghi số thực)
  - core-dna-gate local simulate: `python3 -m src.main harness-eval --json` exit 0

---

## 4. Risks & Gates

### 4.1 Parity gate (re-baseline tại d71e13fa02)

**Baseline command (E0, đã định nghĩa ở §3):**
```
python3 -m pytest tests/ -q --tb=no --ignore=tests/test_world_model.py --continue-on-collection-errors
```
Fail-set extract: `grep "^FAILED " out.txt | sed 's/ - .*//' | sort -u > failset_baseline.txt`

**So sánh sau mỗi lane và trước ship:** chạy cùng lệnh → extract cùng cách → `comm -13 failset_baseline.txt failset_new.txt` phải RỖNG (0 new failures). Passed count được phép dao động ±; failed-set phải ⊆ baseline.

**Nếu Lane E2 thành công (bỏ --ignore):** parity MỚI định nghĩa công bằng = lệnh không còn `--ignore`:
```
python3 -m pytest tests/ -q --tb=no --continue-on-collection-errors
```
và baseline-mới = fail-set của lệnh đó chạy tại d71e13fa02 (chạy 1 lần duy nhất trong E0 song song, ghi vào `.orchestrate/latest/failset_baseline_with_world_model.txt` — dự kiến world_model tests FAIL/timeout trong baseline cũ, đó là lý do ignore tồn tại; fail-set mới sau fix phải ⊆ baseline-cũ ∪ {world_model tests nay PASS}). Quy tắc: bỏ ignore chỉ được chấp nhận nếu không test nào ĐANG pass trở thành fail.

**Nếu Lane E2 fallback:** giữ nguyên lệnh baseline cũ, escrow #2 ghi lại với số liệu chẩn đoán.

### 4.2 Protected flows — anchored grep trên diff
```
git diff --name-only origin/main...HEAD | grep -E '^src/(raas/nowpayments_|api/billing_routes\.py$|middleware/license_gate\.py$|lib/raas_gate/|gateway\.py$)'
```
phải RỖNG trước mọi commit bucket và trước push.

### 4.3 Workflow files — CẤM
`git diff --name-only origin/main...HEAD | grep '^\.github/workflows/'` phải RỖNG (PR #7 sở hữu). LƯU Ý: core-dna-gate.yml:60 gọi `harness-eval` — ta làm command khớp signature đó, KHÔNG sửa workflow.

### 4.4 core-dna-gate manifest rule
Mọi commit đụng feature surface (`src/cli/`, `src/commands/`) PHẢI kèm `dna/*.json` update trong cùng commit — bài học từ chính core-dna-gate red. Lane E1 đã gom sẵn 4 manifest fix; các lane khác (E6 đụng src/commands/run.py) phải kiểm tra: run.py change có đổi command surface không (không — chỉ dispatcher wiring nội bộ; nhưng verify bằng harness-eval sau commit).

### 4.5 Risk register tổng

| Risk | Lane | Mitigation |
|---|---|---|
| Sửa manifest làm eval khác đỏ | E1 | Chạy 6/6 eval local trước commit; từng manifest fix có test |
| Bounded walk đổi semantics | E2 | Giữ output shape; cap kép (output 500 + visited 50k); fallback giữ ignore |
| MOVE gây import sót | E5 | Script whitelist + post-grep RỖNG + parity + import-graph test |
| Delete tracing nhầm consumer | E3 | Verify lại zero consumers tại HEAD trước delete; fallback keep+shim |
| DELEGATE tạo orchestrator ẩn | E6 | Chỉ reuse AgentRegistry+AgentBase; grep sweep §4.4-D |
| x402 accidentally network | E8 | Injected transport duy nhất; fail-closed config test; §18 checklist |
| 2 lane chạm runtime_adapter.py | E6/E9 | Sequential: E6 trước E9 |
| Parity drift do PR #7 merge song song | all | Re-baseline lại nếu origin/main đổi trước push |

---

## 5. Agent Assignments (từng bước)

| Bước | Agent | Ghi chú |
|---|---|---|
| E0 re-baseline | orchestrator tự làm | Không spawn |
| E1 harness-eval + manifests | fullstack-developer → tester | Lane lớn nhất Wave A |
| E2 world_model | debugger (chẩn đoán) → fullstack-developer (fix) → tester | Chẩn đoán có số liệu trước khi hứa fix |
| E3 tracing dedup | fullstack-developer | Lane nhỏ, verify-zero-consumers trước |
| E4 tool_call + conformance | fullstack-developer → tester | |
| E5 MOVE llm_client | fullstack-developer (script) → tester | Sau E4 |
| E6 DELEGATE | fullstack-developer → tester | Trước E9 |
| E7 CF/Docker runtimes | fullstack-developer → tester | Song song E6 |
| E8 x402 provider | fullstack-developer → tester | Song song E6 |
| E9 Gate 2.5 enforcement | fullstack-developer → tester | Sau E6 |
| E10 Buzz escrow | orchestrator ghi | Không spawn |
| Docs | docs-manager | Wave D |
| Final gates + commit + PR | git-manager + orchestrator | Wave D |

---

## 6. Ship Plan

### 6.1 Pre-deploy checklist (trước commit bucket đầu tiên)
- [ ] Worktree @ d71e13fa02, branch đúng, tree clean (verified)
- [ ] E0 baseline files tồn tại trong `.orchestrate/latest/`
- [ ] `git fetch origin` — nếu origin/main đã đổi (PR #7 merge), rebase branch + re-baseline trước

### 6.2 Commit buckets (conventional format, không AI references)
1. `feat(cli): add harness-eval command and repair dna manifests` (E1 — command + 4 manifests CÙNG commit)
2. `fix(world-model): bound file-tree walk with prune-before-descend` (E2 — chỉ khi thành công; nếu bỏ được ignore thì parity command update ghi trong commit body)
3. `refactor(harness): remove dead byte-identical tracing stubs` (E3)
4. `feat(llm): add tool_call to LLMRouter with provider conformance suite` (E4)
5. `refactor(adapters): move llm_client into adapters/llm` (E5 — 1 commit duy nhất cho toàn bộ 68-file repoint để bisect được)
6. `feat(runtime): wire real delegation through agent registry` (E6)
7. `feat(exec-runtime): add Cloudflare and Docker execution runtimes` (E7)
8. `feat(payments): add fail-closed x402 settlement provider` (E8)
9. `feat(governance): enforce agent policy at capability execution` (E9)
10. `docs: update runtime contracts and deprecation notes` (Wave D)

Mỗi commit: ruff clean + touched-tests pass + protected-flow grep RỖNG. `.orchestrate/` KHÔNG bao giờ stage.

### 6.3 Push + PR
- [ ] `git push -u origin feat/runtime-v02-contracts-and-debt`
- [ ] `gh pr create --base main --title "feat: runtime v0.2 — contracts completed + debt closure" --body ...` (body: 10 task status, parity evidence, escrows, link task.md)

### 6.4 CI acceptance
- GREEN set (11 checks §3 E0) phải GIỮ XANH
- KNOWN-RED set chấp nhận nếu y hệt baseline; **core-dna-gate dự kiến FLIP đỏ→xanh** (đây là cải thiện mong muốn từ task #1, không phải regression)
- Đỏ MỚI ngoài 2 set trên = block, điều tra trước merge
- Nếu CI đỏ do thiếu dep harness-eval (bài học wave trước): verify `python3 -m src.main harness-eval --json` local trước push

### 6.5 Merge + post-merge
- [ ] Squash merge qua `gh pr merge --squash` (sau CI accept + human review nếu pipeline yêu cầu)
- [ ] Post-merge verify trên origin/main mới: parity command chạy lại, CLI smoke ≥36 groups, `harness-eval --json` exit 0
- [ ] Rollback plan: `git revert <squash-sha>` (1 commit duy nhất vì squash)
- [ ] Ghi `.orchestrate/latest/ship-report.md` + archive `.orchestrate/latest/` → `.orchestrate/archive-super-command-3/`

---

## 7. STOP CONDITION (sau ship)

Báo cáo rồi DỪNG chờ human architect review:
1. Git diff summary (files changed/added/deleted theo lane)
2. Scores 10 chiều (/100, brutally honest): Core Contracts, Adapter Boundary, Test Coverage, Debt Closure, CI Health, Security Invariants, Docs Accuracy, Anti-Duplication, CLI Compatibility, Autonomy Enforcement
3. Blockers còn lại (Buzz live, 2-agent-stack convergence, stream single-chunk limitation...)
4. Đúng 10 task kế tiếp đề xuất
5. DỪNG — không tự chạy tiếp Phase 3

---

## 8. Assumptions (mọi chỗ phải đoán thay câu hỏi)

| # | Assumption | Confidence | Điều gì sẽ đổi câu trả lời |
|---|---|---|---|
| A1 | Task #1 mở rộng thành sửa 4 dna manifests (ngoài đăng ký command) vì đó là điều kiện cần để core-dna-gate xanh — đúng intent "đóng red cấu trúc" | High | Nếu user chỉ muốn command và chấp nhận gate còn đỏ → tách manifests sang wave sau |
| A2 | Task #5 "keep one + shim" được adapt thành delete dead stubs vì scout chứng minh zero consumers + byte-identical orphan | Medium | Nếu execute-time tìm thấy consumer mới → fallback keep+shim đúng nghĩa đen |
| A3 | harness-eval đăng ký theo flat-command pattern (register_doctor style) vì CI gọi `src.main harness-eval` root-level | High | Nếu build_app group count semantics đòi hỏi add_typer → điều chỉnh, giữ signature `harness-eval --json` |
| A4 | DELEGATE wire qua core stack (agent_registry + agent_base), KHÔNG phải harness/agents — vì runtime_adapter cùng tầng core và AgentMeta policy fields (liên quan task #10) nằm ở agent_registry | Medium | Nếu pipeline muốn harness/agents làm canonical → E6 đổi target, nhưng phải giải quyết 2-stack trước |
| A5 | Unknown/unregistered agent trong Gate 2.5 giữ behavior hiện tại (không fail-closed toàn bộ) để không break run.py flow | Medium | Nếu muốn strict fail-closed → thêm flag, nhưng phải migrate mọi caller |
| A6 | Docker daemon không có sẵn trong CI/dev session → unit path bắt buộc, integration skip-if-no-daemon | High | Nếu có daemon → chạy thêm integration path, không đổi thiết kế |
| A7 | PR #7 chưa merge trong wave này; nếu merge trước push → rebase + re-baseline (đã có bước trong 6.1) | Medium | Nếu PR #7 đổi pytest command trong workflow → parity definition phải align theo |
| A8 | x402 provider dùng fake transport injected; không tồn tại staging x402 endpoint nào được phép gọi | High | Nếu có config staging tường minh + approval → vẫn không gọi trong wave này (§18: no real money in tests) |
