# Báo cáo Brainstorming Chuyên sâu & Thiết kế Kỹ thuật: Maritime Phases 367–370 & Refactor Kiến trúc

**Chủ đề:** Giám sát Chất lượng Nhiên liệu Hàng hải ISO 8217, Hệ thống Pin Tích năng Hàng hải BESS & Chống Thoát nhiệt, Chỉ số Tàu Xanh Cảng biển ESI & Điều khiển Tời buộc tàu Tự động Cân bằng Sóng AHC  
**Kiến trúc:** Hybrid Modular Facade Pattern (< 200 LOC sub-modules + Central Facade + Typer CLI + FastMCP Tools)  
**Tiêu chuẩn Quốc tế & Quy chuẩn Hàng hải:**
- **ISO 8217:2024 / CIMAC Guidelines & MARPOL Annex VI Reg 14 & 18** (Marine fuel specifications, catalytic fines Al+Si <= 60 ppm, kinematic viscosity, flash point >= 60°C, TSP <= 0.10% m/m, ASTM D4740 compatibility spot test).
- **DNV-RU-SHIP Pt.6 Ch.2 Battery(Power/Safety), IEC 62619 & IMO MSC.1/Circ.1455** (Marine Battery Energy Storage System BESS, C-rate limits, cell thermal runaway off-gas H2/CO monitoring, SoC/SoH degradation, 3-stage safety trip & fire deluge).
- **IAPH World Ports Climate Initiative (WPCI) Environmental Ship Index (ESI) & Thông tư 39/2023/TT-BGTVT** (Green port dues discount matrix, ESI NOx, ESI SOx, ESI CO2, OPS Onshore Power Supply cold-ironing bonus, rebate tiers 5-20%).
- **OCIMF MEG4, ISO 3730 & IMCA D 018** (Mooring Winch Auto-Tension render/heave window, Active Heave Compensation AHC vertical wave motion filtering efficiency >= 85%).

---

## 1. Phân tích Nghiệp vụ & Mô hình Tính toán Kỹ thuật

### Phase 367: Marine Fuel Oil Quality Assessment & ISO 8217 Bunker Compatibility Engine
- **Chỉ tiêu Kỹ thuật & Rủi ro Động cơ Diesel Thủy (ISO 8217:2024 & MARPOL VI)**:
  - **Mạt xúc tác nhôm và silic (Al + Si Catalytic Fines)**:
    - Giới hạn pháp lý tối đa theo ISO 8217: $[\text{Al} + \text{Si}] \le 60.0\text{ mg/kg}$ (ppm).
    - Ngưỡng an toàn vận hành trước máy lọc ly tâm (CIMAC recommendations): $[\text{Al} + \text{Si}] \le 25.0\text{ mg/kg}$. Nồng độ vượt ngưỡng gây cào xước sơ-mi xi-lanh và séc-măng nghiêm trọng trong vòng vài chục giờ vận hành.
  - **Điểm chớp cháy kín (Flash Point - Pensky-Martens Closed Cup)**:
    - Bắt buộc theo SOLAS II-2/Reg 4.2.1: $T_{\text{flash}} \ge 60.0^\circ\text{C}$. Nếu $T_{\text{flash}} < 60.0^\circ\text{C}$, nhiên liệu bị xếp loại hàng nguy hiểm dễ bốc cháy nổ, cấm nạp vào két trực nhật tàu.
  - **Độ nhớt động học (Kinematic Viscosity @ 50°C)**:
    - Phân loại cấp độ nhớt từ RMG 180 đến RMK 700 cSt. Cần tính toán nhiệt độ gia nhiệt két lắng/trực nhật để đưa độ nhớt tại vòi phun về dải tối ưu $10.0 - 15.0\text{ cSt}$.
  - **Độ ổn định cặn tiềm năng (Total Sediment Potential - TSP / TSA)**:
    - Giới hạn: $\text{TSP} \le 0.10\%\text{ m/m}$.
  - **Khả năng tương thích nhiên liệu khi phối trộn (Fuel Compatibility Spot Test - ASTM D4740)**:
    - Xếp hạng từ 1 đến 5. Điểm 1-2: tương thích hoàn toàn; Điểm >= 3: mất ổn định, nhựa asphaltene kết tủa làm tắc nghẽn toàn bộ phin lọc tự rửa.

### Phase 368: Marine Battery Energy Storage System (BESS) & Peak Shaving Safety Engine
- **Đặc tính Điện hóa & Bảo vệ An toàn BESS (DNV-RU-SHIP Pt.6 Ch.2 & IEC 62619)**:
  - **Cửa sổ vận hành Dung lượng pin (State of Charge - SoC)**:
    - Giới hạn an toàn: $15.0\% \le \text{SoC} \le 90.0\%$. Ngăn ngừa quá sạc tạo đoản mạch dendrite kim loại lithium và quá xả phá hủy cấu trúc cực dương.
  - **Độ suy hao tuổi thọ pin (State of Health - SoH)**:
    - Ngưỡng cảnh báo: $\text{SoH} < 80.0\%$; Ngưỡng loại thải EOL: $\text{SoH} \le 70.0\%$.
  - **Tốc độ sạc/xả C-rate**:
    - Chế độ sạc thường: $C \le 1.0\text{C}$; Chế độ cắt phụ tải đỉnh (Peak Shaving): xung tối đa $C_{\text{pulse}} \le 2.5\text{C}$.
  - **Chênh lệch nhiệt độ giữa các cell**: $\Delta T_{\text{cell}} \le 5.0^\circ\text{C}$; Nhiệt độ cell tối đa $T_{\text{max}} \le 45.0^\circ\text{C}$.
  - **Phát hiện sớm thoát nhiệt (Thermal Runaway Off-Gas Early Warning)**:
    - Trước khi nhiệt độ bùng phát, pin Li-ion giải phóng khí thoát: Hydro $H_2 \ge 50\text{ ppm}$, Cacbon monoxit $CO \ge 25\text{ ppm}$.
    - Cơ chế an toàn 3 cấp:
      - Cấp 1 (Alarm & De-rate): $T > 45^\circ\text{C}$ hoặc $\Delta T > 5^\circ\text{C}$.
      - Cấp 2 (Electrical Contactor Trip): $T > 55^\circ\text{C}$ hoặc phát hiện khí $H_2/CO$.
      - Cấp 3 (Fire Suppression): $T > 75^\circ\text{C}$ kích hoạt phun sương nước áp lực cao (Water Mist Deluge) ngâm chìm module pin.

### Phase 369: World Ports Environmental Ship Index (ESI) & Green Port Dues Incentive Engine
- **Công thức Tính toán Chỉ số Tàu Xanh ESI (IAPH WPCI Standards)**:
  - Điểm thành phần $\text{ESI}_{\text{NOx}}$ (tính từ độ cắt giảm NOx so với IMO Tier I/II/III).
  - Điểm thành phần $\text{ESI}_{\text{SOx}}$ (tính từ hàm lượng lưu huỳnh nhiên liệu $\le 0.50\%$ hoặc scrubber $\le 0.10\%$).
  - Điểm thành phần $\text{ESI}_{\text{CO2}}$ (tính từ mức cải thiện chỉ số hiệu quả năng lượng EEOI/CII).
  - Điểm thưởng nguồn điện bờ OPS (Onshore Power Supply / Cold Ironing): $+35\text{ điểm}$.
  - Tổng điểm ESI tổng hợp:
    $$\text{ESI}_{\text{Total}} = \frac{2 \cdot \text{ESI}_{\text{NOx}} + 2 \cdot \text{ESI}_{\text{SOx}} + \text{ESI}_{\text{CO2}} + \text{ESI}_{\text{OPS}}}{5} \in [0, 100]$$
  - Ma trận Ưu đãi Miễn giảm Phí cảng biển (Port Dues Rebate - Thông tư 39/2023):
    - $\text{ESI} \ge 50.0$: Hạng Vàng (Giảm 20% phí trọng tải và cầu bến).
    - $30.0 \le \text{ESI} < 50.0$: Hạng Bạc (Giảm 10%).
    - $20.0 \le \text{ESI} < 30.0$: Hạng Đồng (Giảm 5%).
    - $\text{ESI} < 20.0$: Tiêu chuẩn (Không miễn giảm).

### Phase 370: Mooring Winch Auto-Tension & Active Heave Compensation (AHC) Engine
- **Điều khiển Lực căng Tự động (Auto-Tension Window - OCIMF MEG4 & ISO 3730)**:
  - Lực căng mục tiêu đặt trước: $T_{\text{target}} \approx 15\% - 25\% \cdot \text{MBL}$.
  - Cửa sổ nhả tự động (Auto-Render): Khi lực căng $T_{\text{line}} \ge 1.25 \cdot T_{\text{target}}$ (do triều dâng hoặc sóng dạt), tời tự động xả dây để tránh đứt cáp.
  - Cửa sổ thu tự động (Auto-Heave): Khi lực căng $T_{\text{line}} \le 0.75 \cdot T_{\text{target}}$ (do triều rút), tời tự động thu dây để giữ tàu ép sát đệm va.
- **Bù chuyển vị đứng do sóng AHC (Active Heave Compensation - IMCA D 018)**:
  - Tín hiệu gia tốc kế / IMU đo chuyển vị nhấp nhô của tàu $z_{\text{ship}}(t) = A_h \sin(\omega t)$.
  - Vòng điều khiển Feedforward bù trừ vận tốc tời $v_{\text{winch}}(t) = -\dot{z}_{\text{ship}}(t)$.
  - Hiệu suất bù nhấp nhô yêu cầu:
    $$\eta_{\text{AHC}} = \left(1 - \frac{\text{RMS}(z_{\text{load}})}{\text{RMS}(z_{\text{ship}})}\right) \cdot 100\% \ge 85.0\%$$

---

## 2. Chiến lược Tái cấu trúc (Refactoring Architecture)

Bên cạnh việc phát triển 4 micro-engines mới cho Phases 367–370, kế hoạch refactoring tập trung vào:
1. **Kiến trúc Hybrid Modular Facade**: Tất cả các tệp mới tuân thủ nghiêm ngặt $< 200\text{ LOC}$.
2. **Kế hoạch Tách nhỏ các tệp Maritime Monolithic cũ**:
   - `src/core/maritime_operations_engine.py` (695 lines) -> chuẩn bị lộ trình bóc tách thành các module chuyên biệt theo domain.
   - `src/core/maritime_fuel_liens_berth_customs_engine.py` (867 lines) -> phân rã thành các sub-engines nhỏ độc lập.
3. **Đồng bộ Giao diện CLI & FastMCP**: 8 bí danh tiếng Việt trực quan, 4 FastMCP tools phi đồng bộ phục vụ AI agent.

---

## 3. Kiến trúc Module Dự kiến (< 200 LOC per file)

```
src/
├── core/
│   ├── maritime/
│   │   ├── phase_367_fuel_oil_iso8217_compatibility.py   (~120 LOC)
│   │   ├── phase_368_marine_battery_bess_safety.py       (~135 LOC)
│   │   ├── phase_369_port_esi_green_incentive.py         (~115 LOC)
│   │   └── phase_370_mooring_autotension_ahc.py          (~125 LOC)
│   └── maritime_fuel_bess_esi_ahc_engine.py              (~135 LOC)
├── cli/
│   └── commands/
│       └── maritime_fuel_bess_esi_ahc_command.py         (~140 LOC)
```

Suite kiểm thử Zero-mock:
```
tests/
├── test_maritime_fuel_bess_unit_suite.py                 (~125 LOC)
├── test_maritime_esi_ahc_unit_suite.py                   (~120 LOC)
└── test_maritime_367_to_370_cli_mcp_suite.py             (~125 LOC)
```
