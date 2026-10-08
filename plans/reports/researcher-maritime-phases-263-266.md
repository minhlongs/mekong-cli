# Research Report: Maritime Phases 263-266

## Executive Summary
This suite addresses four mission-critical commercial and statutory maritime operations under Vietnam Maritime Code (VMC) 2015, international conventions, and port regulations:
1. **Phase 263: Cargo Delivery under Letter of Indemnity (LOI) & Switch B/L Risk Management**
   - Statutory base: VMC 2015 Arts. 154, 160, 163; English Maritime Law (The Stettin, The Houda, The Giannis NK); International Group of P&I Clubs (IG P&I) Standard LOI Wording.
   - Core mechanics: Delivery without original B/L presentation or change of discharge port requires standard bank-endorsed LOI. P&I insurance cover is prejudiced/excluded for delivery without production of original B/L. Calculation evaluates financial guarantee adequacy (100% to 200% CIF cargo value), bank rating tiers (investment grade vs speculative), 6-year vs 1-year time-bar risks, and switch B/L misrepresentation liabilities.
2. **Phase 264: General Average (GA) Adjustment & York-Antwerp Rules 2016**
   - Statutory base: VMC 2015 Arts. 290-302; York-Antwerp Rules (YAR) 2016 Rules A-G, VI (Salvage), X/XI (Port of refuge), XX (2% commission), XXI (interest rate = ICE LIBOR/SOFR + 4%).
   - Core mechanics: Extraordinary sacrifice or expenditure voluntarily and reasonably incurred for common maritime adventure. Contributory values calculation: Ship (sound value less repair costs), Cargo (CIF value less damage/charges), Freight at risk. GA apportionment formula: $Contribution_i = ContributoryValue_i \times \frac{TotalGAAllowances}{TotalContributoryValue}$. Average Guarantee & Cash Deposit calculation.
3. **Phase 265: Ship Bunkering Bunker Delivery Note (BDN) & MARPOL Annex VI Fuel Sulfur Compliance**
   - Statutory base: MARPOL 73/78 Annex VI Regs. 14, 18; Circular 41/2020/TT-BGTVT; Circular 39/2023/TT-BGTVT; Resolution MEPC.320(74).
   - Core mechanics: Verification of BDN statutory retention (3 years) and fuel sample retention (12 months). Sulfur cap verification: Global 0.50% m/m, ECA / port emission control zone 0.10% m/m, scrubbers (EGCS) equivalent abatement ($SO_2/CO_2 \le 4.3$ ratio for 0.10%, $\le 21.7$ ratio for 0.50%). Calculation of non-compliant fuel penalties, de-bunkering costs, and FONAR (Fuel Oil Non-Availability Report) evaluation.
4. **Phase 266: Seaport Container Demurrage, Detention & Free Time Calculation under Decree 160/2016 & Circular 39/2023**
   - Statutory base: VMC 2015 Arts. 168, 172; Decree 160/2016/NĐ-CP; Circular 39/2023/TT-BGTVT; Circular 12/2024/TT-BGTVT; FIATA Best Practice.
   - Core mechanics: Split demurrage (port terminal storage beyond free time) and detention (carrier container equipment holding beyond free time). Calculation of tiered daily progressive penalty rates (Tier 1: Days 1-5, Tier 2: Days 6-10, Tier 3: Days 11+ at 150-200% rate), calendar days vs working days holidays exclusion, carrier maritime lien exercise on cargo under VMC Art. 168 when storage fees exceed cargo value.

## Architectural Constraints
- Pure Python standard library only (`dataclasses`, `enum`, `typing`, `json`, `datetime`, `math`).
- Zero external dependencies checked via AST invariant test.
- Bilingual CLI commands and FastMCP tools integration.
