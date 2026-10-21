# Plan 261021-1100 — Siết bảo mật endpoint thanh toán

**Cơ sở (chân lý đã xác minh):** `GET /v1/success` tại `src/raas/checkout_router.py:84-89` là endpoint CÔNG KHAI, không xác thực. Bất kỳ ai gọi cũng tạo tenant mới với API key thật + credit thật (`src/raas/checkout_router.py:104` lấy credit, `:112-121` tạo tenant). HMAC guard đã bị gỡ khi tách bỏ provider cũ.
**Mục tiêu:** khôi phục chữ ký HMAC bằng biến môi trường trung lập; không mất route công khai; không dùng tên provider cũ.
**Ràng buộc:** không xoá route; chỉ Additive/Edit trên `src/raas/checkout_router.py`; không chạm git checkout/stash/reset; tên biến trung lập; ≤180 LOC.

## Phase 1 — Xác minh đường cơ sở (baseline)
| Việc | Lệnh | Đầu ra |
|---|---|---|
| Chạy test lọc | `python3 -m pytest tests/ -q -k "payment or raas or billing or webhook or checkout" 2>&1 \| tail -20` | `plans/261021-1100-payment-security-boundary/phase-01-reports/baseline.md` |
| Lint file mục tiêu | `python3 -m ruff check src/raas/checkout_router.py` | ghi kết quả |
| Chụp kích thước | `wc -l src/raas/checkout_router.py src/raas/revenue_router.py` | ghi kết quả |

Mục đích: biết rõ lỗi nào ĐÃ tồn tại trước khi sửa → không đổ lỗi cho thay đổi này.

## Phase 2 — Khôi phục chữ ký bằng biến trung lập
File DUY NHẤT: `src/raas/checkout_router.py` (134 dòng hiện tại).
1. Thêm imports `import hashlib`, `import hmac`, `import os` sau `src/raas/checkout_router.py:17`.
2. Thêm tham số `sig: str = ""` vào signature tại `src/raas/checkout_router.py:85` (giữ nguyên 3 tham số cũ).
3. TRƯỚC dòng `credits = CREDIT_MAP[resolved_tier]` (`:104`), chèn:
   - `secret = os.environ.get("PAYMENT_SUCCESS_SECRET", "")`
   - nếu không có `sig` → trả `SuccessResponse(api_key="pending_webhook_verification", credits=CREDIT_MAP.get(resolved_tier, 0), tier=resolved_tier, tenant_id="provisioned_via_webhook")`
   - nếu có `secret` và `hmac.compare_digest(sig, ...)` sai → trả cùng `SuccessResponse` pending như trên. Chuỗi ký: `hmac.new(secret.encode(), f"{tier.lower()}:{email}".encode(), hashlib.sha256).hexdigest()[:32]`
   - Comment tiếng Việt ghi rõ: khi `PAYMENT_SUCCESS_SECRET` chưa cấu hình, endpoint tự đóng (fail-closed) phần cấp credit — đây là cố ý, chặn cấp key miễn phí cho người gọi không xác thực.
4. Giữ NGUYÊN idempotency guard (`:106-111`) và toàn bộ phần cấp credit phía sau.
5. Nếu `sig` đúng thì đi tiếp luồng cũ (tạo tenant + cấp credit như hiện tại).
6. Thêm `PAYMENT_SUCCESS_SECRET=` vào `.env.example` (file đã tồn tại, 683 byte — kiểm tra trước; KHÔNG ghi giá trị thật).
Lưu ý KHÁC BIỆT bắt buộc: biến môi trường là `PAYMENT_SUCCESS_SECRET`. Không được viết tên provider cũ vào code, comment, tên biến hay tên file.

## Phase 3 — Kiểm gateway không còn đường tên cũ
| Việc | Lệnh | Kỳ vọng |
|---|---|---|
| Quét gateway | `grep -n "polar\|checkout_router" src/gateway.py` | chỉ còn `:31` import, `:87` register — 0 dòng tên cũ |
| Xác nhận 4 route | grep `@router\.(get\|post)` trong `src/raas/checkout_router.py` | `/v1/checkout`, `/v1/success`, `/v1/onboard`, `/v1/pricing` vẫn đủ |
| Báo cáo danh sách còn sót | `grep -rni "polar" src/raas/ --include="*.py"` | CHỈ báo cáo danh sách file, KHÔNG sửa — founder quyết |

## Phase 4 — Chứng minh
| Việc | Lệnh / cách làm | Tiêu chí đạt |
|---|---|---|
| Lint sạch | `python3 -m ruff check src/raas/` | 0 lỗi mới so với Phase 1 |
| Test suite | `python3 -m pytest tests/ -q -k "payment or raas or billing or webhook or checkout" 2>&1 \| tail -20` | không thêm lỗi mới so với baseline |
| Tay test 1 | TestClient, KHÔNG env, KHÔNG sig | `api_key="pending_webhook_verification"`, `tenant_id="provisioned_via_webhook"`, KHÔNG tạo tenant mới trong DB |
| Tay test 2 | env `PAYMENT_SUCCESS_SECRET=test123`, gửi sig sai | trả pending, KHÔNG cấp API key thật |
| Tay test 3 | env `test123`, gửi sig ĐÚNG (sha256 `f"{tier}:{email}"`, cắt 32 ký tự) | tạo tenant thật, trả API key thật |
| Kích thước file | `wc -l src/raas/checkout_router.py` | ≤ 180 |
| Ghi kết quả | 3 kết quả tay test | `plans/261021-1100-payment-security-boundary/phase-01-reports/security-verification.md` |

## Rủi ro công nhận
- Cây làm việc có ~1944 thay đổi chưa commit; `src/raas/revenue_router.py` đã bị sửa 232→141 dòng TRƯỚC plan này. Plan KHÔNG phục hồi file đó.
- Test suite có sẵn lỗi không liên quan (`health_reporter.py` 188 LOC; PermissionError ghi `~/.mekong/usage/`). Phải phân biệt rõ lỗi cũ/lỗi mới trước khi báo cáo.
- Rollback: chỉ cần revert `src/raas/checkout_router.py` về bản 134 dòng và bỏ dòng `.env.example`. Không có migration, không có đổi schema.
