# Research Report: MARPOL Fuel Switchover & Maritime Lien Priority Waterfall (Phases 275-276)

## Executive Summary
This report defines the statutory frameworks, physics/chemical thermodynamics, priority ranking algorithms, and edge-case handling for:
1. **Phase 275: MARPOL Annex VI Fuel Sulfur Cap & Port/ECA Fuel Oil Switchover Engine** (MARPOL Annex VI Reg. 14, MEPC.1/Circ.864/Rev.1, Circular 39/2023/TT-BGTVT).
2. **Phase 276: Maritime Lien Priority Waterfall & Judicial Auction Proceeds Distribution Engine** (VMC 2015 Arts. 37-43, Civil Code 2015, Decree 58/2017/NĐ-CP, Decree 62/2015/NĐ-CP).

---

## 1. Phase 275: MARPOL Annex VI Fuel Oil Switchover Engine

### 1.1 Statutory & Technical Frameworks
- **MARPOL Annex VI Reg. 14**: Global sulfur limit $0.50\% \text{ m/m}$ (effective 2020-01-01); Emission Control Areas (ECA / SECA) limit $0.10\% \text{ m/m}$ (effective 2015-01-01). Port stay EU/local directives enforce $0.10\%$ sulfur at berth.
- **IMO MEPC.1/Circ.864/Rev.1**: *2019 Guidelines on onboard sampling for the verification of the sulfur content of the fuel oil used on board ships* and switchover calculation practices.
- **ISO 8217:2017 / 2024**: Marine fuel standards (VLSFO, ULSFO/MGO). Minimum kinematic viscosity constraint $\nu \ge 2.0\text{ cSt}$ at engine/pump inlet to prevent plunger scuffing/seizure. Maximum temperature gradient $\le 2^\circ\text{C/min}$ across fuel conditioning module to avoid thermal shock.

### 1.2 Mathematical Formulations

#### Exponential Mixing Dilution Model
In a continuously mixed fuel service loop (service tank, buffer/mixing tank, booster pipes), switchover from high sulfur concentration $C_0$ to target sulfur content $C_{\text{target}}$:
$$\frac{dC(t)}{dt} = -\frac{Q_{\text{fuel}}}{V_{\text{system}}} (C(t) - C_{\text{in}})$$
Assuming inlet is pure low-sulfur fuel ($C_{\text{in}} = C_{\text{low}} < C_{\text{target}}$):
$$C(t) = C_{\text{low}} + (C_0 - C_{\text{low}}) \cdot \exp\left(-\frac{Q_{\text{fuel}}}{V_{\text{system}}} \cdot t\right)$$
Switchover duration $t_{\text{so}}$ to reach boundary compliance $C_{\text{target}}$:
$$t_{\text{so}} = \frac{V_{\text{system}}}{Q_{\text{fuel}}} \cdot \ln\left(\frac{C_0 - C_{\text{low}}}{C_{\text{target}} - C_{\text{low}}}\right)$$
Where:
- $V_{\text{system}}$: total active fuel loop volume ($\text{m}^3$)
- $Q_{\text{fuel}}$: engine fuel consumption rate ($\text{m}^3/\text{h}$) at service transit speed
- $C_0$: initial sulfur content ($\% \text{ m/m}$, e.g. $0.50\%$ or $3.5\%$)
- $C_{\text{low}}$: sulfur content of bunker being flushed in (e.g. $0.08\%$ for $0.10\%$ ECA limit)
- $C_{\text{target}}$: regulatory threshold ($0.10\%$ for ECA, $0.50\%$ for global)

#### Thermal Ramping & Viscosity Safety
To prevent fuel pump sticking:
$$\left|\frac{dT}{dt}\right| \le 2.0^\circ\text{C/min} \implies \Delta t_{\text{thermal}} \ge \frac{|T_{\text{HFO}} - T_{\text{MGO}}|}{2.0^\circ\text{C/min}}$$
Viscosity verification via Walther-ASTM D341 equation:
$$\log_{10}(\log_{10}(\nu + 0.7)) = A - B \cdot \log_{10}(T_K)$$
Engine inlet constraint: $\nu(T_{\text{inlet}}) \ge 2.0\text{ cSt}$ (requires chiller/cooler if MGO is too hot).

#### Boundary Transit Distance
$$d_{\text{switchover}} = v_{\text{vessel}} \cdot \max(t_{\text{so}}, \Delta t_{\text{thermal}})$$
Ship must initiate changeover at distance $d \ge d_{\text{switchover}}$ before crossing ECA boundary or entering port jurisdictional waters (Circular 39/2023/TT-BGTVT).

### 1.3 Validation & Edge Cases
- **Already Compliant**: $C_0 \le C_{\text{target}} \implies t_{\text{so}} = 0$, $d_{\text{switchover}} = 0$.
- **Distance Deficit**: $d_{\text{remaining}} < d_{\text{switchover}} \implies$ Violation flag; require speed reduction ($v_{\text{vessel}}$ down) or engine load increase to burn fuel faster.
- **Viscosity Drop Violation**: If $\nu(T) < 2.0\text{ cSt}$, trigger MGO cooler interlock alarm.
- **Unattainable Target**: If $C_{\text{low}} \ge C_{\text{target}}$, mathematically impossible; reject input.

---

## 2. Phase 276: Maritime Lien Priority Waterfall & Judicial Auction Distribution

### 2.1 Statutory Basis (Vietnam Maritime Code 2015 Arts. 37-43)
- **Art. 37 (Statutory Maritime Liens - Quyền cầm giữ hàng hải)**: Rank superior to all mortgages and unsecured debts. Five mandatory statutory tiers:
  1. **Tier 1 (Crew Claims)**: Wages, repatriation costs, social insurance, and medical contributions owed to Master, officers, and ship crew.
  2. **Tier 2 (Life & Bodily Injury)**: Damages for loss of life, personal injury occurring in direct connection with vessel operation.
  3. **Tier 3 (Salvage & General Average)**: Remuneration for maritime salvage (*Cứu hộ hàng hải*) and contribution to General Average (*Tổn thất chung*).
  4. **Tier 4 (Port, Pilotage & Safety Dues)**: Port dues, fairway tolls, pilotage charges, and maritime safety charges.
  5. **Tier 5 (Tortious Damage / Collision)**: Extracontractual physical loss or property damage arising from maritime collision or navigation torts.
- **Art. 38 (Lien Hierarchy & Inversion Rule)**:
  - Higher tiers take precedence over lower tiers.
  - Claims within the same tier share pro-rata if funds are insufficient, **except** Tier 3: Later salvage operations take precedence over earlier salvage operations (*inverse chronological order*).
- **Art. 39 (Extinction / Prescription Timebar)**:
  - Maritime liens expire after **1 year** from the date the claim arose, unless legal arrest or judicial enforcement commenced prior to expiration.
- **Art. 41 (Ranking vs Ship Mortgages)**:
  - Judicial auction costs and court enforcement fees (Decree 62/2015/NĐ-CP) deducted **first** from gross proceeds.
  - Tiers 1-5 liens deducted next.
  - Registered ship mortgages (*Thế chấp tàu biển*) satisfied next (in order of registration time).
  - Residual balance distributed to general unsecured maritime claims (Decree 58/2017/NĐ-CP).

### 2.2 Mathematical Waterfall Distribution Algorithm
Let $P_{\text{gross}}$ be gross auction proceeds.
1. **Deduct Judicial & Auction Enforcement Costs**:
   $$P_{\text{net0}} = P_{\text{gross}} - C_{\text{enforcement}}$$
   If $P_{\text{net0}} \le 0$, net available is 0; enforcement unpaid balance becomes court judgment debt.
2. **Filter Active vs Expired Liens**:
   For claim $i$, if $(t_{\text{auction}} - t_{\text{claim}, i} > 365.25\text{ days})$ and vessel was not arrested prior to expiry, claim is time-barred:
   $$\text{Active}(c_i) = \text{False}$$
3. **Waterfall Cascade across Tiers $k \in \{1, 2, 3, 4, 5\}$**:
   - For Tier 3 (Salvage), sort claims in descending order of salvage date ($t_{s1} > t_{s2} > \dots$).
   - For Tiers 1, 2, 4, 5, sum tier claim obligations $D_k = \sum_{i \in \text{Tier } k} A_i$.
   - If $P_{\text{avail}} \ge D_k$: distribute $100\%$ to all tier claims; $P_{\text{avail}} \leftarrow P_{\text{avail}} - D_k$.
   - If $0 < P_{\text{avail}} < D_k$:
     - For non-Tier 3: allocate pro-rata: $\text{Payout}(c_i) = A_i \cdot \frac{P_{\text{avail}}}{D_k}$; $P_{\text{avail}} \leftarrow 0$.
     - For Tier 3: pay newest salvage in full until $P_{\text{avail}}$ exhausted.
4. **Waterfall to Mortgages & Unsecured Debts**:
   - Registered mortgages sorted by priority of registration timestamp: $\text{Payout}(M_j) = \min(M_j, P_{\text{avail}})$.
   - Residual proceeds $P_{\text{unsecured}}$ allocated pro-rata to general maritime claims.

### 2.3 Edge Cases & Safeguards
- **Zero/Deficit Proceeds**: $P_{\text{gross}} < C_{\text{enforcement}} \implies$ all lienholders receive 0, deficit logged.
- **Time-Barred Crew Claims**: Wages accrued $> 1\text{ year}$ prior to arrest lose lien status, demoted to unsecured claims.
- **Currency Conversion**: Foreign currency claims converted at official SBV rate on auction settlement date.

---

## 3. Unresolved Questions
1. Should dual-fuel LNG/MGO installations account for pilot fuel blending ratios during boil-off gas changeover in Phase 275?
2. Does Vietnam Maritime Court precedent prioritize State wreck-removal costs under Decree 58/2017 ahead of Tier 1 crew wages or as part of Tier 4 port safety dues?
