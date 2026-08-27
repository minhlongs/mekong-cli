# TASK — SUPER COMMAND #3: Runtime v0.2 — Contracts Completed + Debt Closure

## Nguồn

Wave trước (Super Command #2, PR #8 squash `d71e13fa`) đã ship foundation autonomous runtime v0.1 và **DỪNG theo §23 chờ human architect review**. Người dùng đã review danh sách 10 task tiếp theo và phê duyệt: **"go"** (2026-08-26).

Base mới: `origin/main` = `d71e13fa02`. Branch làm việc: `feat/runtime-v02-contracts-and-debt` trong worktree `/Users/macbook/mekong-cli/.claude/worktrees/super-command-2`.

## Phạm vi đã duyệt — đúng 10 task sau (không mở rộng)

1. Register CLI command `harness-eval` (wrap `src/harness/evals/solo_ceo.py:run_solo_ceo_harness_evals`) — đóng red cấu trúc của core-dna-gate. LƯU Ý: command mới = feature surface → PHẢI cập nhật `dna/*.json` (core-dna-gate sẽ check); đăng ký vào free_commands hay advanced_features do planner quyết (harness-eval đã có tên trong free_commands từ trước — verify).
2. Fix world_model collection hang (rglob không prune ~300k entries) — mục tiêu: bỏ `--ignore=tests/test_world_model.py` khỏi parity command, tests collect + pass.
3. Implement `LLMRouter.tool_call()` + bộ conformance test ép ≥2 provider qua cùng interface (generate/stream/structured_output/tool_call/health).
4. MOVE `llm_client` vào adapters/llm sau canonical interface (46 file references — cơ khí, scripted, giữ behavior).
5. Tracing dedup: harness observability ≡ old core copy — giữ 1 bản + shim re-export.
6. Wire DELEGATE thật: `plan()`/`delegate()` trong runtime_adapter spawn multi-agent qua agent protocol hiện có (không tạo framework thứ 2).
7. `CloudflareExecutionRuntime` + `DockerExecutionRuntime` implement ExecutionRuntime Protocol hiện có.
8. Real x402 settlement provider sau PaymentProvider interface — policy-gated fail-closed, approval bắt buộc; KHÔNG gọi network thật nếu thiếu config tường minh; §18: no keys logged, no custody, no real money in tests.
9. Buzz live integration smoke với staging workspace → **BLOCKED-ON-ENVIRONMENT**: session này không có staging Buzz workspace. Planner ghi escrow/deferred rõ ràng, không fake.
10. Enforce authorization runtime: nối `AgentMeta.risk_level/max_budget/max_iterations/approval_policy` vào Governance tại thời điểm `capability.execute()` (hiện chỉ khai báo).

## Ràng buộc kế thừa (từ mandate gốc + wave trước)

- ABSOLUTE RULES 1–18 nguyên văn (không framework thứ 2, không hard-code vendor, prefer adapters, core nhỏ, mọi change có test, CLI backwards compat, no marketplace/tokenomics/custody).
- Protected flows CẤM đụng: `src/raas/nowpayments_*`, `src/api/billing_routes.py`, `src/middleware/license_gate.py`, `src/lib/raas_gate/`, `src/gateway.py` — grep anchored trên diff phải RỖNG.
- Parity gate: re-baseline tại d71e13fa02 bằng lệnh chuẩn `python3 -m pytest tests/ -q --tb=no --ignore=tests/test_world_model.py --continue-on-collection-errors`; normalized failset diff vs baseline mới phải EMPTY suốt pipeline (task #2 nếu xong sẽ đổi lệnh — planner quy định cách chứng minh không mất test nào).
- Phối hợp PR #7 (`fix/ci-runnable-gates`, session song song): họ sở hữu `.github/workflows/*` — nhánh này KHÔNG sửa workflow files; chỉ thêm code src/ mà gate cần.
- CI acceptance: GREEN set giữ xanh; đỏ mới do nhánh gây ra = phải sửa (core-dna-gate: mọi thay đổi feature surface phải kèm dna/*.json).
- §18 security invariants; không secret trong code/tests.
