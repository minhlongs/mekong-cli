# BÁO CÁO TƯ VẤN KỸ THUẬT: TÁI CẤU TRÚC FULL-STACK THƯƠNG MẠI HÓA MEKONG CLI THEO BLUEPRINT OPEN-CORE 25 BƯỚC

**Chế độ thực thi:** `/ak-advise --ultra --deep` (Ultra Verifier Mode: Best-of-5 Evaluated by Kongming)  
**Mã báo cáo:** `advise-261026-0926-fullstack-25-step-commercialization`  
**Ngày lập:** 2026-10-26 | **Địa bàn:** TP. Hồ Chí Minh (`Asia/Saigon`)  
**Đối tượng:** Hệ thống Mekong CLI v6.0 (`/Users/macbook/mekong-cli`)  
**Phương án chiến thắng:** **Candidate E (Ứng viên #5)** — Điểm số: **20/20** (`ultra: picked=E/5 margin=high unanimous=yes rejected_all=no`)

---

## 1. Verdict (Nhận định thẳng thắn)

Nền tảng kỹ thuật của `/Users/macbook/mekong-cli` đã có sẵn các bộ máy thanh toán nội địa và quốc tế hoàn chỉnh (`VietQrEngine` chuẩn EMVCo CRC16 trong `/Users/macbook/mekong-cli/src/core/vietqr_engine.py` và `NowPaymentsProvider` chuẩn HMAC-SHA512 trong `/Users/macbook/mekong-cli/src/raas/nowpayments_provider.py`), nhưng dòng tiền thương mại đang bị chặn đứng bởi 3 đứt gãy kiến trúc nghiêm trọng:

1. **Thiếu hoàn toàn bộ ký và xác thực mật mã `RAAS_LICENSE_KEY`** theo chuẩn 4 gói thương mại `BASIC | PREMIUM | ENTERPRISE | MASTER` (trong khi `/Users/macbook/mekong-cli/src/lib/raas-gate.ts` vẫn dùng hàm băm 4 ký tự không mật mã trên hệ gói lỗi thời `free | pro | enterprise`).
2. **Cổng thanh toán bị cấm `api.polar.sh` vẫn đang chạy trực tiếp** trong `/Users/macbook/mekong-cli/src/raas/checkout_router.py`, `/Users/macbook/mekong-cli/src/raas/revenue_router.py`, `/Users/macbook/mekong-cli/src/api/billing_routes.py` và `/Users/macbook/mekong-cli/src/services/polar_client.py`.
3. **Bộ kiểm toán `/Users/macbook/mekong-cli/src/core/opencore/phase_560_opencore_saas_readiness_engine.py` đang báo "xanh giả" (`25/25`)** vì chỉ đếm chuỗi `- [x]` khớp với 25 slug chính mà lọt qua hai cổng chặn **Step 11b** (`signed-raas-license-key`) và **Step 11c** (`resolve-polar-checkout-path`) đang ở trạng thái `[ ]` trong `/Users/macbook/mekong-cli/plans/company-blueprint/tasks.md`.

Đợt tái cấu trúc sâu (`--deep`) cần triển khai đồng bộ theo 4 trụ cột: đóng mới bộ ký/xác thực `RAAS_LICENSE_KEY` chuẩn HMAC-SHA256 đồng nhất giữa Python và TypeScript, cắt bỏ triệt để `api.polar.sh` để chuyển các route hiện hữu sang Dual-Rail (VietQR + NOWPayments USDT) có giữ nguyên contract URL, nâng cấp `monetization_gate_probes.py` thành bộ kiểm toán hành vi thực thi thật, và nối thẳng Next.js Dashboard vào FastAPI Gateway với cơ chế kết hợp Auto-Provisioning (polling 3 giây) cùng Manual License Input.

---

## 2. What you should do (Các hành động cụ thể theo thứ tự ưu tiên)

Thực hiện tuần tự theo 4 pha từ lõi mật mã ra tới giao diện người dùng:

### Pha 1: Xây dựng chuẩn mật mã `RAAS_LICENSE_KEY` đồng nhất Python & TypeScript (Step 11b)
1. **Tạo mới `/Users/macbook/mekong-cli/src/core/raas_license_verifier.py` (`<= 185 LOC`, stdlib-pure):**
   - Chỉ sử dụng thư viện chuẩn (`hmac`, `hashlib`, `base64`, `json`, `os`, `time`, `dataclasses`, `enum`) để tuân thủ tuyệt đối `/Users/macbook/mekong-cli/tests/test_core_boundary.py`.
   - Định nghĩa `CanonicalLicenseTier(str, Enum)` gồm `BASIC = "BASIC"`, `PREMIUM = "PREMIUM"`, `ENTERPRISE = "ENTERPRISE"`, `MASTER = "MASTER"` kèm bảng ánh xạ tương thích ngược từ `TierKey.aliases()` trong `/Users/macbook/mekong-cli/src/seed/config/tiers_models.py` (`starter -> BASIC`, `growth/pro -> PREMIUM`, `enterprise -> ENTERPRISE`, `master -> MASTER`).
   - Hỗ trợ cả hai tiền tố hợp lệ: `MEKONG-RAAS-v1` và `SOPHIA-RAAS-v1`. Cấu trúc khóa: `<PREFIX>.<base64url_payload_no_pad>.<hmac_sha256_hex>`.
   - Chuẩn hóa payload JSON (canonical JSON `separators=(",", ":")`, `sort_keys=True`) chứa: `{"tenant_id": str, "tier": "BASIC"|"PREMIUM"|"ENTERPRISE"|"MASTER", "issued_at": int, "expires_at": int, "features": list[str]}`.
   - Hàm `sign_license_key(payload, secret=None, prefix="MEKONG-RAAS-v1") -> str` và `verify_license_key(token, secret=None, now=None) -> LicenseVerificationResult`: ký HMAC-SHA256 trên chuỗi `f"{prefix}.{payload_b64}"` bằng `RAAS_LICENSE_SECRET` (fallback sang `JWT_SECRET`; chỉ cho phép secret test mặc định khi có `PYTEST_CURRENT_TEST` hoặc `CI` trong `os.environ`, tuyệt đối fail-closed khi chạy production mà thiếu secret). Sử dụng `hmac.compare_digest` để chống timing attack.
2. **Tích hợp vào `/Users/macbook/mekong-cli/src/core/license_manager.py` và `/Users/macbook/mekong-cli/engine/license/license_store.py`:**
   - Khi `RAAS_LICENSE_KEY` có tiền tố `MEKONG-RAAS-v1.` hoặc `SOPHIA-RAAS-v1.`, gọi `verify_license_key()` để xác thực chữ ký và hạn dùng trực tiếp ngay cả khi chạy local/offline trước khi fallback sang lưu trữ file.
3. **Nâng cấp `/Users/macbook/mekong-cli/src/lib/raas-gate.ts` (Zero `:any`, Zero `console.log`):**
   - Chuyển `LicenseTier` sang `'FREE' | 'BASIC' | 'PREMIUM' | 'ENTERPRISE' | 'MASTER'` (kèm alias lowercase `'free' | 'pro' | 'enterprise'` qua hàm chuẩn hóa `normalizeTier()` để không làm gãy các caller cũ).
   - Thay thế `generateChecksum` 4 ký tự bằng HMAC-SHA256 thật (sử dụng `crypto.createHmac('sha256', secret)` trong môi trường Node/SSR và Web Crypto API cho trình duyệt) khớp từng byte với `src/core/raas_license_verifier.py`.
   - Cập nhật `validateSync(key?: string)` và `validate(key?: string)` để giải mã `<PREFIX>.<base64url_payload>.<hmac_sha256_hex>`, kiểm tra `expires_at > Date.now() / 1000`, kiểm tra chữ ký HMAC, và trả về `{ valid, tier, features, tenantId, expiresAt }`. Từ chối 100% các chuỗi giả mạo chỉ có prefix (`raas_ent_`, `sk-raas-`) mà không có chữ ký HMAC hợp lệ.

### Pha 2: Loại bỏ hoàn toàn Polar.sh & Chuyển sang Dual-Rail VietQR + NOWPayments (Step 11c)
1. **Cập nhật bảng giá chuẩn 4 gói thương mại:**
   - Đồng bộ bảng giá giữa `.mekong/company.json`, `/Users/macbook/mekong-cli/src/raas/revenue_router.py`, `/Users/macbook/mekong-cli/src/raas/checkout_router.py`, và `/Users/macbook/mekong-cli/src/raas/nowpayments_checkout.py`:
     - `BASIC`: `$199/tháng` (`4,975,000 VND`), `1,500 MCU`
     - `PREMIUM`: `$399/tháng` (`9,975,000 VND`), `4,000 MCU`
     - `ENTERPRISE`: `$799/tháng` (`19,975,000 VND`), `10,000 MCU`
     - `MASTER`: `$4,999 one-time` (`124,975,000 VND`), `100,000 MCU`
   - Vẫn giữ alias map cho `starter -> BASIC`, `growth/pro -> PREMIUM` trong parser request để các test cũ gửi `tier="starter"` không bị lỗi `400`.
2. **Tái cấu trúc `/Users/macbook/mekong-cli/src/raas/checkout_router.py` (`<= 185 LOC`):**
   - Giữ nguyên route `POST /v1/checkout` và `GET /v1/success`.
   - Mở rộng `CheckoutRequest` nhận thêm `rail: str = Field("vietqr", description="vietqr | nowpayments")` và `org_id: str = Field("default")`.
   - Khi `rail == "vietqr"`: gọi `VietQrEngine().generate_qr(amount_vnd=..., memo=f"MEKONG {org_id} {order_id}")` và trả về `checkout_url` (QuickLink URL), `qr_payload` (`emvco_payload`), `order_id`, `tier`, `rail="vietqr"`, `amount_usd`, `amount_vnd`.
   - Khi `rail == "nowpayments"`: tạo phiên thanh toán qua `NowPaymentsProvider` / `nowpayments_checkout`, trả về `checkout_url`, `order_id`, `tier`, `rail="nowpayments"`, `pay_currency="usdttrc20"`, `amount_usd`.
   - Thêm endpoint `GET /v1/checkout/status?order_id=...`: kiểm tra trạng thái đơn hàng trong SQLite (`VietQrEngine` transactions hoặc NOWPayments ledger). Nếu đã thanh toán (`status == "success"` / `"finished"`), tự động ký và trả về `license_key` (`MEKONG-RAAS-v1.<payload>.<sig>`), `tier`, `credits`, `tenant_id` để phục vụ Auto-Provisioning 3 giây trên Dashboard.
   - Thêm hai endpoint quản lý license trên Gateway:
     - `POST /v1/license/activate`: nhận `{"license_key": "..."}`, xác thực chữ ký HMAC qua `verify_license_key()`, kích hoạt trong `LicenseStore` & `LicenseManager`, trả về thông tin gói, hạn mức MCU và `features`.
     - `GET /v1/license/status`: trả về trạng thái kích hoạt hiện tại, `tier`, `tenant_id`, `expires_at`, số dư MCU từ `CreditStore`/`MCUBilling`, và danh sách `features`.
3. **Tái cấu trúc `/Users/macbook/mekong-cli/src/raas/revenue_router.py` (`<= 185 LOC`):**
   - Xóa hoàn toàn `_POLAR_PRICE_DEFAULTS`, `_polar_checkout_base()`, và mọi chuỗi `api.polar.sh` hoặc `polar.sh`.
   - Chuyển `POST /webhook/polar` thành cổng trả về `HTTPException(status_code=410, detail={"error": "polar_rail_decommissioned", "allowed_rails": ["vietqr", "nowpayments"]})` để tuân thủ lệnh cấm Polar mà không làm gãy bảng route.
   - Cập nhật `GET /v1/pricing` trả về 4 gói chuẩn (`BASIC`, `PREMIUM`, `ENTERPRISE`, `MASTER`) kèm đường dẫn checkout nội bộ (`/v1/checkout`) và thông tin hỗ trợ Dual-Rail (`vietqr`, `nowpayments`).
4. **Tái cấu trúc `/Users/macbook/mekong-cli/src/api/billing_routes.py` & `/Users/macbook/mekong-cli/src/services/polar_client.py` (`<= 185 LOC`):**
   - Trong `src/api/billing_routes.py` (hiện tại `358 LOC`): rút gọn các luồng xử lý Polar thừa, chuyển `POST /v1/billing/checkout/org` sang Dual-Rail và đưa toàn bộ file về `<= 185 LOC`.
   - Trong `src/services/polar_client.py`: xóa URL `https://api.polar.sh/v1` và chuyển module này thành deprecation shim cho các test cũ, đảm bảo `grep -rn "api.polar.sh" src/` trả về đúng `0` kết quả.

### Pha 3: Khóa chặt Kiểm toán Hành vi 25 Bước (Step 11b & 11c Behavioral Probes)
1. **Nâng cấp `/Users/macbook/mekong-cli/src/core/opencore/monetization_gate_probes.py` (`<= 185 LOC`):**
   - Bổ sung kiểm tra hành vi thật cho **Step 11b** trong `_probe_license_gate()`:
     - Import `src.core.raas_license_verifier` và chạy thử nghiệm tự kiểm (self-test) trong bộ nhớ: ký 1 khóa `MEKONG-RAAS-v1` và 1 khóa `SOPHIA-RAAS-v1` cho gói `ENTERPRISE`, xác thực phải trả về `valid=True`; sửa đổi 1 ký tự trong payload hoặc chữ ký, xác thực phải trả về `valid=False`.
     - Kiểm tra `/Users/macbook/mekong-cli/src/lib/raas-gate.ts` có chứa đầy đủ 4 gói `'BASIC'`, `'PREMIUM'`, `'ENTERPRISE'`, `'MASTER'` và kiểm tra chữ ký HMAC-SHA256.
   - Bổ sung kiểm tra hành vi thật cho **Step 11c** trong `_probe_billing()`:
     - Quét toàn bộ cây thư mục `src/`: nếu phát hiện bất kỳ chuỗi `"api.polar.sh"` nào trong `src/`, ghi nhận ngay vào `billing_gaps` khiến `mcu_http402_billing_wired = False`.
     - Kiểm tra `/Users/macbook/mekong-cli/src/core/vietqr_engine.py` và `/Users/macbook/mekong-cli/src/raas/nowpayments_provider.py` tồn tại và import thành công.
2. **Nâng cấp `/Users/macbook/mekong-cli/src/core/opencore/phase_560_opencore_saas_readiness_engine.py` (`<= 185 LOC`):**
   - Trong `audit_blueprint()`: ngoài 25 bước trong `TWENTY_FIVE_OPENCORE_STEPS`, bắt buộc kiểm tra thêm 2 cổng phụ chặn thương mại là `signed-raas-license-key` (Step 11b) và `resolve-polar-checkout-path` (Step 11c) trong `plans/company-blueprint/tasks.md` phải được đánh dấu `- [x]`, và trong `.mekong/company.json` cả `open_core.boundary.cloud.verified` lẫn `open_core.boundary.enterprise.verified` phải là `True` (đồng thời `payment_rails.polar_sh.status` là `"decommissioned"` / `"removed"`).
   - Trong `/Users/macbook/mekong-cli/src/core/opencore/phase_559_opencore_25_step_catalog.py`: cập nhật mô tả Step 20 dòng 45 từ `"PayOS / NOWPayments / Polar IPN"` thành `"PayOS / VietQR / NOWPayments IPN"`.
3. **Đồng bộ hồ sơ Blueprint:**
   - Cập nhật `/Users/macbook/mekong-cli/plans/company-blueprint/tasks.md`: đánh dấu `- [x]` cho **Step 11b (10b)** và **Step 11c (10c)** sau khi code và test đã pass.
   - Cập nhật `/Users/macbook/mekong-cli/plans/company-blueprint/plan.md` và `/Users/macbook/mekong-cli/.mekong/company.json`: cập nhật `verified: true` cho `cloud` và `enterprise`, xóa `blocking_dependencies`, giữ nguyên `revenue_events: []` (tuyệt đối không chèn doanh thu giả).

### Pha 4: Nối mạch thật lên Next.js Dashboard (`/Users/macbook/mekong-cli/apps/dashboard/`)
1. **Mở rộng `/Users/macbook/mekong-cli/apps/dashboard/lib/agentops-api.ts` (Zero `:any`, Zero `console.log`):**
   - Đọc URL từ `process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8000'`.
   - Xóa bỏ `: any` tại dòng 144 và 166.
   - Bổ sung các hàm gọi API thật: `createDualRailCheckout`, `getCheckoutStatus`, `activateLicenseKey`, `getLicenseStatus`, `getOpenCoreStatus`, `getRevenueTelemetry`.
2. **Nâng cấp `/Users/macbook/mekong-cli/apps/dashboard/app/checkout/demo/page.tsx`:**
   - Thay thế 3 sản phẩm giả (`Vibe Starter $47`, PayPal mock) bằng 4 gói chuẩn: `BASIC ($199/tháng)`, `PREMIUM ($399/tháng)`, `ENTERPRISE ($799/tháng)`, `MASTER ($4,999 trọn đời)`.
   - Thêm bộ chọn cổng thanh toán Dual-Rail: **VietQR Napas 247** (hiển thị mã QR EMVCo từ `quicklink_url`, số tài khoản, số tiền VND, nội dung chuyển khoản) và **NOWPayments USDT (TRC20)**.
   - Triển khai `useEffect` polling `getCheckoutStatus(orderId)` mỗi `3000ms` khi đang chờ thanh toán: ngay khi nhận `status === 'paid'` kèm `license_key`, tự động lưu vào `localStorage.setItem('RAAS_LICENSE_KEY', res.license_key)` và hiển thị trạng thái kích hoạt thành công (Auto-Provisioning).
3. **Nâng cấp `/Users/macbook/mekong-cli/apps/dashboard/app/dashboard/settings/page.tsx`:**
   - Thêm ô nhập khóa `RAAS_LICENSE_KEY` thủ công (`MEKONG-RAAS-v1...` hoặc `SOPHIA-RAAS-v1...`) kèm nút kích hoạt gọi `activateLicenseKey()` và kiểm tra chữ ký qua `raas-gate.ts` (Manual License Input).
   - Hiển thị thẻ trạng thái bản quyền hiện tại: Gói (`BASIC | PREMIUM | ENTERPRISE | MASTER`), `tenant_id`, thời hạn `expires_at`, hạn mức MCU còn lại, và bảng **25-Step Open-Core Readiness Matrix** lấy trực tiếp từ `GET /api/open-core/status`.
4. **Nâng cấp `/Users/macbook/mekong-cli/apps/dashboard/app/dashboard/revenue/page.tsx`:**
   - Xóa bỏ các con số giả định cứng (`$12,450`). Nối trực tiếp vào API Gateway để hiển thị tổng doanh thu thực tế từ `VietQrEngine` (`total_volume_received_vnd`, `recent_transactions`) và sổ cái `NOWPayments`, hiển thị trạng thái `$0` trung thực khi chưa phát sinh giao dịch.

---

## 3. What you shouldn't do (Các bẫy cụ thể cần tránh)

1. **Không xóa các route `/v1/checkout`, `/v1/success`, `/v1/pricing`, `/v1/billing/checkout/org` hoặc `/webhook/polar` khỏi FastAPI router:** Giữ nguyên URL route nhưng thay đổi nội hàm bên trong: chuyển `/v1/checkout`, `/v1/pricing`, `/v1/billing/checkout/org` sang VietQR + NOWPayments, và cho `/webhook/polar` trả về `HTTP 410 Gone`.
2. **Không import bất kỳ thư viện bên thứ ba nào vào `/Users/macbook/mekong-cli/src/core/raas_license_verifier.py`:** File `/Users/macbook/mekong-cli/tests/test_core_boundary.py` kiểm tra AST tĩnh toàn bộ `src/core/`. Chỉ dùng Python stdlib (`hmac`, `hashlib`, `base64`, `json`, `time`, `os`, `dataclasses`, `enum`).
3. **Không nhồi nhét toàn bộ code mới vào một file vượt quá `185 LOC`:** Chú ý `checkout_router.py` (180 LOC), `revenue_router.py` (233 LOC), và `billing_routes.py` (358 LOC). Bắt buộc phải rút gọn phần xử lý Polar cũ để mọi file đều `<= 185 LOC`.
4. **Không ghi dữ liệu doanh thu mẫu vào `/Users/macbook/mekong-cli/.mekong/company.json`:** Hàm `OpenCoreSaasReadinessEngine.audit_blueprint()` kiểm tra cứng `len(revenue_events) == 0`. Bất kỳ sự kiện doanh thu giả nào cũng sẽ khiến kiểm toán Open-Core thất bại.
5. **Không `git add` bất kỳ file nào trong `apps/` hoặc `billing/` ngoài những file đã được cho phép:** Hàm `verify_filesystem_hygiene()` chạy `git ls-files apps/ billing/` và sẽ chặn nếu phát hiện file riêng tư bị lộ vào git index.
6. **Không để mật khẩu mặc định (fallback secret) hoạt động trên môi trường production:** Chỉ cho phép fallback secret khi `PYTEST_CURRENT_TEST` hoặc `CI` có mặt trong biến môi trường.

---

## 4. What could be better / more efficient (Lối tắt kỹ thuật tối ưu)

1. **[Effort: Thấp | Impact: Rất cao] Tái sử dụng `TierKey.aliases()` trong `src/seed/config/tiers_models.py`:** Thêm helper `to_commercial_tier(raw: str) -> str` quy chuẩn về 4 gói thương mại, vừa thỏa mãn chuẩn gói mới vừa giữ cho các bài test cũ gửi `tier="starter"` chạy xanh 100%.
2. **[Effort: Thấp | Impact: Cao] Dùng `VietQrEngine.generate_qr()` và `VietQrEngine.get_status()` trực tiếp:** `src/core/vietqr_engine.py` đã cài sẵn toàn bộ chuẩn EMVCo CRC16-CCITT, tạo URL ảnh QR `quicklink_url`, lưu SQLite WAL tại `.mekong/vietqr.db`, và có sẵn hàm `get_status()`. Không cần tạo thêm bảng SQLite mới.
3. **[Effort: Trung bình | Impact: Cao] Khóa `RAAS_LICENSE_KEY` dạng Self-Contained Stateless Token:** Cả CLI Python, FastAPI Gateway lẫn Next.js Dashboard (`raas-gate.ts`) đều giải mã và biết ngay `tier` + `features` trong `< 1ms` mà không cần tra cứu DB ở mỗi request.

---

## 5. My take and how to get there (Lộ trình triển khai)

- **Bước 1 — Khởi tạo bộ ký/xác thực `RAAS_LICENSE_KEY`:** Viết `src/core/raas_license_verifier.py` (`~130 LOC`) + `tests/test_raas_license_verifier.py`, cập nhật `src/lib/raas-gate.ts` (`~160 LOC`).
- **Bước 2 — Chuyển đổi các router thanh toán sang Dual-Rail và dọn sạch `api.polar.sh`:** Sửa `checkout_router.py`, `revenue_router.py`, `billing_routes.py`, và `polar_client.py`. Mở 3 endpoint `/v1/checkout/status`, `/v1/license/activate`, `/v1/license/status`.
- **Bước 3 — Siết chặt kiểm toán hành vi 25 bước và cập nhật Blueprint:** Nâng cấp `monetization_gate_probes.py` và `phase_560_opencore_saas_readiness_engine.py`. Đánh dấu `[x]` cho Step 11b & 11c trong `tasks.md`, `plan.md`, `.mekong/company.json`.
- **Bước 4 — Nối mạch thật trên Next.js Dashboard:** Cập nhật `agentops-api.ts` (xóa `:any`), nâng cấp `checkout/demo/page.tsx`, `settings/page.tsx`, và `revenue/page.tsx`.
- **Bước 5 — Chạy toàn bộ cổng kiểm định chất lượng (Quality Gates):** Quét `grep -rn "api.polar.sh" src/`, kiểm tra LOC `<= 185`, chạy `ruff check`, và chạy `pytest` toàn bộ.

---

## 6. Benefits (Lợi ích cốt lõi)

- **Mở khóa thu tiền thật nội địa và quốc tế (Goal 1 & 2):** VietQR Napas 247 cho thị trường Việt Nam và USDT TRC20 cho quốc tế.
- **Bản quyền mật mã thực chất và kiểm toán trung thực (Goal 1 & 3):** Khóa `MEKONG-RAAS-v1` / `SOPHIA-RAAS-v1` dùng HMAC-SHA256 chống giả mạo 100%; `OpenCoreSaasReadinessEngine` kiểm tra hành vi thực thi thật.
- **Trải nghiệm kích hoạt kép không ma sát (Goal 4):** Tự động kích hoạt sau 3 giây trên Web (Auto-Provisioning) kết hợp dán key thủ công (Manual Activation) cho môi trường self-hosted/CLI.

---

## 7. Trade-offs (Đánh đổi & Điều kiện chuyển đổi)

- **HMAC-SHA256 đối xứng vs. Ed25519/RSA bất đối xứng:**
  - *Chi phí:* Cần secret key để xác thực chữ ký. Trình duyệt client-side chỉ parse payload/hạn dùng và gọi `POST /v1/license/activate` về Gateway để xác thực chữ ký chính thức.
  - *Khi nào hết phù hợp:* Khi phân phối binary cho khách hàng Enterprise chạy hoàn toàn offline (air-gapped 100%) mà không có Gateway.
  - *Chi phí chuyển đổi:* Rất thấp (`~40 LOC`). Định dạng đã có prefix phiên bản, sau này chỉ cần thêm nhánh `MEKONG-RAAS-v2` dùng Ed25519 mà không đổi cấu trúc payload hay API.
- **Polling 3 giây (`GET /v1/checkout/status`) vs. WebSockets/SSE:**
  - *Chi phí:* Tạo ~20 request HTTP nhẹ trong 1 phút chờ thanh toán cho mỗi phiên checkout.
  - *Khi nào hết phù hợp:* Khi có hơn 5,000 phiên thanh toán mở cùng một giây. Ở quy mô hiện tại, polling đơn giản hơn gấp 5 lần và chuyển sang SSE trong 1 file duy nhất khi cần.

---

## 8. Unverified (Xác minh vs. Giả định)

### Đã xác minh trực tiếp trong Repository (Verified Facts)
- `src/core/vietqr_engine.py` (`450 LOC`) đã hoạt động hoàn chỉnh, stdlib-pure, hỗ trợ 10 ngân hàng Napas 247, tự sinh chuỗi EMVCo có CRC16-CCITT và URL ảnh QR `img.vietqr.io`.
- `src/raas/nowpayments_provider.py` (`164 LOC`) và `src/raas/nowpayments_webhook_handler.py` (`152 LOC`) đã xác thực HMAC-SHA512.
- `src/lib/raas-gate.ts` (`150 LOC`) hiện dùng `free | pro | enterprise` và hàm `generateChecksum` 4 ký tự không mật mã (dòng 97-107).
- `src/raas/checkout_router.py` (180 LOC), `src/raas/revenue_router.py` (233 LOC), `src/api/billing_routes.py` (358 LOC), và `src/services/polar_client.py` đang chứa kết nối tới `api.polar.sh`.
- `src/core/opencore/phase_559_opencore_25_step_catalog.py:45` còn chứa chuỗi `"Polar IPN"`.
- `apps/dashboard/lib/agentops-api.ts` có `: any` ở dòng 144 và 166.

### Chưa xác minh (Unverified Assumptions & Cách kiểm chứng)
1. **Kết nối Webhook thực tế từ Sepay/Ngân hàng và NOWPayments trên server Live:**
   - *Cách kiểm chứng:* Chuyển khoản thật `10,000 VND` qua Napas 247 trên staging để xác nhận webhook kích hoạt đúng `order_id`.
2. **Tỷ lệ chuyển đổi thực tế ở 4 mức giá `$199 / $399 / $799 / $4,999`:**
   - *Cách kiểm chứng:* Thực hiện 15 cuộc phỏng vấn khách hàng mục tiêu và chạy thử nghiệm pilot có thu phí với 3 đối tác thiết kế theo đúng lộ trình trong `tasks.md`.

---

## 9. Work checklist, success metrics & handoff brief

### Work Checklist
- [ ] **Step 11b (Python Core):** Tạo `src/core/raas_license_verifier.py` (`<= 185 LOC`, stdlib-pure) hỗ trợ ký và xác thực HMAC-SHA256 cho `MEKONG-RAAS-v1` và `SOPHIA-RAAS-v1` trên 4 gói `BASIC | PREMIUM | ENTERPRISE | MASTER`.
- [ ] **Step 11b (TypeScript SDK):** Nâng cấp `src/lib/raas-gate.ts` sang hệ gói `BASIC | PREMIUM | ENTERPRISE | MASTER`, xác thực chữ ký HMAC-SHA256 và hạn dùng `expires_at`, loại bỏ kiểu `:any` và `console.log`.
- [ ] **Step 11c (Decommission Polar.sh):** Loại bỏ toàn bộ lệnh gọi `api.polar.sh` khỏi `checkout_router.py`, `revenue_router.py`, `billing_routes.py`, và `polar_client.py`; chuyển `POST /webhook/polar` trả về `HTTP 410 Gone`.
- [ ] **Step 11c (Dual-Rail & License Endpoints):** Tích hợp `VietQrEngine` và `NowPaymentsProvider` vào `POST /v1/checkout`, `GET /v1/pricing`, `POST /v1/billing/checkout/org`; bổ sung `GET /v1/checkout/status`, `POST /v1/license/activate`, `GET /v1/license/status` và đảm bảo mọi file Python chạm tới đều `<= 185 LOC`.
- [ ] **25-Step Behavioral Audit:** Nâng cấp `monetization_gate_probes.py` và `phase_560_opencore_saas_readiness_engine.py` để kiểm tra hành vi thật của Step 11b & 11c; sửa `phase_559_opencore_25_step_catalog.py:45`; cập nhật `[x]` trong `tasks.md`, `plan.md`, và `.mekong/company.json`.
- [ ] **Next.js Dashboard Wiring:** Cập nhật `agentops-api.ts` (xóa `:any`), nâng cấp `checkout/demo/page.tsx` (Dual-Rail + polling 3s Auto-Provisioning), `settings/page.tsx` (Manual License Input + MCU Quota + 25-Step Matrix), và `revenue/page.tsx` (dữ liệu giao dịch thật từ Gateway).
- [ ] **Verification & Tests:** Viết unit/integration tests cho `raas_license_verifier`, Dual-Rail checkout, `410 Gone` trên `/webhook/polar`, và Open-Core readiness engine; chạy `ruff` và `pytest` đạt 100% xanh.

### Success Metrics (Chỉ số kiểm chứng định lượng)
1. **Zero Polar Leak:** Lệnh `grep -rn "api.polar.sh" /Users/macbook/mekong-cli/src/` trả về đúng `0` dòng.
2. **Cryptographic License Enforcement:** 100% khóa hợp lệ `MEKONG-RAAS-v1.<payload>.<sig>` và `SOPHIA-RAAS-v1.<payload>.<sig>` cho 4 gói `BASIC | PREMIUM | ENTERPRISE | MASTER` được xác thực thành công; 100% khóa bị sửa 1 byte bất kỳ hoặc hết hạn bị từ chối ở cả Python và TypeScript.
3. **Open-Core Readiness Verdict:** Chạy:
   ```bash
   python3 -c "from src.core.opencore.phase_560_opencore_saas_readiness_engine import OpenCoreSaasReadinessEngine; r = OpenCoreSaasReadinessEngine.audit_repository('.'); assert r.verdict.value == 'PUBLIC_GITHUB_SAAS_READY' and r.completion_pct == 100.0 and r.saas_paywall_active is True and r.monetization_gaps == ()"
   ```
   trả về exit code `0`.
4. **Strict Module Ceiling & Lint:** Mọi file Python mới hoặc được chỉnh sửa đều có số dòng `wc -l <= 185`; lệnh `python3 -m ruff check src/ tests/` trả về `0` lỗi; `pytest` đạt `100% pass`.
5. **CLI Integrity:** Lệnh `python3 -c "from src.cli.app_setup import build_app; assert len(build_app().registered_groups) == 39"` trả về exit code `0`.

### Handoff Brief

```text
Objective: Tái cấu trúc sâu (--deep) toàn bộ hệ thống Full-Stack của /Users/macbook/mekong-cli (Core CLI Python, FastAPI Gateway, TypeScript SDK, Next.js Dashboard) để hoàn tất 100% lộ trình thương mại hóa 25 bước Open-Core, bao gồm đóng mới bộ ký/xác thực RAAS_LICENSE_KEY chuẩn HMAC-SHA256 (Step 11b), thay thế hoàn toàn Polar.sh bằng Dual-Rail VietQR + NOWPayments USDT (Step 11c), khóa chặt kiểm toán hành vi 25 bước, và nối thông Dashboard với cơ chế Auto-Provisioning (polling 3s) kết hợp Manual License Activation.
Done means:
- /Users/macbook/mekong-cli/src/core/raas_license_verifier.py (<= 185 LOC, stdlib-pure) và /Users/macbook/mekong-cli/src/lib/raas-gate.ts ký/xác thực thành công khóa MEKONG-RAAS-v1.<payload>.<sig> và SOPHIA-RAAS-v1.<payload>.<sig> trên 4 gói BASIC | PREMIUM | ENTERPRISE | MASTER, từ chối 100% khóa giả mạo hoặc hết hạn.
- grep -rn "api.polar.sh" /Users/macbook/mekong-cli/src/ trả về 0 kết quả; POST /webhook/polar trả về HTTP 410 Gone; POST /v1/checkout và POST /v1/billing/checkout/org trả về phiên thanh toán Dual-Rail (VietQR EMVCo hoặc NOWPayments USDT) trên 4 gói ($199, $399, $799, $4,999); các route GET /v1/checkout/status, POST /v1/license/activate, GET /v1/license/status hoạt động đầy đủ.
- OpenCoreSaasReadinessEngine.audit_repository(".") trả về PUBLIC_GITHUB_SAAS_READY với completion_pct == 100.0, saas_paywall_active == True, monetization_gaps == (); plans/company-blueprint/tasks.md đánh dấu [x] cho cả 25 bước kèm Step 11b & Step 11c; .mekong/company.json cập nhật verified: true cho cloud & enterprise.
- Next.js Dashboard (/Users/macbook/mekong-cli/apps/dashboard/lib/agentops-api.ts, app/checkout/demo/page.tsx, app/dashboard/settings/page.tsx, app/dashboard/revenue/page.tsx) kết nối thật tới FastAPI Gateway (:8000), hỗ trợ chọn Dual-Rail VietQR/USDT, tự động lưu & kích hoạt key qua polling 3s (Auto-Provisioning), hỗ trợ dán key kích hoạt thủ công (Manual Activation), và hiển thị số liệu giao dịch thật.
- Mọi file Python tạo mới hoặc chỉnh sửa <= 185 LOC; python3 -m ruff check src/ tests/ đạt 0 lỗi; pytest đạt 100% pass.
Out of scope: Không đưa thư mục apps/ hoặc billing/ lên git index công khai; không tạo dữ liệu doanh thu giả trong .mekong/company.json (giữ nguyên revenue_events: []); không làm thay đổi hoặc giảm số lượng 39 nhóm lệnh CLI trong build_app() hoặc thay đổi giấy phép MIT của phần lõi.
Constraints: Mỗi module Python mới hoặc sửa đổi phải <= 185 LOC; src/core/ phải hoàn toàn stdlib-pure (zero vendor SDK imports); zero :any trong TypeScript; zero console.log trong code production; không hardcode secrets.
Stop and ask only if: Phát hiện một bài kiểm thử hiện có trong tests/ yêu cầu cứng chuỗi URL "https://api.polar.sh" trong kết quả trả về của một public contract mà không thể giải quyết bằng tương thích ngược, hoặc có xung đột schema dữ liệu trong file SQLite hiện hữu (.mekong/vietqr.db).
```
