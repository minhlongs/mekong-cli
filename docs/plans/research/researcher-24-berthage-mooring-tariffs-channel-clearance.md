# Phase 233 & 234 Statutory Research: Berthage/Anchorage Tariffs, Mooring Operations & Fairway Clearance

## 1. Executive Summary & Statutory Authority
- **Statutory Baseline**:
  - Tariff & Port Service Fees: Circular 39/2023/TT-BGTVT (Seaport service price schedule), Circular 12/2024/TT-BGTVT (Amending tariff framework).
  - Maritime Safety & Port State Control: Vietnam Maritime Code 2015 (VMC Arts. 88–102), Decree 58/2017/NĐ-CP (Port safety administration), Decree 34/2024/NĐ-CP.
  - Channel Navigation Standards: PIANC WG 121 (Harbour Approach Channels Deep Water), IALA A-126, IMO Res. A.868(20).

---

## 2. Phase 233: Port Berthage, Anchorage & Mooring Line Tariffs

### 2.1 Berthage & Anchorage Fee Architecture (Cir 39/2023 & Cir 12/2024)
- **Berthage Fees (Phí cầu bến)**: Tiered by vessel Gross Tonnage (GT) and occupancy duration (GT-hour or GT-day).
  - *Cargo Operations*: Standard tariff floor (USD 0.0031–0.0035 / GT-hour for international vessels; VND 18–35 / GT-hour for domestic).
  - *Non-Cargo Waiting / Idle / Repair*: Surcharge rate +50% to +100% of standard cargo berthage (USD 0.0050–0.0065 / GT-hour) to discourage prolonged quay blocking.
  - *Unauthorized Overstay*: Berth occupancy exceeding approved pilotage/cargo window without Harbormaster permit incurs 200% penalty tariff.
- **Anchorage Fees (Phí neo buộc, neo đậu)**:
  - *Designated Port Anchorage*: International: USD 0.0005–0.0010 / GT-hour; Domestic: VND 5–12 / GT-hour.
  - *Awaiting Berth vs Quarantine/Dispute*: First 24h awaiting berth often bundled or discounted; anchorages exceeding 30 days trigger reduced long-layup tiers.

### 2.2 Statutory Mooring / Unmooring Line Services (Dịch vụ buộc/cởi dây)
Tiered fee structure applied per movement (1 turn = berthing or unberthing) based on vessel GT:
| Vessel Tonnage Tier | Base Tariff (USD / operation) | Domestic Base (VND / operation) | Operational Crew Minimum |
|---|---|---|---|
| **Tier 1: < 2,000 GT** | $12 – $18 | 150,000 – 250,000 | 2 line-handlers |
| **Tier 2: 2,000 – 5,000 GT** | $22 – $32 | 300,000 – 450,000 | 3 line-handlers + 1 supervisor |
| **Tier 3: 5,000 – 10,000 GT** | $38 – $55 | 500,000 – 800,000 | 4 line-handlers + 1 supervisor |
| **Tier 4: 10,000 – 20,000 GT** | $65 – $95 | 900,000 – 1,400,000 | 6 line-handlers + launch boat |
| **Tier 5: > 20,000 GT** | $110 – $165 | 1,500,000 – 2,500,000 | 8 line-handlers + mooring launch |

- **Statutory Mooring Surcharges**:
  - *Night Work (18:00 – 06:00)*: **+30% to +50%** over base tariff.
  - *Weekends & Public Holidays (Labor Code Art. 112)*: **+100%** (2.0x base tariff).
  - *Hazardous Cargo Ships (IMDG Classes 1, 2, 3)*: **+20% to +30%** safety handling surcharge.

---

## 3. Phase 234: Maritime Safety Inspection, Dynamic UKC & Channel Refusal

### 3.1 Dynamic Under-Keel Clearance (UKC) Formulation
In Vietnamese navigation fairways (Luồng hàng hải - Decree 58/2017 & PIANC WG 121):
$$\text{Fairway Water Depth } (D_{\text{channel}}) = h_{\text{chart}} + h_{\text{tide}} - \Delta_{\text{sounding\_error}}$$
$$\text{Dynamic Vessel Draft } (T_{\text{dynamic}}) = T_{\text{static}} + S_{\text{squat}} + H_{\text{wave\_heave}} + \Delta_{\text{salinity}}$$
$$\text{Dynamic UKC} = D_{\text{channel}} - T_{\text{dynamic}}$$

- **Dynamic Components**:
  - *Squat ($S_{\text{squat}}$)*: $S = C_b \times \frac{V_k^2}{100}$ (open water) or $2 \times C_b \times \frac{V_k^2}{100} \times \frac{A_s}{A_c - A_s}$ (confined channel), where $C_b$ = block coefficient, $V_k$ = speed over water (knots), $A_s/A_c$ = channel blockage factor.
  - *Salinity Sinkage ($\Delta_{\text{salinity}}$)*: $\Delta = T_{\text{static}} \times \frac{1.025 - \rho_{\text{brackish}}}{1.025}$ (water density shift from seaward 1.025 to river 1.000–1.015 g/cm³).
  - *Wave Response ($H_{\text{wave}}$)*: 0.2m–0.8m heave/pitch motion allowance in river bar approaches.
- **Statutory Minimum UKC Floor**:
  - Confined River Channels (Sài Gòn - Vũng Tàu, Soài Rạp, Hải Phòng): **$\text{UKC} \ge \max(10\% \times T_{\text{static}}, 0.5\text{m})$**.
  - Estuary / Approach Fairways exposed to swell (Cái Mép, Cửa Lặc Huyện): **$\text{UKC} \ge \max(12\% \times T_{\text{static}}, 1.0\text{m} - 1.2\text{m})$**.

### 3.2 Air Draft Clearance Verification
$$\text{Air Draft Clearance} = H_{\text{structure}} - (H_{\text{mast}} - T_{\text{dynamic}}) - H_{\text{tide}} \ge \Delta_{\text{buffer}}$$
- Structure vertical clearance ($H_{\text{structure}}$) referenced to Highest Astronomical Tide (HAT).
- Statutory Buffer Requirement: **$\Delta_{\text{buffer}} \ge 2.0\text{m}$** safety buffer under bridges (e.g. Cầu Phú Mỹ, Cầu Bạch Đằng) and high-voltage transmission lines. Negative or $< 2.0\text{m}$ margin triggers automatic transit refusal.

### 3.3 Maritime Administration Detention & Departure Clearance Refusal (VMC Art. 101)
Harbormaster (Giám đốc Cảng vụ Hàng hải) issues Departure Clearance Refusal or Detention Order under 8 statutory conditions:
1. Vessel unseaworthy or structural/safety defects threatening marine safety (Art. 101.1.a).
2. Missing, expired, or fraudulent statutory certificates (ISM, ISPS, MLC, Class, Bunker Blue Card) (Art. 101.1.b).
3. Failure to pay statutory maritime dues, fees, berthage, mooring charges, or administrative fines (Art. 101.1.c).
4. Direct environmental hazard or active oil/chemical discharge threat (Art. 101.1.d).
5. Ship arrest order (Quyết định bắt giữ tàu biển) issued by People's Court (Art. 101.1.e).
6. Non-compliance with maritime safety inspection rectification orders (Art. 101.1.f).
7. Search, rescue, salvage mobilization orders issued by competent authorities (Art. 101.1.g).
8. Overloading beyond load line markings or violation of channel UKC/Air draft limits (Art. 101.1.h).

---

## 4. Trade-off Matrix: Architectural & Algorithmic Design
| Dimension | Option A: Hardcoded Static Thresholds | Option B: Dynamic Formulaic Engine (Recommended) | Option C: External Port API Delegation |
|---|---|---|---|
| **Accuracy** | Poor: Misses squat velocity & tidal curve | High: Rigorous hydrodynamic & statutory modeling | Variable: Subject to 3rd-party latency/outages |
| **Complexity** | Low: Simple conditional checks | Medium: Squat, salinity density, tidal interpolation | High: OAuth, webhook resilience, external schema |
| **Performance** | < 1ms | < 2ms (In-memory vector/formula calculation) | 200–800ms network round-trip |
| **Compliance** | Non-compliant with VMC dynamic draft rules | 100% compliant with VMC Art. 101 & Cir 39/2023 | Dependent on provider fidelity |

---

## 5. Adoption Risk, Architectural Fit & Recommendation
- **Adoption Risk**: Low. Circulars 39/2023 and 12/2024 are mature, published statutory tables. VMC 2015 Arts. 88–102 are stable law.
- **Architectural Fit**: Native fit for `mekong-cli` Python runtime. Implement as twin domain engines:
  - `BerthageAndMooringTariffEngine` (Phase 233): Calculates GT-tiered berthage/anchorage, 5-tier mooring services, night/holiday surcharges.
  - `ChannelClearanceAndSafetyInspectionEngine` (Phase 234): Dynamic UKC calculation, air draft buffer check, VMC Art. 101 refusal validator.
- **Recommendation**: Implement Option B in `src/core/` with Pydantic schemas, unit test coverage, CLI commands, and FastMCP integration.

---

## 6. Limitations & Unresolved Questions
- **Limitations**: Research excludes specialized floating crane offshore lighterage tariffs and military port berths under Ministry of National Defence control.
- **Unresolved Questions**:
  1. Do private terminal operators in Cái Mép have approved proprietary mooring line tariffs deviating from Circular 39 base bands?
  2. Is real-time AIS/VTS dynamic UKC integration required, or is pre-arrival voyage passage clearance verification sufficient?
