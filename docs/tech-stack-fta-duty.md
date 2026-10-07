# Tech Stack Specification — Vietnam FTA Concessions, EPE, AEO & Duty Exemption Suite (Phases 171 - 174)

**Date:** 2026-10-07  
**Architecture Layer:** Mekong CLI Core Domain & CLI Subsystems  
**Target:** Phases 171, 172, 173, 174  

---

## 1. Core Architecture Principles

1. **AST Dependency Purity in Domain Core:**
   - `src/core/fta_duty_engine.py` is written in 100% Python standard library (`__future__`, `dataclasses`, `enum`, `typing`, `datetime`, `math`, `json`).
   - Zero external dependencies in the core layer to ensure microsecond execution speeds, pure deterministic business logic, and resilient offline execution. Verified via `ast.parse` in automated CI test suites.

2. **Dual-Interface Operation:**
   - **CLI Layer:** `src/cli/commands/fta_command.py` powered by Typer and Rich formatting with `--json` output flags, registered under `mekong fta` and `mekong dncx`.
   - **Agent/MCP Layer:** `scripts/mcp_server.py` exposing FastMCP & JSON-RPC tools (`mekong_fta_tariff_savings`, `mekong_fta_origin_criterion`, `mekong_epe_conditions_check`, `mekong_aeo_eligibility_eval`, `mekong_duty_reconciliation_bcqt15`).

---

## 2. Component Layout

| Module | Location | Dependencies | Role |
|---|---|---|---|
| Domain Core | `src/core/fta_duty_engine.py` | Python StdLib only | Calculation algorithms for FTA savings, CTC/RVC origin criteria, EPE supervision, AEO channeling, SXXK refund & BCQT 15 reconciliation. |
| CLI Commands | `src/cli/commands/fta_command.py` | Typer, Rich | 10 interactive CLI commands aliased under `mekong fta` and `mekong dncx`. |
| MCP Handlers | `scripts/mcp_server.py` | JSON-RPC, FastMCP | AI agent tool registry for automated customs compliance. |
| Test Suite | `tests/test_fta_duty_suite.py` | pytest, typer.testing | 48 automated tests: AST boundary tests, mathematical tests, CLI tests, MCP tests. |

---

## 3. Algorithms & Statutory Formulas

- **Tariff Savings:**
  $$\text{Savings} = V_{\text{customs}} \times (\text{Rate}_{\text{MFN}} - \text{Rate}_{\text{FTA}})$$
- **Rules of Origin (ROO):**
  - **CTC:** CC (2-digit change), CTH (4-digit change), CTSH (6-digit change).
  - **RVC:** $\text{RVC} \ge 40\%$ threshold.
  - **De Minimis:** Non-originating materials failing CTC qualify if total value $\le 10\%$ FOB.
- **EPE Customs Supervision:** Enforces 4 mandatory physical and digital criteria under Decree 35/2022/NĐ-CP (Article 26).
- **On-Spot Counterpart Declaration:** Enforces 15-working-day statutory limit pursuant to Circular 38/2015/TT-BTC (Article 86).
- **AEO Risk Channeling:** Automated routing into Green (0% physical check), Yellow (documentary), or Red (physical inspection) pursuant to Decision 1399/QĐ-TCHQ.
- **SXXK Duty Refund:** Refund ratio based on materials incorporated into exported goods (Decree 134/2016/NĐ-CP, Article 36).
- **BCQT 15 Reconciliation:**
  $$\text{Closing}_{\text{theoretical}} = \text{Opening} + \text{Imported} - (\text{Exported} \times \text{BOM}) - \text{Scrap}$$
  Late payment interest of 0.03%/day on deficit duty arrears pursuant to Law on Tax Administration 2019.
