# Product Development Requirements (PDR) — Dispute Resolution & Maritime Law Suite

**Phase Target:** Phases 159 - 162  
**Status:** Completed & Tested (100% Pass)  
**Target User:** Vietnamese enterprises, legal counsels, shipping operators, cargo owners, and general counsel.

---

## 1. Executive Summary

Provides automated legal calculations, jurisdictional assessments, and liability limitations under Vietnamese Civil and Commercial Law and International Maritime Conventions.

## 2. Scope & Key Features

### Phase 159: Commercial Arbitration & VIAC 2024
- **Regulatory Framework:** Law on Commercial Arbitration 2010, VIAC Arbitration Rules 2024, Decision 89/QĐ-VIAC.
- **Features:**
  - Clause validity check (Articles 16 & 18).
  - 6-tier VIAC fee calculator with Sole Arbitrator discount (30% reduction).
  - 2-year arbitration statute of limitations tracker (Article 33).

### Phase 160: Civil Judgment Enforcement (THADS)
- **Regulatory Framework:** Law on Civil Judgment Enforcement 2008/2014, Circular 216/2016/TT-BTC.
- **Features:**
  - 5-year enforcement limitation check (Article 30).
  - 3% fee calculator with statutory 200M VND ceiling.
  - Multi-tier statutory payment distribution sequence (Article 47).

### Phase 161: Court Litigation & Civil Procedure
- **Regulatory Framework:** Civil Procedure Code 2015 (BLTTDS), Resolution 326/2016/UBTVQH14.
- **Features:**
  - Jurisdiction assignment (District vs Provincial).
  - 6-bracket first-instance court fee scale.
  - 50% court fee advance calculation.

### Phase 162: Maritime Law & Shipping
- **Regulatory Framework:** Vietnam Maritime Code 2015, Hague-Visby SDR Protocol 1979, York-Antwerp Rules 2016.
- **Features:**
  - Carrier cargo liability limitation: $\max(666.67 \text{ SDR/package}, 2.0 \text{ SDR/kg}) \times \text{SDR rate}$.
  - General Average (Tổn thất chung) distribution engine with zero-sum equilibrium guarantee.
  - Salvage reward evaluation ("No Cure No Pay", capped by property value).
  - Statutory ranking of maritime claims & liens (Articles 40-41).

### Phase 163: Multimodal Transport Operator (MTO)
- **Regulatory Framework:** Decree 87/2009/ND-CP, Decree 144/2018/ND-CP.
- **Features:**
  - Unlocalized loss limit: $\max(666.67 \text{ SDR/package}, 2.0 \text{ SDR/kg})$ with sea leg; $8.33 \text{ SDR/kg}$ for inland only.
  - Delay in delivery compensation capped at $2 \times \text{freight charge}$.
  - 9-month limitation period calculation (Article 29).

### Phase 164: Civil Aviation Carrier Liability
- **Regulatory Framework:** Law on Civil Aviation of Vietnam 2006/2014, Montreal Convention 1999 (2019 ICAO limits).
- **Features:**
  - Passenger bodily injury: Tier 1 strict liability (128,821 SDR); Tier 2 fault-based unlimited.
  - Cargo destruction, loss or delay: 22.0 SDR per kg gross weight.
  - Baggage destruction or delay: 1,288 SDR per passenger.
  - Passenger flight delay: 5,346 SDR per passenger.
  - 2-year extinction of action limitation period (Article 173).

### Phase 165: CISG 1980 & Incoterms 2020
- **Regulatory Framework:** UN CISG 1980, ICC Incoterms 2020.
- **Features:**
  - Fundamental breach evaluation (Article 25) & contract avoidance entitlement (Articles 49 & 64).
  - Price reduction formula for non-conforming goods (Article 50).
  - Complete 11 Incoterms 2020 definitions with risk transfer point and insurance rules (CIP ICC A 110%, CIF ICC C 110%).

### Phase 166: Vietnamese Trade Remedies & Anti-Dumping
- **Regulatory Framework:** Law on Foreign Trade Management 2017, Decree 10/2018/ND-CP.
- **Features:**
  - Dumping margin calculation: $DM = \frac{NV - EP}{EP} \times 100\%$.
  - De minimis threshold ($DM < 2.0\%$) and negligible volume exemption ($< 3.0\%$).
  - 5-year maximum duty duration evaluation.
  - Safeguard sudden import surge assessment.

### Phase 171: Vietnam FTAs Preferential Tariffs & Rules of Origin
- **Regulatory Framework:** EVFTA (NĐ 115/2022), CPTPP (NĐ 116/2022), RCEP (NĐ 129/2022), ATIGA (NĐ 126/2022).
- **Features:**
  - Preferential tariff savings calculation: $\text{Savings} = V_{\text{customs}} \times (\text{Rate}_{\text{MFN}} - \text{Rate}_{\text{FTA}})$.
  - Rules of Origin (ROO) evaluations: Wholly Obtained (WO), CTC (CC/CTH/CTSH), Regional Value Content (RVC >= 40%), and De Minimis (<= 10% FOB).
  - Proof of origin determination: REX self-certification (<= 6,000 EUR), EUR.1, CPTPP self-certification, ATIGA Form D.

### Phase 172: Export Processing Enterprises (EPE) & Industrial Parks
- **Regulatory Framework:** Decree 35/2022/NĐ-CP (Article 26), Circular 38/2015/TT-BTC (Articles 75 & 86), Circular 39/2018/TT-BTC.
- **Features:**
  - Verification of 4 mandatory customs supervision criteria (fence, 24/7 camera streaming, separate gate, ERP inventory).
  - Tracking 15-working-day counterpart declaration deadline for on-spot import/export transactions.
  - Calculation of import duty and VAT for domestic sales of scrap under declaration form A42.

### Phase 173: Authorized Economic Operator (AEO) & Risk Channeling
- **Regulatory Framework:** Law on Customs 2014 (Article 42), Circular 72/2015/TT-BTC, Circular 07/2019/TT-BTC, Decision 1399/QĐ-TCHQ.
- **Features:**
  - Statutory turnover threshold evaluations ($100M general trader, $40M agri/textile, $30M high-tech, 20,000 broker declarations).
  - 2-year clean compliance check and unqualified audit opinion verification.
  - Automated risk channeling into Green (0.05h clearance), Yellow (documentary), and Red (physical inspection).

### Phase 174: Duty Exemption, Refund & BCQT 15 Reconciliation
- **Regulatory Framework:** Decree 134/2016/NĐ-CP (Articles 34 & 36), Circular 39/2018/TT-BTC (Form 15/BCQT-NVL/GSQL), Law on Tax Administration 2019.
- **Features:**
  - Duty refund calculation for raw materials imported for production of exported goods (SXXK).
  - Unused re-export refund calculation.
  - Electronic material reconciliation balancing theoretical closing balance against physical counts with 0.03%/day late payment interest on deficit arrears.

### Phase 175: Cross-Border E-Commerce Customs & Fraud Detection
- **Regulatory Framework:** Decree 134/2016/NĐ-CP (Article 29), Decision 78/2010/QĐ-TTg (Repealed), Circular 80/2021/TT-BTC, Law on Tax Administration 2019.
- **Features:**
  - De minimis import duty exemption for parcel customs value $\le 1,000,000 \text{ VND}$.
  - 100% VAT liability payable from $0 \text{ VND}$ customs value following Decision 78 repeal.
  - Marketplace platform tax withholding & remittance deduction (Shopee, Lazada, TikTok Shop).
  - 72-hour sliding window order-splitting fraud detection for single-recipient parcels.

### Phase 176: Hazardous Chemicals Import Declaration via NSW & Dangerous Goods Segregation
- **Regulatory Framework:** Decree 113/2017/NĐ-CP & Decree 82/2022/NĐ-CP (Annexes I-V), IMDG Code 41-22 Table 7.2.4, IATA DGR.
- **Features:**
  - Automated classification against Annexes I, II, III, IV, and V.
  - Annex III strict prohibition enforcement & Annex II MOIT license verification.
  - Annex IV $\ge 50,000 \text{ kg}$ threshold check for mandatory Chemical Incident Prevention & Response Plan.
  - National Single Window (VNSW) electronic clearance token generation.
  - IMDG Code 41-22 co-loading dangerous goods segregation matrix (Away from 3m, Separated 6m, Compartment 12m, Longitudinal 24m, Forbidden 999m).

### Phase 177: Specialized Food Safety & Quarantine Inspection
- **Regulatory Framework:** Decree 15/2018/NĐ-CP (Articles 16-20), Circular 25/2016/TT-BNNPTNT, Circular 33/2014/TT-BNNPTNT.
- **Features:**
  - 3-tier food inspection methods (Reduced $\le 5\%$, Normal 100% dossier, Tightened 100% lab testing).
  - 3-consecutive-batch dynamic transition state machine with HACCP / ISO 22000 certification fast-track.
  - Quarantine certificate statutory validity tracking (Animal products $\le 15$ days, Plant products $\le 30$ days).

### Phase 179: Vietnam Seaport Terminal Operations, Port Tariffs, DEM/DET & SOLAS VGM
- **Regulatory Framework:** Circular 39/2023/TT-BGTVT, Vietnam Maritime Code 2015 (Art. 168), IMO SOLAS Ch. VI Reg. 2, MSC.1/Circ.1475, Decree 142/2017/NĐ-CP.
- **Features:**
  - Automated port tariff (THC) calculation for 20ft/40ft/45ft containers, specialized reefer electricity surcharges, dangerous goods multipliers, and Out-of-Gauge flat-rack adjustments.
  - 3-tier sliding scale Demurrage & Detention (DEM/DET) engine.
  - Statutory carrier cargo lien enforcement for penalties $\ge$ 50% CIF value or overdue $> 25$ days.
  - SOLAS VGM gate-in validation with $\pm$ tolerance lockout and re-weighing penalty automation.

### Phase 180: Cross-Border Trade Finance & L/C Strict Compliance
- **Regulatory Framework:** ICC UCP 600, ISBP 745.
- **Features:**
  - 5-rule discrepancy detector (Shipment, Expiry, Stale B/L, Invoice Description Mismatch, Amount Overdrawn).
  - Usance L/C discounting engine with Act/360 day-count and Term SOFR spread.

### Phase 181: Pharmaceutical Cold Chain GDP & Arrhenius MKT
- **Regulatory Framework:** Circular 02/2018/TT-BYT.
- **Features:**
  - Numerical Arrhenius integration for Deep Frozen, Cold Chain, and CRT stability budgets.
  - Mandatory quarantine hold dispositions based on excursion severity.

### Phase 182: Multimodal Freight Carbon Accounting & Scope 3
- **Regulatory Framework:** ISO 14083:2023 (GLEC v3.0), Decree 06/2022/NĐ-CP.
- **Features:**
  - WTW multimodal GHG aggregation (Road, Barge, Feeder, Rail, Air).
  - Modal shift financial valuation based on 125,000 VND/tCO2e offset price.

### Phase 183: Maritime Pilotage & Harbor Tugboat Assistance Tariffs
- **Regulatory Framework:** Circular 39/2023/TT-BGTVT, Decree 142/2017/NĐ-CP.
- **Features:**
  - GT-NM unit tariff calculator across Area I (North), Area II (Central), Area III (South / Cái Mép), and Offshore oil rigs.
  - Surcharge matrices: Night shift (+50%), Hazardous/oil tanker (+10%), Dead ship towing without engine (+150%), Pilot waiting detention fee ($10.0/h after 1h free).
  - Harbor Tugboat Assistance tariffs (Classes A-E from <1,000 HP to >4,000 HP) with mandatory 2-hour minimum billing rule and holiday/weekend (+30%) surcharges.

### Phase 184: Ship Husbandry Agency Disbursement & Seafarer MLC 2006 Compliance
- **Regulatory Framework:** Decree 160/2016/NĐ-CP, Decree 86/2020/NĐ-CP, Maritime Labour Convention (MLC 2006 Standard A2.3 & Reg. 2.1/2.5).
- **Features:**
  - Standard disbursement schedule calculation (base agency fee, prolonged stay $150/day beyond 3 days, crew change handling fees, and 1.5% Cash-to-Master commission).
  - Seafarer rest hours fatigue auditor enforcing daily $\ge 10\text{h}/24\text{h}$, 7-day $\ge 77\text{h}/7\text{d}$, max 2 rest intervals, and continuous rest block $\ge 6\text{h}$.
  - Continuous sea service duration tracker triggering mandatory repatriation alerts at 11 months (330 days).

### Phase 185: Marine Insurance (H&M / P&I) & Constructive Total Loss (CTL)
- **Regulatory Framework:** Institute Time Clauses Hulls 1/10/83 (ITC Hulls 83), Vietnam Maritime Code 2015 (Art. 326), Bunkers Convention 2001.
- **Features:**
  - Hull & Machinery (H&M) claim adjuster deducting policy deductible for Particular Average.
  - Constructive Total Loss (CTL) evaluation against statutory 80% casualty threshold.
  - 180-day statutory Notice of Abandonment deadline calculation with countdown tracker.
  - Protection & Indemnity (P&I) bunker oil spill pollution statutory liability limits using tiered SDR schedule under Bunkers Convention 2001.

### Phase 186: Port State Control (PSC) Tokyo MOU NIR & Deficiency Matrix
- **Regulatory Framework:** Tokyo MOU Port State Control Manual, New Inspection Regime (NIR), IMO SOLAS / MARPOL / MLC Conventions.
- **Features:**
  - New Inspection Regime Ship Risk Profile (SRP) scoring engine aggregating Generic (vessel type, age, flag black/grey/white list, RO performance) and Historic (detentions, deficiencies in last 36m) risk points into LRS, SRS, and HRS tiers.
  - Dynamic inspection window scheduling (LRS: 9-18 months, SRS: 5-8 months, HRS: 2-4 months).
  - Deficiency severity evaluator detecting serious SOLAS Ch. II-2 fire safety, MARPOL oily water, and MLC living condition non-compliances, automatically issuing Code 30 Detention orders.

## 3. Quality & Acceptance Criteria
- 100% Python Standard Library in `src/core/`.
- 100% test pass rate across unit, CLI, and MCP handlers.
- Both human-readable Rich output and JSON output (`--json`) available on CLI.
