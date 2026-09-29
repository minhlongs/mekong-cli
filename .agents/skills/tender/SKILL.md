---
name: tender
description: Vietnamese public procurement, National E-GP electronic bidding dossiers (E-HSMT), 4-step E-HSDT bid evaluation, and collusion detection under Bidding Law 2023.
---

# /tender — Autonomous Public Procurement, National E-GP Electronic Tender & Bid Evaluation Engine

Autonomous Vietnamese Public Procurement and Bidding conforming to:
- **Luật Đấu thầu 2023 (Luật số 22/2023/QH15)**:
  - **Điều 20**: Đấu thầu rộng rãi (Open Bidding) — phương thức cạnh tranh mặc định trên Hệ thống Mạng Đấu thầu Quốc gia (E-GP).
  - **Điều 23**: Chỉ định thầu (Direct Contracting) — áp dụng cho các gói dịch vụ tư vấn ≤ 500 triệu VND; hàng hóa, xây lắp, phi tư vấn ≤ 1 tỷ VND.
  - **Điều 24**: Chào hàng cạnh tranh (Competitive Quotation) — áp dụng cho các gói hàng hóa, dịch vụ thông dụng ≤ 5 tỷ VND.
  - **Điều 14**: Biện pháp bảo đảm dự thầu (Bid Security / Bid Bond) từ 1% đến 3% giá gói thầu.
  - **Điều 16**: Kiểm soát các hành vi bị nghiêm cấm trong đấu thầu (thông thầu, chuyển nhượng thầu trái phép).
- **Nghị định 24/2024/NĐ-CP**:
  - Quy trình đánh giá hồ sơ dự thầu (E-HSDT) 4 bước: Tính hợp lệ → Năng lực và kinh nghiệm → Tiêu chuẩn kỹ thuật → Đánh giá tài chính và xếp hạng nhà thầu.
  - Tiêu chuẩn năng lực tài chính: Doanh thu bình quân 3 năm gần nhất tối thiểu 1.5x giá gói thầu; tối thiểu 1 hợp đồng tương tự có giá trị ≥ 70% giá gói thầu.
- **Thông tư 06/2024/TT-BKHĐT**:
  - Mẫu hồ sơ mời thầu điện tử (E-HSMT) chuẩn hóa trên Hệ thống Mạng Đấu thầu Quốc gia (`muasamcong.mpi.gov.vn`).

## Architecture

```
mekong tender
     │
     ├── (overview)         ── National E-GP procurement dashboard, budget, savings rate
     ├── method             ── Advisory on legal procurement method (Open Bidding, Direct, Competitive)
     ├── create             ── Synthesize and publish electronic tender dossier (E-HSMT)
     ├── eval               ── Execute statutory 4-step E-HSDT bid evaluation (Nghị định 24/2024)
     ├── collusion-scan     ── Scan bids for anti-competitive collusion / abnormal price clustering (Điều 16)
     ├── list               ── Query historical tender packages and active biddings
     └── status             ── Procurement engine database telemetry in .mekong/tenders.db
```

## CLI Usage

```bash
// turbo
mekong tender [OPTIONS]
```

### Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong tender` | `[--json]` | Overview E-GP tenders dashboard, budgets, and savings |
| `mekong tender method` | `<type> <budget> [--urgent] [--proprietary] [--json]` | Advise legal procurement method and caps |
| `mekong tender create` | `<name> <entity> <budget> [--type GOODS] [--method M] [--json]` | Publish E-HSMT tender dossier on National E-GP |
| `mekong tender eval` | `<tender_id> <bidder> <price> [--rev-3yr N] [--contract-val N] [--json]` | 4-step E-HSDT bid evaluation |
| `mekong tender collusion-scan` | `<tender_id> [--json]` | Audit competition integrity & detect collusion |
| `mekong tender list` | `[--status S] [--limit N] [--json]` | Query registered public tenders |
| `mekong tender status` | `[--json]` | Tender engine status and metrics |

## MCP Tools Integration

- `mekong_tender_method(package_type, budget_vnd, is_urgent=False, is_proprietary_tech=False)`: Determine statutory procurement method under Bidding Law 2023.
- `mekong_tender_create(package_name, procuring_entity, budget_vnd, package_type="GOODS", procurement_method=None, submission_days=15)`: Synthesize electronic tender dossier.
- `mekong_tender_eval(tender_id, bidder_name, bid_price_vnd, bidder_tax_id="0101234567", revenue_3yr_avg_vnd=0.0, similar_contract_val_vnd=0.0, tech_score=85.0, has_valid_security=True)`: Evaluate bid under Decree 24/2024/ND-CP.
- `mekong_tender_collusion_scan(tender_id)`: Audit bids for anti-competitive collusion under Article 16.
- `mekong_tender_list(status="ALL", limit=20)`: List tender packages.
- `mekong_tender_status()`: Retrieve procurement engine telemetry and budget savings.
