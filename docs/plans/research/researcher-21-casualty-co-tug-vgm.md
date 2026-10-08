# Technical & Legal Research Report: Maritime Casualty, e-C/O, Tugboat Tariffs & SOLAS VGM Suite (Phases 271-274)

## Executive Summary
This research establishes the statutory frameworks, international conventions, and computational formulas for Phases 271-274 of Mekong CLI v6.0:
1. **Phase 271: Maritime Casualty Investigation, Formal Inquiry & Marine Board** (IMO Res. MSC.255(84), Circular 34/2015/TT-BGTVT, VMC 2015 Arts. 113-116).
2. **Phase 272: Electronic Certificate of Origin (e-C/O) & Preferential Rules of Origin (ROO)** (Decree 31/2018/NĐ-CP, Circular 05/2018/TT-BCT, EVFTA/CPTPP RVC & CTC algorithms).
3. **Phase 273: Seaport Tugboat Towage Tariffs & Assisted Berthing/Unberthing Service Charges** (Circular 39/2023/TT-BGTVT Section III, Circular 12/2024/TT-BGTVT).
4. **Phase 274: SOLAS Verified Gross Mass (VGM) Container Weighing & Tolerance Verification** (SOLAS Reg. VI/2, IMO MSC.1/Circ.1475, Circular 39/2023/TT-BGTVT).

---

## 1. Phase 271: Marine Casualty Formal Inquiry & Severity Classification
### Statutory & Treaty Basis
- **IMO Casualty Investigation Code** (Resolution MSC.255(84) / MSC.257(84)).
- **Vietnam Maritime Code 2015** (Law No. 95/2015/QH13, Arts. 113-116: Báo cáo tai nạn hàng hải & Điều tra tai nạn hàng hải).
- **Circular 34/2015/TT-BGTVT** (Quy định về báo cáo và điều tra tai nạn hàng hải).

### Casualty Classification Hierarchy
1. **Very Serious Marine Casualty (VSMC)**:
   - Total loss of the ship.
   - Loss of life (fatality directly caused by marine casualty).
   - Severe pollution (significant environmental damage exceeding MARPOL thresholds).
   - Mandatory statutory marine safety investigation under IMO Code.
2. **Serious Marine Casualty (SMC)**:
   - Structural fire, explosion, grounding, collision, heavy weather damage, hull cracking, machinery failure causing immobilization.
   - Severe environmental pollution threat or severe disabling damage preventing vessel from proceeding.
3. **Marine Casualty (MC)**:
   - Damage to ship or equipment affecting seaworthiness or safety, but not qualifying as SMC/VSMC.
4. **Marine Incident (MI)**:
   - Hazardous occurrence, near-miss, or event affecting operations without actual damage.

### Statutory Reporting Timelines (Circular 34/2015/TT-BGTVT Art. 7)
- **Emergency initial notification**: within **24 hours** from occurrence to nearest Port Authority (Cảng vụ hàng hải).
- **Formal casualty report (Bản khai báo tai nạn hàng hải)**: within **48 hours** from port arrival.
- **Investigation duration**: maximum **60 days** for normal casualties; up to **90 days** for complex/VSMC investigations.

---

## 2. Phase 272: Electronic Certificate of Origin (e-C/O) & Preferential ROO Evaluator
### Statutory & Treaty Basis
- **Decree 31/2018/NĐ-CP** (Quy định chi tiết Luật Quản lý ngoại thương về xuất xứ hàng hóa).
- **Circular 05/2018/TT-BCT** (Quy định về xuất xứ hàng hóa).
- Free Trade Agreements: **EVFTA (Form EUR.1)**, **CPTPP**, **RCEP**, **VKFTA (Form VK)**, **ATIGA (Form D)**.

### Mathematical Qualification Algorithms
1. **Wholly Obtained (WO)**:
   - Raw materials, agricultural products, marine catches completely extracted or harvested in Vietnam.
2. **Change in Tariff Classification (CTC)**:
   - **CC**: Change in Chapter (2-digit HS Code shift).
   - **CTH**: Change in Tariff Heading (4-digit HS Code shift).
   - **CTSH**: Change in Tariff Sub-heading (6-digit HS Code shift).
3. **Regional Value Content (RVC)**:
   - **Direct (Build-Up) Method**:
     $$\text{RVC} = \frac{\text{VOM} + \text{Direct Labor} + \text{Direct Overhead} + \text{Profit}}{\text{FOB Value}} \times 100\%$$
   - **Indirect (Build-Down) Method**:
     $$\text{RVC} = \frac{\text{FOB Value} - \text{VNM}}{\text{FOB Value}} \times 100\%$$
     where $\text{VOM}$ is Value of Originating Materials, $\text{VNM}$ is Value of Non-Originating Materials.
   - Typical threshold: $\text{RVC} \ge 40\%$ (ATIGA/RCEP), $\text{RVC} \ge 45\%-50\%$ (CPTPP).
4. **De Minimis Tolerance Rule**:
   - Non-originating materials failing CTC are permitted if $\text{VNM} \le 10\%$ of FOB price.

---

## 3. Phase 273: Seaport Tugboat Towage Tariffs (Circular 39/2023/TT-BGTVT)
### Statutory Basis
- **Circular 39/2023/TT-BGTVT** (Biểu khung giá dịch vụ hoa tiêu, cầu bến, bốc dỡ, lai dắt tại cảng biển Việt Nam, Section III).
- **Circular 12/2024/TT-BGTVT** (Sửa đổi, bổ sung Thông tư 39/2023/TT-BGTVT).

### Port Geographic Zones
- **Zone I (North)**: Hải Phòng, Quảng Ninh, Nghi Sơn.
- **Zone II (Central)**: Đà Nẵng, Quy Nhơn, Dung Quất, Nha Trang.
- **Zone III (South)**: TP. Hồ Chí Minh, Cái Mép - Thị Vải, Vũng Tàu, Đồng Nai.

### Tariff Structure
- **International Voyages (USD/hour per tug capacity)**:
  - Tugboat $\le 1,000$ HP: \$120 - \$180 / hour.
  - Tugboat $1,001 - 2,000$ HP: \$190 - \$280 / hour.
  - Tugboat $2,001 - 3,000$ HP: \$300 - \$450 / hour.
  - Tugboat $3,001 - 4,000$ HP: \$480 - \$650 / hour.
  - Tugboat $> 4,000$ HP: \$700 - \$950 / hour.
- **Domestic Voyages (VND/hour)**:
  - Tugboat $\le 1,000$ HP: 2,500,000 - 3,800,000 VND / hour.
  - Tugboat $1,001 - 2,000$ HP: 4,000,000 - 6,000,000 VND / hour.
  - Tugboat $2,001 - 3,000$ HP: 6,500,000 - 9,500,000 VND / hour.
  - Tugboat $3,001 - 4,000$ HP: 10,000,000 - 14,000,000 VND / hour.
  - Tugboat $> 4,000$ HP: 15,000,000 - 20,000,000 VND / hour.
- **Statutory Surcharges**:
  - Night work (22:00 to 06:00): $+30\%$.
  - Hazardous / tanker cargo escort: $+30\%$.
  - Adverse weather / high current (wind Beaufort $\ge 6$ or current $\ge 3$ kts): $+50\%$.
  - Standby / cancellation within 2 hours: $50\%$ of hourly rate.

---

## 4. Phase 274: SOLAS Verified Gross Mass (VGM) Container Weighing & Tolerances
### Statutory & International Treaty Basis
- **SOLAS Chapter VI, Regulation 2** (Carriage of Cargoes - Cargo information).
- **IMO MSC.1/Circ.1475** (Guidelines regarding the verified gross mass of a container carrying cargo).
- **Circular 39/2023/TT-BGTVT** (Statutory container weighing tariffs at Vietnamese terminals).

### Authorized Methods
1. **Method 1 (Weighing the packed container)**:
   - Weighing the entire sealed container using calibrated weighbridge or terminal RTG/load cell scale.
2. **Method 2 (Calculating component weights)**:
   - Weighing all packages and cargo items + packing material + dunnage + container tare mass (stenciled on door).

### Statutory Tolerance & Gate Rejection Thresholds
- **Vietnam Maritime Administration (Vinamarine) & International Guideline**:
  - Weight discrepancy tolerance: $\pm 5\%$ or $\pm 500\text{ kg}$ (whichever is smaller) between declared VGM and terminal weighbridge check.
  - Maximum Gross Mass Check: Total weight must NEVER exceed maximum operating gross mass ($R_{\text{max}}$) stenciled on CSC safety plate (typically 30,480 kg or 32,500 kg for modern containers).
  - Terminal Action on Missing / Discrepant VGM: "NO VGM, NO LOAD" rule strictly enforced. Container placed on hold; weighing service tariff applied (150,000 - 350,000 VND per container under Circular 39/2023).
