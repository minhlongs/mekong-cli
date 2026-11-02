# Báo cáo Tư vấn Kỹ thuật (`--ultra` Best-of-5): Supreme Command #01.2 — Adversarial Hardening & Sophia Handoff

- **Ngày:** 2026-11-02
- **Repository:** `minhlongs/mekong-cli`
- **Reference HEAD:** `2c3c8dd13e9e7fadab244f2fb21c84018fffc112` (PR #125 — MERGED)
- **Nhánh đích khi thi công:** `fix/supreme-command-01-2-runtime-hardening`
- **Chế độ tư vấn:** `/ak-advise --ultra` (Best-of-5 Verifier Synthesis)

---

## 1. Verdict (Nhận định tổng thể)

Supreme Command #01 và #01.1 đã hoàn tất hội tụ trục thực thi (Canonical Runtime + SQLiteGoalStore + CLI/Adapter wiring), nhưng **4 lỗ hổng bảo mật và tính đúng đắn (`F01`–`F04`)** trong bản đặc tả Supreme Command #01.2 hoàn toàn có thật trên `HEAD` (`2c3c8dd13e9e7fadab244f2fb21c84018fffc112`) và **bắt buộc phải khóa trước khi Sophia AI Factory ủy quyền thực thi tự trị cho Mekong CLI**. Nguy hiểm nhất không chỉ là 4 điểm đã nêu trong đề bài mà còn có **3 bẫy ngầm (latent traps)** được Candidate 1 và Candidate 5 phát hiện khi đối chiếu dòng-theo-dòng:
1. **`GoalEngine.verify_goal()` (`src/mekongcli/core/goal_engine/service.py:263-266, 638-670`)**: Khi gọi `run_goal(..., execute_commands=True)` trên các task mặc định có `task.command is None` (do `GoalPlanner.decompose()` sinh ra), các task này rơi vào nhánh `else:` (`task.truth_status = SIMULATED`), nhưng `run_goal()` lại truyền cứng `simulated_run=not execute_commands` (`False`) vào `verify_goal()`. Hệ quả là `verify_goal()` bỏ qua việc mọi task đều là `SIMULATED` và đóng dấu `goal.truth_status = VERIFIED_SUCCESS` dù không có một lệnh thực tế nào chạy!
2. **`WorktreeIsolationManager` (`src/mekongcli/core/goal_engine/worktree_manager.py:58-74, 111-125`)**: Ngoài việc `finally:` xóa sạch artifact (`F02`), khi chạy song song (`run_goal_parallel`), nhiều luồng gọi `git worktree add/remove` đồng thời gây tranh chấp `.git/config.lock` và rơi vào nhánh `except` chỉ tạo thư mục rỗng `wt_path.mkdir()`, làm mất toàn bộ file nguồn của workspace.
3. **`SQLiteGoalStore.admit_ticket()` (`src/mekongcli/core/goal_engine/store.py:636-683`)**: Kiểm tra `SELECT` rồi mới `INSERT` mà không bắt `sqlite3.IntegrityError` khi 2 kết nối SQLite đua nhau (race condition TOCTOU) hoặc khi trùng `ticket_id` PK.

---

## 2. What you should do (Những việc cần làm theo thứ tự ưu tiên)

### Gate G0 — Thiết lập nhánh cô lập & Baseline
1. Kiểm tra trạng thái sạch trên `main` (`2c3c8dd13e9e7fadab244f2fb21c84018fffc112`) và tạo nhánh `fix/supreme-command-01-2-runtime-hardening`.
2. Ghi nhận SHA-256 của `src/core/opencore/phase_559_opencore_25_step_catalog.py` và kiểm tra trần `<= 185 LOC` cho toàn bộ `src/core/opencore/*.py`, `src/core/raas_license_verifier.py`, `src/opc/*.py`.

### Gate G1 — Khóa chặt `F01`: False Verified Success (`src/core/adapters/goal_engine_adapter.py` & `src/mekongcli/core/goal_engine/service.py`)
1. **Tại `src/core/adapters/goal_engine_adapter.py:147-195`**:
   - Xóa bỏ suy diễn lạc quan ở nhánh `else:`: khi `raw_truth` là `None`, `MagicMock`, hoặc chuỗi không thuộc `ExecutionTruthStatus`, nếu `exec_cmds=True` thì gán `truth_enum = ExecutionTruthStatus.UNAVAILABLE` (tuyệt đối không gán `VERIFIED_SUCCESS`); nếu `exec_cmds=False` thì gán `ExecutionTruthStatus.SIMULATED`.
   - Đọc `tasks = self._store.get_tasks(svc_goal_id)` **trước** khi tính `success`:
     - Khi `exec_cmds=True`, `success=True` **chỉ khi**:
       - `completed_goal.status == GoalStatus.SATISFIED`
       - `truth_enum == ExecutionTruthStatus.VERIFIED_SUCCESS`
       - `profile != "none"`
       - `len(tasks) > 0` và mọi task đều có `t.status == TaskStatus.COMPLETED` và `t.truth_status == ExecutionTruthStatus.VERIFIED_SUCCESS` (nếu có bất kỳ task nào là `SIMULATED`, hạ `truth_enum` xuống `ExecutionTruthStatus.SIMULATED` và đặt `simulated=True, success=False`).
   - Khi `exec_cmds=False`: ép `truth_enum = ExecutionTruthStatus.SIMULATED`, `simulated = True`, và giữ `success = (completed_goal.status == GoalStatus.SATISFIED)` để tương thích ngược 100% với `tests/test_goal_engine_adapter.py` và `tests/ports/test_goal_engine_conformance.py`.
2. **Tại `src/mekongcli/core/goal_engine/service.py:637-671` (`verify_goal`)**:
   - Không để `simulated_run=False` ghi đè trạng thái thật của task. Tính:
     - Nếu `not tasks` hoặc bất kỳ task nào có `t.status != TaskStatus.COMPLETED`, không bao giờ trả về `VERIFIED_SUCCESS`.
     - Nếu bất kỳ task nào có `t.truth_status == ExecutionTruthStatus.SIMULATED` hoặc `not t.command`, coi toàn bộ goal là `SIMULATED` (`goal.truth_status = ExecutionTruthStatus.SIMULATED`), không được phép gắn `VERIFIED_SUCCESS`.

### Gate G2 — Khóa chặt `F02`: Vòng đời Worktree 3 trạng thái & SHA-256 Artifact Handoff (`src/mekongcli/core/goal_engine/worktree_manager.py` & `service.py`)
1. **Thêm `WorktreeMode` (`SCRATCH`, `ARTIFACT`, `RECOVERY`) và `ArtifactManifest` trong `worktree_manager.py`**:
   - Quản lý 3 thư mục tách biệt dưới `.mekong/`:
     - `.mekong/worktrees/<safe_ticket>_<safe_task>` (worktree thực thi)
     - `.mekong/artifacts/<safe_ticket>/<safe_task>/attempt_<n>/` (artifact đã thu hoạch + `manifest.json`)
     - `.mekong/recovery_worktrees/<safe_ticket>_<safe_task>_attempt_<n>/` (bảo toàn hiện trường khi lỗi/timeout/uncertain)
   - Bọc các lệnh `subprocess.run(["git", "worktree", ...])` bằng `threading.RLock()` để tránh lỗi `.git/config.lock` khi chạy song song.
   - Khi `repo_root` không phải git repo (ví dụ `tmp_path` trong unit test), sau khi `wt_path.mkdir()`, copy các file nguồn cấp cao nhất (loại trừ `.git`, `.mekong`, `__pycache__`, `.venv`, `node_modules`) vào `wt_path` để lệnh chạy trong worktree cô lập vẫn thấy script trong `tmp_path`.
2. **Cơ chế `finalize_worktree()` thay cho `cleanup()` mù quáng trong `finally:` (`service.py:148-150, 382-384`)**:
   - Phát hiện thay đổi trong worktree (file mới / file sửa đổi / `git status --porcelain` / diff so với baseline khi cấp phát).
   - **Nếu task thành công (`outcome.success`) và có artifact (`ARTIFACT` mode hoặc có file sinh ra/sửa đổi)**:
     - Thu hoạch các file thay đổi + bản vá `changes.patch` vào `.mekong/artifacts/<ticket_id>/<task_id>/attempt_<n>/`.
     - Tính `sha256` từng file, kiểm tra chống path traversal/symlink escape qua `validate_path_within_worktree()`, ghi `manifest.json` (`ticket_id`, `task_id`, `attempt_id`, `artifact_type`, `safe_ref`, `sha256`, `verification_status`, `created_at`), đối chiếu lại `sha256` trên đĩa rồi mới dọn worktree tạm.
   - **Nếu task thất bại (`not outcome.success`), timeout, hoặc `side_effect_uncertain=True` (`RECOVERY`)**:
     - Không xóa dữ liệu! Chuyển/bảo toàn sang `.mekong/recovery_worktrees/<ticket_id>_<task_id>_attempt_<n>/` kèm `recovery_manifest.json` và tháo đăng ký git worktree (`git worktree prune`) để không khóa git của repo chính.
   - **Nếu task thành công và không sinh artifact (`SCRATCH`)**:
     - Gọi `cleanup(wt_path, worker_id=...)` an toàn.
3. **Làm `cleanup()` có nhận thức quyền sở hữu (ownership-aware) và idempotent**:
   - Kiểm tra `wt_path` nằm gọn trong `self.base_dir` (nếu nằm ngoài -> `WorktreeEscapeError`).
   - Nếu `wt_path` đang được giữ bởi một `worker_id` khác (active lease) và `force=False` -> từ chối xóa (`PermissionError`).
   - Nếu `wt_path` đã được dọn trước đó -> trả về `False` nhẹ nhàng (idempotent 100%).

### Gate G3 — Khóa chặt `F03`: Durable Webhook Admission (`src/core/buzz_runtime_adapter.py`, `src/core/buzz_adapter.py`, `src/mekongcli/core/goal_engine/store.py`)
1. **Phân tách rõ `ingress_mode="external_webhook"` và `ingress_mode="trusted_local"`**:
   - Trong `BuzzRuntimeAdapter.__init__()` và `assign_mission()`, hỗ trợ `ingress_mode: Literal["trusted_local", "external_webhook"] = "trusted_local"`, đồng thời tự động kích hoạt chế độ webhook bền vững khi `ingress_mode == "external_webhook"` hoặc khi `self._outbox_store is not None` hoặc khi payload có dấu hiệu webhook ngoài (`source_id`, `event_id`, `webhook_event`).
   - Khi ở chế độ `external_webhook`:
     - Nếu `self._outbox_store is None` -> **fail-closed ngay lập tức** với `BuzzConfigError` trước khi chạm vào `runtime`.
     - Nếu thiếu `event_id` tường minh (`not str(payload.get("event_id") or "").strip()`) -> **fail-closed** với `ValueError("missing required event_id")` (không tự ý dùng `mission_id` thay thế cho `event_id` ở cổng webhook ngoài).
     - Nếu thiếu `goal`/`text` -> **fail-closed** với `ValueError`.
2. **Đảm bảo tính nguyên tử (Atomicity) và chống chạy lại khi restart (`store.py` & `buzz_runtime_adapter.py`)**:
   - Trong `SQLiteGoalStore.admit_ticket()` (`store.py:634-683`) và `enqueue_outbox()` (`store.py:969-1008`), bọc lệnh `INSERT` trong `try ... except sqlite3.IntegrityError:` để truy vấn lại bản ghi hiện có và trả về `deduplicated=True` an toàn khi có 2 luồng/tiến trình ghi đồng thời.
   - Khi `admit_webhook_event()` trả về `deduplicated=True`:
     - Kiểm tra trạng thái ticket trong DB (`COMPLETED`/`VERIFIED_SUCCESS`, `RUNNING`, `WAITING_APPROVAL`, `EXECUTION_FAILED`) và trả về ngay kết quả idempotent (`status="duplicate_ignored"`, `duplicate=True`, kèm `ticket_truth_status`) mà không gọi `run_from_payload()` lần thứ hai.
   - Cập nhật `truth_status` của ticket trong bảng `tickets` sau khi `run_from_payload()` kết thúc (`VERIFIED_SUCCESS`, `SIMULATED`, `CANCELLED`, hoặc `EXECUTION_FAILED`).

### Gate G4 — Khóa chặt `F04`: Server-Side `WebhookAuthorityPolicy` & Chống Callback SSRF (`src/core/buzz_adapter.py`)
1. **Bổ sung `WebhookAuthorityPolicy` và `BuzzSecurityError(BuzzConfigError, PermissionError, ValueError)`**:
   - Không bao giờ tin tưởng các trường quyền hạn do webhook payload tự khai báo.
   - Trong `BuzzAdapter.admit_webhook_event()`:
     - Kiểm tra `requester` nằm trong danh sách được phép của `WebhookAuthorityPolicy`.
     - Kiểm tra `permitted_capabilities`: mọi capability yêu cầu phải nằm trong `policy.allowed_capabilities` (mặc định `("buzz.mission",)`). Nếu payload đòi quyền ngoài danh sách (ví dụ `"shell.exec"`, `"deploy.prod"`) -> **raise `BuzzSecurityError`**.
     - Kiểm tra `resource_boundaries` và `authorized_scope`: chặn `".."` path traversal, chuẩn hóa đường dẫn và bắt buộc phải nằm trong `policy.allowed_resource_boundaries` (chặn `"/"`, `"/etc"`).
     - Kiểm tra `risk_classification`: chặn giá trị lạ/rỗng; không cho phép payload tự hạ mức rủi ro xuống thấp hơn `policy.min_risk_classification`.
     - Kiểm tra `cost_budget` và `retry_budget`: từ chối (`BuzzSecurityError`) nếu `<= 0` hoặc vượt trần `policy.max_cost_budget` / `policy.max_retry_budget`.
     - Các trường `mandate_version`, `policy_version`, `accepted_at`, `verification_requirements` do server ấn định.
2. **Chống SSRF & Redirect ở tầng Callback (`validate_callback_destination` & `_urllib_transport`)**:
   - Chỉ cho phép giao thức `https://` (chặn `http://`, `file://`, `ftp://`, `gopher://`, trừ khi host nằm trong allowlist test nội bộ tường minh).
   - Chặn `localhost`, `.local`, `.internal`, và mọi địa chỉ IP thuộc dải:
     - Loopback (`127.0.0.0/8`, `::1`, `::ffff:127.0.0.1`)
     - Private RFC1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fc00::/7`)
     - Link-local / Cloud Metadata (`169.254.0.0/16`, `169.254.169.254`, `fe80::/10`)
     - Carrier-Grade NAT / Cloud internal (`100.64.0.0/10`), Multicast, Unspecified (`0.0.0.0`, `::`).
   - Phân giải DNS qua `socket.getaddrinfo()` và kiểm tra **tất cả** IP trả về trước khi kết nối (với cơ chế tương thích cho domain giả lập RFC 6761 `.test`/`.example.com` khi dùng fake in-memory transport trong unit test hiện có).
   - Dùng `_NoRedirectHandler(urllib.request.HTTPRedirectHandler)` trong `_urllib_transport` để **chặn đứng mọi HTTP 301/302/303/307/308 redirect** (raise `BuzzSecurityError`).

### Gate G5 — Hợp đồng Tích hợp Sophia v1.0 (`src/core/contracts/sophia_integration_v1.py` & `docs/sophia-integration-contract.md`)
1. Thiết lập `CONTRACT_VERSION = "mekong.sophia.execution_contract.v1"` với 10 thao tác chuẩn hóa:
   - `submit_task`
   - `get_ticket` (`receive_durable_ticket_id`)
   - `get_status` (`read_ticket_status`)
   - `get_verification_evidence` (`obtain_verification_evidence`)
   - `get_artifacts` (`retrieve_artifact_references`)
   - `request_cancel` (`request_cancellation`)
   - `report_approval_required`
   - `resume_reconcile` (`resume_or_reconcile_interrupted_work`)
   - `list_durable_reports` (`subscribe_or_retrieve_durable_reports`)
   - `get_cost_usage` (`obtain_resource_cost_usage`)
2. Tách bạch 4 chiều trạng thái độc lập trong `SophiaStatusEnvelope`:
   - `execution_outcome`: `NOT_STARTED | RUNNING | WAITING_APPROVAL | RETRY_WAIT | COMPLETED | SIMULATED | FAILED | BLOCKED | CANCELLED | UNAVAILABLE`
   - `verification_outcome`: `UNVERIFIED | PASSED | FAILED | SKIPPED_OR_SIMULATED`
   - `delivery_outcome`: `PENDING | SENT | FAILED_RETRYABLE | DEAD_LETTER | NOT_APPLICABLE`
   - `business_outcome`: `PENDING | SATISFIED | APPROVAL_REQUIRED | REJECTED | RECONCILIATION_REQUIRED | FAILED | UNCONFIRMED`
3. Quy tắc bất biến `verified_success_claim_permitted`:
   - Chỉ bằng `True` khi và chỉ khi: `execution_outcome == "COMPLETED" and verification_outcome == "PASSED" and delivery_outcome in ("SENT", "NOT_APPLICABLE") and business_outcome == "SATISFIED"`.

### Gate G6–G9 — Ma trận Kiểm thử Đối kháng (`A01`–`A22`), Vệ sinh Git/CI & Draft PR
1. Tạo `tests/test_supreme_command_01_2_adversarial.py` và `tests/test_sophia_integration_contract.py` bao phủ toàn bộ `F01-T01..T06`, `F02-T01..T10`, `F03-T01..T11`, `F04-T01..T11` và 22 kịch bản `A01`–`A22`.
2. Nếu có chỉnh sửa bất kỳ file nào trong `src/cli/` hoặc `src/commands/`, cập nhật `dna/core-dna.json` để vượt qua `.github/workflows/core-dna-gate.yml`.
3. Mở **Draft PR** (`gh pr create --draft`) với đầy đủ bằng chứng kiểm thử và không tự động merge.

---

## 3. What you shouldn't do (Những bẫy cần tránh)

1. **Đừng xóa worktree mù quáng trong `finally:` (`service.py:148-150, 382-384`)**: Đó chính là nguyên nhân khiến mọi file đầu ra trong worktree cô lập bị xóa sạch trước khi caller kịp đọc.
2. **Đừng dùng `git_dir.is_dir()` trong `WorktreeIsolationManager` (`worktree_manager.py:58, 111`)**: Trong một git worktree liên kết (như chính `/Users/macbook/mekong-cli-autonomous-worktree`), `.git` là một **file** chứa con trỏ `gitdir:`, không phải thư mục. Phải giữ `git_dir.exists()`.
3. **Đừng gọi `socket.getaddrinfo()` chặn cứng trên domain `.test` / `.example.com` khi caller truyền custom fake transport trong unit test**: Các test hiện hữu trong `tests/test_buzz_adapter.py` và `tests/test_buzz_transport.py` dùng `https://buzz.test/cb` với `RecordingTransport` không qua mạng thật. Hãy luôn chạy kiểm tra cú pháp, scheme `https`, IP literal, và `socket.getaddrinfo` (nếu `getaddrinfo` trả về IP private/loopback thì chặn ngay; nếu `getaddrinfo` báo `gaierror` tên miền `.test`/`.example.com` chỉ khi dùng fake transport thì cho qua, còn với `_urllib_transport` thật hoặc `validate_callback_destination(..., strict_dns=True)` thì chặn fail-closed 100%).
4. **Đừng chạm vào `src/core/opencore/phase_559_opencore_25_step_catalog.py` hoặc vượt trần `185 LOC` của `src/opc/*.py`**: Hiện tại `src/opc/usage.py` và `src/opc/models.py` đều đang ở mức `176 LOC` (chỉ còn dư 9 dòng so với trần `185 LOC`). Đặt hợp đồng Sophia mới tại `src/core/contracts/sophia_integration_v1.py` thay vì nhồi thêm vào `src/opc/models.py`.

---

## 4. What could be better / more efficient (Tối ưu hóa hiệu suất & độ gọn)

1. **Tái sử dụng `SQLiteGoalStore` và `UsageLedger` sẵn có cho `SophiaIntegrationContractV1` (Effort thấp, Impact cao)**:
   - Không cần thêm bảng SQLite mới nếu tận dụng `tickets`, `worker_leases`, `report_outbox`, `verification_runs`, `checkpoints`, và `goal_events` kết hợp với thư mục `.mekong/artifacts/` có `manifest.json`.
2. **Đồng bộ hóa `git worktree` bằng khóa mức tiến trình (`_GIT_WORKTREE_LOCK = threading.RLock()`)**:
   - Chỉ tốn 4 dòng code trong `WorktreeIsolationManager` nhưng triệt tiêu hoàn toàn lỗi đua `.git/config.lock` khi `run_goal_parallel` cấp phát và thu hồi worktree trên 2 worker đồng thời.
3. **gom toàn bộ lỗi bảo mật Buzz về một phân cấp ngoại lệ `BuzzSecurityError(BuzzConfigError, PermissionError, ValueError)`**:
   - Giúp cả caller bắt `ValueError`, `PermissionError`, hay `BuzzConfigError` đều hoạt động nhất quán mà không làm vỡ hợp đồng ngoại lệ cũ.

---

## 5. My take and how to get there (Lộ trình triển khai từng bước)

Lộ trình ngắn gọn, an toàn và kiểm chứng được ngay ở từng chặng:
1. **Bước 1 (Branch & Baseline - G0)**: Tạo nhánh `fix/supreme-command-01-2-runtime-hardening` từ `HEAD` (`2c3c8dd13e9e7fadab244f2fb21c84018fffc112`).
2. **Bước 2 (F01 - G1)**: Sửa `src/core/adapters/goal_engine_adapter.py` và `src/mekongcli/core/goal_engine/service.py` (`verify_goal`), đảm bảo không bao giờ suy diễn `VERIFIED_SUCCESS` khi thiếu bằng chứng hoặc khi task là `SIMULATED`/`PENDING`.
3. **Bước 3 (F02 - G2)**: Nâng cấp `src/mekongcli/core/goal_engine/worktree_manager.py` và `service.py` với vòng đời 3 trạng thái (`SCRATCH`, `ARTIFACT`, `RECOVERY`), thu hoạch artifact kèm SHA-256 manifest vào `.mekong/artifacts/`, và bảo toàn worktree lỗi vào `.mekong/recovery_worktrees/`.
4. **Bước 4 (F03 & F04 - G3/G4)**: Nâng cấp `src/core/buzz_adapter.py`, `src/core/buzz_runtime_adapter.py`, và `src/mekongcli/core/goal_engine/store.py` với `ingress_mode="external_webhook"` fail-closed, `WebhookAuthorityPolicy`, xử lý `sqlite3.IntegrityError` nguyên tử, và `validate_callback_destination()` + `_NoRedirectHandler`.
5. **Bước 5 (Sophia Contract v1 - G5)**: Tạo `src/core/contracts/sophia_integration_v1.py`, `docs/sophia-integration-contract.md`, và `tests/test_sophia_integration_contract.py`.
6. **Bước 6 (Adversarial Suite A01–A22 & Regression - G6/G7/G8)**: Viết `tests/test_supreme_command_01_2_adversarial.py`, chạy toàn bộ suite mới + cũ, kiểm tra git/LOC/Core DNA gates.
7. **Bước 7 (Draft PR - G9)**: Commit, push nhánh `fix/supreme-command-01-2-runtime-hardening`, mở **Draft PR** kèm báo cáo bằng chứng tiếng Việt.

---

## 6. Benefits (Lợi ích đạt được)

- **Chấm dứt hoàn toàn báo cáo hoàn thành giả (`False Positive Completion`)**: Mọi đường gọi từ CLI, `GoalEngineAdapter.commit()`, đến `SophiaIntegrationContractV1` đều chỉ cho phép `VERIFIED_SUCCESS` khi task thực sự chạy lệnh (`exit_code == 0`) và vượt qua cổng kiểm chứng thực chất.
- **Không còn mất trắng Artifact hay dấu vết lỗi trong Worktree cô lập**: Sản phẩm đầu ra được kiểm tra SHA-256 và bàn giao sang `.mekong/artifacts/`; worktree lỗi được giữ lại tại `.mekong/recovery_worktrees/` để điều tra.
- **Khóa chặt bề mặt tấn công Webhook & SSRF**: Payload từ bên ngoài không thể tự cấp quyền `shell.exec`, tự nâng ngân sách, bỏ qua `event_id`, hoặc ép Mekong CLI gọi ngược vào `127.0.0.1` / `169.254.169.254` qua DNS hay HTTP 302 redirect.
- **Sẵn sàng bàn giao cho Sophia AI Factory**: Hợp đồng `mekong.sophia.execution_contract.v1` định nghĩa rõ 10 thao tác và 4 chiều trạng thái độc lập, có kiểm thử hợp đồng tự động (`A22`).

---

## 7. Trade-offs (Đánh đổi & Điều kiện chuyển đổi)

- **Chi phí I/O đĩa cho `ARTIFACT` và `RECOVERY` worktree**: Việc lưu bản sao artifact vào `.mekong/artifacts/` và giữ lại worktree lỗi tại `.mekong/recovery_worktrees/` sẽ tiêu tốn dung lượng đĩa theo thời gian nếu có nhiều task thất bại liên tiếp.
- **Phân tách `trusted_local` và `external_webhook`**: Để không làm gãy các unit test nội bộ cũ gọi `BuzzRuntimeAdapter(runtime=rt).assign_mission({"goal": "..."})` không có `outbox_store`, mặc định khởi tạo không đối số vẫn hỗ trợ `trusted_local`, nhưng mọi luồng có `ingress_mode="external_webhook"` hoặc có `outbox_store` đều ép buộc fail-closed 100%.
- **Khi nào khuyến nghị này không còn đủ**: Khi Mekong CLI chuyển từ SQLite đơn máy sang cụm worker phân tán đa máy chủ (multi-node), thư mục `.mekong/artifacts/` cục bộ và khóa `threading.RLock()` sẽ cần được thay bằng Object Storage (R2/S3) có Content-Addressable SHA-256 và khóa phân tán; chi phí chuyển đổi lúc đó chỉ nằm ở tầng lưu trữ của `WorktreeIsolationManager` và `SophiaIntegrationContractV1` vì manifest SHA-256 đã được chuẩn hóa từ bây giờ.

---

## 8. Unverified (Những điểm chưa xác minh)

- Không có điểm nào trong phạm vi repository hiện tại chưa được xác minh: toàn bộ 4 phát hiện `F01`–`F04`, các dòng code liên quan, và các test suite hiện hữu đã được kiểm chứng trực tiếp trên `HEAD` (`2c3c8dd13e9e7fadab244f2fb21c84018fffc112`).

---

## 9. Work Checklist, Success Metrics & Handoff Brief

### Work Checklist
- [ ] **G0**: Tạo nhánh `fix/supreme-command-01-2-runtime-hardening` từ `2c3c8dd13e9e7fadab244f2fb21c84018fffc112`; xác nhận SHA-256 của `phase_559_opencore_25_step_catalog.py`.
- [ ] **G1 (`F01`)**: Sửa `GoalEngineAdapter.commit()` (`src/core/adapters/goal_engine_adapter.py`) và `GoalEngine.verify_goal()` (`src/mekongcli/core/goal_engine/service.py`) để chặn mọi suy diễn `VERIFIED_SUCCESS` giả tạo; vượt qua `F01-T01..T06`.
- [ ] **G2 (`F02`)**: Nâng cấp `WorktreeIsolationManager` (`src/mekongcli/core/goal_engine/worktree_manager.py`) và `GoalEngine` (`service.py`) với vòng đời `SCRATCH` / `ARTIFACT` / `RECOVERY`, SHA-256 manifest tại `.mekong/artifacts/`, bảo toàn `.mekong/recovery_worktrees/`, khóa `RLock` cho git worktree, và `cleanup()` kiểm tra quyền sở hữu + idempotent; vượt qua `F02-T01..T10`.
- [ ] **G3 (`F03`)**: Nâng cấp `BuzzRuntimeAdapter`, `BuzzAdapter`, và `SQLiteGoalStore.admit_ticket()`/`enqueue_outbox()` để ép buộc `external_webhook` fail-closed khi thiếu `outbox_store` hoặc `event_id`, chống race condition `sqlite3.IntegrityError`, và cập nhật `truth_status` cho ticket; vượt qua `F03-T01..T11`.
- [ ] **G4 (`F04`)**: Triển khai `WebhookAuthorityPolicy`, `BuzzSecurityError`, `validate_callback_destination()`, và `_NoRedirectHandler` trong `src/core/buzz_adapter.py`; vượt qua `F04-T01..T11`.
- [ ] **G5 (Sophia Contract v1.0)**: Tạo `src/core/contracts/sophia_integration_v1.py`, `docs/sophia-integration-contract.md`, và `tests/test_sophia_integration_contract.py` với 10 thao tác và 4 chiều trạng thái độc lập (`execution_outcome`, `verification_outcome`, `delivery_outcome`, `business_outcome`).
- [ ] **G6 & G7 (Adversarial Matrix & Non-Regression)**: Tạo `tests/test_supreme_command_01_2_adversarial.py` bao phủ đầy đủ `F01`–`F04` và `A01`–`A22`; chạy toàn bộ suite mới và cũ xanh 100%.
- [ ] **G8 & G9 (Git Hygiene & Draft PR)**: Kiểm tra trần `<= 185 LOC`, kiểm tra `phase_559_opencore_25_step_catalog.py` byte-for-byte, cập nhật docs/Core DNA nếu cần, push nhánh và mở **Draft PR** (`gh pr create --draft`).

### Success Metrics
- `pytest -q tests/test_supreme_command_01_2_adversarial.py tests/test_sophia_integration_contract.py` → **100% PASS** (bao phủ đủ `F01-T01..T06`, `F02-T01..T10`, `F03-T01..T11`, `F04-T01..T11`, và `A01`–`A22`).
- `pytest -q tests/test_autonomous_runtime_trust_matrix.py tests/test_autonomous_runtime_e2e_callers.py tests/test_goal_engine_adapter.py tests/ports/test_goal_engine_conformance.py tests/test_buzz_adapter.py tests/test_buzz_transport.py tests/mekongcli/test_goal_engine.py tests/mekongcli/test_goal_cli.py tests/test_core_lifecycle_contract.py tests/test_core_boundary.py tests/test_opc_platform_contract.py tests/test_opc_approval_security.py` → **100% PASS, 0 regressions**.
- `git diff src/core/opencore/phase_559_opencore_25_step_catalog.py` → **rỗng (0 byte thay đổi)**.
- Mọi file trong `src/core/opencore/*.py`, `src/core/raas_license_verifier.py`, và `src/opc/*.py` → **`<= 185 LOC`**.
- Draft PR được tạo trên `minhlongs/mekong-cli` từ nhánh `fix/supreme-command-01-2-runtime-hardening` với trạng thái `isDraft: true`.

### Handoff Brief

```text
Objective: Execute Supreme Command #01.2 (Mekong CLI Adversarial Hardening & Sophia Handoff) across Gates G0–G9 on branch fix/supreme-command-01-2-runtime-hardening and deliver a verified Draft PR.
Done means: (1) F01 closed in src/core/adapters/goal_engine_adapter.py and src/mekongcli/core/goal_engine/service.py so missing/unverified/simulated truth_status never fabricates VERIFIED_SUCCESS (F01-T01..T06 green); (2) F02 closed in src/mekongcli/core/goal_engine/worktree_manager.py and service.py with SCRATCH/ARTIFACT/RECOVERY worktree lifecycle, SHA-256 artifact handoff to .mekong/artifacts/, recovery worktree preservation in .mekong/recovery_worktrees/, and ownership-aware idempotent cleanup (F02-T01..T10 green); (3) F03 closed in src/core/buzz_runtime_adapter.py, src/core/buzz_adapter.py, and src/mekongcli/core/goal_engine/store.py with fail-closed external_webhook admission and atomic SQLite deduplication (F03-T01..T11 green); (4) F04 closed in src/core/buzz_adapter.py with server-side WebhookAuthorityPolicy and callback SSRF/DNS/redirect blocking via _NoRedirectHandler (F04-T01..T11 green); (5) Sophia Integration Contract v1.0 implemented in src/core/contracts/sophia_integration_v1.py, documented in docs/sophia-integration-contract.md, and verified in tests/test_sophia_integration_contract.py; (6) All 22 adversarial scenarios A01–A22 in tests/test_supreme_command_01_2_adversarial.py and all existing regression/boundary suites pass 100%; (7) Draft PR opened on minhlongs/mekong-cli without merging.
Out of scope: Rewriting MekongCoreRuntimeImpl or SQLiteGoalStore from scratch, modifying Sophia AI Factory repository, deploying to production, or merging the PR.
Constraints: Preserve src/core/opencore/phase_559_opencore_25_step_catalog.py byte-for-byte; keep all src/core/opencore/*.py, src/core/raas_license_verifier.py, and src/opc/*.py files <= 185 LOC; never run git reset --hard, git clean -fd, or force push; deliver report in Vietnamese.
Stop and ask only if: An unexpected test failure or architectural conflict cannot be resolved within the confirmed scope, or an action requires modifying protected Open-Core catalog files or merging/deploying to production.
```
