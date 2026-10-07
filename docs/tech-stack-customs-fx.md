# Tech Stack Specification — Vietnam Customs, FX & Bonded Logistics Suite (Phases 167 - 170)

**Date:** 2026-10-07  
**Architecture Layer:** Mekong CLI Core & CLI Subsystems  
**Target:** Phases 167, 168, 169, 170

---

## 1. Core Architecture Principles

1. **Zero External Dependencies in Core:**
   - `src/core/customs_fx_engine.py` is written in 100% Python Standard Library (`dataclasses`, `enum`, `typing`, `datetime`, `math`).
   - Strictly no imports of third-party libraries (`requests`, `pydantic`, `fastapi`, `rich`) in the domain layer to guarantee instantaneous startup, deterministic test runs, and clean boundary isolation.

2. **Dual-Interface Consumption:**
   - **CLI Layer:** `src/cli/commands/customs_command.py` powered by Typer and Rich formatting with `--json` output flags.
   - **Agent/MCP Layer:** `scripts/mcp_server.py` exposing FastMCP & JSON-RPC tools for agentic systems.

---

## 2. Component Layout

| Module | Location | Dependencies | Role |
|---|---|---|---|
| Domain Core | `src/core/customs_fx_engine.py` | Python StdLib only | Calculation algorithms for Customs Valuation, RVC, FX Loans, Royalty, and Bonded Storage. |
| CLI Commands | `src/cli/commands/customs_command.py` | Typer, Rich | 12 interactive CLI commands aliased under `mekong customs` and `mekong haiquan`. |
| MCP Handlers | `scripts/mcp_server.py` | JSON-RPC, FastMCP | AI agent tool registry for automated customs compliance. |
| Test Suite | `tests/test_customs_fx_suite.py` | pytest, typer.testing | Automated AST boundary tests, mathematical tests, CLI tests, MCP tests. |

---

## 3. Algorithms & Statutory Formulas

- **Customs Valuation:** Method 1: $V_{customs} = P_{invoice} + Adjustments_{add} - Adjustments_{deduct}$.
- **Rules of Origin (RVC):**
  - Build-down: $RVC = \frac{FOB - VNM}{FOB} \times 100\%$.
  - Build-up: $RVC = \frac{VOM}{FOB} \times 100\%$.
- **SBV Foreign Loan:** Medium/long term ($> 365$ days) requires SBV registration within 30 days.
- **Technology Transfer Royalty:** $Royalty = NetSales \times r\%$ (1.0% - 5.0% standard; 25% profit-split rule).
- **Bonded Warehouse Limits:** Max 12 months, 1 extension max 12 months (24 months total cap). CFS max 90 days.
