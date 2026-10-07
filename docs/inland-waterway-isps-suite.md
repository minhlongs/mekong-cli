# Vietnam Inland Waterway Navigation, Container Feeder Barging, Maritime Search & Rescue (SAR) & ISPS Security Suite (Phases 187–190)

## 1. Overview & Regulatory Framework
This suite implements end-to-end statutory calculations, decision engines, CLI commands, and FastMCP tools for Vietnam's inland waterway logistics, maritime search & rescue operations, and port facility security.

- **Phase 187: Vietnam Inland Waterway Navigation & Bridge Clearance**
  - *Statutory Basis*: Luật Giao thông đường thủy nội địa 2004 (sửa đổi 2014) & Thông tư 46/2016/TT-BGTVT.
  - *Key Formulas*:
    - Bridge Net Air Clearance: $\Delta h_{air} = H_{bridge} - H_{vessel\_air} \ge 0.50\text{ m}$ (safety margin).
    - Under Keel Clearance: $\text{UKC} = D_{channel} - D_{vessel\_draft} \ge 0.30\text{ m}$ (grounding safety).
    - Waterway Classifications: Cấp Đặc biệt (depth $\ge 4.0\text{m}$, air draft $\ge 11.0\text{m}$) down to Cấp VI.

- **Phase 188: Container Feeder Barging & Mekong Transit Freight**
  - *Statutory Basis*: Thông tư 39/2023/TT-BGTVT, Thông tư 248/2016/TT-BTC, and the Vietnam-Cambodia Mekong Navigation Treaty.
  - *Tariffs*:
    - TP.HCM – Cái Mép: 1,800,000 VND / TEU; 3,200,000 VND / FEU (4.5 hours).
    - ĐBSCL – Cái Mép: 3,500,000 VND / TEU; 6,200,000 VND / FEU (14.0 hours).
    - TP.HCM – Phnom Penh: 8,500,000 VND / TEU; 15,000,000 VND / FEU + 2,500,000 VND Treaty Fee (32.0 hours).
    - Hải Phòng – Bắc Ninh ICD: 2,200,000 VND / TEU; 3,900,000 VND / FEU (7.0 hours).
    - Dangerous Goods (DG) Surcharge: +10% per dangerous box.
    - Waterway Port Dues: 150 VND / DWT + 50,000 VND clearance fee.

- **Phase 189: Maritime Search & Rescue (SAR) & Wreck Removal**
  - *Statutory Basis*: IAMSAR Manual Vol II & Nghị định 05/2017/NĐ-CP (Quản lý và xử lý tài sản chìm đắm).
  - *Drift Vector Physics*:
    - Water Current Drift: $V_{current} \times t$, direction $\theta_{current}$.
    - Wind Leeway Drift: $V_{leeway} = 0.03 \times V_{wind}$, downwind direction $(\theta_{wind} + 180^\circ) \bmod 360^\circ$.
    - Coordinate translation: $d_{lat} = dy / 60$, $d_{lon} = dx / (60 \times \cos(\text{avg\_lat}))$.
    - Search Area: Square bounding box $(2 \times R_{search})^2$ based on navigational error and drift variance.
  - *Wreck Removal Plan Window*: 30 calendar days statutory limit; triggers mandatory forced removal and maritime lien enforcement under Bộ luật Hàng hải 2015 Art. 284 upon breach.

- **Phase 190: Port Facility & Ship Security (ISPS Code)**
  - *Statutory Basis*: SOLAS 74 Chapter XI-2, ISPS Code Parts A & B, Nghị định 159/2018/NĐ-CP.
  - *Security Levels*: Level 1 (Normal), Level 2 (Heightened), Level 3 (Exceptional/Crisis).
  - *Effective Security Tier*: $\max(\text{Port Level}, \text{Ship Level})$.
  - *Declaration of Security (DoS)*: Mandatory if Level(Port) $\neq$ Level(Ship) or either party is at Level 3.

---

## 2. CLI Usage Examples

```bash
# 1. Evaluate Bridge Clearance & UKC
mekong waterway clearance "Barge SG-9988" --class CLASS_I --bridge "Binh Loi Bridge" --bridge-air 11.0 --vessel-air 8.5 --channel-depth 4.5 --vessel-draft 3.0

# 2. Calculate Feeder Barging Freight
mekong barge freight HCM_CAI_MEP --teu 50 --feu 10 --dg 2 --dwt 2000

# 3. Compute Maritime SAR Search Box
mekong sar datum SAR-2026-VT01 --region REGION_III --lat 10.25 --lon 107.05 --drift-hours 4.0 --current-speed 1.5 --current-dir 210 --wind-speed 15 --wind-dir 45

# 4. Assess Wreck Removal Deadline
mekong sar wreck "MV THAI HUNG 28" --sinking-date 2026-10-01 --assess-date 2026-10-10

# 5. Evaluate ISPS Port & Ship Security Compliance
mekong isps compliance "Cai Mep International Terminal" --port-level LEVEL_1 --vessel "MV COSCO SAIGON" --ship-level LEVEL_2
```

All commands support `--json` for headless automation and JSON pipelines.

---

## 3. FastMCP Tool Interface
External AI Agents and LLMs can interact with these capabilities via MCP endpoints:
- `mekong_waterway_clearance` / `waterway_clearance`
- `mekong_barge_freight` / `barge_freight`
- `mekong_sar_datum` / `sar_datum`
- `mekong_sar_wreck` / `sar_wreck`
- `mekong_isps_compliance` / `isps_compliance`
