---
name: fdi
description: Foreign Direct Investment (FDI), State Bank of Vietnam (SBV) DICA capital accounts, offshore profit remittance, foreign loans, and WTO market access compliance.
---

# /fdi — Foreign Direct Investment & SBV Capital Compliance Engine

Providing automated market access condition checks, Direct Investment Capital Account (DICA) validation, legal offshore profit remittance workflows, and foreign loan registration with the State Bank of Vietnam (SBV / NHNN) under Law on Investment 2020 and Circulars 06/2019/TT-NHNN & 12/2022/TT-NHNN.

## Statutory Regulatory Framework

1. **Luật Đầu tư 2020 (Luật số 61/2020/QH14) & Nghị định 31/2021/NĐ-CP**:
   - Danh mục ngành nghề hạn chế tiếp cận thị trường đối với nhà đầu tư nước ngoài (Phụ lục I NĐ 31/2021/NĐ-CP).
   - Tỷ lệ sở hữu vốn nước ngoài (foreign ownership cap / FDI cap): Không hạn chế (100% FDI) đối với CNTT, phần mềm; hoặc có điều kiện (49%, 65%) đối với viễn thông có hạ tầng mạng, logistics, quảng cáo.
   - Thủ tục cấp Giấy chứng nhận đăng ký đầu tư (IRC) và Giấy chứng nhận đăng ký doanh nghiệp (ERC).

2. **Thông tư 06/2019/TT-NHNN — Quản lý ngoại hối đối với hoạt động FDI tại Việt Nam**:
   - Mở và sử dụng **Tài khoản vốn đầu tư trực tiếp (DICA - Direct Investment Capital Account)** bằng ngoại tệ hoặc VND tại 01 ngân hàng được phép.
   - Nguyên tắc chuyển tiền: Mọi giao dịch góp vốn điều lệ, chuyển nhượng vốn, giải ngân vốn vay nước ngoài, và chuyển lợi nhuận hợp pháp ra nước ngoài **bắt buộc phải thực hiện qua DICA**.

3. **Thông tư 186/2010/TT-BTC — Chuyển lợi nhuận ra nước ngoài của nhà đầu tư nước ngoài**:
   - Điều kiện chuyển lợi nhuận: Doanh nghiệp FDI đã nộp Báo cáo tài chính có kiểm toán độc lập, hoàn thành toàn bộ nghĩa vụ thuế (TNDN) và không còn số lỗ lũy kế theo quy định của Luật Thuế TNDN.
   - Thời điểm chuyển lợi nhuận hàng năm: Sau khi kết thúc năm tài chính và thông báo cho cơ quan thuế trực tiếp quản lý trước ít nhất 07 ngày làm việc.

4. **Thông tư 12/2022/TT-NHNN — Đăng ký khoản vay nước ngoài tự vay, tự trả**:
   - Các khoản vay nước ngoài trung và dài hạn (thời hạn trên 01 năm) bắt buộc phải đăng ký với Ngân hàng Nhà nước Việt Nam (Cục Quản lý Ngoại hối) trước khi rút vốn.

## Architecture

```
mekong fdi
     │
     ├── (overview)         ── FDI compliance posture, capital accounts, and registered loans
     ├── market-access      ── Check WTO / CPTPP / EVFTA foreign ownership caps & conditions
     ├── remittance         ── Verify statutory conditions & calculate legal offshore profit remittance
     ├── foreign-loan       ── Evaluate SBV foreign loan registration thresholds & compliance
     ├── irc                ── Synthesize Investment Registration Certificate (IRC) filing dossier
     └── status             ── FDI regulatory telemetry in .mekong/fdi.db
```

## CLI Usage

```bash
// turbo
mekong fdi [OPTIONS]
```

### Options & Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong fdi` | `[--json]` | Overview dashboard with active DICA accounts, loans, and remittance records. |
| `mekong fdi market-access <sector>` | `[--ratio 100] [--json]` | Inspect WTO/FTA market access conditions and foreign ownership limits. |
| `mekong fdi remittance <amount_usd> <year>` | `[--audited] [--tax-cleared] [--json]` | Validate statutory conditions and generate profit remittance notice. |
| `mekong fdi foreign-loan <amount_usd> <months> <rate>` | `[--lender L] [--purpose P] [--json]` | Check SBV loan registration requirement and interest cap. |
| `mekong fdi irc <project_name> <capital_usd>` | `[--location LOC] [--sector S] [--investor I] [--json]` | Synthesize statutory IRC investment project dossier. |
| `mekong fdi status` | `[--json]` | FDI database metrics and regulatory telemetry in `.mekong/fdi.db`. |

## Native MCP Tools

| MCP Tool Name | Arguments | Description |
|---------------|-----------|-------------|
| `mekong_fdi_market_access` | `sector_code, foreign_ratio` | Query WTO/FTA market access conditions and ownership caps. |
| `mekong_fdi_remittance` | `amount_usd, tax_year, is_audited, has_tax_clearance` | Verify legal offshore profit remittance eligibility under TT 186. |
| `mekong_fdi_foreign_loan` | `amount_usd, tenor_months, interest_rate, lender_country` | Evaluate SBV foreign loan registration requirements under TT 12. |
| `mekong_fdi_irc` | `project_name, capital_usd, investor_country, sector_code` | Synthesize statutory Investment Registration Certificate dossier. |
| `mekong_fdi_status` | *(none)* | Retrieve FDI investment capital telemetry and regulatory status. |
