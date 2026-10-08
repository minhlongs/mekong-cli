# Research Report: Phases 255-258 Statutory Maritime & Harbor Engineering Suite

## Executive Summary
This research synthesizes the statutory frameworks, mathematical models, and operational validation criteria for Phases 255-258 of the Mekong CLI v6.0 maritime legal engineering layer:
1. **Phase 255: Maritime Ship Agency Disbursements & Husbandry PDA/FDA Accounting** (Decree 160/2016/NĐ-CP, Decree 74/2023/NĐ-CP, VMC 2015 Arts. 154-165, Circular 39/2023/TT-BGTVT).
2. **Phase 256: Maritime Salvage Contracts & LOF 2024 / SCOPIC Clause Settlement** (VMC 2015 Arts. 282-289, 1989 Salvage Convention, LOF 2024, SCOPIC 2020).
3. **Phase 257: Seafarer Repatriation & Abandonment Financial Security Guarantee** (MLC 2006 Reg 2.5 / Standard A2.5.2, Circular 22/2017/TT-BYT, Decree 12/2022/NĐ-CP, VMC 2015 Art. 64).
4. **Phase 258: Seaport Green Tug & Clean Energy Harbor Craft Transition Incentives** (Decision 876/QĐ-TTg, Circular 39/2023/TT-BGTVT, IMO GHG Strategy 2023).

---

## 1. Phase 255: Maritime Ship Agency & Husbandry PDA/FDA Accounting
### Statutory Basis & Operational Scope
- **Decree 160/2016/NĐ-CP & Decree 74/2023/NĐ-CP**: Enterprise registration conditions for maritime ship agencies in Vietnam (capital requirements, professional staff certifications).
- **Vietnam Maritime Code 2015 Arts. 154-165**: Legal representation of shipowner/charterer, fiduciary duties, agency remuneration, and freight collection rights.
- **Port Disbursement Accounting (PDA/FDA)**:
  - **Proforma Disbursement Account (PDA)**: Advance estimation of port dues, pilotage, tugboat services, mooring, waste reception, customs tally, and husbandry services.
  - **Final Disbursement Account (FDA)**: Itemized reconciliation against official port authority/service invoices, calculating the refund or top-up due ($Balance = Advance_{paid} - Total_{actual}$).
  - **Statutory Agency Fee Schedules**: Based on vessel Gross Tonnage (GT) brackets and duration of port stay under Circular 39/2023/TT-BGTVT.
  - **Freight Commission**: Statutory commission allowed (1.0% - 2.5%) for inbound/outbound freight collected by agent.

---

## 2. Phase 256: Maritime Salvage Contracts & LOF 2024 / SCOPIC Clause Settlement
### Statutory Basis & Operational Scope
- **Vietnam Maritime Code 2015 Arts. 282-289 & 1989 International Convention on Salvage**:
  - Principle of "No Cure - No Pay": Salvage remuneration requires successful outcome.
  - Salved value calculation: $V_{salved} = V_{ship\_sound} - C_{repairs} + V_{cargo\_CIF} + Freight_{at\_risk}$.
  - Article 13 criteria: Salvor skill, promptness, risks run, property salved, environmental protection.
  - Article 14 Special Compensation: In coastal waters or inland waterways of Vietnam, if vessel/cargo threatened marine environment, salvor receives expenses plus up to 30% (extendable to 100% by tribunal) uplift.
- **SCOPIC 2020 Clause (Special Compensation P&I Club Clause)**:
  - Invoked by salvor at written notice to shipowner.
  - Rates: Tugboat day-rate by BHP/bollard pull, equipment day-rate, personnel per diem + standard 25% SCOPIC bonus markup.
  - SCOPIC discount penalty: If salvor invokes SCOPIC and later receives an Article 13 award greater than the SCOPIC remuneration, the Article 13 award is reduced by 25% of the difference between the two amounts.

---

## 3. Phase 257: Seafarer Repatriation & Abandonment Financial Security Guarantee
### Statutory Basis & Operational Scope
- **MLC 2006 Regulation 2.5 & Standard A2.5.2 (2014 Amendments)**:
  - Mandatory financial security certificate posted on board (issued by P&I Club or authorized insurer).
  - Definition of Abandonment:
    1. Shipowner fails to cover costs of seafarer repatriation;
    2. Shipowner has left seafarer without necessary maintenance and support (food, potable water, fuel, medical care);
    3. Shipowner has severed ties, including failure to pay contractual wages for at least 2 consecutive months.
- **Statutory Coverage Caps**:
  - Maximum 4 months of outstanding wages and all contractual entitlements.
  - Full repatriation transport costs (economy class airfare to home country, terminal transfers, baggage allowance).
  - Subsistence allowance: Daily food, water, medical necessities, and telecommunication access ($20 - $35/day/seafarer) for the duration of stranding.
  - Direct Action Right: Seafarers/unions may claim directly against the guarantor institution without prior court judgment against the insolvent shipowner.

---

## 4. Phase 258: Seaport Green Tug & Clean Energy Harbor Craft Transition Incentives
### Statutory Basis & Operational Scope
- **Decision 876/QĐ-TTg & Circular 39/2023/TT-BGTVT**:
  - Prime Minister's Action Plan: Harbor craft, tugboats, and port terminal equipment transitioning to electric, green hydrogen, and green methanol.
  - Green Port Tariff Rebate: Ports certified green or harbor craft utilizing green energy qualify for statutory fee reductions of 5% to 20% on tugage and berthage fees.
- **Emission & Decarbonization Metrics**:
  - Harbor craft engine emission baseline: Specific fuel consumption (SFOC $\approx 205\text{ g/kWh}$) $\times$ MGO emission factor ($3.206\text{ t CO}_2/\text{t fuel}$).
  - Green technology tiers:
    - Tier 1: Hybrid diesel-electric (15% - 25% CO2 abatement).
    - Tier 2: Pure battery-electric tug with shore charging (60% - 90% CO2 abatement depending on grid carbon intensity).
    - Tier 3: Zero-emission green hydrogen fuel cell / e-methanol (90% - 100% net lifecycle reduction).
  - Financial Evaluation: Annual operational fuel savings, OPEX carbon cost savings, port tariff rebate revenue, and simple payback period ($PBP = \frac{\Delta CAPEX}{Annual\_Savings}$).

---

## Architectural Invariant & Zero-Dependency Rule
- All mathematical modeling, statutory formulas, and diagnostic workflows will reside in `src/core/maritime_agency_salvage_abandonment_cleanport_engine.py` using strictly standard Python library modules (`dataclasses`, `enum`, `math`, `typing`, `json`, `datetime`, `sys`, `os`).
- Full integration with Typer CLI (`src/cli/commands/maritime_agency_salvage_abandonment_cleanport_command.py`), FastMCP (`scripts/mcp_server.py`), and test suite (`tests/test_maritime_agency_salvage_abandonment_cleanport_suite.py`).
