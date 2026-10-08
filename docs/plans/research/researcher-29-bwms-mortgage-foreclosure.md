# Research Report: Ballast Water Management (BWMS) & Ship Mortgage Foreclosure (Phases 279-280)

## Executive Summary
This report formalizes statutory frameworks, physical/chemical stoichiometry, risk mitigation algorithms, and lien priority waterfalls for:
1. **Phase 279: Ballast Water Management System (BWMS) D-2 Compliance, Commissioning Testing & Salinity Exchange Engine** (IMO BWM Convention Regs. D-1/D-2, BWM.2/Circ.70/Rev.1, Circular 39/2023/TT-BGTVT).
2. **Phase 280: Ship Mortgage Enforcement, Private Sale vs Judicial Auction & Escrow Proceeds Distribution Engine** (Vietnam Maritime Code 2015 Arts. 31-36, Decree 58/2017/NĐ-CP, Decree 21/2021/NĐ-CP, Civil Code 2015 Art. 468).

---

## 1. Phase 279: BWMS D-2 Compliance, Commissioning & Salinity Exchange Engine

### 1.1 Statutory Framework & Legal Gates
- **IMO BWM Convention 2004**: Entry into force Sept 8, 2017; full D-2 enforcement mandated by Sept 8, 2024 (IOPPC renewal cut-off).
- **Reg. D-1 (Ballast Water Exchange Standard)**: Volumetric exchange efficiency $\ge 95\%$. Geographic gate: $\ge 200\text{ NM}$ from nearest land and $\ge 200\text{m}$ water depth. Fallback gate: $\ge 50\text{ NM}$ and $\ge 200\text{m}$ depth. In port state designated exchange areas where neither is feasible.
- **Reg. D-2 (Ballast Water Performance Standard)**: Viable organism limits:
  - $\ge 50\,\mu\text{m}$ (macro-organisms/zooplankton): $< 10\text{ viable organisms}/\text{m}^3$.
  - $10 - 50\,\mu\text{m}$ (micro-algae/phytoplankton): $< 10\text{ viable organisms}/\text{mL}$.
  - Indicator Microbes:
    - Toxicogenic *Vibrio cholerae* (O1 and O139): $< 1\text{ cfu}/100\text{ mL}$ (or $< 1\text{ cfu}/1\text{ g}$ wet weight zooplankton).
    - *Escherichia coli*: $< 250\text{ cfu}/100\text{ mL}$.
    - Intestinal *Enterococci*: $< 100\text{ cfu}/100\text{ mL}$.
- **BWM.2/Circ.70/Rev.1**: Mandatory commissioning testing during initial/additional survey; representative indicative and detailed biological sampling.
- **Circular 39/2023/TT-BGTVT**: Vietnam port dues, environmental monitoring charges, and port state control (PSC) discharge certification.

### 1.2 Mathematical & Chemical Formulations
1. **Volumetric Exchange Methods (Reg. D-1)**:
   - *Sequential (Empty/Refill)*: $E_{\text{vol}} = 1.0 - (V_{\text{residual}} / V_{\text{total}}) \ge 0.95$.
   - *Flow-Through / Dilution ($3\times$ pump capacity)*:
     $$E_{\text{dilution}} = 1.0 - e^{-N_{\text{flushes}}} \quad \text{for } N_{\text{flushes}} = 3.0 \implies 1.0 - e^{-3} \approx 95.02\%$$
2. **TRO Neutralization Stoichiometry (Electrochlorination / Chemical BWMS)**:
   - Primary active oxidant: Sodium hypochlorite ($\text{NaOCl}$) / Total Residual Oxidant ($\text{TRO}$, measured as $\text{Cl}_2$ equivalent).
   - Neutralizing agent: Sodium bisulfite ($\text{NaHSO}_3$, MW 104.06 g/mol) or Sodium thiosulfate ($\text{Na}_2\text{S}_2\text{O}_3$, MW 158.11 g/mol).
   - Stoichiometric reaction: $\text{NaOCl} + \text{NaHSO}_3 \to \text{NaCl} + \text{NaHSO}_4$.
   - Chlorine eq: $1\text{ mol } \text{Cl}_2 \ (70.9\text{ g}) \equiv 1\text{ mol } \text{NaHSO}_3 \ (104.06\text{ g}) \implies \text{mass ratio } R_{\text{stoich}} \approx 1.468\text{ g } \text{NaHSO}_3/\text{g } \text{Cl}_2$.
   - Safety factor overdosing multiplier: $k_{\text{safety}} \in [1.10, 1.30]$.
   - Dosing rate: $\dot{M}_{\text{neutralizer}} = Q_{\text{discharge}} \times C_{\text{TRO, raw}} \times R_{\text{stoich}} \times k_{\text{safety}}\text{ (g/h)}$.
   - Discharge constraint: $C_{\text{TRO, discharge}} \le 0.10\text{ mg/L}$ (BWM Convention G9 maximum allowable discharge concentration - MADC).
3. **PSC Contingency Protocols (BWM.2/Circ.62)**:
   - On D-2 equipment trip/fault:
     1. Internal retention (no deballasting permitted).
     2. Open sea mid-ocean exchange fallback (Reg. D-1 compliance) prior to port arrival.
     3. Discharge to port reception facility (PRF) / mobile treatment barge.
     4. Deballasting in port authority designated contingency offshore deep-water zone.

---

## 2. Phase 280: Ship Mortgage Enforcement, Sale & Waterfall Engine

### 2.1 Statutory & Jurisdictional Framework
- **Vietnam Maritime Code 2015 Arts. 31-36**:
  - *Art. 31*: Mortgage of Vietnamese sea-going ship takes effect upon registration in the Vietnam National Register of Ships (*Sổ đăng ký tàu biển quốc gia Việt Nam*). Certified extract/transcript (*Bản trích lục*) establishes definitive perfection.
  - *Art. 32*: Priority of multiple mortgages determined strictly by the chronologic order of registration.
  - *Art. 34 (Enforcement & Notice)*: Mortgagee has the right to enforce mortgage if debtor defaults. Mandatory statutory requirement: Mortgagee must deliver written demand notice to shipowner and co-mortgagees $\ge 15\text{ days}$ prior to disposal.
  - *Art. 35 (Disposal Methods)*: Private agreed sale (*Bán thỏa thuận*) vs Judicial auction (*Đấu giá theo thủ tục thi hành án/tòa án*).
- **Decree 58/2017/NĐ-CP & Decree 21/2021/NĐ-CP**: Perfection and enforcement procedures of security interests over movable maritime assets.
- **Civil Code 2015 Art. 468**: Statutory interest rate cap on private loans $\le 20\%/\text{year}$. (Exception: Credit institutions governed by Law on Credit Institutions 2024 Art. 10 / Circular 39/2016/TT-NHNN, allowing agreed commercial rates, capped at $150\%$ of normal rate for overdue principal).

### 2.2 Forensic Escrow Proceeds Distribution Waterfall
Proceeds from judicial ship sale or private mortgage liquidation must be partitioned in strict lexicographic order pursuant to VMC 2015 Arts. 35, 37-43:
1. **Tier 0 (Enforcement & Custody Costs)**: Court filing fees, marshal fees, port custody/berthage, bailiff appraisal, and auction house commissions.
2. **Tier 1 to 5 (Statutory Maritime Liens - VMC Art. 37)**: Subrogates and primes ALL registered mortgages:
   - *Lien 1*: Crew wages, repatriation, social insurance contributions.
   - *Lien 2*: Life & bodily injury compensation.
   - *Lien 3*: Salvage rewards & General Average contributions.
   - *Lien 4*: Port dues, pilotage, maritime safety fees, channel tolls.
   - *Lien 5*: Tortious physical collision damages.
3. **Tier 6 (Senior Registered Mortgage - 1st Mortgage)**: Principal, contractually compliant interest, and collection costs according to registration timestamp.
4. **Tier 7 (Subordinated Mortgages - 2nd/3rd Mortgage)**: Ordered strictly by registration sequence.
5. **Tier 8 (Unsecured Maritime Claims)**: Ship repairers, bunker suppliers, ship suppliers without possessory lien.
6. **Tier 9 (Residual Equity)**: Remainder wired to shipowner/debtor.

### 2.3 Multi-Currency Escrow & FX Haircut
- Auction escrow received in USD or VND. Cross-currency claims converted using SBV / commercial spot fixing on day of distribution waterfall execution. Default interest verified against statutory ceiling.

---

## 3. Comparative Architecture & Trade-Off Matrix

| Dimension | Option A: Pure Deterministic Rulebook | Option B: Real-Time Dynamic Solver (Chosen) | Option C: External Optimization Engine |
| :--- | :--- | :--- | :--- |
| **Complexity** | Low (O(1) rigid table) | Balanced (Deterministic Python stdlib) | High (scipy/numpy/ortools dependencies) |
| **BWM Compliance** | Hardcoded checks | Dynamic titration & coordinate distance math | Excess bloat for straightforward stoichiometry |
| **Waterfall Accounting** | Integer roundoff risks | Exact Decimal 128-bit monetary precision | Float rounding drifts violate court audit |
| **Adoption Risk** | High failure on boundary edge cases | Zero dependencies, transparent legal trace | External binary dependency failure in sandbox |

### Concrete Recommendation: Option B (Ranked #1)
Architected as two isolated domain engines in `src/harness/maritime/`:
1. `bwms_engine.py`: Reg. D-1 coordinates Haversine distance & depth verifier; Reg. D-2 microbe count validator; bisulfite titration dosing calculator; TRO safety alert interlock.
2. `mortgage_foreclosure_engine.py`: 15-day notice timeline validator; multi-tier statutory lien & mortgage waterfall using Python `decimal.Decimal`; interest cap limiter (20% CC / 150% LCI).

---

## 4. Limitations & Boundary Conditions
- Research assumes GPS fix and bathymetry data are pre-validated by bridge ECDIS.
- Excludes salvage reward adjudications pending London Maritime Arbitrators Association (LMAA) awards.
- Interest capping logic assumes domestic Vietnamese jurisdiction unless contractual choice-of-law specifies foreign flag law under VMC Art. 3.

## 5. Unresolved Questions
- None. Statutory requirements in VMC 2015 Arts. 31-43 and IMO BWM Convention Regs. D-1/D-2 provide complete determinism.
