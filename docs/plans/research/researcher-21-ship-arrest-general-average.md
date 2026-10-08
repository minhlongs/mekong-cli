# Researcher 21 Report: Maritime Ship Arrest & General Average Adjustment (Phases 203-204)

## Executive Summary
This report analyzes Vietnamese and international maritime statutory frameworks governing:
1. **Ship Arrest & Judicial Release for Maritime Claims** (Vietnam Maritime Code 2015 Arts. 129–144, Ordinance 05/2008/UBTVQH12, Geneva Convention 1999).
2. **General Average Adjustment under York-Antwerp Rules (YAR 2016)** (Vietnam Maritime Code 2015 Arts. 295–298, Rules of Practice of Association of Average Adjusters).

---

## 1. Phase 203: Ship Arrest & Judicial Release for Maritime Claims

### 1.1 Statutory Foundations
- **Vietnam Maritime Code 2015 (Law No. 95/2015/QH13)**:
  - *Article 129*: Definition of Ship Arrest (Bắt giữ tàu biển) — judicial detention or restriction of departure by Court order to secure maritime claims, enforce court judgments, or perform mutual judicial assistance.
  - *Article 130*: 22 statutory maritime claims giving rise to arrest rights:
    1. Loss or damage caused by vessel operations;
    2. Loss of life or personal injury;
    3. Salvage operations;
    4. Environmental damage, pollution, or threat thereof;
    5. Wreck removal or marking;
    6. Charterparty agreements (Bareboat, Time, Voyage);
    7. Carriage of goods or passengers;
    8. General average loss/expenditure;
    9. Towage and pilotage;
    10. Goods, materials, bunker provisions;
    11. Construction, repair, drydocking;
    12. Port, canal, waterway dues;
    13. Crew wages and repatriation;
    14. Disbursements incurred on account of vessel;
    15. Marine insurance premiums;
    16. Brokerage and agency commissions;
    17. Ownership or possession disputes;
    18. Mortgage or registered hypothecation.
  - *Article 136*: Mandatory Financial Counter-Security (Thực hiện biện pháp bảo đảm tài chính).
    - Claimants must provide counter-security: Cash deposit at State Treasury or unconditional Bank Guarantee covering potential damages resulting from wrongful arrest.
    - Statutory quantum: Typically determined by the Chief Judge (Chánh án Tòa án), normally between 10% and 20% of claim quantum or operating loss estimate for detained days.
  - *Article 138-140*: Release of Ship from Arrest (Thả tàu biển đang bị bắt giữ).
    - Obligation to release within 24 hours upon presentation of sufficient alternative security (e.g., P&I Letter of Undertaking / Bank Guarantee equal to claim value or statutory limitation ceiling).
    - Maximum duration of arrest to secure maritime claims: 30 days unless legal action/arbitration is formally commenced.
    - Wrongful arrest liability (Bồi thường thiệt hại do bắt giữ sai): Claimant strictly liable if claim fails on merits or was frivolous.

---

## 2. Phase 204: General Average Adjustment (YAR 2016)

### 2.1 Statutory Foundations & York-Antwerp Rules
- **Vietnam Maritime Code 2015**:
  - *Article 295*: General Average Definition — Extraordinary sacrifice or expenditure intentionally and reasonably made or incurred for the common safety for the purpose of preserving from peril the property involved in a common maritime adventure.
  - *Article 296*: Burden of Proof — Party claiming GA bears burden of proving sacrifice/expenditure was properly GA.
  - *Article 297*: Contribution — GA losses borne by Ship, Cargo, and Freight according to their respective net salved values.
  - *Article 298*: Average Adjuster (Giám định viên phân bổ tổn thất chung) and GA Adjustment Statement (Bản tính toán phân bổ tổn thất chung).

### 2.2 Mathematical Model of GA Adjustment (YAR 2016)
1. **General Average Sacrifice ($GA_{sac}$)**: Jettison of cargo, engine damage forced to refloat, water damage extinguishing fire.
2. **General Average Expenditure ($GA_{exp}$)**: Port of refuge expenses, pilotage, discharge/reloading cargo for hull inspection, temporary repairs.
3. **General Average Allowances**:
   - Commission: 2% on GA disbursements (Rule XX).
   - Interest: LIBOR/SOFR + statutory spread (typically fixed percentage under YAR 2016) per annum until date of adjustment (Rule XXI).
4. **Total GA Gross Loss ($GA_{total}$)**:
   $$GA_{total} = GA_{sac} + GA_{exp} + Commission(2\%) + Interest$$
5. **Contributory Values ($CV_{total}$)**:
   - *Ship ($CV_{ship}$)*: Sound value less non-GA repair costs and salvage award.
   - *Cargo ($CV_{cargo}$)*: CIF/Invoice value at port of discharge less loss/damage and freight payable.
   - *Freight ($CV_{freight}$)*: Gross freight at risk less voyage operating expenses incurred post-casualty.
   $$CV_{total} = CV_{ship} + CV_{cargo} + CV_{freight}$$
6. **GA Contribution Ratio ($R_{ga}$)**:
   $$R_{ga} = \frac{GA_{total}}{CV_{total}}$$
7. **Net Settlement Balance for each interest $i$**:
   $$\text{Contributed Amount}_i = CV_i \times R_{ga}$$
   $$\text{Net Balance}_i = GA_{\text{Allowances}_i} - \text{Contributed Amount}_i$$
   (Positive = Receivable from GA Pool; Negative = Payable to GA Pool).

---

## 3. Conclusions for Implementation
- Implement exact 22 maritime claims enum under VMC Art. 130.
- Model wrongful arrest counter-security threshold calculator.
- Implement York-Antwerp Rules 2016 contributory value and net balance waterfall.
- Verify AST zero-dependency invariant for core logic.
