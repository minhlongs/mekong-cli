# Research Report 30: Maritime Pilotage Dues & Seaport FTZ / Transshipment Cargo Supervision Suite (Phases 281-282)

## Phase 281: Maritime Pilotage Service Allocation, Pilot Ladder Safety & Tariff Engine
### 1. Statutory & Legal Framework
- **Vietnam Maritime Code 2015 Articles 246–258**:
  - Compulsory pilotage zones for sea-going vessels in Vietnamese inland waterways and maritime zones.
  - Exemption conditions: Masters holding statutory exemption certificates after qualifying calls ($\ge 10$ calls within 12 months in the specific zone), and domestic vessels $< 2,000\text{ GT}$.
- **Decree 58/2017/NĐ-CP Articles 45–52**: Maritime pilotage organization, boarding areas, dispatch, and safety regimes.
- **Circular 39/2023/TT-BGTVT (Section 2, Arts. 11–13)**:
  - Pilotage tariff formulation: $T_{base} = GT \times d_{NM} \times R_{unit}$.
  - Minimum call charge brackets by pilotage zone (Zone I: 150-300 USD; Zone II: 120-250 USD; Zone III: 100-200 USD).
  - Night navigation surcharge: $+40\%$ for piloting between 18:00 and 06:00.
  - Bad weather standby fee: $20\text{ USD/hour}$ (or VND equivalent) when pilot is kept on board.
  - Late cancellation penalty: cancellation $< 2\text{ hours}$ before boarding incurs up to $80\%$ pilotage charge; $\ge 2\text{ hours}$ incurs $10\%$.
- **SOLAS Reg. V/23 & IMO Resolution A.1045(27)**:
  - Pilot ladder rigging: Freeboard $> 9.0\text{ m}$ mandates combination arrangement (accommodation ladder + pilot ladder).
  - Climbing height on pilot ladder: $\le 9.0\text{ m}$ and $\ge 1.5\text{ m}$ above water level.
  - Angle of accommodation ladder: $\le 45^\circ$ (or max $55^\circ$ with rest platforms).

---

## Phase 282: Seaport Free Trade Zone (FTZ) & Bonded Transshipment Cargo Supervision Engine
### 1. Statutory & Legal Framework
- **Law on Customs 2014 (Articles 42–44)**:
  - Customs procedures for goods in international transshipment (hàng hóa quá cảnh, trung chuyển quốc tế).
  - Supervision of goods entering, exiting, or stored in seaport bonded logistics areas and free trade zones.
- **Decree 08/2015/NĐ-CP & Decree 59/2018/NĐ-CP**:
  - Transshipment cargo dwell limit: strictly $\le 30\text{ days}$ at the seaport terminal.
  - One-time extension: up to $30\text{ days}$ upon approval of Customs Branch Director ($\max 60\text{ days}$ total).
  - Expiration enforcement: automatic violation alert at 20 days (warning), 25 days (urgent warning), $> 30$ days (overstay/re-export seizure).
  - Bonded warehouse term: 12 months, extendable once by up to 12 months.
- **Circular 38/2015/TT-BTC & Circular 39/2018/TT-BTC & Decision 2185/QĐ-TCHQ**:
  - E-seal electronic customs monitoring (niêm phong điện tử định vị GPS).
  - GPS corridor tracking: Haversine distance tracking along approved transport corridor from seaport terminal to inland clearance depot (ICD) or bonded warehouse (allowed corridor width deviation $\le 500\text{ m}$).
  - Real-time tampering detection: cable cutting, housing open switch, battery drop alerts.
  - Cryptographic tamper-evident SHA-256 seal verification token.
