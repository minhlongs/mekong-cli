---
name: electric-tug-charterparty-research
description: Research on green tugboat energy metrics and maritime charterparty arbitration
metadata:
  type: reference
---

# Research Report: Ph 337-338 (Green Tug & BIMCO Arbitration)

## 1. Phase 337: Green Port Tug Energy & Cold Ironing (IEC/IEEE 80005)
*   **Standards**: IEC/IEEE 80005-1 (HVSC), 80005-3 (LVSC).
*   **Peak Shaving Algebra**: 
    $P_{shore} = P_{vessel} - P_{bat\_discharge}$. Reserve SoC $\ge$ 20%.
*   **Bollard Pull Energy Metric (kWh/t-pull)**:
    $E_{pull} = \frac{\int_{t} P_{prop}(t) dt}{BP_{total}}$. Target baseline $\le$ 0.15 kWh/t-pull for Tier 3 hybrid.
*   **Data Model**: `{ soc: float, charge_rate_kw: float, b_pull_t: float, net_emission_sav: float }`.
*   **Validation**: Load-shedding sequence when $V_{bus}$ threshold is breached.

## 2. Phase 338: BIMCO Charterparty & Arbitration (NYPE/GENCON)
*   **Warranty Clause**: Fuel/Speed warranty underperformance follows $Q_{allowed} = Q_{base} \times (1 + \Delta_{sea\_state} + \Delta_{wind})$.
*   **Weather Exclusion**: Exclude data points where $SeaState > 3$ (Douglas) or $Beaufort > 4$.
*   **Apportionment**: LMAA Intermediate Claims Procedure (ICP) for claims $<\$100k$. VMAC rules mimic local jurisdiction.
*   **Data Model**: `{ charter_type: string, laytime_rule: string, demurrage_daily: float, exclusion_filter: object }`.
*   **Edge Case**: Reversible laytime mismatch (port/berth congestion vs. vessel unreadiness).

## 3. Comparative Matrix
| Metric | Electric Tug (337) | Charterparty (338) |
| :--- | :--- | :--- |
| **Primary Driver** | Emissions (CII/EEXI) | Contractual Liability |
| **Complexity** | High (Electrical) | High (Contractual/Legal) |
| **Unit** | kWh / System State | Days / USD / MT |
| **Data Source** | Ship-to-Shore PLC | Daily Reports (NOR) |

## 4. Recommendations
1. **Model** tug energy as a continuous state-machine (SoC thresholds) rather than static logs.
2. **Standardize** weather exclusion logic in the charterparty app to avoid subjective disputes.
3. **Connect** energy savings in 337 to carbon credit tokens verified by MRV (Monitoring, Reporting, Verification) schemas for compliance.

**Unresolved Questions:** 
- How does the Mekong grid volatility impact the 80005-1 synchronization window?
- Are port-specific tariff structures for Shore-to-Ship Power (SSP) integrated into the demurrage/despatch accounting?
