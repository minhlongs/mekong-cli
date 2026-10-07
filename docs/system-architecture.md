# System Architecture — Mekong Dispute Resolution & Maritime Law Suite

## 1. High-Level Architecture

The Mekong Dispute Resolution & Maritime Law Suite extends Mekong CLI v6.0 with four dedicated legal and maritime calculation engines compliant with Vietnamese statutes and international maritime conventions.

```
+-------------------------------------------------------------------------------+
|                                 CLIENT SURFACES                                |
|  +-------------------------------+   +--------------------------------------+  |
|  | CLI Terminal (Typer + Rich)   |   | MCP Server (JSON-RPC + FastMCP)      |  |
|  | mekong dispute <command>      |   | claude_ai / cursor / windsurf tools  |  |
|  +---------------+---------------+   +------------------+-------------------+  |
+------------------|--------------------------------------|---------------------+
                   |                                      |
+------------------v--------------------------------------v---------------------+
|                             ROUTING & ADAPTER LAYER                           |
|  - src/cli/commands/dispute_command.py (CLI Options & Formatting)             |
|  - scripts/mcp_server.py (JSON-RPC Tools: handle_dispute_*)                   |
+------------------+--------------------------------------+---------------------+
                   |                                      |
+------------------v--------------------------------------v---------------------+
|                            CORE ENGINE DOMAIN LAYER                           |
|             (100% Python Standard Library - Zero External Dependencies)        |
|                                                                               |
|  +--------------------------------+   +------------------------------------+  |
|  | src/core/dispute_engine.py     |   | src/core/maritime_law_engine.py    |  |
|  |                                |   |                                    |  |
|  | - CommercialArbitrationEngine  |   | - MaritimeLawEngine                |  |
|  |   * VIAC 2024 Fee Scale        |   |   * Carrier Liability (Hague-Visby)|  |
|  |   * Clause Validity & Risks    |   |   * General Average (York-Antwerp) |  |
|  |   * 2-Year Limitation Period   |   |   * Salvage Rewards (No Cure No Pay|  |
|  |                                |   |   * Maritime Liens Priority Ranking|  |
|  | - CivilEnforcementEngine       |   +------------------------------------+  |
|  |   * 5-Year Statute Check       |                                           |
|  |   * 3% Fee & 200M Cap          |                                           |
|  |   * Article 47 Priority Queue  |                                           |
|  |                                |                                           |
|  | - CourtLitigationEngine        |                                           |
|  |   * District vs Provincial     |                                           |
|  |   * Resolution 326 Fee Scale   |                                           |
|  |   * 50% Court Fee Advance      |                                           |
|  +--------------------------------+                                           |
+-------------------------------------------------------------------------------+
```

## 2. Key Modules & Boundaries

1. **`src/core/dispute_engine.py`**:
   - Zero-dependency Python standard library implementation.
   - Enforces statutory rules for arbitration, judgment enforcement, and court litigation.

2. **`src/core/maritime_law_engine.py`**:
   - Zero-dependency Python standard library implementation.
   - Enforces Vietnam Maritime Code 2015, Hague-Visby SDR limits, and York-Antwerp 2016 General Average zero-sum balance.

3. **`src/core/trade_transport_engine.py`**:
   - Zero-dependency Python standard library implementation.
   - Enforces statutory rules for Multimodal Transport (NĐ 87/2009), Civil Aviation (Montreal 1999 & Luật HKDD), CISG 1980 & Incoterms 2020, and Trade Remedies / Anti-Dumping (Luật QLNT 2017).

4. **`src/cli/commands/dispute_command.py`**:
   - Rich terminal interface with tables, panels, and machine-readable `--json` flags.
   - Aliased under both `dispute` and `tranhchap`.

5. **`src/cli/commands/trade_command.py`**:
   - Rich terminal interface with 13 commands for MTO, aviation, CISG, Incoterms, and trade remedies.
   - Aliased under both `trade` and `thuongmai`.

6. **`src/core/customs_fx_engine.py`**:
   - Zero-dependency Python standard library implementation.
   - Enforces statutory rules for Customs Valuation & RVC origin rules (TT 39/2015/TT-BTC, TT 60/2019/TT-BTC & NĐ 31/2018/NĐ-CP), SBV Foreign Loan & Profit Remittance (TT 12/2022/TT-NHNN & TT 186/2010/TT-BTC), Technology Transfer Royalty & Licensing (Luật CGCN 2017 & NĐ 76/2018/NĐ-CP), and Bonded Warehouse & CFS Operations (Luật HQ 2014 & NĐ 08/2015/NĐ-CP).

7. **`src/cli/commands/customs_command.py`**:
   - Rich terminal interface with 8 subcommands (`valuation`, `rvc`, `audit-check`, `sbv-loan`, `profit-remit`, `tech-registration`, `royalty`, `storage-check`).
   - Aliased under both `customs` and `haiquan`.

8. **`src/core/fta_duty_engine.py`**:
   - Zero-dependency Python standard library implementation.
   - Enforces statutory rules for FTA Concessions & Origin (EVFTA/CPTPP/RCEP/ATIGA), EPE Customs Supervision & On-Spot Deadlines (NĐ 35/2022 & TT 38/2015), AEO Priority Enterprises & Risk Channeling (Luật HQ 2014 & TT 72/2015), and SXXK Duty Refund & BCQT 15 Reconciliation (NĐ 134/2016 & TT 39/2018).

9. **`src/cli/commands/fta_command.py`**:
   - Rich terminal interface with 10 subcommands (`savings`, `origin`, `proof`, `epe-check`, `on-spot`, `scrap`, `aeo`, `channel`, `refund-sxxk`, `bcqt`).
   - Aliased under both `fta` and `dncx`.

10. **`scripts/mcp_server.py`**:
   - Dual-protocol (FastMCP + JSON-RPC) tool definitions for agentic workflows (868+ tools active).
