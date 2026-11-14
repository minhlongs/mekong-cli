# Báo cáo Kiểm toán Pháp y Chỉ đọc — Mekong CLI Baseline (`V-01..V-08` & `G0..G13`)

- **Kho mã nguồn:** `minhlongs/mekong-cli`
- **Nhánh làm việc cô lập:** `feat/strategy-e-forensic-pilot-a-bench15`
- **Mã băm `HEAD` nguyên bản khi kiểm toán:** `30cf3895d6ee409b592f66627c9aaad1b2790cbf`
- **Trạng thái cây thư mục tại thời điểm chạy:** Sạch tuyệt đối (`git status --short` rỗng)
- **Phơi nhiễm khóa bí mật:** `0` giá trị khóa được in/ghi; chỉ ghi nhận trạng thái tồn tại dạng boolean (`is_set`) và độ dài.
- **Chi phí API bên ngoài:** `0 USD / 0 VNĐ` (chạy 100% cục bộ / offline).

---

## 1. Kết quả Thực thi 8 Lệnh Kiểm chứng Pháp y Chỉ đọc (`V-01..V-08`)

| Mã bước | Mục tiêu kiểm chứng | Phán quyết Baseline | Bằng chứng thực nghiệm trên `30cf3895d6ee409b592f66627c9aaad1b2790cbf` |
| :--- | :--- | :---: | :--- |
| **V-01** | Chốt `HEAD` SHA, lịch sử commit & đếm nhóm lệnh CLI thực tế | **PASS** | `HEAD` = `30cf3895d6ee409b592f66627c9aaad1b2790cbf` (commit gần nhất `2026-11-09 19:17:05 +0700`, `#152`). Phát hiện lệch tài liệu: `len(build_app().registered_groups) == 189` nhóm lệnh thực tế (so với con số `39` ghi trong `CLAUDE.md`/`README.md`). |
| **V-02** | Ranh giới bí mật Git (`test_opencore_git_boundary_guard.py`) | **PASS** | `8 passed` trong `1.46s`; `0` tệp `.env` hoặc tiền tố khóa thật (`sk-or-v1-`, `sk-ant-`, `AIzaSy`) bị theo dõi trong Git. |
| **V-03** | Kiểm toán AST `phase_559_opencore_25_step_catalog.py` | **PASS** | Tệp tồn tại (`51` dòng vật lý, `2` class `OpenCorePhase`, `OpenCoreStepSpec`, `0` hàm thực thi): xác nhận đây là danh mục khai báo tĩnh `TWENTY_FIVE_OPENCORE_STEPS` (bất biến byte-for-byte), không phải engine thực thi. |
| **V-04** | Quét AST tỷ lệ hàm thật so với `pass`/`...`/`NotImplementedError`/hằng tĩnh | **PASS** | Đã quét `1,242` tệp Python trên `src/` và `integrations/`: `src/opc` (`13` tệp, `1,654` LOC, `63/64` hàm thực thi = `98.44%`), `src/raas` (`76` tệp, `19,166` LOC, `649/654` hàm = `99.24%`), `src/cli` (`229` tệp, `71,679` LOC, `1,687/1,690` hàm = `99.82%`), `src/core` (`471` tệp, `218,582` LOC, `6,492/6,627` hàm = `97.96%`), `integrations` (`2` tệp, `126` LOC, `8/8` hàm = `100.0%`). |
| **V-05** | Cổng cấp phép HMAC-SHA256 `raas_license_verifier.py` đóng an toàn | **PASS** | `env -u RAAS_LICENSE_SECRET pytest tests/test_raas_license_verifier.py` đạt `6 passed`. Khi bỏ cả `RAAS_LICENSE_SECRET` và `PYTEST_CURRENT_TEST` ở chế độ production, `verify_license_key(...)` trả về `(False, "RAAS_LICENSE_SECRET must be configured in production")`. |
| **V-06** | Khóa bất biến `CreditStore`, `/webhook/polar` HTTP 410 & chặn crypto cho VN | **PASS** | `13 passed` (`test_dual_rail_checkout.py` + `test_opencore_saas_25_step_suite.py`): `/webhook/polar` trả `HTTP 410 Gone`, `CreditStore` SQLite WAL chống cộng trùng qua `act_<sha256>`, và `/v1/checkout` đã chặn `nowpayments` đối với `VN` hoặc tổ chức không khai báo khu vực pháp lý (`HTTP 403`). |
| **V-07** | Kiểm chứng TOCTOU & khóa HMAC phê duyệt trong `src/opc/approval.py` | **HOLD (CẦN KHẮC PHỤC)** | `PayloadBoundApprovalEngine` đã băm SHA-256 đầy đủ `(principal, capability, connector, recipient, content, parameters, attachments, budget_amount, budget_currency, expires_at)` và khóa nguyên tử SQLite, **nhưng** khi gỡ `MEKONG_APPROVAL_SECRET` ngoài `pytest` (`env -u MEKONG_APPROVAL_SECRET -u PYTEST_CURRENT_TEST`), hệ thống vẫn âm thầm rơi về khóa cứng `_LOCAL_FALLBACK_HMAC_KEY` (`SILENT_FALLBACK_ALLOWED`). Được khắc phục triệt để ở Hạng mục 2. |
| **V-08** | Kiểm toán SBOM CycloneDX 1.5, giấy phép MIT & cổng bảo mật CI (`gates.yml`) | **PASS (CÓ LƯU Ý CI)** | `scripts/generate-sbom.py` sinh hợp lệ CycloneDX `1.5` với `1,240` thành phần (`pyproject.toml` dùng giấy phép `MIT`; tệp `sbom.json` sinh động trong CI để tránh xung đột hash). Lưu ý kiểm toán: job `g2-security` trong `.github/workflows/gates.yml` đang chạy `bandit --exit-zero`, `semgrep` với `continue-on-error: true`, và `trivy` với `exit-code: 0` (chưa chặn cứng PR khi phát hiện cảnh báo tĩnh). |

---

## 2. Bảng Trạng thái Cơ sở 14 Cổng Chấp nhận Cứng (`G0..G13`) tại Baseline `30cf3895d6`

| Cổng | Nội dung Cổng Chấp nhận | Trạng thái Baseline (`30cf3895d6`) | Hướng xử lý trong Phiên Thực thi Chiến lược E (`#153`) |
| :--- | :--- | :---: | :--- |
| **G0** | Baseline mã nguồn & kiến trúc xác thực | **PASS** | Đã khóa SHA `30cf3895d6ee409b592f66627c9aaad1b2790cbf` và lưu `forensic-audit-baseline-v01-v08.json`. |
| **G1** | Khảo sát nỗi đau khách hàng thực địa (>=15 SME/Agency) | **OUT OF SCOPE** | Công việc thương mại thực địa của Founder (ngoài phạm vi thay đổi mã nguồn). |
| **G2** | Khả năng chi trả & bảng giá nội địa VNĐ | **FAIL (Ở GIÁ USD CŨ)** | Bổ sung song song `VN_SME_WORKFLOW_TIERS` (`790k / 990k / 1.99M / 4.9M VNĐ`, chỉ `vietqr`) trong khi giữ tương thích ngược `COMMERCIAL_TIERS`. |
| **G3** | Tương thích giấy phép MIT & chặn crypto nội địa VN | **PASS** | Đã chặn `nowpayments` cho `VN` (`HTTP 403`) và xác minh SBOM CycloneDX 1.5 (`1,240` components, MIT). |
| **G4** | Toàn vẹn hợp đồng giao diện & ranh giới AST | **PASS** | Duy trì ranh giới AST nghiêm ngặt trong `src/opc/` (`<= 185 LOC` mỗi tệp). |
| **G5** | Runtime đóng an toàn (Fail-Closed) | **HOLD → FIXING** | Đóng lỗ hổng fallback khóa `MEKONG_APPROVAL_SECRET` ngoài `pytest` và thêm bộ kiểm tra lệch số học / điểm tự tin `< 0.85` (`HALT_FOR_HUMAN`). |
| **G6** | An toàn ủy quyền & bí mật thông tin xác thực | **HOLD → FIXING** | Khóa cứng `ApprovalSecurityError` khi `MEKONG_APPROVAL_SECRET` thiếu hoặc `< 16` ký tự ngoài `pytest`. |
| **G7** | Cô lập đa khách hàng (Multi-tenant SQLite) | **NOT VERIFIED → FIXING** | Bổ sung trình xác thực đường dẫn `{tenant_id}.db` chống path-traversal và kiểm chứng bằng Lớp 10 của `MEKONG-BENCH`. |
| **G8** | Chống thực thi kép & khôi phục sau sự cố | **HOLD → FIXING** | Mở rộng kiểm chứng khôi phục tiến trình, đối soát VietQR có chữ ký và bù trừ lỗi từng phần qua Lớp 5, 6, 7, 13 của `MEKONG-BENCH`. |
| **G9** | Độ phủ xác minh tất định độc lập với LLM | **HOLD → FIXING** | Bổ sung trình kiểm tra toán học chứng từ/báo giá hai giai đoạn (`MATH_MISMATCH_REQUIRES_HUMAN`) và kiểm chứng qua Lớp 1, 8, 15 của `MEKONG-BENCH`. |
| **G10** | Tuân thủ Zalo OpenAPI 2026, Nghị định 13 & Nghị định 52 | **FAIL → FIXING** | Xây dựng `ZaloOAConnector` chuẩn sản xuất (kiểm tra hạng gói Growth/Enterprise, MAC webhook, cửa sổ 48h, lỗi ngầm HTTP 200 `error != 0`), nối cổng Consent + xóa DLCN `<72h` Nghị định 13, ẩn danh PII nội địa và chỉ xuất nháp `DRAFT_PENDING_TVAN`. |
| **G11** | Đối chuẩn hiệu năng, chi phí & khóa hạn ngạch nguyên tử | **HOLD → FIXING** | Bổ sung giữ chỗ hạn ngạch quy trình nguyên tử (`BEGIN IMMEDIATE`) trong SQLite WAL và kiểm chứng qua Lớp 11, 12, 14 của `MEKONG-BENCH`. |
| **G12** | Vận hành Pilot trả phí 60 ngày & biên lợi nhuận đóng góp | **OUT OF SCOPE** | Mốc thương mại Ngày 61–90 sau khi phát hành bản cứng hóa Pilot A. |
| **G13** | Phê duyệt độc lập của Chủ sở hữu | **PASS** | Chủ sở hữu đã xác nhận Cổng 1 (`Confirm`) và Cổng 2 (`Sẵn sàng — Chạy tự hành Cổng 3`). |
