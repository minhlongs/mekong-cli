# MISA AMIS Export — Founder Guide

> **Phase 7 P03** — Export pilot conversions as MISA AMIS-compatible
> CSV for monthly accounting close. Ships with **DRAFT** account codes
> pending accountant confirmation.

## ⚠️ DRAFT Account Codes — Accountant Action Required

Default codes baked into the exporter:

| Code | Account | Side | Source |
|------|---------|------|--------|
| **131** | Phải thu khách hàng (Customer AR) | Debit | VAS standard chart |
| **511** | Doanh thu bán hàng và CCDV (Service revenue) | Credit | VAS standard chart |
| **33311** | Thuế GTGT đầu ra (Output VAT 10%) | Credit | VAS standard chart |

**Before first real export:** generate a sample CSV (steps below), email
to your accountant for review. Accountant may instruct different codes
based on chart-of-accounts customization. Update via env vars — no code
change needed:

```bash
export MEKONG_MISA_DEBIT_ACCOUNT=1311
export MEKONG_MISA_CREDIT_ACCOUNT=5113
export MEKONG_MISA_VAT_ACCOUNT=33311
```

Or add to launchd plist `EnvironmentVariables` for persistence across reboots.

## Endpoint

```
GET /v1/pilot/export/misa?from=YYYY-MM&to=YYYY-MM
  Authorization: Bearer $MEKONG_ADMIN_TOKEN
```

Response: 8-column CSV with UTF-8 BOM (Excel + AMIS Vietnamese-friendly).

| Column | Example | Notes |
|--------|---------|-------|
| `voucher_date` | `2026-05-15` | From `conversions.started_at` |
| `voucher_no` | `PIL-202605-001` | Ascending per month |
| `debit_account` | `131` | DRAFT — accountant review pending |
| `credit_account` | `511` | DRAFT — accountant review pending |
| `amount_vnd` | `199000` | Integer dong |
| `description` | `Mekong pilot starter_vnd — opc_001_abc` | Human-readable |
| `partner_id` | `opc_001_abc` | Pilot user_id as placeholder |
| `tax_code` | `` (empty) | Blank for pilot tier (50% disc, no invoice) |

## Usage — Manual Curl (Founder)

```bash
TOKEN=$(cat ~/.mekong/admin-token.txt)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://gateway.cashclaw.cc/v1/pilot/export/misa?from=2026-05&to=2026-05" \
  > ~/Desktop/misa-2026-05.csv

# Open in Excel to verify Vietnamese accents render correctly
open ~/Desktop/misa-2026-05.csv
```

## Usage — CLI Script (Local Founder Ops)

```bash
# Default: current month, write to ~/.mekong/exports/
python3 scripts/pilot-export-misa.py --month 2026-05

# Custom output path
python3 scripts/pilot-export-misa.py --month 2026-05 --out ~/Documents/misa.csv

# Range across multiple months
python3 scripts/pilot-export-misa.py --from 2026-05 --to 2026-06
```

The CLI script reads `~/.mekong/conversions.jsonl` directly — no network
call. Safe for offline / pre-deploy testing.

> **Note:** the CLI script is gitignored (`scripts/` per founder-ops
> convention). Copy from `examples/scripts/pilot-export-misa.py` after
> initial clone — or generate via the inline template at the end of this
> guide.

## Upload to MISA AMIS

1. Log into MISA AMIS (https://amis.misa.vn/)
2. Navigate: **Sổ kế toán → Nhập từ file Excel / CSV**
3. Choose file → select `misa-pilots-YYYY-MM-YYYY-MM.csv`
4. Map columns (AMIS may prompt on first import — column names match exactly)
5. Preview → fix any rejected rows → Import
6. Verify: **Sổ cái → 511 (Doanh thu)** — new entries appear

First import will likely surface accountant feedback (codes, tax_code
field, partner_id format). Adjust env vars accordingly and re-export.

## Accountant Review Workflow (One-Time)

Send your accountant a sample 5-row CSV before doing real imports:

### Step 1 — Generate Sample

```bash
# Create a few mock conversions in a scratch dir
SCRATCH=$(mktemp -d)
cat > "$SCRATCH/conversions.jsonl" <<'EOF'
{"user_id":"opc_001_sample","tier":"starter_vnd","monthly_vnd":199000,"started_at":"2026-05-05","recorded_at":"2026-05-05T10:00:00+00:00"}
{"user_id":"opc_002_sample","tier":"starter_vnd","monthly_vnd":199000,"started_at":"2026-05-12","recorded_at":"2026-05-12T10:00:00+00:00"}
{"user_id":"opc_003_sample","tier":"growth_vnd","monthly_vnd":299000,"started_at":"2026-05-15","recorded_at":"2026-05-15T10:00:00+00:00"}
{"user_id":"opc_004_sample","tier":"starter_vnd","monthly_vnd":199000,"started_at":"2026-05-20","recorded_at":"2026-05-20T10:00:00+00:00"}
{"user_id":"opc_005_sample","tier":"pro_vnd","monthly_vnd":499000,"started_at":"2026-05-28","recorded_at":"2026-05-28T10:00:00+00:00"}
EOF

# Generate sample CSV using the exporter
MEKONG_PILOT_DIR="$SCRATCH" python3 -c "
import json
from src.services.misa_exporter import build_misa_rows, write_csv
with open('$SCRATCH/conversions.jsonl') as f:
    convs = [json.loads(line) for line in f if line.strip()]
rows = build_misa_rows(convs, '2026-05', '2026-05')
with open('$SCRATCH/sample-misa.csv', 'w', encoding='utf-8') as f:
    write_csv(rows, f)
print(f'Wrote {len(rows)} rows to $SCRATCH/sample-misa.csv')
"

open "$SCRATCH/sample-misa.csv"
```

### Step 2 — Email to Accountant

Draft template (Vietnamese):

```
Subject: Mekong VN — Xác nhận tài khoản hạch toán cho doanh thu pilot

Chào anh/chị [tên kế toán],

Em gửi anh/chị file CSV mẫu xuất từ hệ thống Mekong VN (5 dòng), định
dạng để import vào MISA AMIS hàng tháng. Em muốn xác nhận với anh/chị:

1. Tài khoản hạch toán hiện đang đặt:
   - Nợ: 131 (Phải thu khách hàng)
   - Có: 511 (Doanh thu bán hàng và CCDV)
   - VAT đầu ra: 33311 (chưa dùng — tier pilot không xuất hóa đơn)

2. Doanh thu pilot là dịch vụ phần mềm SaaS, mỗi tháng khách trả 199K-499K VND.
   Hiện tại đang giảm giá 50% giai đoạn pilot, KHÔNG xuất hóa đơn GTGT.

3. Câu hỏi nhờ anh/chị review:
   - Có nên dùng tài khoản con (131.1, 511.3, etc.) thay vì cấp 3 không?
   - Khi pilot chuyển paid (Phase 8) và xuất hóa đơn GTGT, em update CSV
     thêm cột tax_code = "C01" (10% VAT) đúng không?
   - voucher_no đang format "PIL-202605-001" — anh/chị có pattern khác
     cho phù hợp với chart of accounts hiện tại không?

Em gửi kèm file CSV mẫu. Anh/chị cho em biết cần chỉnh gì để em update
hệ thống trước khi import thật vào AMIS đầu tháng 6.

Cảm ơn anh/chị,
[founder name]
```

### Step 3 — Apply Accountant Feedback

Once accountant confirms (or requests) account codes, update env vars in
the gateway plist:

```bash
sudo plutil -insert EnvironmentVariables.MEKONG_MISA_DEBIT_ACCOUNT \
  -string "1311" /Library/LaunchDaemons/com.mekong.gateway.plist

sudo plutil -insert EnvironmentVariables.MEKONG_MISA_CREDIT_ACCOUNT \
  -string "5113" /Library/LaunchDaemons/com.mekong.gateway.plist

sudo launchctl kickstart -k system/com.mekong.gateway
```

Re-export and verify the new codes appear.

## Versioning

The exporter is versioned implicitly via the comment block in
`src/services/misa_exporter.py`. When MISA AMIS schema changes
(annual), bump the version comment + add a regression test. Founder
should re-confirm with accountant on major MISA AMIS updates.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Vietnamese chars show as `?` in Excel | Missing BOM | Confirmed via test; if persists, open Excel via Data → From Text → UTF-8 |
| AMIS rejects rows | Account codes don't match founder's chart | Set env vars per accountant guidance |
| Empty CSV | No conversions in date range | Verify with `curl GET /v1/pilot/revenue` |
| `401` on curl | Admin token missing or wrong | `cat ~/.mekong/admin-token.txt` and use that |
| `422` "Invalid month format" | Missing leading zero | Use `2026-05` not `2026-5` |
| `tax_code` blank | Intentional for pilot tier (no GTGT invoice) | When pilot graduates to paid + invoicing, add `--tax-code C01` flag (future) |

## Related

- `src/services/misa_exporter.py` — exporter implementation (DRAFT codes documented inline)
- `tests/vn/test_misa_export.py` — 16 test cases covering schema + route + env override
- `docs/handoff-shipping-playbook.md` — overall ops chain
- CLAUDE.md § "VN HUB" — gateway + admin token reference

## Open Questions (founder must resolve)

1. **Account codes** — confirm 131/511/33311 with accountant before first real import.
2. **PII in CSV** — currently includes `partner_id = user_id`. Some accountants prefer redacted IDs. Decide if `partner_id` should be `[REDACTED]` or kept as `user_id`.
3. **Voucher prefix** — `PIL-` is arbitrary. Accountant may want a 4-letter code matching their AMIS setup.
4. **Tax code** — empty for pilot tier. When invoicing starts (Phase 8?), need code mapping (C01 for 10% VAT? C02 for exempt?).
