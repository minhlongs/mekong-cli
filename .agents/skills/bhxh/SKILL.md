---
name: bhxh
description: >-
  Vietnamese social insurance (BHXH, BHYT, BHTN) contribution calculations, salary ceilings, and D02-LT statutory declarations.
---

# /bhxh — Autonomous Vietnamese Social Insurance (BHXH, BHYT, BHTN) Contribution & Statutory Declaration Engine

Providing deterministic labor compliance, statutory social insurance deductions, contribution ceiling enforcement, and electronic D02-LT declaration filing for solo founders, SMEs, and enterprise HR swarms operating in Vietnam under the Labor Code 2019 and Social Insurance Law.

## Statutory Regulations & Thresholds

1. **Căn cứ Pháp lý Hiện hành**:
   - **Nghị định 73/2024/NĐ-CP**: Mức lương cơ sở **2.340.000 đ/tháng** (áp dụng từ 01/07/2024).
   - **Nghị định 74/2024/NĐ-CP**: Mức lương tối thiểu vùng (Vùng I: 4.960.000 đ, Vùng II: 4.410.000 đ, Vùng III: 3.860.000 đ, Vùng IV: 3.450.000 đ).
2. **Mức trần Đóng Bảo hiểm (Ceiling Limits)**:
   - **BHXH & BHYT**: Tối đa 20 lần mức lương cơ sở = **46.800.000 đ/tháng**.
   - **BHTN**: Tối đa 20 lần mức lương tối thiểu vùng (Vùng I: **99.200.000 đ/tháng**).
3. **Tỷ lệ Trích nộp Bắt buộc (Contribution Rates)**:
   - **Người lao động (Employee / NLĐ)**:
     - BHXH (Hưu trí / Tử tuất): **8.0%**
     - BHYT (Y tế): **1.5%**
     - BHTN (Thất nghiệp): **1.0%**
     - **Tổng NLĐ đóng: 10.5%**
   - **Người sử dụng lao động (Employer / NSDLĐ)**:
     - BHXH (Hưu trí 14%, Ốm đau-thai sản 3%, TNLĐ-BNN 0.5%): **17.5%**
     - BHYT (Y tế): **3.0%**
     - BHTN (Thất nghiệp): **1.0%**
     - **Tổng NSDLĐ đóng: 21.5%**
     - *(Kinh phí Công đoàn KPCĐ 2% tính riêng)*
   - **Tổng cộng cả DN + NLĐ: 32.0%** (hoặc 34.0% gồm KPCĐ).
4. **Hồ sơ Điện tử Mẫu D02-LT**:
   - Quyết định 595/QĐ-BHXH & Quyết định 490/QĐ-BHXH:
   - Nghiệp vụ: `bao_tang` (báo tăng lao động mới), `bao_giam` (báo giảm nghỉ việc/thai sản), `dieu_chinh_luong` (thay đổi mức lương đóng bảo hiểm).

## Architecture

```
mekong bhxh
     │
     ├── (overview)             ── Executive insurance telemetry, contribution funds, and statutory decrees
     ├── calc [SALARY]          ── Detailed breakdown of NLĐ (10.5%) & NSDLĐ (21.5%) deductions with ceiling caps
     ├── employees              ── Roster of registered employees, BHXH codes, and base insurance salaries
     ├── declaration [TYPE]     ── Draft and generate statutory D02-LT e-filing records
     └── status                 ── System status, statutory parameters, and calculation history
```

## CLI Usage

```bash
// turbo
mekong bhxh [OPTIONS]
```

### Options & Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong bhxh` | `[--json]` | Overview dashboard with statutory thresholds, fund totals, and recent calculations. |
| `mekong bhxh calc` | `<salary> [--region 1\|2\|3\|4] [--kpcd] [--json]` | Compute detailed employee (10.5%) and employer (21.5%) contributions. |
| `mekong bhxh employees` | `[--status active\|all] [--json]` | Query employee roster with BHXH codes and insurance wage brackets. |
| `mekong bhxh declaration`| `<type> <employee_id> [--month MM/YYYY] [--new-salary S] [--note T] [--json]` | Create statutory D02-LT declaration (`bao_tang`, `bao_giam`, `dieu_chinh_luong`). |
| `mekong bhxh status` | `[--json]` | Inspection of statutory decrees, base salary, ceiling parameters, and ledger telemetry. |

## Native MCP Tools Integration

Antigravity multi-agent swarms and finance subagents access social insurance capabilities via 4 native MCP tools:

1. **`mekong_bhxh_calc(salary: float, region: int = 1, include_kpcd: bool = False, employee_id: str = "ADHOC")`**:
   Calculate progressive statutory contributions with automated ceiling caps.
2. **`mekong_bhxh_employees(status: str = "all")`**:
   Retrieve registered employee list for insurance compliance reporting.
3. **`mekong_bhxh_declaration(change_type: str, employee_id: str, effective_month: str = "", new_salary: float = 0.0, note: str = "")`**:
   Generate electronic D02-LT declaration record compliant with Decision 595/QĐ-BHXH.
4. **`mekong_bhxh_status()`**:
   Query aggregated fund statistics, active employees, and statutory parameter baselines.
