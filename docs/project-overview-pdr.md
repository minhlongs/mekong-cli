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

### Phase 178: EU CBAM & EUDR Green Supply Chain Export Compliance
- **Regulatory Framework:** EU Regulation 2023/956 (CBAM), EU Regulation 2023/1115 (EUDR).
- **Features:**
  - Embedded emissions calculation: $\text{Total Emissions} = \text{Quantity} \times (\text{Scope 1} + \text{Scope 2})$.
  - Net CBAM financial liability computation adjusted for EU certificate benchmark and Vietnamese domestic carbon price offset ($5 \text{ EUR/tCO}_2\text{e}$).
  - EUDR closed GPS polygon coordinates verification (first vertex equals last vertex) for agricultural plots $\ge 4 \text{ ha}$.
  - Dec 31, 2020 deforestation cut-off date and land legal title compliance check.

## 3. Quality & Acceptance Criteria
- 100% Python Standard Library in `src/core/`.
- 100% test pass rate across unit, CLI, and MCP handlers.
- Both human-readable Rich output and JSON output (`--json`) available on CLI.
