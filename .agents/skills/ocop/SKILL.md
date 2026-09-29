---
name: ocop
description: Vietnamese OCOP agricultural star rating evaluation (1-5 stars), HS codes, and B2B export marketplace compliance.
---

# /ocop — Autonomous Vietnamese OCOP Agricultural Star Rating, HS Code & Export Compliance Engine

Providing deterministic agricultural product evaluation, national OCOP star grading (1–5 stars), HS code classification, international trade compliance (EVFTA, US FDA, Japan AJCEP, China GACC), and B2B marketplace listing synthesis (Alibaba, Amazon, Shopee) under Prime Minister Decisions 919/QĐ-TTg and 148/QĐ-TTg.

## Statutory Regulations & Standards

1. **Căn cứ Pháp lý Quốc gia**:
   - **Quyết định 919/QĐ-TTg**: Phê duyệt Chương trình Mỗi xã một sản phẩm (OCOP) giai đoạn 2021–2025.
   - **Quyết định 148/QĐ-TTg**: Ban hành Bộ tiêu chí và quy trình đánh giá, phân hạng sản phẩm OCOP quốc gia (thang điểm 100).
2. **Thang Điểm Phân Hạng Sao (100 Điểm Tối Đa)**:
   - **Phần A**: Các tiêu chí về sản phẩm và sức mạnh cộng đồng (tối đa **35 điểm**).
   - **Phần B**: Các tiêu chí về khả năng tiếp thị và tổ chức thương mại (tối đa **25 điểm**).
   - **Phần C**: Các tiêu chí về chất lượng sản phẩm, an toàn thực phẩm và chứng nhận (tối đa **40 điểm**).
   - **Phân Hạng**:
     - **90 – 100 điểm**: **5 Sao** (Cấp Quốc gia — Tiêu chuẩn xuất khẩu toàn cầu).
     - **70 – 89 điểm**: **4 Sao** (Cấp Tỉnh — Tiềm năng xuất khẩu khu vực).
     - **50 – 69 điểm**: **3 Sao** (Cấp Tỉnh/Huyện — Tiêu chuẩn phân phối nội địa).
     - **30 – 49 điểm**: **2 Sao** (Khởi đầu cấp xã/huyện).
     - **Dưới 30 điểm**: **1 Sao** (Ý tưởng sơ khai).
3. **Thị Trường Xuất Khẩu & Hiệp Định FTA**:
   - **EU**: Hiệp định EVFTA (thuế suất 0%), tuân thủ MRLs dư lượng BVTV, ISO 22000, HACCP, nhãn 1169/2011/EU.
   - **Mỹ**: US FDA Facility Registration, FSMA Preventive Controls, Nutrition Facts tiếng Anh.
   - **Nhật Bản**: Tiêu chuẩn nông nghiệp JAS, VJEPA/CPTPP 0%, kiểm dịch thực vật MAFF.
   - **Trung Quốc**: Mã số doanh nghiệp GACC (Lệnh 248), mã số vùng trồng PUC (Lệnh 249), ACFTA.
   - **Trung Đông**: Chứng nhận Halal (JAKIM/GCC công nhận), nhãn song ngữ Anh - Ả Rập.

## Architecture

```
mekong ocop
     │
     ├── (overview)         ── National OCOP status, star breakdown, and featured export products
     ├── eval [NAME]        ── Evaluate 1-5 star rating per Decision 148/QĐ-TTg (Parts A, B, C)
     ├── products           ── Query registered OCOP catalog with HS codes and international certs
     ├── listing [ID]       ── Generate B2B export marketplace listing (Alibaba, Amazon, Shopee)
     ├── compliance [MKT]   ── Check FTA tariff preferences, rules of origin, and mandatory certs
     ├── analyze [FILE]     ── AI-powered vision/multimodal agricultural analysis
     ├── export             ── Legacy export listing generator
     └── status             ── System telemetry, database metrics, and export history
```

## CLI Usage

```bash
// turbo
mekong ocop [OPTIONS]
```

### Options & Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong ocop` | `[--json]` | Overview dashboard with national OCOP star distribution and export products. |
| `mekong ocop eval` | `<product> [--part-a N] [--part-b N] [--part-c N] [--json]` | Evaluate 1–5 star rating per Decision 148/QĐ-TTg. |
| `mekong ocop products` | `[--min-stars N] [--province P] [--json]` | Browse registered products with HS codes and certifications. |
| `mekong ocop listing` | `<product_id> [--market M] [--platform P] [--json]` | Generate B2B export marketplace listing and trade review. |
| `mekong ocop compliance` | `<market> [--json]` | Inspect technical barriers and tariff rates for target markets. |
| `mekong ocop status` | `[--json]` | Telemetry and database records in `.mekong/ocop.db`. |

## Native MCP Tools

| MCP Tool Name | Arguments | Description |
|---------------|-----------|-------------|
| `mekong_ocop_eval` | `product_name, part_a, part_b, part_c` | Evaluate star rating per Decision 148/QĐ-TTg. |
| `mekong_ocop_products` | `min_stars, province` | List registered OCOP products with star ratings and HS codes. |
| `mekong_ocop_listing` | `product_id, target_market, platform` | Synthesize B2B export listing and compliance audit. |
| `mekong_ocop_compliance` | `market` | Query export regulations and tariff benefits. |
| `mekong_ocop_status` | *(none)* | Aggregated OCOP program telemetry. |
