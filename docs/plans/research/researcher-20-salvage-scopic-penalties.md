# Research Report: Marine Salvage (LOF/SCOPIC) & Port State Penalties (Phases 201-202)

## 1. Statutory Grounding & Sources
- **Vietnam Maritime Code 2015 (Law 95/2015/QH13)**: Chapter XIV (Arts. 280-294) governing marine salvage contracts, rewards, and special compensation.
- **International Convention on Salvage 1989**: Art. 12 ("No Cure - No Pay"), Art. 13 (Reward criteria & fund cap), Art. 14 (Special compensation for environmental protection).
- **Lloyd's Form of Salvage Agreement (LOF 2024) & SCOPIC Clause 2020/2024**: Industry-standard contractual framework replacing Art. 14 with tariff-based remuneration and P&I security.
- **Decree 162/2016/NĐ-CP** (amended by **Decree 123/2021/NĐ-CP** & **Decree 142/2021/NĐ-CP**): Statutory fine schedules and administrative sanctions for maritime safety and environmental violations.
- **Decree 58/2017/NĐ-CP**: Art. 78 on statutory conditions for refusing port departure clearance.

*Credibility Weight*: Primary statutory instruments (National Assembly / Gov decrees) > IMO Treaties & Lloyd's/IG P&I standards > secondary legal commentaries.

---

## 2. Phase 201: Marine Salvage, LOF 2024 & SCOPIC Mechanics

### 2.1 "No Cure - No Pay" (Article 13 / VMC Art. 284)
- **Core Condition**: Salvage operations with useful result entitle salvor to reward; zero success = zero payment (`useful_result == True`).
- **Statutory Ceiling**: Salvage reward $R_{art13} \le Salved\_Fund$, where:
  $$Salved\_Fund = V_{ship} + V_{cargo} + V_{freight\_at\_risk} + V_{bunker} - Post\_Casualty\_Liens$$
- **10 Evaluation Criteria (Art. 13(1) & VMC Art. 285)**:
  1. Salved value of vessel and property ($w_1$).
  2. Skill/efforts in preventing/minimizing environmental damage ($w_2$).
  3. Measure of success obtained ($w_3$).
  4. Nature and degree of danger ($w_4$).
  5. Skill/efforts in saving vessel, cargo, and human life ($w_5$).
  6. Time used, expenses, and losses incurred by salvor ($w_6$).
  7. Risk of liability and other risks run by salvor ($w_7$).
  8. Promptness of service rendered ($w_8$).
  9. Availability and use of specialized salvage vessels/equipment ($w_9$).
  10. Readiness, efficiency, and capital value of salvor equipment ($w_{10}$).
- **Formula**: $R_{art13} = \min\left(Salved\_Fund, \sum_{i=1}^{10} w_i \cdot Score_i \cdot Base\_Expense\right)$.

### 2.2 SCOPIC Clause (Special Compensation P&I Club Clause)
- **Trigger**: Invoked unilaterally by salvor via written notice when environmental threat exists and property value is low/negligible ($Salved\_Fund \ll Estimated\_Costs$).
- **Remuneration Formula**:
  $$R_{scopic} = \sum (Tariff\_Rate_{tug/crew/gear} \times Time) + Out\_Of\_Pocket\_Expenses + 25\% \times Standard\_Bonus$$
  - *Standard Bonus*: Fixed at $25\%$ of tariff rates + allowable expenses.
  - *Zero Profit Margin*: Tariffs represent agreed compensation rates, not open-market contingency upside.
- **Security Mechanism**: Shipowner P&I Club must post initial security of USD 3,000,000 within 2 working days. If security fails, salvor can de-invoke SCOPIC and revert to Article 14 / general liens.
- **Sub-Clause 6 Penalty (Article 13 Discount)**:
  - If salvor invokes SCOPIC, but the final Article 13 award exceeds SCOPIC remuneration:
  $$R_{payable} = R_{art13} - 0.25 \times \max(0, R_{art13} - R_{scopic})$$
  - Prevents opportunistic SCOPIC invocation when high salved fund was readily attainable.

---

## 3. Phase 202: Port State Administrative Penalties & Sanctions

### 3.1 Violation Fine Schedules (Decree 162/2016/NĐ-CP & Decree 123/2021/NĐ-CP)
*Note: Fines apply to organizations; individuals pay 50% per Decree 162 Art. 3(2).*

| Violation Type | Statutory Clause | Individual Fine (VND) | Org Fine (VND) | Severity Factor / Condition |
| :--- | :--- | :--- | :--- | :--- |
| **Navigation w/o Pilot** | Art. 16, D.162 / D.123 | 20M - 40M | 40M - 80M | Compulsory pilot zone entry w/o licensed pilot |
| **Exceeding Speed Limit** | Art. 13, D.162 / D.123 | 5M - 15M | 10M - 30M | Margin $\le 2\text{ kts}$ vs $> 2\text{ kts}$ over channel limit |
| **Exceeding Authorized Draft**| Art. 14, D.162 / D.123 | 20M - 40M | 40M - 80M | Vessel dynamic/static draft > proclaimed channel depth |
| **Illegal Discharge (Oil/Waste)**| Art. 24, D.162 / D.123 | 50M - 100M | 100M - 200M | Bilge/sludge/ballast discharge; env harm triggers D.45/2022 |
| **Failure to Report Accident**| Art. 32, D.162 / D.123 | 10M - 20M | 20M - 40M | Late reporting ($>2\text{h}$) or failure to submit formal report |
| **Concealing Maritime Accident**| Art. 32(3), D.162 | 20M - 40M | 40M - 80M | Falsifying logbooks, destroying VDR records |

### 3.2 Supplementary Sanctions & Remedial Enforcement
- **GCNKNCM Suspension**:
  - 1 to 3 months: Navigation without pilot, gross speeding, draft violation endangering channel.
  - 3 to 6 months: Illegal pollutant discharge, concealing accident, deliberate grounding/obstruction.
- **Forced Remediation (Biện pháp khắc phục hậu quả)**:
  - Mandatory pollutant recovery, sea surface decontamination, oily water treatment under Art. 24.
  - Channel dredging/obstruction removal at violator's sole cost if vessel causes siltation or grounding.
- **Port Departure Clearance Refusal (Từ chối cấp phép rời cảng)**:
  - Port Authority (Cảng vụ hàng hải) exercises statutory refusal under Decree 58/2017 Art. 78 until:
    1. Full payment of administrative fine receipt from State Treasury (KBNN), OR
    2. Irrevocable bank guarantee / P&I Club Letter of Undertaking (LOU) accepted by Maritime Administration.

---

## 4. Trade-Off Matrix

| Dimension | Option A: Pure Art. 13 Salvage | Option B: LOF + SCOPIC Mechanism | Option C: Fixed Commercial Towage |
| :--- | :--- | :--- | :--- |
| **Downside Risk** | Salvor absorbs all losses if ship sinks | Guaranteed tariff cost + 25% bonus | Zero contingency; shipowner pays flat rate |
| **Upside Reward** | Up to 100% of salved fund | Capped by Art 13 discount penalty (-25% diff) | Flat daily/hourly rate; zero bonus |
| **Environmental Hazard**| Minimal protection for low-value hulks | Optimal: funds wreck prevention immediately | Non-responsive to emergency escalation |
| **Dispute Overhead** | High (Arbitration needed for salved values)| Predictable (Tariff audit + P&I security)| Low (Contractual invoice check) |

---

## 5. Architectural Fit & Implementation Plan

### 5.1 Project Fit
- Integrates into `src/core/maritime_salvage_penalty_engine.py`.
- Pure Python 3.11+ standard library (`dataclasses`, `enum`, `datetime`, `typing`).
- Deterministic, zero external dependencies, 100% testable via `pytest`.

### 5.2 Core State Machines & Data Models
1. `SalvageContractType`: `NO_CURE_NO_PAY_ART13`, `SCOPIC_INVOKED`, `COMMERCIAL_TOWCON`.
2. `ScopicRemunerationCalculator`: Computes equipment tariffs, crew days, out-of-pocket costs, 25% bonus, and sub-clause 6 discount penalty.
3. `MaritimeSanctionEngine`: Validates violation types against Decree 162/123 brackets, applies corporate multiplier ($2\times$), computes GCNKNCM suspension window, and enforces clearance block flag.

---

## 6. Adoption Risks & Limitations
- **P&I Security Cross-Border Enforcement**: Enforcing Club LOU against non-IG clubs in Vietnam waters requires local bank counter-guarantee.
- **SDR / USD Exchange Rate Volatility**: SCOPIC uses USD tariff rates while VMC Art. 280-294 references VND/SDR; dynamic FX conversion needed.
- **Limitations**: Research excludes criminal liability under Criminal Code 2015 Art. 272 (Maritime navigation safety offenses causing catastrophic loss of life).

---

## 7. Concrete Ranked Recommendations
1. **Rank 1 (Architecture)**: Implement combined `MaritimeSalvageEngine` and `MaritimePenaltiesEngine` with standard dataclass models conforming to Phase 162/179 architecture.
2. **Rank 2 (SCOPIC Rule Engine)**: Implement automated sub-clause 6 clawback arithmetic ($R_{payable} = R_{art13} - 0.25 \times (R_{art13} - R_{scopic})$) to prevent valuation over-awards.
3. **Rank 3 (Sanctions Gate)**: Bind administrative violations directly to Port Clearance status (`clearance_status: BLOCKED | CLEARED`) driven by fine settlement status.

---

## 8. Unresolved Questions
1. Does Vietnam Maritime Administration officially accept electronic P&I Club Letters of Undertaking (Club LOU) via the National Single Window (VNSW) without Vietnamese consular notarization for immediate port clearance release?
2. Under Decree 123/2021/NĐ-CP, does concurrent violation of channel draft and navigation without pilot trigger cumulative maximum fine or absorption under general administrative violations doctrine?
