---
name: corporate
description: Vietnamese corporate governance, business incorporation, Articles of Association (charter), Board resolutions, and statutory filings under Law on Enterprises 2020.
---

# /corporate — Vietnamese Corporate Governance & Legal Incorporation Engine

Providing automated corporate legal document synthesis, Articles of Association (Điều lệ công ty), Board/Member Council resolutions, and statutory incorporation dossiers under the Law on Enterprises 2020 (Law No. 59/2020/QH14) and Decree 01/2021/NĐ-CP.

## Statutory Regulatory Framework

1. **Luật Doanh nghiệp 2020 (Luật số 59/2020/QH14)**:
   - **Điều 24**: Nội dung bắt buộc của Điều lệ công ty (Tên, địa chỉ, ngành nghề, vốn điều lệ, quyền và nghĩa vụ thành viên/cổ đông, cơ cấu quản lý, người đại diện theo pháp luật).
   - **Chương III**: Công ty trách nhiệm hữu hạn 2 thành viên trở lên & Công ty TNHH 1 thành viên.
   - **Chương V**: Công ty cổ phần (Đại hội đồng cổ đông, Hội đồng quản trị, Ban kiểm soát/Ban kiểm toán nội bộ).
   - **Điều 12**: Người đại diện theo pháp luật của doanh nghiệp.

2. **Nghị định 01/2021/NĐ-CP & Quyết định 27/2018/QĐ-TTg (Hệ thống ngành kinh tế Việt Nam - VSIC)**:
   - Hồ sơ đăng ký thành lập doanh nghiệp qua Cổng thông tin quốc gia đăng ký doanh nghiệp.
   - Mã ngành chuẩn: 6201 (Lập trình máy vi tính), 6202 (Tư vấn máy vi tính), 6311 (Xử lý dữ liệu), 7020 (Tư vấn quản trị).

3. **Cơ cấu Doanh nghiệp Hỗ Trợ**:
   - `TNHH_1TV`: Công ty TNHH một thành viên (Chủ sở hữu là cá nhân hoặc tổ chức).
   - `TNHH_2TV`: Công ty TNHH hai thành viên trở lên (Tối đa 50 thành viên).
   - `JSC`: Công ty Cổ phần (Tối thiểu 3 cổ đông sáng lập, phát hành cổ phần).

## Architecture

```
mekong corporate
     │
     ├── (overview)         ── Corporate governance posture, registered entities, and filings
     ├── charter            ── Generate statutory 10-chapter Corporate Charter (Điều lệ công ty)
     ├── resolution         ── Synthesize Board / Member Council resolution & meeting minutes
     ├── dossier            ── Create complete statutory incorporation filing package
     ├── list               ── Query historical corporate documents and dossiers
     └── status             ── Corporate registry metrics in .mekong/corporate.db
```

## CLI Usage

```bash
// turbo
mekong corporate [OPTIONS]
```

### Options & Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong corporate` | `[--json]` | Overview dashboard with corporate filings and statutory governance posture. |
| `mekong corporate charter <name>` | `[--type TNHH_1TV\|TNHH_2TV\|JSC] [--capital N] [--legal-rep NAME] [--address ADDR] [--json]` | Generate statutory Articles of Association / Corporate Charter. |
| `mekong corporate resolution <company>` | `[--type APPOINTMENT\|CAPITAL_INCREASE\|BRANCH] [--title T] [--json]` | Synthesize corporate resolution and minutes. |
| `mekong corporate dossier <name>` | `[--type TNHH_1TV\|TNHH_2TV\|JSC] [--capital N] [--legal-rep NAME] [--industry 6201] [--json]` | Generate statutory incorporation filing dossier. |
| `mekong corporate list` | `[--limit N] [--json]` | Browse created legal documents and corporate records. |
| `mekong corporate status` | `[--json]` | Database telemetry and legal synthesis metrics. |

## Native MCP Tools

| MCP Tool Name | Arguments | Description |
|---------------|-----------|-------------|
| `mekong_corporate_charter` | `company_name, entity_type, charter_capital, legal_rep_name, address` | Generate statutory Articles of Association (Điều lệ công ty). |
| `mekong_corporate_resolution` | `company_name, resolution_type, title, decisions` | Synthesize corporate Board/Shareholder resolution and minutes. |
| `mekong_corporate_dossier` | `company_name, entity_type, charter_capital, legal_rep_name, address, main_industry` | Generate complete statutory incorporation filing dossier. |
| `mekong_corporate_list` | `limit` | Browse historical corporate filings and statutory documents. |
| `mekong_corporate_status` | *(none)* | Retrieve corporate governance engine metrics and filing counts. |
