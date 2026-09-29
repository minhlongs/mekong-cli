---
name: payroll
description: Vietnamese statutory payroll, Gross-to-Net / Net-to-Gross salary calculation, PIT withholding, insurance deductions, and electronic payslip generator.
---

# /payroll — Vietnamese Statutory Payroll & Compensation Engine

Providing deterministic Gross-to-Net and Net-to-Gross salary calculations, progressive Personal Income Tax (PIT) withholding, mandatory social insurance deductions (BHXH, BHYT, BHTN), employer burden costs, and electronic payslips under the Labor Code 2019 and Decrees 73/2024/NĐ-CP & 74/2024/NĐ-CP.

## Statutory Regulatory Framework

1. **Khung Pháp Lý Lao Động & Tiền Lương**:
   - **Bộ luật Lao động 2019 (Luật số 45/2019/QH14)**: Quy định về tiền lương, phụ cấp, tiền làm thêm giờ (overtime 150%, 200%, 300%).
   - **Nghị định 73/2024/NĐ-CP**: Mức lương cơ sở 2,340,000 VND / tháng. Trần đóng BHXH/BHYT là 20 lần = 46,800,000 VND.
   - **Nghị định 74/2024/NĐ-CP**: Mức lương tối thiểu vùng từ 01/07/2024 (Vùng 1: 4.96M, Vùng 2: 4.41M, Vùng 3: 3.86M, Vùng 4: 3.45M). Trần đóng BHTN là 20 lần lương tối thiểu vùng (Vùng 1 là 99,200,000 VND).
   - **Nghị quyết 954/2020/UBTVQH14 & Thông tư 111/2013/TT-BTC**:
     - Giảm trừ bản thân: 11,000,000 VND / tháng.
     - Giảm trừ người phụ thuộc: 4,400,000 VND / tháng / người.
     - Phụ cấp miễn thuế: Tiền ăn giữa ca tối đa 730,000 VND / tháng.

2. **Tỷ Lệ Trích Nộp Bảo Hiểm & Công Đoàn**:
   - **Người lao động (10.5%)**: BHXH 8.0% + BHYT 1.5% + BHTN 1.0%.
   - **Doanh nghiệp / Người sử dụng LĐ (23.5%)**: BHXH 17.5% + BHYT 3.0% + BHTN 1.0% + Kinh phí công đoàn 2.0%.
   - **Tổng gánh nặng phúc lợi xã hội**: 34.0%.

3. **Biểu Thuế Thu Nhập Cá Nhân Lũy Tiến Từng Phần (7 Bậc)**:
   - Bậc 1: Đến 5 triệu VND → 5%
   - Bậc 2: Trên 5 đến 10 triệu VND → 10%
   - Bậc 3: Trên 10 đến 18 triệu VND → 15%
   - Bậc 4: Trên 18 đến 32 triệu VND → 20%
   - Bậc 5: Trên 32 đến 52 triệu VND → 25%
   - Bậc 6: Trên 52 đến 80 triệu VND → 30%
   - Bậc 7: Trên 80 triệu VND → 35%

## Architecture

```
mekong payroll
     │
     ├── (overview)         ── Payroll summary, disburse totals, and statutory tax metrics
     ├── gross-to-net       ── Convert Gross salary to Net, deductions, and employer cost
     ├── net-to-gross       ── Convert desired Net salary to equivalent Gross contract
     ├── payslip            ── Issue itemized electronic payslip and persist record
     ├── list               ── Browse historical payroll disburse records
     └── status             ── Payroll database metrics in .mekong/payroll.db
```

## CLI Usage

```bash
// turbo
mekong payroll [OPTIONS]
```

### Options & Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong payroll` | `[--json]` | Overview dashboard with recent payroll runs and statutory metrics. |
| `mekong payroll gross-to-net <gross>` | `[--dependents N] [--region 1-4] [--lunch 730000] [--json]` | Compute Net take-home pay, employee deductions, and employer cost. |
| `mekong payroll net-to-gross <net>` | `[--dependents N] [--region 1-4] [--lunch 730000] [--json]` | Back-calculate Gross compensation needed for target Net salary. |
| `mekong payroll payslip <name> <gross>` | `[--id EMP_ID] [--month YYYY-MM] [--dependents N] [--bonus N] [--json]` | Generate and store itemized electronic payslip. |
| `mekong payroll list` | `[--month YYYY-MM] [--limit N] [--json]` | Query generated payslips and compensation history. |
| `mekong payroll status` | `[--json]` | Database telemetry and aggregate payroll disbursement records. |

## Native MCP Tools

| MCP Tool Name | Arguments | Description |
|---------------|-----------|-------------|
| `mekong_payroll_gross_to_net` | `gross, dependents, region, lunch_allowance` | Compute Net take-home, taxes, insurance, and employer total cost. |
| `mekong_payroll_net_to_gross` | `net, dependents, region, lunch_allowance` | Calculate required Gross contract for target Net salary. |
| `mekong_payroll_payslip` | `employee_name, gross, employee_id, month, dependents, bonus` | Issue itemized electronic payslip and save to database. |
| `mekong_payroll_list` | `month, limit` | Browse historical payslip records and compensation history. |
| `mekong_payroll_status` | *(none)* | Retrieve payroll ledger metrics, total disbursed, and tax withheld. |
