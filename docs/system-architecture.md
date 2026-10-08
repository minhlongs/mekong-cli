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

## 5. Port Operations, Labor Safety, Ship Waste & Remediation Escrow Architecture (Phases 227-230)

```
+---------------------------------------------------------------------------------------+
|        PORT TERMINAL STEVEDORING, LABOR SAFETY, SHIP WASTE & REMEDIATION ESCROW       |
+---------------------------------------------------------------------------------------+
                                           |
    +------------------+-------------------+-------------------+-------------------+
    |                  |                                       |                   |
    v                  v                                       v                   v
[Phase 227]        [Phase 228]                             [Phase 229]         [Phase 230]
Port Stevedoring   Marine Labor Safety                     Port Reception      Remediation Escrow
& Terminal Caps    & Enclosed Space Entry                  Facilities (AWN)    & Cleanup Bond
-----------------  ---------------------------             -----------------   -----------------
- VMC 2015 Arts    - IMO Res. A.1050(27) & SOLAS           - Cir 41/2020 AWN   - LEP 2020 Art 136
  214-224 Hague-     Ch. III Reg. 19 atmosphere:             24h pre-arrival     & Decree 08/2022
  Visby limits:      O2 >= 20.9%, LEL <= 1.0%,               notice rule       - Base: 18M VND/m3
  max(500 SDR/pkg,   H2S <= 5.0 ppm, CO <= 25.0 ppm        - Retention rule    - Persistence:
  2.0 SDR/kg)      - Mechanical ventilation >= 30m           Capacity >= 1.2x    1.8x / 1.4x / 1.0x
- Notice timebar:  - Mandatory gear: Calibrated gas          Generation to     - ESI Sensitivity:
  apparent: 0 days   detector, standby crew, harness         next port           1.0x / 1.3x / 2.0x
  concealed: 3 days- Law on OSH 2015 Art. 38 scale:        - 1.2M VND base fee - +20% restoration
- 365d (1y) bar      5-10% -> 1.5m, +0.4m/1% (11-80%),       + per-m3 tariffs    contingency buffer
- Gross reck-        >= 81% / death -> 30 months           - Waste Transfer    - Irrevocable bank
  lessness break                                             Note (WTN) receipt  guarantee required
+---------------------------------------------------------------------------------------+
|  Zero-dependency Python Core: src/core/maritime_portops_labor_waste_remediation_engine.py|
|  CLI Sub-apps: stevedore (bocxep), maritimesafety (antoanlaodong),                    |
|                portwaste (chatthaicang), remediationescrow (kiquymoitruong)           |
|  FastMCP Tools: mekong_stevedore_terminal_liability, mekong_marine_labor_safety_audit,|
|                 mekong_port_waste_reception_verify, mekong_maritime_remediation_escrow|
+---------------------------------------------------------------------------------------+
```

## 6. Maritime ISM Code SMS, Green Ship Recycling, Port Waste PRF & ISPS Security Architecture (Phases 243-246)

```
+---------------------------------------------------------------------------------------+
|          MARITIME ISM CODE SMS, SHIP RECYCLING, PORT WASTE & ISPS SECURITY SUITE      |
+---------------------------------------------------------------------------------------+
                                           |
    +------------------+-------------------+-------------------+-------------------+
    |                  |                                       |                   |
    v                  v                                       v                   v
[Phase 243]        [Phase 244]                             [Phase 245]         [Phase 246]
Maritime ISM SMS   Green Ship Recycling                    Port Reception      Seaport ISPS
& DPA Oversight    & IHM Compliance                        Facilities (PRF)    Maritime Security
-----------------  ---------------------------             -----------------   -----------------
- SOLAS Ch. IX &   - Hong Kong Convention 2009 &           - MARPOL Annex I-VI - ISPS Parts A & B
  IMO A.741(18)      EU SRR (EU) 1257/2013                   Circular 39/2023    SOLAS Ch. XI-2 &
- DOC / SMC        - Prohibited Table A substances:          indirect tariff:    Decree 58/2017
  5-year lifecycle   Asbestos (<=1000 mg/kg), ODS (0),       120 VND/GT/call   - Security Levels
  with +-90d audit   PCBs (<=50 mg/kg), Cybutryne            (1.5M - 18M VND)    1, 2, and 3
  window check     - Declarable Table B substances         - Mandatory PRF:    - Mandatory DoS:
- Major NC vessel  - 88% structural steel scrap &            fill >= 75% or      Level 3, Level
  suspension &       3.5% non-ferrous metals recovery        capacity < 1.25x    mismatch, DG,
  downgrade with   - Hazardous decontamination tariff        next leg buffer     or STS transfer
  90-day CAP dead-   deductions & net salvage value        - Sludge 950k/m3,   - TVC risk matrix
  line evaluation  - Decree 08/2022 & Decree 82/2019         Bilge 650k/m3       (TxVxC 1-125)
+---------------------------------------------------------------------------------------+
|  Zero-dependency Python Core: src/core/maritime_ism_recycling_waste_isps_engine.py    |
|  CLI Sub-apps: ismsafety (antoanism), shiprecycling (taichetau),                      |
|                portwaste (racbienthu), ispssecurity (anninhisps)                      |
|  FastMCP Tools: mekong_ism_safety_management_evaluate,                                |
|                 mekong_ship_recycling_ihm_evaluate,                                   |
|                 mekong_port_reception_waste_evaluate,                                 |
|                 mekong_isps_port_security_evaluate                                    |
+---------------------------------------------------------------------------------------+
```

## 7. Maritime Charterparty Speed & Consumption, e-D/O Deposit, Seaport Tonnage Dues & IMDG Handling Architecture (Phases 267-270)

```
+---------------------------------------------------------------------------------------+
|          MARITIME CHARTERPARTY, e-D/O, SEAPORT TONNAGE & IMDG HANDLING SUITE          |
+---------------------------------------------------------------------------------------+
                                           |
    +------------------+-------------------+-------------------+-------------------+
    |                  |                                       |                   |
    v                  v                                       v                   v
[Phase 267]        [Phase 268]                             [Phase 269]         [Phase 270]
Charterparty Speed Electronic Delivery                     Seaport Tonnage     IMDG Hazardous
& Consumption      Order (e-D/O) & Deposit                 & Safety Tariffs    Cargo Segregation
-----------------  ---------------------------             -----------------   -----------------
- NYPE 93/2015 &   - VMC 2015 Arts. 160 & 168              - TT 39/2023/BGTVT  - IMDG Code Amdt 41-22
  The Didymi &       Decree 58/2017 & VNSW                   & TT 12/2024/BGTVT  Table 7.2.4 Matrix
  The Gas Enterprise- Container equipment return           - Dual currency:    - Numerical codes 0-4
- "About" margins:   settlement (Dry 20/40, Reefer)          USD (Int'l) vs      (Away >=3m to
  -0.5 kts speed,  - Detention charges vs free               VND (Domestic)      Longitudinal >=24m)
  +5% fuel rate      days allowed                          - Tonnage dues:     - Mandatory direct
- Good weather     - IICL-5 damage deductions &              $0.034 / 350 VND    delivery dock dwell:
  eval (<= BF 4)     depot cleaning fee charges            - Safety dues:        max 2h (Cl. 1 & 7)
- Netting bunker   - Statutory 3-day refund                  $0.076 / 1,000 VND- Hazmat yard 48h
  savings vs time    settlement SLA (or balance            - 10% Green Award   - Stevedoring sur-
  loss claims        due on excessive damage)                vessel discount     charges (+50%-+200%)
+---------------------------------------------------------------------------------------+
|  Zero-dependency Python Core: src/core/maritime_charterparty_edo_tonnage_imdg_engine.py|
|  CLI Sub-apps: charterpartyspeed (tocdotau), edorelease (lenhgiaohang),               |
|                tonnagedues (phitrongtai), imdgport (hangnguyhiem)                     |
|  FastMCP Tools: mekong_charterparty_speed_consumption_evaluate,                       |
|                 mekong_edo_deposit_settlement_calculate,                             |
|                 mekong_seaport_tonnage_safety_dues_calculate,                         |
|                 mekong_imdg_port_safety_handling_evaluate                             |
+---------------------------------------------------------------------------------------+
```

## 8. Maritime Casualty Inquiry, e-C/O ROO, Seaport Tugboat Tariffs & SOLAS VGM Architecture (Phases 271-274)

```
+---------------------------------------------------------------------------------------+
|             MARITIME CASUALTY, e-C/O, SEAPORT TUG TARIFFS & SOLAS VGM SUITE           |
+---------------------------------------------------------------------------------------+
                                           |
    +------------------+-------------------+-------------------+-------------------+
    |                  |                                       |                   |
    v                  v                                       v                   v
[Phase 271]        [Phase 272]                             [Phase 273]         [Phase 274]
Casualty Inquiry   Electronic C/O                          Seaport Tugboat     SOLAS VGM
& Safety Board     Rules of Origin (ROO)                   Towage Tariffs      Container Weighing
-----------------  ---------------------------             -----------------   -----------------
- IMO MSC.255(84)  - Decree 31/2018/NĐ-CP &                - TT 39/2023/BGTVT  - SOLAS Reg. VI/2
  Circular 34/2015   Circular 05/2018/TT-BCT                 Section III &       IMO MSC.1/Circ.1475
  VMC Arts 113-116 - Multi-FTA support:                      TT 12/2024/BGTVT  - Methods 1 & 2
- 4 Casualty tiers:  EVFTA, CPTPP, RCEP, ATIGA,            - Dual-currency:    - Tolerance limits:
  VSMC, SMC,         VKFTA                                   USD (Int'l) vs      min(5%, 500 kg)
  MC, Incident     - RVC Build-Down:                         VND (Domestic)    - "No VGM, No Load"
- Timelines:         ((FOB - VNM) / FOB) * 100%            - 5 HP brackets:      strict gate check
  24h emergency,   - RVC Build-Up:                           <=1000 to >4000   - CSC Plate max
  48h port formal,   ((VOM + Direct) / FOB) * 100%         - Port Zones I-III    overload safety
  90d VSMC inquiry - CTH 4-digit shift evaluation          - Surcharges:       - Weighbridge fees:
- Mandatory Board  - De Minimis 10% tolerance rule           Night (+30%),       250k (20ft) /
  triggers (VSMC)  - Statutory e-C/O qualification           Hazmat (+30%),      350k (40ft)
                     verdict & preferential duty             Weather (+50%),
                                                             Standby (50% base)
+---------------------------------------------------------------------------------------+
|  Zero-dependency Python Core: src/core/maritime_casualty_co_tug_vgm_engine.py         |
|  CLI Sub-apps: casualty (tainan), coform (xuatxuhanghoa),                             |
|                tugtariff (laidatcang), solasvgm (xacnhankhoiluong)                    |
|  FastMCP Tools: mekong_marine_casualty_inquiry_evaluate,                              |
|                 mekong_electronic_co_origin_evaluate,                                 |
|                 mekong_seaport_tugboat_tariff_calculate,                              |
|                 mekong_solas_vgm_container_verify                                     |
+---------------------------------------------------------------------------------------+
```

## 9. MARPOL Fuel Switchover, Maritime Liens Waterfall, Berth Planning UKC & Customs VASSCM Architecture (Phases 275-278)

```
+---------------------------------------------------------------------------------------+
|        MARPOL FUEL SWITCHOVER, MARITIME LIENS, BERTH PLANNING & VASSCM SUITE         |
+---------------------------------------------------------------------------------------+
                                           |
    +------------------+-------------------+-------------------+-------------------+
    |                  |                                       |                   |
    v                  v                                       v                   v
[Phase 275]        [Phase 276]                             [Phase 277]         [Phase 278]
MARPOL Annex VI    Maritime Liens                          Berth Allocation    Customs Risk &
Fuel Switchover    Auction Waterfall                       Dynamic UKC & BOR   VASSCM Gate-Out
-----------------  ---------------------------             -----------------   -----------------
- MARPOL VI Reg. 14- VMC 2015 Arts. 37-43 &                - Decree 58/2017 &  - Law on Customs 2014
  MEPC.1/Circ.864    Decree 62/2015 Enforcement              PIANC Report 158    Decisions 1399 & 2185
  TT 39/2023/BGTVT - 1st priority: court costs &           - Slot safety length- Multi-factor R-score:
- Exponential mixing custody expenses ($P_{net}$)            LOA + max(15m,10%)  0.40*E + 0.35*H + 0.25*O
  dilution duration- 5 statutory lien tiers (VMC 37):      - Harmonic tide     - 3-Channel routing:
  t_dilution         Tier 1: Crew wages & repatriation       prediction h(t)     Green (R<0.35, <5s)
- Thermal ramp limit Tier 2: Life loss & personal injury   - Barass squat:       Yellow (0.35<=R<0.70)
  <= 2.0 C/min       Tier 3: Salvage (inverse order)         (Cb*Brat*V^2)/(30K) Red (R>=0.70 / alert)
- Critical time:     Tier 4: Port dues & safety dues       - Salinity sinkage: - VASSCM 3-way match:
  max(t_dil, t_therm)Tier 5: Collision tort damages         Draft*(1.025-p)/p   Decl RELEASED +
- Required distance- Subordinated: ship mortgage           - Dynamic UKC check:  e-D/O valid +
  d_req = t_crit * V - Lowest: unsecured pro-rata split      >= max(10% d,0.6m)  Manifest seal == Gate
- ISO 8217 visc:   - 1-year statutory timebar (VMC 39)     - PIANC BOR target: - SHA-256 clearance token
  >= 2.0 cSt         extinguishes unarrested liens           congestion > 65%    & gate-out auth hash
+---------------------------------------------------------------------------------------+
|  Zero-dependency Python Core: src/core/maritime_fuel_liens_berth_customs_engine.py    |
|  CLI Sub-apps: fuelswitch (doinhienlieu), maritimeliens (daugiahanghai),              |
|                berthplan (dieudocau), customsvasscm (haiquancang)                     |
|  FastMCP Tools: mekong_marpol_fuel_switchover_calculate,                              |
|                 mekong_maritime_lien_waterfall_distribute,                            |
|                 mekong_berth_allocation_ukc_evaluate,                                 |
|                 mekong_customs_risk_vasscm_verify                                     |
+---------------------------------------------------------------------------------------+
```

## 11. Maritime Garbage Discharge, STCW Rest, Port Wharfage & CFS E-Seal Architecture (Phases 287-290)

```
+---------------------------------------------------------------------------------------+
|       MARPOL GARBAGE, STCW REST HOURS, PORT WHARFAGE & CFS E-SEAL LOGISTICS SUITE     |
+---------------------------------------------------------------------------------------+
                                           |
    +------------------+-------------------+-------------------+-------------------+
    |                  |                                       |                   |
    v                  v                                       v                   v
[Phase 287]        [Phase 288]                             [Phase 289]         [Phase 290]
MARPOL Annex V     STCW 2010 Manila &                      Circular 39/2023    Customs Bonded CFS &
Garbage Management MLC 2006 Rest Hours                     Wharfage Tariffs    E-Seal Telemetry
-----------------  ---------------------------             -----------------   -----------------
- Regs. 3, 4, 5, 6 - STCW Table A-VIII/1 &                 - TT 39/2023/BGTVT  - Law on Customs 2014
  MEPC.295(71)       MLC 2006 Standard A2.3                  TT 12/2024/BGTVT    Decree 08/2015
  VMC Arts 107-111 - 24-Hour statutory rule:               - Multi-area tiers: - Statutory 90-day cap,
- Total bans:        Rest >= 10.0h in 24h                    Area I North 0.95x  extendable once +90d
  Plastics, cooking  Max 2 periods in 24h                    Area II Central 0.90x (180 days max)
  oil, ashes, HME    Longest period >= 6.0h                  Area III South 1.0x- Expiring warning:
- Food waste:        Gap between rests <= 14.0h            - Berth types:        <= 15 days remaining
  Comminuted (<=25mm)- Rolling 7-Day rule:                   Container: $0.0035- E-Seal integrity:
  >= 3 NM (OSA),     Total rest >= 77.0h                     General: $0.0031    Cable cut / tamper
  >= 12 NM (SA)    - Emergency exception:                    Liquid: $0.0042     sensor triggers
  En-route >= 0.5kts Emergency, SAR & drills                 Buoy: $0.00175      quarantine alert
- Animal carcasses:  automated compensatory rest           - Surcharges:       - Telemetry alerts:
  >= 100 NM & >= 100m- Zero-tolerance non-compliant         Overstay laytime    Corridor dev > 500m
- GRB log Part I/II  audit flag                              (+50%), Holiday(+30%)GPS signal lost >30m
+---------------------------------------------------------------------------------------+
|  Zero-dependency Python Core: src/core/maritime_garbage_stcw_wharfage_cfs_engine.py   |
|  CLI Sub-apps: garbage (quanlyrac), resthours (gionghithuyenvien),                    |
|                wharfage (cuoccauben), cfseseal (khohangcfs)                           |
|  FastMCP Tools: mekong_marpol_garbage_discharge_evaluate,                             |
|                 mekong_stcw_seafarer_rest_verify,                                     |
|                 mekong_port_wharfage_tariff_calculate,                                |
|                 mekong_cfs_eseal_supervision_evaluate                                 |
+---------------------------------------------------------------------------------------+
```
