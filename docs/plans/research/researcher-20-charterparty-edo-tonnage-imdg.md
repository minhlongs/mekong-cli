# Research Report: Phases 267-270 Maritime Operations & Commercial Compliance

## Executive Summary
This report analyzes statutory frameworks, mathematical models, and operational workflows for Phases 267-270 of Mekong CLI v6.0:
1. **Phase 267: Time Charterparty Speed & Consumption Warranty Claim** (VMC 2015 Arts. 215-230, BIMCO NYPE 93 / NYPE 2015, *The Didymi* [1988], *The Gas Enterprise* [1993]).
2. **Phase 268: Electronic Delivery Order (e-D/O) & Container Deposit Settlement** (VMC 2015 Arts. 160 & 168, Circular 38/2015/TT-BTC, Circular 39/2018/TT-BTC, Decree 58/2017/NĐ-CP).
3. **Phase 269: Seaport Tonnage Dues & Maritime Safety Tariffs** (VMC 2015 Arts. 104, 107-112, Circular 39/2023/TT-BGTVT, Circular 12/2024/TT-BGTVT).
4. **Phase 270: IMDG Dangerous Goods Seaport Handling & Segregation Safety Matrix** (IMDG Code Amdt 41-22, Decree 58/2017/NĐ-CP Arts. 73-77, Decree 34/2024/NĐ-CP).

---

## 1. Phase 267: Time Charterparty Speed & Consumption Warranty
### Legal & Contractual Basis
- **BIMCO NYPE 93 Cl. 8 & 15 / NYPE 2015 Cl. 12**: "Speed and consumption warranted in good weather conditions..."
- **Good Weather Criteria**: Wind $\le$ Beaufort Force 4, Sea State $\le$ Douglas 3 (significant wave height $\le 1.25\text{m}$), no adverse currents or negative swell.
- **English Law Precedents**:
  - *The Didymi* [1988] 2 Lloyd's Rep. 108: Establish underperformance in good weather, then extrapolate across the entire sea passage.
  - *The Gas Enterprise* [1993] 2 Lloyd's Rep. 352: Net financial offsetting between speed underperformance (time lost) and bunker savings, or speed overperformance vs bunker overconsumption.
### Mathematical Formulation
1. **Good Weather Speed Deficiency**:
   $$V_{\text{gw\_deficiency}} = V_{\text{warranted}} - V_{\text{actual\_gw}}$$
2. **Net Time Lost on Passage**:
   $$T_{\text{lost\_hours}} = \left(\frac{D_{\text{total}}}{V_{\text{actual\_all\_weather}} + \Delta V_{\text{curr}}}\right) - \left(\frac{D_{\text{total}}}{V_{\text{warranted}}}\right)$$
3. **Bunker Overconsumption**:
   $$F_{\text{over\_tonnes}} = F_{\text{actual}} - \left(T_{\text{allowed\_days}} \times F_{\text{warranted\_per\_day}}\right)$$
4. **Net Financial Claim Value (USD)**:
   $$\text{Claim} = (T_{\text{lost\_days}} \times \text{Daily Hire Rate}) + \sum (F_{\text{over}, i} \times P_{\text{bunker}, i})$$

---

## 2. Phase 268: Electronic Delivery Order (e-D/O) & Container Deposit Settlement
### Legal & Regulatory Basis
- **VMC 2015 Art. 160**: Obligation to deliver cargo upon surrender of Bill of Lading or electronic substitute.
- **Circular 38/2015/TT-BTC & Circular 39/2018/TT-BTC**: Electronic customs clearance integration via Vietnam National Single Window (VNSW).
- **Container Demurrage & Empty Return Deposit Lifecycle**:
  - Consignee pays ocean carrier freight, terminal handling charges (THC), and container deposit (*cược vỏ cont*): Typically 1,000,000 - 3,000,000 VND/20ft; 2,000,000 - 5,000,000 VND/40ft; 5,000,000 - 10,000,000 VND for Reefers.
  - Verification of empty container return at depot within allowed free time.
  - Deductions: Container damage (IICL-5 survey repair estimate), equipment cleaning fee, and overdue detention.
  - Net refund calculation within statutory 3-5 banking days.

---

## 3. Phase 269: Seaport Tonnage Dues & Maritime Safety Tariffs
### Statutory Tariff Structure (Circular 39/2023/TT-BGTVT & Circular 12/2024)
- **Tonnage Dues (*Phí trọng tải tàu thuyền*)**:
  - International voyages: USD 0.034 / GT per entry/exit call.
  - Domestic voyages: 250 - 450 VND / GT per entry/exit call.
- **Maritime Safety Dues (*Phí bảo đảm hàng hải*)**:
  - International voyages: USD 0.076 / GT for entry/exit; reduced 50% for special transshipment.
  - Domestic voyages: 700 - 1,400 VND / GT depending on port zone (Zone I, II, III).
- **Anchorage & Fairway Channel Dues (*Phí neo đậu*)**:
  - In port water / wait area: USD 0.0005 / GT-hour (international) or 15 - 30 VND / GT-hour (domestic).
  - Extended stay penalty: +50% after 30 consecutive days at anchorage.
- **Green Port Incentive**: 10% to 20% discount on safety and tonnage dues for vessels with Clean Shipping Index / Green Award / EEDI reduction certificate.

---

## 4. Phase 270: IMDG Dangerous Goods Seaport Handling & Segregation Matrix
### Statutory & Regulatory Basis
- **IMO IMDG Code Amendment 41-22**: Classification Class 1 to 9.
- **Decree 58/2017/NĐ-CP Arts. 73-77 & Decree 34/2024/NĐ-CP**: Hazardous cargo port safety regulations.
- **Handling Requirements by IMDG Class**:
  - Class 1 (Explosives) & Class 7 (Radioactive): Direct delivery to/from barge or truck (*giao thẳng*), dwell time $\le 2$ hours at wharf, strictly prohibited in standard yard.
  - Class 2.1 (Flammable Gas), Class 3 (Flammable Liquids), Class 5.1/5.2 (Oxidizers/Peroxides): Dedicated hazardous yard, 50m blast/fire barrier, continuous water deluge.
  - Class 6.1 (Toxic), Class 8 (Corrosives): Chemical catchment sumps and neutralizers required.
- **Segregation Table 7.2.4**:
  - 1: "Away from" (min 3m horizontal distance).
  - 2: "Separated from" (min 6m or 1 container space).
  - 3: "Separated by a complete compartment or hold" (min 12m or bulkhead).
  - 4: "Separated longitudinally by an intervening complete compartment".
- **Port Surcharges**: +50% for Class 4, 6, 8; +100% for Class 2, 3, 5; +150% to +200% for Class 1 & 7 under Circular 39/2023.
