# Research Report: Berth Allocation Planning, Tidal UKC & VASSCM Customs Engine (Phases 277-278)

## Executive Summary
This report analyzes statutory frameworks, mathematical models, risk channeling algorithms, and system integration patterns for:
1. **Phase 277: Seaport Berth Allocation Planning, Tidal Window UKC & Berth Occupancy Rate (BOR) Engine** (Decree 58/2017/NĐ-CP Arts. 53-61, Circular 39/2023/TT-BGTVT, PIANC Report 158 / WG 121).
2. **Phase 278: Automated Customs Clearance Risk Channeling & Seaport VASSCM Clearance Engine** (Law on Customs 2014 Arts. 16-17, Circular 38/2015 & 39/2018/TT-BTC, Decisions 1399/QĐ-TCHQ & 2185/QĐ-TCHQ).

---

## 1. Phase 277: Berth Allocation Planning, Tidal Window UKC & BOR
### Statutory & Technical Standards
- **Decree 58/2017/NĐ-CP Arts. 53-61**: Harbor Master (*Cảng vụ hàng hải*) berthing dispatch authority, safe draft notification, mandatory pilotage boarding.
- **Circular 39/2023/TT-BGTVT**: Port tariff framework for berthage (*cầu bến*), mooring (*phao neo*), and shifting operations.
- **PIANC Report 158 / WG 121**: Guidelines for Container Terminal Design & Approach Channel Water Depths.

### Mathematical Formulations
1. **Harmonic Tidal Prediction Curve**:
   $$h(t) = h_{CD} + \sum_{i=1}^n A_i \cos(\omega_i t - \phi_i) \quad \text{or semidiurnal approximation:} \quad h(t) = h_{ML} + A \cos\left(\frac{2\pi (t - t_{HW})}{T_{tide}}\right)$$
2. **Dynamic Under-Keel Clearance (Dynamic UKC)**:
   $$UKC_{dyn}(t) = \left(D_{chart} + h(t)\right) - \left(T_{static} + S_{squat} + Z_{wave} + \Delta T_{salinity}\right)$$
   - $S_{squat}$ (Barass Confined/Open Channel Formula):
     $$S_{squat} = \frac{C_b \times B_{ratio} \times V_k^2}{30 \times K} \quad \text{where } B_{ratio} = \frac{B_{ship} \times T_{draft}}{W_{channel} \times D_{water}}, \; K = 1 \text{ (open)} \dots 2 \text{ (restricted)}$$
   - $\Delta T_{salinity}$ (Freshwater sinkage): $\Delta T = T_{static} \times \left(\frac{1.025 - \rho_{water}}{\rho_{water}}\right)$.
   - Statutory Constraint: $UKC_{dyn}(t) \ge UKC_{min} = \max(0.10 \times T_{static}, 0.60\text{m})$.
3. **Tidal Transit Window**: $[t_{entry}, t_{exit}] = \{t \mid UKC_{dyn}(t) \ge UKC_{min}\} \text{ with duration } \Delta t \ge T_{transit} + T_{safety\_buffer}$.
4. **Berth Spatial Allocation & Safety Spacing**:
   $$L_{slot} = LOA + \max(15\text{m}, 0.10 \times LOA)$$
   Spatial conflict check: $\forall i \ne j, [x_i, x_i + L_{slot, i}] \cap [x_j, x_j + L_{slot, j}] = \emptyset$ whenever $[t_{arr, i}, t_{dep, i}] \cap [t_{arr, j}, t_{dep, j}] \ne \emptyset$.
5. **Berth Occupancy Rate (BOR)**:
   $$BOR = \frac{\sum_{i=1}^N T_{service, i}}{M_{berths} \times T_{period}} \times 100\%$$
   - PIANC Threshold: $BOR \le 65\%$ (Container berths), $BOR \le 70\%$ (Multi-purpose berths). $BOR > 70\%$ triggers exponential queue delay ($M/M/c$ congestion).

---

## 2. Phase 278: Customs Risk Channeling & Seaport VASSCM Clearance
### Statutory & Regulatory Framework
- **Law on Customs 2014 Arts. 16-17**: Automated risk management & risk-based clearance categorization.
- **Circular 38/2015/TT-BTC & 39/2018/TT-BTC**: Electronic customs declaration procedures and inspection SLA.
- **Decision 1399/QĐ-TCHQ**: Enterprise compliance assessment (Levels 1 to 5) and commodity/origin risk channeling.
- **Decision 2185/QĐ-TCHQ**: Vietnam Automated System for Seaport Customs Management (VASSCM) gate-out supervision.

### Customs Risk Channeling Engine
1. **Channel Classification & Statutory SLA**:
   - **Green (Luồng Xanh - Code 1)**: Document & physical inspection exempt -> instant automated release token. SLA < 5 seconds.
   - **Yellow (Luồng Vàng - Code 2)**: Detailed documentary examination (invoice, C/O, packing list). SLA $\le$ 2 business hours.
   - **Red (Luồng Đỏ - Code 3)**: Physical inspection:
     - *3A*: Container X-ray scanner (Soi chiếu).
     - *3B*: Physical unpacking 5% - 10%.
     - *3C*: Comprehensive physical unpacking 100%.
     - SLA $\le$ 8 business hours (Art. 23 Law on Customs).
2. **Risk Score Formulation**:
   $$R_{score} = w_e \cdot E_{risk} + w_h \cdot H_{risk} + w_o \cdot O_{risk} + I_{alert}$$
   - $E_{risk} \in [0.1, 1.0]$: Enterprise compliance rating (Level 1 AEO = 0.1; Level 2 = 0.3; Level 3 = 0.6; Level 4 = 0.8; Level 5 High Risk = 1.0).
   - $H_{risk} \in [0.0, 1.0]$: HS Code sensitivity tier (raw low-tariff = 0.1; scrap/dual-use/conditional = 1.0).
   - $O_{risk} \in [0.0, 1.0]$: Origin/Transit route risk rating.
   - $I_{alert} \in \{0.0, 1.0\}$: Intelligence blacklists or mandatory targeted inspections.
   - Channel threshold: $R < 0.35 \to \text{Green}$; $0.35 \le R < 0.70 \to \text{Yellow}$; $R \ge 0.70 \text{ or } I_{alert}=1.0 \to \text{Red}$.

### VASSCM Seaport Gate-Out 3-Way Match
- **Verification Triad**:
  1. Customs Declaration Clearance Status (`RELEASED` / `CONDITIONAL_RELEASE`).
  2. Electronic Delivery Order (`e-D/O`) issued by carrier and active.
  3. Container Seal Number matches declaration & physical barcode payload (`SHA-256(decl_no + cont_no + seal_no)`).
- **Gate-Out Actions**:
  - `MATCH_SUCCESS`: Gate open, issue electronic exit ticket, send VASSCM status `01-GATE_OUT`.
  - `DISCREPANCY_FAIL`: Gate hold (`GATE_HOLD`), alert port authority & customs oversight station.

---

## 3. Trade-off Matrix & Architecture Evaluation

| Criterion | Option A: Pure Heuristic / Rule Matrix | Option B: Hybrid Algorithmic + Deterministic Engine | Option C: Black-Box ML Classifier |
| :--- | :--- | :--- | :--- |
| **Performance** | O(1) rules, sub-millisecond | O(N log N) interval tree + greedy allocation | O(1) inference, slow training |
| **Explainability** | High, explicit tables | High, transparent math & statutory citations | Low (Unacceptable for Customs Law audit) |
| **Maintainability** | Simple, easy config | Excellent, modularized pure Python | High debt, retraining drift |
| **Statutory Fit** | Rigid, misses edge tidal windows | **Best: Fully adheres to Decree 58 & Decision 1399** | Fails legal auditability |

- **Recommendation**: **Option B (Ranked #1)**. Pure Python deterministic calculation engine using interval checks for berth-time windows and weighted statutory risk scoring. Zero external heavy dependencies.

---

## 4. Adoption Risks & Mitigations
- **Tidal Harmonic Phase Discrepancy**: Real meteorological surge deviates from harmonic tide. Mitigation: allow real-time water level sensor offsets ($\Delta h_{sensor}$).
- **Customs Gateway Downtime (VNACCS/VASSCM)**: Terminal gate blocked on API timeout. Mitigation: offline cryptographic QR fallback with signed timestamp and post-sync reconciliation.
- **Squat Model Underestimation in Canal**: Shallow-water canal effect increases squat by 30%. Mitigation: conservative Barass open/confined selector with fail-safe safety margin.

---

## 5. Limitations
- Research omits quay crane split scheduling (QC-to-hatch optimization) and container yard slot stacking micro-mechanics.
- Vessel wave motion ($Z_{wave}$) assumes empirical wave allowance rather than full 3D hydrodynamic seakeeping panel analysis.

---

## 6. Unresolved Questions
1. Does the target terminal have real-time UKC telemetry (D-UKC) integrated with VTS or rely solely on pre-computed tide tables?
2. Does VASSCM gate-out require dedicated MQ/SOAP web services with TCHQ or HTTPS REST API v2?
