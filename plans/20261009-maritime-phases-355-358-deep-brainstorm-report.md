# Báo cáo Brainstorming Chuyên sâu & Thiết kế Kỹ thuật: Maritime Phases 355–358 & Refactor Kiến trúc

**Chủ đề:** Tái hóa lỏng Hầm hàng LPG, Quản lý Cặn dầu & Lò đốt MARPOL, Lực căng Dây buộc tàu OCIMF MEG4 & An ninh Mạng Hàng hải IACS UR E26/E27  
**Kiến trúc:** Hybrid Modular Facade Pattern (< 200 LOC sub-modules + Central Facade + Typer CLI + FastMCP Tools)  
**Tiêu chuẩn Quốc tế & Quy chuẩn Hàng hải:**
- **IMO IGC Code Ch.7** (Cargo Pressure/Temperature Control) & **SIGTTO LPG Guidelines** (Re-liquefaction, Cascade Refrigeration Cycle COP, Cargo Boil-Off Gas re-condensation).
- **MARPOL Annex I Reg 12** (Sludge Tanks & Piping) & **IMO Res. MEPC.259(68) / MEPC.76(40)** (Shipboard Incinerator combustion temperature interlocks, calorific waste heat recovery, OWS 15 ppm 3-way divert valve).
- **OCIMF MEG4** (Mooring Equipment Guidelines 4th Edition), **PIANC Working Group 115/121** (Mooring line tension limits, passing ship hydrodynamic surge forces & snap-back zone prediction).
- **IMO Res. MSC.428(98)**, **MSC-FAL.1/Circ.3** & **IACS Unified Requirements (UR) E26 & E27** (Cyber resilience of ships, OT/IT network segmentation, anomaly detection, satellite link failover).

---

## 1. Phân tích Nghiệp vụ & Mô hình Tính toán Kỹ thuật

### Phase 355: LPG Cargo Reliquefaction & Compressor Control Engine
- **Môi trường & Cơ chế Vật lý (IGC Code Ch.7 & SIGTTO)**:
  - Tàu chở khí dầu mỏ hóa lỏng (Fully Refrigerated LPG Carriers) chở Propan ($-42^\circ\text{C}$) hoặc Butan ($-0.5^\circ\text{C}$) ở áp suất khí quyển.
  - Xâm nhập nhiệt từ môi trường sinh ra khí bay hơi (Boil-Off Gas - BOG):
    $$\dot{m}_{\text{BOG}} = \frac{Q_{\text{leakage}}}{\Delta H_{\text{vap}}} = \frac{U \cdot A \cdot (T_{\text{ambient}} - T_{\text{cargo}})}{\Delta H_{\text{vap}}} \quad (\text{kg/h})$$
  - Hệ thống tái hóa lỏng chu trình trực tiếp hoặc tầng (Cascade cycle với môi chất R404A/R134a hoặc chính hơi gas LPG):
    - Hệ số hiệu quả năng lượng (COP):
      $$\text{COP}_{\text{reliq}} = \frac{\dot{Q}_{\text{cooling}}}{W_{\text{compressor\_shaft}}}$$
    - Tỷ số nén tổng thể:
      $$r_p = \frac{P_{\text{condenser}}}{P_{\text{suction}}} = \frac{P_{\text{cond}}(T_{\text{SW}})}{P_{\text{tank}}}$$
  - Cơ chế bảo vệ áp suất hầm hàng theo IGC Code MARVS (Maximum Allowable Relief Valve Setting):
    - Áp suất tank $P_{\text{tank}}$ phải luôn được duy trì an toàn dưới $0.80 \cdot \text{MARVS}$.
    - Khóa an toàn: Tự động khởi động máy nén bổ sung khi $P_{\text{tank}} \ge 0.70 \cdot \text{MARVS}$; cảnh báo khẩn cấp khi $P_{\text{tank}} \ge 0.90 \cdot \text{MARVS}$.

### Phase 356: MARPOL Annex I Bilge Sludge Management & Incinerator Control Engine
- **Định mức phát sinh cặn dầu (MARPOL Annex I Reg 12 & MEPC.1/Circ.753)**:
  - Tốc độ sinh cặn nhiên liệu nặng (HFO Purification Sludge):
    $$V_{\text{sludge\_gen}} = k \cdot V_{\text{fuel\_consumed}} \approx 0.015 \cdot V_{\text{fuel}} \quad (\text{m}^3/\text{ngày})$$
  - Quá trình tách nước nhiệt (thermal dewatering) trong Sludge Settling Tank được gia nhiệt lên $85 - 90^\circ\text{C}$ để phân tầng tách nước tự nhiên trước khi đưa vào Service Tank.
- **Tiêu chuẩn kiểm soát buồng đốt Lò đốt rác Tàu biển (MEPC.259(68) / MEPC.76(40))**:
  - Khóa liên động nhiệt độ bắt buộc ngăn ngừa khí thải Dioxin và Furan:
    - Nhiệt độ buồng sơ cấp (Primary Chamber): $T_1 \ge 850^\circ\text{C}$.
    - Nhiệt độ buồng thứ cấp (Secondary Chamber): $T_2 \ge 1100^\circ\text{C}$.
    - Khóa vòi phun cặn dầu (sludge injection nozzle): Tuyệt đối không cho phép bơm cặn dầu vào lò đốt khi $T_1 < 850^\circ\text{C}$.
  - Tận dụng nhiệt trị chất thải (Waste heat recovery): Cặn dầu có nhiệt trị khoảng $28 - 35\text{ MJ/kg}$, có thể phối trộn với DO/MGO để duy trì ngọn lửa ổn định.
  - Khóa van 3 ngả tự động ngắt xả mạn OWS khi nồng độ dầu nước la-can vượt $15\text{ ppm}$ theo MEPC.107(49).

### Phase 357: Smart Mooring Line Tension & Quay Berth Surge Monitoring Engine
- **Quy chuẩn OCIMF MEG4 (Mooring Equipment Guidelines 4th Edition)**:
  - Giới hạn tải trọng làm việc an toàn (Working Load Limit - WLL):
    - Dây cáp thép (Wire ropes): $\text{WLL} \le 55\% \cdot \text{MBL}_{\text{sd}}$ (Ship Design Minimum Breaking Load).
    - Dây tổng hợp (Synthetic fiber ropes): $\text{WLL} \le 50\% \cdot \text{MBL}_{\text{sd}}$.
  - Phân bổ lực căng giữa các tuyến dây: Dây dọc mũi/lái (Head/Stern lines), Dây ngang (Breast lines), Dây chéo (Spring lines).
- **Tác động thủy động học của tàu chạy qua (Passing Ship Hydrodynamic Surge Interaction - PIANC)**:
  - Khi tàu khác chạy qua luồng sát bến ở vận tốc $V_{\text{pass}}$, hiện tượng sụt áp Bernoulli và dòng xoáy đáy tạo lực kéo/đẩy đột ngột lên thân tàu cập bến:
    $$F_{\text{surge}} = C_{\text{surge}} \cdot \frac{1}{2} \rho_{\text{water}} \cdot V_{\text{pass}}^2 \cdot \left(\frac{\nabla_{\text{pass}}}{L_{\text{pass}}}\right) \cdot \frac{1}{d_{\text{sep}}}$$
  - Lực đột biến này làm gia tăng lực căng dây chéo (Spring lines) và có nguy cơ đứt dây giật ngược.
- **Dự báo vùng nguy hiểm bật giật (Snap-Back Hazard Boundary Prediction)**:
  - Khi dây chịu lực căng cao ($T \ge 60\% \text{ MBL}$) tích lũy thế năng đàn hồi lớn. Nếu đứt, đầu dây bật ngược tạo vùng xoay nguy hiểm (snap-back zone).
  - Thuật toán định vị ranh giới an toàn trên boong theo hướng bố trí bích kéo, con lăn dẫn hướng (fairleads & chocks).

### Phase 358: Maritime Cyber Risk Management & OT/IT Network Resilience Engine
- **Quy định IMO Res. MSC.428(98) & IACS Unified Requirements E26/E27**:
  - Tích hợp quản trị an ninh mạng vào Hệ thống Quản lý An toàn Tàu biển (SMS/ISM Code).
  - Phân vùng mạng (Conduits & Zones) theo IEC 62443:
    1. **Zone 1: Navigation OT** (ECDIS, Radar, Autopilot, Gyro, GPS qua IEC 61162-450 / NMEA bus) — Cách ly vật lý hoặc qua Firewall kiểm soát gói tin nghiêm ngặt.
    2. **Zone 2: Machinery & Propulsion OT** (VMS, PMS, Main Engine Governor, Ballast Water Control).
    3. **Zone 3: Cargo & Safety OT** (CTMS, Fire Alarm, Gas Detection).
    4. **Zone 4: Administrative IT** (Tàu văn phòng, VNSW, Hải quan, Email đại lý).
    5. **Zone 5: Crew Welfare IT** (Mạng thủy thủ, Internet vệ tinh, giải trí).
  - Phát hiện bất thường (Anomaly Detection):
    - Giám sát tấn công giả mạo tọa độ GPS Spoofing, NMEA frame injection, bất thường tốc độ truyền.
  - Quản lý đường truyền vệ tinh đa kênh (Multi-WAN Satellite Failover):
    - Tự động chuyển đổi giữa Starlink/LEO, VSAT GEO, và L-band FBB/Iridium Certus khi mất kết nối hoặc bị can nhiễu.
    - Phân bổ băng thông QoS: Ưu tiên tuyệt đối OT Telemetry & Port Clearance > IT Admin > Chặn/ngắt Crew Welfare khi có sự cố an ninh mạng.

---

## 2. Đánh giá Hiện trạng Mã nguồn & Chiến lược Refactor

### Hiện trạng
- Toàn bộ các Phase Hàng hải từ 315 đến 354 đã tuân thủ triệt để nguyên tắc **Hybrid Modular Facade**:
  - Mỗi micro-engine độc lập `< 200 LOC` trong `src/core/maritime/`.
  - Tách bạch rõ ràng Data Classes, Engine Logic, Typer CLI, và FastMCP Tools.
  - Kiểm thử 100% zero-mock: Không phụ thuộc internet, không dùng mock giả lập logic.
- Một số tệp lớn trong hệ thống (`src/cli/app_setup.py`, `scripts/mcp_server.py`) đang tích lũy nhiều nhóm lệnh qua các phase.
- Chiến lược cho Phase 355–358:
  - Tiếp tục phát triển theo mô hình micro-engines nhỏ gọn (`< 150 LOC/file`).
  - Tách facade tinh gọn `src/core/maritime_lpg_sludge_mooring_cyber_engine.py` (~45 LOC).
  - CLI group tích hợp `src/cli/commands/maritime_lpg_sludge_mooring_cyber_command.py` (~140 LOC).
  - Viết 3 test suites độc lập tách nhỏ: Unit test hầm hàng & lò đốt, Unit test lực căng dây & an ninh mạng, CLI/MCP integration test.

---

## 3. Kiến trúc Chi tiết Phase 355–358

### Cấu trúc Tệp & Phân bổ LOC

```
src/
├── core/
│   ├── maritime/
│   │   ├── phase_355_lpg_reliquefaction_compressor.py   (~120 LOC)
│   │   ├── phase_356_marpol_sludge_incinerator.py       (~125 LOC)
│   │   ├── phase_357_smart_mooring_surge_meg4.py        (~130 LOC)
│   │   └── phase_358_maritime_cyber_resilience.py       (~135 LOC)
│   └── maritime_lpg_sludge_mooring_cyber_engine.py      (~45 LOC)
├── cli/
│   └── commands/
│       └── maritime_lpg_sludge_mooring_cyber_command.py (~145 LOC)
scripts/
└── mcp_server.py                                        (Đăng ký 4 FastMCP Tools)
tests/
├── test_maritime_lpg_sludge_unit_suite.py               (~110 LOC)
├── test_maritime_mooring_cyber_unit_suite.py            (~120 LOC)
└── test_maritime_lpg_sludge_mooring_cyber_cli_mcp_suite.py (~135 LOC)
```

### Danh mục Lệnh CLI & 8 Bí danh Tiếng Việt
1. **LPG Reliquefaction**:
   - Tên lệnh: `lpgreliq`
   - Bí danh tiếng Việt: `hoalonglpg`
   - Chức năng: Đánh giá tốc độ BOG, hệ số nén COP máy nén và áp suất hầm hàng so với MARVS.
2. **Sludge & Incinerator**:
   - Tên lệnh: `sludgeburn`
   - Bí danh tiếng Việt: `xulydaucan`
   - Chức năng: Tính toán thể tích cặn dầu phát sinh hàng ngày, khóa nhiệt độ lò đốt 850°C/1100°C và van ngắt OWS 15 ppm.
3. **Smart Mooring Tension**:
   - Tên lệnh: `mooringtension`
   - Bí danh tiếng Việt: `cangdaybuoc`
   - Chức năng: Kiểm tra giới hạn WLL/MBL dây buộc, tính lực giật do tàu vượt bến surge force và khoanh vùng snap-back zone.
4. **Maritime Cyber Resilience**:
   - Tên lệnh: `maritimecyber`
   - Bí danh tiếng Việt: `anninhmangtau`
   - Chức năng: Đánh giá phân vùng mạng OT/IT, phát hiện bất thường NMEA bus, tính điểm rủi ro an ninh mạng và chuyển đổi dự phòng vệ tinh.

### 4 Công cụ FastMCP Đăng ký
1. `mekong_lpg_reliquefaction_evaluate`: Đánh giá chu trình tái hóa lỏng và áp suất hầm hàng LPG.
2. `mekong_marpol_sludge_incinerator_evaluate`: Kiểm soát quản lý cặn dầu và khóa liên động lò đốt rác.
3. `mekong_smart_mooring_surge_evaluate`: Tính toán lực căng dây buộc tàu và cảnh báo tàu lướt qua bến.
4. `mekong_maritime_cyber_resilience_evaluate`: Kiểm toán an ninh mạng tàu biển và phân vùng OT/IT.

---

## 4. Kế hoạch Kiểm thử Zero-Mock (100% Pass)
- **Unit Suite 1 (LPG & Sludge)**:
  - Test case tính toán BOG và chu trình nén tái hóa lỏng an toàn ($P < 0.8 \text{ MARVS}$).
  - Test case cảnh báo áp suất cao hầm hàng và yêu cầu kích hoạt máy nén dự phòng.
  - Test case lò đốt liên động nhiệt độ: Từ chối phun cặn dầu khi buồng sơ cấp $< 850^\circ\text{C}$.
  - Test case khóa van 3 ngả OWS khi phát hiện cặn dầu vượt 15 ppm.
- **Unit Suite 2 (Mooring & Cyber)**:
  - Test case dây buộc tàu tổng hợp vượt giới hạn $50\% \text{ MBL}$ khi có tàu chạy qua tốc độ cao.
  - Test case xác định vùng nguy hiểm đứt giật snap-back zone trên boong mũi/lái.
  - Test case phát hiện bất thường giả mạo dữ liệu hải đồ GPS/NMEA trên mạng OT buồng lái.
  - Test case chuyển kênh vệ tinh dự phòng Starlink -> LEO/L-band và ngắt kết nối Crew WiFi khi bị tấn công.
- **Integration Suite (CLI & FastMCP)**:
  - Gọi thực thi cả 4 lệnh CLI và 8 bí danh tiếng Việt qua `CliRunner`.
  - Gọi trực tiếp 4 hàm FastMCP tools và xác thực cấu trúc JSON trả về.

---

## 5. Kết luận & Đề xuất Bước Tiếp theo
Bản thiết kế này cung cấp đầy đủ cơ sở toán học, quy chuẩn hàng hải quốc tế (IGC, MARPOL, OCIMF MEG4, IACS UR E26/E27), kiến trúc module phân mảnh chuẩn mực và ma trận kiểm thử chi tiết. Đề xuất sẵn sàng chuyển sang bước lập Kế hoạch Triển khai (`/plan:parallel`) và thực thi triển khai Phase 355–358.
