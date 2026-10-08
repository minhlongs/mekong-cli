# Research Report: Maritime Wreck Removal & Limitation of Liability (Phases 199-200)

## 1. Statutory Grounding & Sources
- **Vietnam Maritime Code 2015 (Law No. 95/2015/QH13)**: Chapter VII Arts. 109-114 (Sunken Property Salvage & Clearance); Chapter XVI Arts. 299-309 (Limitation of Liability for Maritime Claims).
- **Decree 58/2017/NĐ-CP (amended by Decree 57/2024/NĐ-CP)**: Arts. 45-56 on shipwreck handling, safety marking, salvage plans, auctioning, and administrative enforcement.
- **Nairobi International Convention on the Removal of Wrecks 2007 (Nairobi WRC 2007)**: Strict liability of registered owner, compulsory financial security, direct action.
- **Convention on Limitation of Liability for Maritime Claims (LLMC 1976/1996 Protocol)**: Incorporating IMO Resolution LEG.5(99) 2012 raising limits by 51%, codified directly into VN Maritime Code 2015.

Credibility: Primary statutory codes and IMO treaties directly governing Vietnamese jurisdiction and foreign vessels in Vietnamese maritime zones.

---

## 2. Phase 199: Wreck Removal & Hazardous Obstruction Clearance

### Operational Timelines & Legal Gates
- **Emergency Classification**: Port Authority (Cảng vụ hàng hải) surveys obstruction. If navigational channel or environment is acutely threatened, Port Authority orders immediate emergency marking (buoyage/AIS) and emergency salvage.
- **Statutory Notice (Art. 110)**: Port Authority delivers official salvage notice to owner/insurer. Owner granted **30 calendar days** from notice to file formal salvage plan and clear security deposit.
- **Salvage Start Deadline (Art. 111)**: Owner must initiate physical salvage operations within **60 calendar days** from receipt of salvage order. Failure forfeits salvage rights.
- **Forced Salvage & Auctioning Rights (Arts. 112-114)**:
  - If 60-day window expires or owner abandons wreck, Port Authority contracts licensed salvage company.
  - Port Authority has statutory right to seize and conduct public auction of salvaged property to recover expenditures.
  - Expense Recovery Waterfall: `Net Proceeds = Gross Auction - (Direct Salvage Costs + Port Dues/Marking Fees + Storage Costs + Auction Admin Fees)`.
  - Escrow & Escheatment: Remaining surplus held in treasury escrow for **180 days** (Decree 58/2017) or **1 year** (Code Art. 114). If owner fails to claim, funds escheat to State Treasury.
- **Compulsory Insurance Certificate (WRC Certificate)**:
  - Threshold: All sea-going vessels of **300 GT and above** entering Vietnamese maritime zones.
  - Must carry valid Certificate of Insurance or Financial Security in Respect of Liability for the Removal of Wrecks issued by State of Registry.
  - Non-compliant vessels face port denial, detention, and administrative fines up to 100M VND.

---

## 3. Phase 200: Limitation of Liability for Maritime Claims (LLMC)

### Statutory Calculation Formulas (IMO 2012 / VN Maritime Code Arts. 302-303)

#### Tier A: Loss of Life / Personal Injury (Art. 302)
$$L_{life}(GT) = \begin{cases} 
3,020,000 \text{ SDR} & \text{if } GT \le 2,000 \\
3,020,000 + (GT - 2,000) \times 1,208 \text{ SDR} & \text{if } 2,000 < GT \le 30,000 \\
36,844,000 + (GT - 30,000) \times 906 \text{ SDR} & \text{if } 30,000 < GT \le 70,000 \\
73,084,000 + (GT - 70,000) \times 604 \text{ SDR} & \text{if } GT > 70,000 
\end{cases}$$

#### Tier B: Property & Other Maritime Claims (Art. 303)
$$L_{prop}(GT) = \begin{cases} 
1,510,000 \text{ SDR} & \text{if } GT \le 2,000 \\
1,510,000 + (GT - 2,000) \times 604 \text{ SDR} & \text{if } 2,000 < GT \le 30,000 \\
18,422,000 + (GT - 30,000) \times 453 \text{ SDR} & \text{if } 30,000 < GT \le 70,000 \\
36,542,000 + (GT - 70,000) \times 302 \text{ SDR} & \text{if } GT > 70,000 
\end{cases}$$

#### Concurrency & Priority Rule (Art. 304 / LLMC Art. 6(2))
If total personal injury claims exceed $L_{life}(GT)$, unpaid balances roll into property fund and rank *pari passu* (pro-rata) with property claims against $L_{prop}(GT)$.

### Limitation Fund Constitution & Legal Invariants (Arts. 305-309)
- **Constitution**: Shipowner/salvor deposits cash in VND (converted via SBV official SDR exchange rate on fund creation date) or tenders irrevocable bank guarantee to competent People's Court.
- **Bar to Enforcement (Art. 307)**: Once fund is validated, claimants are legally barred from arresting vessel or seizing other assets of owner within Vietnamese jurisdiction; any existing arrest orders must be vacated immediately.
- **Exception Triggers / Breaking Limitation (Art. 300(2) & LLMC Art. 4)**:
  - General Rule: Right to limit is unbreakable except upon strict burden of proof.
  - Disqualification Condition: Loss resulted from personal act or omission committed with **intent to cause such damage** (`DOLUS`), or **recklessly with knowledge that damage would probably result** (`LUXURIA`). Negligence or gross negligence alone does not break limitation.

---

## 4. Trade-off Matrix & Options Evaluation

| Option / Dimension | Option A: Hardcoded Static Limits | Option B: Dynamic Tier Engine + SDR FX Fetch | Option C: Integrated Port Workflow Engine |
| :--- | :--- | :--- | :--- |
| **Statutory Precision** | Low (misses brackets & FX volatility) | High (exact brackets, real-time FX) | High (covers end-to-end statutory cycle) |
| **Operational Automation** | None (manual lookup) | Medium (calc only) | High (tracks 30d/60d gates, fund escrow) |
| **Implementation Complexity** | Low | Low-Medium | Medium (state machine + calculation) |
| **Maintenance & Debt** | High statutory decay risk | Low (declarative brackets) | Low (pure python dataclasses) |
| **Recommendation Rank** | Rank 3 (Rejected) | Rank 2 (Partial) | **Rank 1 (Selected)** |

---

## 5. Architectural Fit & Recommendations

1. **Recommended Architecture**: Build unified engine `src/core/maritime_salvage_llmc_engine.py` using Python standard library dataclasses (`@dataclass`) and enums with zero external runtime dependencies.
2. **Phase 199 Component**:
   - `WreckRemovalCase`: Manages status transitions (`REPORTED` -> `ORDERED_30D` -> `SALVAGE_ACTIVE_60D` -> `FORCE_SALVAGE` -> `AUCTIONED` -> `ESCHEATED`).
   - `WRCInsuranceVerifier`: Validates 300 GT rule, validity window, and direct action eligibility.
   - `AuctionWaterfallCalculator`: Calculates cost deductions, surplus, and 180-day/1-year retention schedules.
3. **Phase 200 Component**:
   - `LLMCEngine`: Implements piecewise linear SDR tiers for Life and Property with automatic pro-rata rollover under Art. 304.
   - `LimitationFundTracker`: Computes statutory deposit in VND, verifies arrest immunization status, and validates exception triggers (`willful_intent_or_recklessness`).
4. **CLI Integration**: Mount commands under Typer groups `mekong wreck` and `mekong llmc` in `src/cli/commands/maritime_salvage_llmc_command.py`.

---

## 6. Adoption Risks, Limitations & Unresolved Questions

- **Adoption Risk**: Very low. Formulas and deadlines are stable statutory law codified in Vietnam Maritime Code 2015 and international conventions with multi-decade stability.
- **Scope Limitations**: Does not cover CLC 1992 / Bunker Convention 2001 oil pollution civil liability funds (separate dedicated regime under Maritime Code Arts. 310-316).
- **Unresolved Statutory Questions**:
  1. *Escrow Period Discrepancy*: Decree 58/2017 Art. 52 states 180 days for auction surplus retention before state treasury escheatment, whereas Maritime Code 2015 Art. 114 cites 1 year. *Recommendation*: Engine defaults to conservative 1-year timeline with 180-day warning gate.
  2. *SDR-to-VND Conversion Source*: SBV does not publish a daily official SDR rate directly; rate is synthesized via IMF SDR basket (USD, EUR, CNY, JPY, GBP) against SBV central cross rates. Engine requires configurable SDR fallback rate (e.g. 33,500 VND/SDR).
