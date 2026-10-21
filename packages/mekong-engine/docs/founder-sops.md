# Mekong Engine — Founder & Operator SOPs (Invited Pilot)

Hướng dẫn vận hành cho Founder / Operator trong giai đoạn **Invited Pilot (tối đa 5 đối tác)**.
Chỉ sử dụng dữ liệu giả lập (synthetic data) và tích hợp thử nghiệm (test integrations).

- **Engine API:** `https://api.cashclaw.cc`
- **Dashboard Demo (Synthetic Data Only):** `https://ide.mekongmind.com`
- **Public Site:** `https://mekongmind.com`

---

## 1. Cấp Mã Mời Pilot (Operator-Only, Tối Đa 5 Mã)

Mỗi đối tác cần 1 mã mời dùng 1 lần (`invite_code`). Hệ thống chỉ lưu mã băm SHA-256 (`code_hash`) trong D1.

```bash
curl -X POST https://api.cashclaw.cc/billing/invites \
  -H "Authorization: Bearer $SERVICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"partner_name":"Partner 1","partner_email":"partner1@example.com"}'
```

**Response (`201 Created`):**
```json
{
  "invite_id": "inv_...",
  "invite_code": "mk_inv_...",
  "partner_name": "Partner 1",
  "max_partners": 5,
  "remaining_quota": 4,
  "message": "Save this invite_code now — only its SHA-256 hash is stored."
}
```

Xem danh sách mã mời đã cấp:
```bash
curl https://api.cashclaw.cc/billing/invites \
  -H "Authorization: Bearer $SERVICE_TOKEN"
```

---

## 2. Tạo Tenant Mới Kèm `invite_code` (Hiển Thị API Key 1 Lần)

Trong chế độ Pilot, mọi đường dẫn tạo tenant (`/billing/tenants` và `/v1/onboard/signup`) đều bắt buộc có `invite_code` hợp lệ.

```bash
curl -X POST https://api.cashclaw.cc/billing/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"Tên công ty đối tác","invite_code":"mk_inv_..."}'
```

**Response (`201 Created`):**
```json
{
  "tenant_id": "abc-123...",
  "name": "Tên công ty đối tác",
  "api_key": "mk_7945abd8b629...",
  "api_key_display_once": true,
  "tier": "free",
  "credits": 10,
  "invite_redeemed": true
}
```

**LƯU Ý:** `invite_code` chỉ dùng được 1 lần và `api_key` chỉ hiển thị 1 lần duy nhất.

---

## 3. Khách Tự Cài LLM Key (BYOK) Hoặc Dùng Workers AI

```bash
curl -X POST https://api.cashclaw.cc/v1/settings/llm \
  -H "Authorization: Bearer mk_xxx" \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","api_key":"sk-proj-..."}'
```

Kiểm tra cấu hình LLM (key đã che):
```bash
curl https://api.cashclaw.cc/v1/settings/llm \
  -H "Authorization: Bearer mk_xxx"
```

---

## 4. Gửi Mission (LLM-Only) & Xem Kết Quả

Trong giai đoạn Pilot, các bước thực thi chỉ cho phép **LLM-only** (`api` và `shell` bị từ chối). Mission được ghi vào D1 outbox và xử lý qua Cloudflare Queue (`MISSION_QUEUE`) với tối đa 3 lần thử lại và hoàn credit 1 lần duy nhất nếu thất bại cuối cùng.

```bash
# Tạo mission (trả về 201 pending)
curl -X POST https://api.cashclaw.cc/v1/tasks \
  -H "Authorization: Bearer mk_xxx" \
  -H "Content-Type: application/json" \
  -d '{"goal":"Tóm tắt báo cáo thử nghiệm tuần 1","params":{"complexity":"simple"}}'

# Kiểm tra trạng thái và kết quả
curl https://api.cashclaw.cc/v1/tasks/<mission_id> \
  -H "Authorization: Bearer mk_xxx"
```

---

## 5. Kiểm Tra Sức Khỏe Hệ Thống & Bindings

```bash
curl https://api.cashclaw.cc/health
```

Kết quả mong đợi:
```json
{
  "status": "ok",
  "version": "3.1.0",
  "bindings": { "d1": true, "kv": true, "ai": true, "queue": true },
  "pilot": { "invite_only": true, "llm_only": true }
}
```

---

## 6. Quy Định Pilot & Giám Sát Sau Triển Khai

- **Mục tiêu đối tác:** Tối đa 5 đối tác, mỗi đối tác chạy 5 missions/tuần, phản hồi trong vòng 48 giờ.
- **Không thu phí thương mại / Không cam kết SLA:** Pilot sử dụng synthetic credits để kiểm thử luồng sản phẩm.
- **Giám sát 30 phút sau cutover:** Theo dõi liên tục 30 phút sau khi deploy. Rollback ngay nếu:
  1. Tỷ lệ lỗi (error rate) > 5%
  2. Độ trễ (latency) > 2x mức cơ sở (baseline)
  3. Bất kỳ cảnh báo bảo mật nào (security alert)
