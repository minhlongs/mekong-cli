# Sophia AI Factory ↔ Mekong CLI — Execution Integration Contract v1.0
# Hợp Đồng Tích Hợp Thực Thi Sophia AI Factory ↔ Mekong CLI v1.0

- **Contract Version / Phiên bản hợp đồng:** `mekong.sophia.execution_contract.v1`
- **Canonical Module / Module chuẩn:** `src/core/contracts/sophia_integration_v1.py`
- **Status / Trạng thái:** Production-Ready (Supreme Command #01.2)

---

## 1. Purpose & Authority Boundary / Mục Đích & Ranh Giới Thẩm Quyền

### English
This contract defines the strict operational boundary between **Sophia AI Factory** (executive orchestrator, approval authority, business KPI evaluator) and **Mekong CLI** (durable ticket runtime, isolated worktree executor, deterministic verifier, SHA-256 artifact producer, and transactional outbox reporter):
1. **Sophia AI Factory** submits tasks, approves or rejects `WAITING_APPROVAL` checkpoints, consumes verified artifacts, and evaluates business KPIs.
2. **Mekong CLI** owns server-side ticket admission (`WebhookAuthorityPolicy`), HMAC-SHA256 `ImmutableMandate` pinning, isolated worktree execution (`SCRATCH / ARTIFACT / RECOVERY`), deterministic verification (`VERIFIED_SUCCESS`), and SSRF-safe transactional outbox delivery.
3. **Zero Trust Invariant:** Inbound webhook payloads cannot forge `mandate_hash`, override `policy_version` or `mandate_version`, escalate `permitted_capabilities`, escape `resource_boundaries`, downgrade `risk_classification`, or exceed server `cost_budget`/`retry_budget` ceilings.

### Tiếng Việt
Hợp đồng này quy định ranh giới vận hành rõ ràng giữa **Sophia AI Factory** (bộ điều phối cấp cao, thẩm quyền phê duyệt, đánh giá KPI kinh doanh) và **Mekong CLI** (runtime lưu trữ ticket bền vững, thực thi trong worktree cô lập, xác minh tất định, xuất bản artifact có kiểm chứng SHA-256 và báo cáo qua outbox giao dịch):
1. **Sophia AI Factory** gửi yêu cầu công việc, phê duyệt hoặc từ chối các điểm dừng `WAITING_APPROVAL`, nhận artifact đã kiểm chứng và đánh giá KPI kinh doanh.
2. **Mekong CLI** nắm toàn quyền kiểm soát chính sách nhận việc phía server (`WebhookAuthorityPolicy`), khóa `ImmutableMandate` bằng HMAC-SHA256, quản lý vòng đời worktree 3 trạng thái (`SCRATCH / ARTIFACT / RECOVERY`), xác minh kết quả thực thi (`VERIFIED_SUCCESS`), và gửi callback an toàn chống SSRF.
3. **Bất biến Zero Trust:** Payload từ bên ngoài không được tự gán `mandate_hash`, không được ghi đè `policy_version`/`mandate_version`, không được tự nâng quyền `permitted_capabilities`, không được vượt ranh giới thư mục `resource_boundaries`, không được hạ cấp `risk_classification`, và không được vượt trần `cost_budget`/`retry_budget` của server.

---

## 2. Ten Canonical Operations / 10 Thao Tác Chuẩn (`SophiaExecutionContractV1`)

| # | Operation | Input | Output / Guarantee |
|---|-----------|-------|--------------------|
| 1 | `submit_task` | `SophiaTaskSubmissionRequest` / `dict` | Deduplicates on `(source_id, event_id)`, validates SSRF & authority policy, persists ticket + `ImmutableMandate`, optionally runs in isolated worktree. |
| 2 | `get_ticket` | `ticket_id: str` | Returns `SophiaTicketAssignment` and verifies HMAC-SHA256 `mandate_hash` on read (`MandateIntegrityError` if tampered). |
| 3 | `get_status` | `ticket_id: str` | Returns `SophiaOutcomeEnvelope` with 4 independent outcome axes + `verified_success_claim_permitted`. |
| 4 | `get_verification_evidence` | `ticket_id: str` | Returns latest `VerificationRun`, task-level `truth_status` & exit codes, and `AcceptanceCriterion` evidence. |
| 5 | `get_artifacts` | `ticket_id: str` | Returns harvested artifact manifests and SHA-256 verified file/patch records from `.mekong/artifacts/<ticket_id>/`. |
| 6 | `request_cancel` | `ticket_id: str, reason: str` | Cancels goal & tasks and transitions ticket `truth_status` to `CANCELLED`. |
| 7 | `report_approval_required` | `ticket_id: str, task_id: str \| None, reason: str` | Transitions task, goal, and ticket to `WAITING_APPROVAL` fail-closed checkpoint. |
| 8 | `resume_reconcile` | `ticket_id: str, now: float \| None` | Reconciles expired worker leases: re-queues idempotent tasks and blocks non-idempotent uncertain tasks in `WAITING_APPROVAL`. |
| 9 | `list_durable_reports` | `ticket_id: str \| None, delivery_status: str \| None` | Lists transactional outbox rows (`PENDING`, `SENT`, `FAILED_RETRYABLE`, `DEAD_LETTER`). |
| 10 | `get_cost_usage` | `ticket_id: str` | Returns `measured_tokens`, `estimated_tokens`, `actual_cost`, `estimated_cost`, and `cost_status` (`MEASURED`, `ESTIMATED`, `UNKNOWN`, `BUDGET_EXCEEDED`). Never fabricates `0.0` for unmeasured usage. |

---

## 3. Four Independent Outcome Axes / 4 Trục Kết Quả Độc Lập

Every `SophiaOutcomeEnvelope` separates four orthogonal dimensions so that a simulated run, an unverified command, a failed webhook callback, or a pending business KPI can never be conflated:

1. **`execution_outcome`**: `"PLANNED" | "RUNNING" | "SIMULATED" | "EXECUTED" | "EXECUTION_FAILED" | "CANCELLED" | "UNAVAILABLE"`
2. **`verification_outcome`**: `"UNVERIFIED" | "VERIFIED_SUCCESS" | "VERIFICATION_FAILED" | "WAITING_APPROVAL" | "NOT_RUN"`
3. **`delivery_outcome`**: `"NOT_REQUESTED" | "PENDING" | "SENT" | "FAILED_RETRYABLE" | "DEAD_LETTER"`
4. **`business_outcome`**: `"NOT_EVALUATED" | "KPI_PENDING" | "KPI_ATTRIBUTED" | "REQUIRES_EXTERNAL_ORACLE"`

### `verified_success_claim_permitted` Rule / Quy Tắc Công Bố Thành Công Đã Xác Minh
`verified_success_claim_permitted` is `True` **if and only if**:
- `truth_status == "VERIFIED_SUCCESS"`
- `execution_outcome == "EXECUTED"`
- `verification_outcome == "VERIFIED_SUCCESS"`
- `simulated is False`

Any attempt to construct or validate a fixture with `verified_success_claim_permitted=True` when any of those conditions is false raises `SophiaContractValidationError`.
