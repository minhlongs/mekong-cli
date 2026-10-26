# Mô Tả Pull Request / Pull Request Description

## Loại Thay Đổi / Type of Change
- [ ] ✨ Tính năng mới (New Feature)
- [ ] 🐛 Sửa lỗi (Bug Fix)
- [ ] 📚 Tài liệu (Documentation — `README.md` / `README.vi.md` / `docs/`)
- [ ] ♻️ Tái cấu trúc (Refactor)
- [ ] ⚡ Hiệu năng (Performance)
- [ ] 🛡️ Bảo mật & Ranh giới Open-Core (Security / Open-Core Boundary)

## Mô Tả Chi Tiết / Summary
<!-- Mô tả rõ ràng những thay đổi bạn đã thực hiện / Clearly describe your changes -->

## Issue Liên Quan / Related Issue
<!-- Ví dụ: Closes #101 -->

## 🛡️ Binh Pháp Quality Gates (BẮT BUỘC / MANDATORY)
Vui lòng kiểm tra các mục sau trước khi yêu cầu review:

- [ ] **Tech Debt**: Không còn `console.log`, `TODO`, `FIXME` trong code production.
- [ ] **Type Safety**: Không sử dụng `:any` (TypeScript) hoặc bỏ qua kiểu dữ liệu không rõ ràng.
- [ ] **Security**: Không commit secrets, API keys, `.env*`, hoặc dữ liệu riêng tư của tenant.
- [ ] **Tests**: Đã chạy và pass tất cả unit tests và boundary gates.
- [ ] **Docs**: Đã đồng bộ song ngữ (`README.md` + `README.vi.md`) nếu thay đổi kiến trúc hoặc bảng giá.

## 🔒 Open-Core 25-Step & RaaS Boundary Gate (BẮT BUỘC / MANDATORY)

- [ ] **Catalog Invariant**: `git diff HEAD -- src/core/opencore/phase_559_opencore_25_step_catalog.py` hoàn toàn rỗng (`0` byte thay đổi).
- [ ] **Readiness Verdict**: `OpenCoreSaasReadinessEngine.audit_repository(".")` trả về `PUBLIC_GITHUB_SAAS_READY` (`100.0%`).
- [ ] **LOC Ceiling**: Mọi module trong `src/core/opencore/`, `src/core/raas_license_verifier.py` và `tests/test_github_content_25_step_sync.py` đều `<= 185 LOC` (`< 200 LOC` trên toàn repo mới).
- [ ] **Dual-Rail & Zero Polar**: Chỉ sử dụng `vietqr` (Napas 247) và `nowpayments` (USDT); không gọi `api.polar.sh` (`POST /webhook/polar` trả về `HTTP 410 Gone`).
- [ ] **Boundary Suite**: Đã chạy xanh `pytest tests/test_opencore_saas_25_step_suite.py tests/test_core_boundary.py tests/test_dual_rail_checkout.py tests/test_raas_license_verifier.py tests/test_github_content_25_step_sync.py`.

## Core DNA Contribution Gate

- [ ] Nếu thêm command/feature mới, đã cập nhật `dna/core-dna.json` và/hoặc `dna/command-surface.json`.
- [ ] Nếu thay đổi doctrine/agent operating model, đã cập nhật `dna/binh-phap-operating-system.json`.
- [ ] Feature không tự ý mở local-only bypass; phải qua PR owner/community review.

## Ảnh Chụp Màn Hình / Screenshots (Nếu có)
<!-- Thêm ảnh minh họa cho thay đổi UI/UX -->

---
*"Binh quý thắng, bất quý cửu"*
