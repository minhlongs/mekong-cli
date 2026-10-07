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

10. **`src/core/ecom_inspect_engine.py`**:
   - Zero-dependency Python standard library implementation.
   - Enforces statutory rules for Cross-Border E-Commerce Customs Management (Decision 78 repeal, platform withholding, anti-structuring), Hazardous Chemicals NSW & IMDG/IATA Dangerous Goods (Decree 113/2017 & 82/2022), Specialized Food Safety & Quarantine Inspection (Decree 15/2018), and EU CBAM & EUDR Green Supply Chain Export Compliance (EU Reg 2023/956 & 2023/1115).

11. **`src/cli/commands/ecom_inspect_command.py`**:
   - Rich terminal interface for e-commerce tax, parcel fraud detection, chemical declarations, food inspection tiering, and CBAM/EUDR compliance.
   - Aliased under `ecom` and `inspect` (`tmdt`, `kiemtra`).

12. **`src/core/port_supply_chain_engine.py`**:
    - Zero-dependency Python standard library implementation.
    - Enforces statutory rules for Seaport Terminal Tariffs (Circular 39/2023/TT-BGTVT), Demurrage & Detention with Carrier Maritime Liens (Vietnam Maritime Code 2015 Art. 168), SOLAS VGM gate-in validation (MSC.1/Circ.1475), L/C document examination & usance discounting (ICC UCP 600 / ISBP 745), Pharma cold chain Arrhenius MKT integration (Circular 02/2018/TT-BYT), and ISO 14083 / GLEC v3.0 multimodal freight carbon accounting.

13. **`src/cli/commands/port_supply_chain_command.py`**:
    - Rich terminal interfaces with `port` (`cangbien`) and `tradefinance` (`scf`).

14. **`src/core/maritime_operations_engine.py`**:
    - Zero-dependency Python standard library implementation.
    - Enforces statutory rules for Maritime Pilotage & Tugboat Assistance Tariffs (Circular 39/2023/TT-BGTVT), Ship Husbandry Agency Disbursement & Seafarer MLC 2006 Rest Hours Auditing (Decree 160/2016/NĐ-CP & MLC 2006 Reg. 2.1/2.3), Marine Hull Insurance ITC Hulls 83 Constructive Total Loss (80% threshold + 180-day Notice of Abandonment under Vietnam Maritime Code 2015 Art. 326) & P&I Bunker Pollution SDR Limits (Bunkers Convention 2001), and Port State Control (PSC) Tokyo MOU NIR Ship Risk Profile (LRS/SRS/HRS) & Code 30 Detention Risk Matrix.

15. **`src/cli/commands/maritime_operations_command.py`**:
    - Rich terminal interfaces with 4 command groups: `pilotage` (`hoatieu`), `shipagency` (`daily`), `marineins` (`baohiemhanghai`), `psc` (`kiemtratau`).

16. **`scripts/mcp_server.py`**:
    - Dual-protocol (FastMCP + JSON-RPC) tool definitions for agentic workflows (890+ tools active).

## 3. Vietnam Port Terminal, SCF & Cold Chain Architecture (Phases 179-182)

```
+---------------------------------------------------------------------------------------+
|                    VIETNAM SEAPORT, TRADE FINANCE & SUPPLY CHAIN SUITE                |
+---------------------------------------------------------------------------------------+
                                           |
    +------------------+-------------------+-------------------+-------------------+
    |                  |                                       |                   |
    v                  v                                       v                   v
[Phase 179]        [Phase 180]                             [Phase 181]         [Phase 182]
Seaport Operations Cross-Border SCF                        Cold Chain Pharma   Multimodal Carbon
& SOLAS VGM        & UCP 600 L/C                           GDP & Arrhenius MKT Accounting
-----------------  ---------------------------             -----------------   -----------------
- TT 39/2023 THC   - ICC UCP 600 Art 14 5-day              - TT 02/2018/TT-BYT - ISO 14083:2023
  tariff Area I-III  examination rule                        Arrhenius MKT       GLEC v3.0 WTW
- Reefer 85k VND/h - 5-Rule Discrepancy detector             integration         multimodal GHG
- DEM/DET 3-tier   - Act/360 Usance L/C discount           - Freezing breach   - Modal shift
- Art 168 lien       with Term SOFR + spread                 hold disposition    valuation @
- SOLAS VGM gate                                           - Degree-hours        125k VND/tCO2e
+---------------------------------------------------------------------------------------+
|  Zero-dependency Python Core: src/core/port_supply_chain_engine.py                    |
|  CLI Sub-apps: mekong port (cangbien) & mekong tradefinance (scf)                     |
|  Dual MCP Tools: mekong_port_* & mekong_tradefinance_*                                |
+---------------------------------------------------------------------------------------+
```

## 4. Vietnam Maritime Operations, Pilotage, P&I & Tokyo MOU PSC Architecture (Phases 183-186)

```
+---------------------------------------------------------------------------------------+
|            VIETNAM MARITIME OPERATIONS, HUSBANDRY, INSURANCE & PSC SUITE              |
+---------------------------------------------------------------------------------------+
                                           |
    +------------------+-------------------+-------------------+-------------------+
    |                  |                                       |                   |
    v                  v                                       v                   v
[Phase 183]        [Phase 184]                             [Phase 185]         [Phase 186]
Maritime Pilotage  Ship Husbandry Agency                   Marine Insurance    Tokyo MOU Port State
& Tugboat Tariffs  & Seafarer MLC 2006                     H&M CTL & P&I SDR   Control (PSC) NIR
-----------------  ---------------------------             -----------------   -----------------
- TT 39/2023 GT-NM - NĐ 160/2016 Agency fee                - ITC Hulls 83      - Tokyo MOU NIR
  tariff Area I-III  schedules & prolonged stay              Particular vs CTL   Ship Risk Profile
- Surcharges: night- 1.5% Cash-to-Master                   - 80% CTL threshold   (LRS / SRS / HRS)
  (+50%), hazardous  commission + crew handling              + 180d Notice of  - Generic & Historic
  (+10%), dead ship- MLC 2006 Standard A2.3                  Abandonment (Art    risk scoring
  (+150%)            rest audit (>=10h/24h,                  326 VN Maritime)  - Deficiency code
- Tugboat Class A-E  >=77h/7d, max 2 blocks)               - Bunkers 2001        evaluation &
  with min 2h rule - 11-month (330d) statutory               Tiered SDR limit    Code 30 Detention
  and weekend +30%   mandatory repatriation                  calculation         risk triggers
+---------------------------------------------------------------------------------------+
|  Zero-dependency Python Core: src/core/maritime_operations_engine.py                  |
|  CLI Sub-apps: pilotage (hoatieu), shipagency (daily), marineins (baohiemhanghai),    |
|                psc (kiemtratau)                                                       |
|  Dual MCP Tools: mekong_pilotage_*, mekong_shipagency_*, mekong_marineins_*,          |
|                  mekong_psc_*                                                         |
+---------------------------------------------------------------------------------------+
```
