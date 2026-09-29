---
name: thue
description: >-
  Vietnamese tax calculator for personal income tax (TNCN), corporate income tax (TNDN), and VAT (GTGT).
---

# /thue — Autonomous Vietnamese Tax Calculation, Progressive Deductions & Filing Simulation Engine

Serving as the deterministic tax computation and regulatory simulation engine for solo founders, SME operators, and enterprise finance agents in Vietnam, `mekong thue` manages personal income tax brackets, corporate income tax incentives, and VAT reconciliations.

## Statutory Regulations & Rates Embedded

1. **Thuế Thu Nhập Cá Nhân (TNCN)**:
   - Điều 22, Luật Thuế TNCN (7 progressive tax brackets: 5%, 10%, 15%, 20%, 25%, 30%, 35%)
   - Giảm trừ bản thân người nộp thuế: **11.000.000 đ/tháng**
   - Giảm trừ mỗi người phụ thuộc: **4.400.000 đ/người/tháng**
2. **Thuế Thu Nhập Doanh Nghiệp (TNDN)**:
   - Thuế suất tiêu chuẩn: **20%**
   - Thuế suất ưu đãi SME (doanh thu ≤ 3 tỷ VND/năm): **17%**
3. **Thuế Giá Trị Gia Tăng (GTGT / VAT)**:
   - Nghị định 123/2020/NĐ-CP & Nghị định 72/2024/NĐ-CP (0%, 5%, 8%, 10%)

## Architecture

```
mekong thue
     │
     ├── (overview)       ── Executive tax simulation telemetry & statutory deduction thresholds
     ├── tncn [INCOME]    ── Progressive personal income tax calculation with dependent deductions
     ├── tndn [REVENUE]   ── Corporate income tax with SME preferential rate (17%) support
     ├── gtgt [AMOUNT]    ── Value added tax (VAT 0%, 5%, 8%, 10%) calculation
     ├── list             ── Historical tax calculation ledger stored in .mekong/thue.db
     └── status           ── Aggregated simulated tax, total runs, and statutory parameter check
```

## CLI Usage

```bash
// turbo
mekong thue [OPTIONS]
```

### Options & Subcommands

| Command | Arguments / Flags | Description |
|---------|-------------------|-------------|
| `mekong thue` | `[--json]` | Overview dashboard with total tax simulated, calculation history, and deduction rates. |
| `mekong thue tncn` | `<income> [--dependents N] [--json]` | Progressive personal income tax calculation (Điều 22 Luật thuế TNCN). |
| `mekong thue tndn` | `<revenue> [--profit N] [--sme/--no-sme] [--json]` | Corporate income tax calculation with 20% standard or 17% SME rate. |
| `mekong thue gtgt` | `<amount> [--rate 0\|5\|8\|10] [--json]` | Value added tax calculation with subtotal, VAT amount, and total inclusive. |
| `mekong thue status` | `[--json]` | Inspection of tax engine status, deduction limits, and type breakdown. |
| `mekong thue list` | `[--type tncn\|tndn\|gtgt\|all] [--limit N] [--json]` | Query recorded historical tax calculations from `.mekong/thue.db`. |

## Native MCP Tools Integration

The Tax engine provides 4 native MCP tools for programmatic finance agent operations:

1. **`mekong_thue_tncn(monthly_income: float, dependents: int = 0)`**:
   Calculate progressive Personal Income Tax (TNCN) with personal and dependent deductions.

2. **`mekong_thue_tndn(annual_revenue: float, profit: float = 0.0, is_sme: bool = True)`**:
   Calculate Corporate Income Tax (TNDN) with standard or SME preferential rate.

3. **`mekong_thue_gtgt(amount: float, rate: int = 10)`**:
   Calculate Value Added Tax (GTGT) under Decree 123 & Circular 78.

4. **`mekong_thue_status()`**:
   Retrieve tax engine telemetry, historical calculation counts, and statutory parameters.

Both FastMCP and pure-Python stdio JSON-RPC 2.0 engines support 100% parity.
