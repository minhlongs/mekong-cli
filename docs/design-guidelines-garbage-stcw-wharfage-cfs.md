# Hướng dẫn Thiết kế Giao diện Terminal: Phases 287-290

## Bảng màu & Phong cách Hiển thị (Rich CLI)
- **Primary / Border**: `cyan` & `blue` cho phân hệ hàng hải và cảng biển.
- **Success / Tuân thủ**: `green` (Đạt chuẩn MARPOL, đủ giờ nghỉ STCW, trong hạn CFS).
- **Warning / Cảnh báo**: `yellow` (Gần chạm trần 90 ngày CFS, tàu làm việc gần ngưỡng 14h, neo quá giờ).
- **Error / Vi phạm**: `bold red` (Xả nhựa xuống biển, vi phạm giờ nghỉ MLC, cáp E-Seal bị cắt, vượt 90 ngày CFS).

## Wireframe CLI Terminal

### 1. Phase 287: MARPOL Annex V Rác thải (`mekong garbage evaluate`)
```
╭──────────────── MARPOL Annex V Garbage Discharge Evaluation ────────────────╮
│ Category: FOOD_WASTE (Comminuted <=25mm)  | Zone: OUTSIDE_SPECIAL_AREA       │
│ Distance: 4.5 NM (Min req: 3.0 NM)        | Speed: 11.2 kts (En route: PASS) │
│ Verdict: PERMITTED_OVERBOARD              | GRB Log Code: D-1                │
│ SHA-256 Token: 4f8a29b...c1e9             | Storage Method: DISCHARGE_SEA    │
╰─────────────────────────────────────────────────────────────────────────────╯
```

### 2. Phase 288: STCW & MLC Giờ nghỉ thuyền viên (`mekong resthours verify`)
```
╭─────────────── STCW A-VIII/1 & MLC 2006 Seafarer Rest Verification ─────────╮
│ Seafarer: Chief Officer (Nguyen Van A)    | Cycle: 24h & 7-Day Window        │
│ 24h Rest Total: 11.0 hrs (Min: 10.0 hrs)  | Longest Rest: 7.0 hrs (Min: 6.0) │
│ Rest Periods: 2 (Max: 2)                  | Span Between Rests: 11.0 hrs     │
│ 7-Day Rest Total: 82.0 hrs (Min: 77.0 hrs)| Status: FULLY_COMPLIANT          │
╰─────────────────────────────────────────────────────────────────────────────╯
```

### 3. Phase 289: Cước Cầu bến Cảng biển (`mekong wharfage calculate`)
```
╭─────────────── Circular 39/2023/TT-BGTVT Wharfage & Berth Occupancy ────────╮
│ Vessel GT: 35,000 GT                      | Berth Type: CONTAINER_BERTH      │
│ Port Area: AREA_III (Cái Mép - Thị Vải)   | Duration: 36.0 hrs               │
│ Standard Rate: $0.0035/GT/hr              | Base Berthage: $4,410.00 USD     │
│ Overstay: 4.0 hrs (+50% surcharge)        | Overstay Fee: $735.00 USD        │
│ Total Berth Charge: $5,145.00 USD (VND: 128,625,000)                        │
╰─────────────────────────────────────────────────────────────────────────────╯
```

### 4. Phase 290: CFS & E-Seal Tracking (`mekong cfs supervise`)
```
╭─────────────── Customs CFS Deconsolidation & E-Seal Security Log ────────────╮
│ Container ID: TCNU8923410                 | CFS Location: Cat Lai CFS        │
│ Cargo Type: LCL Deconsolidation (12 pkgs) | Days in Storage: 42 / 90 days    │
│ E-Seal ID: ESEAL-VN-2026-9921             | Cable State: INTACT              │
│ GPS Route Deviation: 0.0 m (Max: 500 m)   | Tamper Status: NORMAL            │
│ Customs Audit Status: COMPLIANT_CLEARED                                      │
╰─────────────────────────────────────────────────────────────────────────────╯
```
