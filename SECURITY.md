# Chính Sách Bảo Mật / Security Policy (v6.0 Open-Core & Cloud RaaS)

## Các Phiên Bản Được Hỗ Trợ / Supported Versions

Chúng tôi cam kết hỗ trợ bảo mật cho dòng phát hành v6.0.x của Mekong CLI (kiến trúc 25-Step Open-Core & Cloud RaaS Control Plane).
We provide active security updates for the v6.0.x release line of Mekong CLI.

| Phiên Bản / Version | Được Hỗ Trợ / Supported | Ghi Chú / Notes |
| ------------------- | ----------------------- | --------------- |
| **6.0.x**           | ✅                      | Current 25-Step Open-Core + Dual-Rail RaaS |
| 2.1.x               | ❌                      | Legacy runtime (End of Life) |
| < 2.1               | ❌                      | Unsupported |

---

## Báo Cáo Lỗ Hổng / Reporting a Vulnerability

Chúng tôi coi trọng sự an toàn của người dùng và hệ thống doanh nghiệp. Nếu bạn phát hiện một lỗ hổng bảo mật, vui lòng làm theo hướng dẫn sau:

**KHÔNG** báo cáo lỗ hổng công khai qua GitHub Issues hoặc Pull Requests.
**DO NOT** report security vulnerabilities through public GitHub issues.

Vui lòng gửi báo cáo qua GitHub Private Vulnerability Reporting tại tab **Security → Report a vulnerability** của repository `minhlongs/mekong-cli`, hoặc gửi email chi tiết tới: **security@mekongmind.com**

### Quy trình xử lý / Response SLA:
1. **Xác nhận (Acknowledgment):** Trong vòng 48 giờ kể từ khi nhận được báo cáo.
2. **Đánh giá (Triage & Impact):** Phân loại CVSS và phạm vi ảnh hưởng trên tầng MIT Open-Core hoặc Cloud RaaS trong 72 giờ.
3. **Bản vá (Remediation):** Phát hành bản vá bảo mật và cập nhật CycloneDX 1.5 SBOM trong thời gian sớm nhất.
4. **Công bố (Disclosure):** Ghi nhận đóng góp của bạn trong Security Advisories sau khi bản vá được phát hành.

---

## Kiến Trúc Bảo Mật 25 Bước / 25-Step Open-Core Security Posture

Mekong CLI v6.0 thực thi các lớp bảo vệ tất định theo chuẩn `TWENTY_FIVE_OPENCORE_STEPS` (`src/core/opencore/phase_559_opencore_25_step_catalog.py`):

1. **Step 01 (`git-history-secret-purge`) & Step 03 (`gitignore-quarantine-lock`):** Toàn bộ lịch sử git và cây thư mục được kiểm toán tự động bởi `tests/test_opencore_git_boundary_guard.py` nhằm chặn tuyệt đối các tiền tố khóa thật (`sk-or-v1-`, `sk-ant-`, `AIzaSy`), tệp `.env*` và dữ liệu riêng tư của tenant.
2. **Step 05 (`mit-license-and-sbom`):** Mọi bản build CI (`gates.yml`) đều sinh và xác minh CycloneDX 1.5 Software Bill of Materials (`sbom.json`) kết hợp quét lỗ hổng bằng Semgrep, Bandit và Trivy.
3. **Step 09 (`local-sandbox-runtime`):** Lệnh thực thi của AI agent đi qua `LocalExecutionRuntime` và `Governance.classify_risk` với bộ lọc lệnh fail-closed sanitizer.
4. **Step 11 (`jwt-license-gate`):** Khóa bản quyền `RAAS_LICENSE_KEY` (`MEKONG-RAAS-v1` / `SOPHIA-RAAS-v1`) được ký và xác minh bằng HMAC-SHA256 thời gian hằng số (`hmac.compare_digest`) trong `src/core/raas_license_verifier.py`; từ chối chạy nếu thiếu `RAAS_LICENSE_SECRET` trên môi trường production.
5. **Step 15 (`encrypted-key-vault`):** Khóa API của tenant trên Cloud RaaS được mã hóa bằng KMS; ở chế độ local BYOK chỉ sử dụng mẫu `.env.example` không chứa bí mật thật.
6. **Step 17 (`compliance-audit-ledger`):** Mọi giao dịch tính phí MCU và hành động nhạy cảm được ghi vào sổ cái kiểm toán bất biến băm chuỗi SHA-256 phục vụ tuân thủ TT78 / SOC2.
7. **Step 20 (`payment-webhook-activation`):** Thanh toán Dual-Rail (`vietqr` Napas 247 + `nowpayments` USDT) áp dụng khóa chống phát lại (replay-safe idempotency key `act_<sha256>`) trong SQLite WAL `CreditStore`; cổng cũ `/webhook/polar` đã bị đóng vĩnh viễn (`HTTP 410 Gone`).

---
*"Cẩn tắc vô ưu — Defense in Depth across Local CLI & Cloud Control Plane"*
