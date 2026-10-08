# UI/UX & Design Guidelines: Maritime Commercial & Port Ops (Phases 267-270)

## Design System Tokens
- **Theme**: Oceanic Navy & High-Alert Maritime Industrial
- **Palette**:
  - Primary Base: `#0B192C` (Deep Ocean Navy)
  - Secondary Base: `#1E3E62` (Maritime Steel Blue)
  - Accent Safe / Compliant: `#00B4D8` (Pacific Turquoise) / `#10B981` (Vessel Cleared Green)
  - Warning / Underperformance: `#F59E0B` (Advisory Amber)
  - Hazard / IMDG Danger: `#EF4444` (Hazard Red) / `#F97316` (Explosive Orange)
  - Neutral / Card Background: `#1F2937`
  - Typography: Monospace for numeric values (speeds, tons, coordinates, coordinates, dues, GT), clean sans-serif for legal disclaimers.

---

## Wireframe & Interaction Specs

### 1. Charterparty Speed & Consumption Cockpit (`charterpartyspeed`)
- **Inputs**: Warranted speed (kts), warranted fuel (t/day), actual passage log (distance, steaming hours, actual fuel, good weather window % or hours, weather factors).
- **Outputs**:
  - Net time lost / gained (hrs / days).
  - Net bunker overconsumption (VLSFO / LSMGO tonnes).
  - Net hire adjustment value ($ USD) with color-coded liability badge (`OWNERS_LIABLE`, `CHARTERERS_OFFSET`, `BALANCED`).

### 2. e-D/O & Container Deposit Settlement Matrix (`edorelease`)
- **Inputs**: B/L number, container count, container type (20ft Dry, 40ft Dry, 40ft Reefer), deposit amount per unit, return date, free time, damage repair cost (IICL-5), cleaning fee.
- **Outputs**:
  - Free time adherence status (`ON_TIME`, `OVERDUE`).
  - Total deductions (detention + damage repairs + washing).
  - Net deposit refund payable to consignee within statutory 3-5 days.

### 3. Port Tonnage Dues & Safety Charges Calculator (`tonnagedues`)
- **Inputs**: Vessel Gross Tonnage (GT), voyage type (`INTERNATIONAL`, `DOMESTIC`), port zone, entry/exit count, anchorage duration (hours), green vessel certification.
- **Outputs**:
  - Tonnage dues itemization ($ USD or VND).
  - Maritime safety dues itemization.
  - Anchorage fairway dues itemization.
  - Total official state port charges.

### 4. IMDG Dangerous Goods Port Handling & Segregation Matrix (`imdgport`)
- **Inputs**: Primary IMDG Class (e.g., 3 - Flammable Liquid), Secondary IMDG Class (e.g., 5.1 - Oxidizing Substances), gross weight (tons), dwell time planned (hours).
- **Outputs**:
  - Required Segregation Category (`AWAY_FROM`, `SEPARATED_FROM`, `SEPARATED_BY_COMPARTMENT`, `PROHIBITED_ADJACENT`).
  - Handling Mode (`DIRECT_DELIVERY_MANDATORY`, `HAZARDOUS_YARD_WITH_BUFFER`, `STANDARD_STORAGE`).
  - Minimum buffer safety distance (meters) & Fire Schedule (EmS).
  - Port handling statutory surcharge (+50% to +200%).
