# Maritime Suite: Phases 263-266 Final Integration Report

## Executive Summary
This report documents the completion of the 4-phase maritime compliance suite for **Mekong CLI v6.0**:
- **Phase 263**: Letter of Indemnity (LOI) & Switch B/L Risk Management Under Vietnam Maritime Code (VMC) 2015 Arts. 154, 160, 163 & International Group of P&I Clubs (IG P&I) Standard Wording.
- **Phase 264**: General Average (GA) Adjustment & York-Antwerp Rules 2016 Under VMC 2015 Arts. 290-302 and CMI York-Antwerp Rules 2016 (Rules A-G, VI, X, XI, XX, XXI).
- **Phase 265**: Bunker Delivery Note (BDN) & MARPOL Annex VI Fuel Sulfur Compliance Under MARPOL 73/78 Annex VI Regs. 14 & 18, Circular 41/2020/TT-BGTVT, and Circular 39/2023/TT-BGTVT.
- **Phase 266**: Seaport Container Demurrage & Detention (D&D) Progressive Tariffs Under VMC 2015 Arts. 168 & 172, Decree 160/2016/NĐ-CP, and Circular 39/2023/TT-BGTVT.

---

## 1. Statutory Architecture & Core Features

### Phase 263: Letter of Indemnity (LOI) & Switch B/L Risk Evaluation
- **Standard Wording Coverage**: Evaluates delivery without presentation of original Bills of Lading (B/L), change of discharge port, split B/L, and clean B/L issued against damaged cargo.
- **P&I Cover Prejudice Warning**: Automatic detection of P&I Club exclusion of liability for delivery without original B/L or deviation.
- **Bank Guarantee Discounting**:
  - `first_class_international_bank`: 100% security adequacy.
  - `local_commercial_bank`: 85% security adequacy.
  - `unsecured_corporate_only`: 15%-40% security adequacy (flagged high risk).
  - `no_bank_join`: 0% bank protection.
- **Fraud & Void Detection**: Flags *The Brown Jenkinson* precedent where issuing clean bills against damaged cargo is deemed commercial fraud and void under law.

### Phase 264: General Average (GA) Adjustment Calculator
- **York-Antwerp Rules 2016 Implementation**:
  - Base allowances: Ship sacrifices (damage, port of refuge, fuel/stores) + Cargo sacrifices (jettison) + Salvage awards + Adjuster/legal fees.
  - Rule XX: 2% cash disbursement commission.
  - Rule XXI: Interest at 7% p.a. (SOFR/LIBOR + 4%).
- **Contributory Interests**:
  - Ship net contributory value = Sound value - Repairs not GA + GA ship sacrifice.
  - Cargo net contributory value = CIF sound value - Non-GA damage + GA cargo sacrifice.
  - Freight net contributory value = Gross freight at risk - Contingent expenses.
- **Average Bond / Cash Deposit**: Automatically computes net balance per party and recommends Average Cash Deposit with a 20% safety margin.

### Phase 265: Bunker Delivery Note (BDN) & Sulfur Cap
- **Emission Standards**:
  - Global Open Ocean: $\le 0.50\% \text{ m/m}$ sulfur (IMO 2020 Sulfur Cap).
  - IMO ECA & Vietnamese Seaport Waters: $\le 0.10\% \text{ m/m}$ sulfur.
- **EGCS Scrubber Equivalence**: Checks SO2/CO2 continuous monitoring ratios ($\le 21.7$ for global, $\le 4.3$ for ECA/ports).
- **SOLAS Safety**: Flash point threshold $\ge 60^\circ\text{C}$ check (Regulation II-2/4.2.1).
- **Enforcement & Costs**: Calculates potential de-bunkering and MGO replacement costs upon violation and mandates statutory document retention (BDN 3 years, MARPOL sample 12 months).

### Phase 266: Demurrage & Detention (D&D) Progressive Tariffs
- **Progressive Brackets**:
  - Tier 1 (Days 1–5 overdue): Base tariff.
  - Tier 2 (Days 6–10 overdue): +50% surcharge.
  - Tier 3 (Days 11+ overdue): +100% surcharge.
- **Equipment & Terminal Segregation**: Terminal demurrage fees segregated from carrier equipment detention fees.
- **Maritime Lien Trigger**: When accumulated D&D charges exceed 70% of cargo CIF value, triggers statutory warning under VMC 2015 Art. 168.

---

## 2. Verification & Test Metrics
- **Test File**: `tests/test_maritime_loi_ga_bunker_demurrage_suite.py`
- **Total Tests**: 23 tests (100% passing).
- **Breakdown**:
  - Zero-dependency AST verification: PASSED.
  - LOI & Switch B/L assessments: 4 tests PASSED.
  - General Average adjustments & exceptions: 3 tests PASSED.
  - Bunker sulfur compliance & flash point: 4 tests PASSED.
  - Demurrage & detention progressive calculations & lien: 3 tests PASSED.
  - CLI commands execution: 4 tests PASSED.
  - MCP tool invocation handlers: 4 tests PASSED.
- **CLI Commands Available**: `loi`, `thuboiduong`, `ga`, `tonthatchung`, `bunker`, `nhienlieutau`, `demurrage`, `luubai`. Total command groups registered: **370 groups**.
- **MCP Server Tools Registered**: `mekong_loi_risk_evaluate`, `mekong_general_average_adjust`, `mekong_bunker_sulfur_compliance_check`, `mekong_demurrage_detention_calculate`. Total tools: **958 tools**, **1,878 handlers**.
