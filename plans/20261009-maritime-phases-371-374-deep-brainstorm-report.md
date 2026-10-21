# Báo cáo Brainstorming Chuyên sâu & Thiết kế Kỹ thuật: Maritime Phases 371–374 & Refactor Kiến trúc

**Chủ đề:** Trục Phát Điện Lai ghép PTO/PTI, Tối ưu Điều độ Cầu bến & Cần cẩu BAP/QCSP, Đánh giá Hà bám Vỏ tàu & Vệ sinh Dưới nước Biofouling, Tuần hoàn Dầu thải Cảng biển MARPOL Annex I  
**Kiến trúc:** Hybrid Modular Facade Pattern (< 200 LOC sub-modules + Central Facade + Typer CLI + FastMCP Tools)  
**Tiêu chuẩn Quốc tế & Quy chuẩn Việt Nam:**
- **DNV-RU-SHIP Pt.4 Ch.8, IEC 60092-501 & IMO MEPC.333(76)** (Shaft Generator Power Take-Off / Power Take-In, SFOC main engine savings vs aux generators, interlock at low rpm < 65% MCR and overload > 80% MCR).
- **UNCTAD Port Development Handbook, PIANC MarCom WG 158 & Quyết định 1579/QĐ-TTg** (Continuous Berth Allocation BAP, Quay Crane Scheduling QCSP, minimum clearance >= 35m, draft UKC >= 1.5m, tidal window gating at Cai Mep - Thi Vai & Lach Huyen).
- **IMO Res. MEPC.378(80) (2023 Biofouling Guidelines), BIMCO/ICS In-Water Cleaning Standard 2021 & QCVN 08-MT:2015/BTNMT** (Level of Fouling LoF 0–5, added hydrodynamic powering resistance penalty 2.5–35%, in-water cleaning permission gates with 99% capture down to 5 um, drydock requirement for LoF >= 4).
- **MARPOL Annex I Reg 12/13, Basel Convention, Thông tư 02/2022/TT-BTNMT & Thông tư 39/2023/TT-BGTVT** (Flash point Pensky-Martens >= 60.0°C safety gate, centrifugal dewatering 15 ppm effluent, Recovered Fuel Oil RFO LHV >= 38.0 MJ/kg, cement clinker co-processing CO2 offset 1.2 kg CO2 eq / kg RFO).

---

## 1. Phân tích Nghiệp vụ & Mô hình Tính toán Kỹ thuật

### Phase 371: Marine Shaft Generator PTO/PTI Hybrid Propulsion Engine
- **Chế độ Vận hành PTO (Power Take-Off)**:
  - Máy chính (Main Engine) kéo máy phát điện trục thông qua hộp số tunnel gear hoặc gắn trực tiếp trên trục chân vịt để cấp điện cho lưới tàu (hotel & auxiliary load).
  - Tối ưu suất tiêu hao nhiên liệu (SFOC): Máy chính 2 thì cỡ lớn dùng HFO/VLSFO có SFOC (~165 g/kWh) thấp hơn đáng kể so với máy phát điện phụ 4 thì (~195 g/kWh).
  - Tiết kiệm nhiên liệu thực tế:
    $$\Delta F_{\text{save}} = \frac{P_{\text{shaft}} \cdot (\text{SFOC}_{\text{aux}} - \text{SFOC}_{\text{ME}})}{1000} \quad (\text{kg/h})$$
  - Khóa liên động an toàn (Interlock Logic):
    - Tự động ngắt/khóa PTO khi vòng quay máy chính $< 65.0\%\text{ MCR}$ để tránh sụt áp/tần số trên lưới tàu.
    - Cảnh báo hoặc de-rate khi phụ tải mô-men trục vượt quá $80.0\%\text{ MCR}$.
- **Chế độ Vận hành PTI (Power Take-In / Booster & Take-Me-Home PTH)**:
  - Máy phát điện phụ hoặc hệ thống pin BESS đóng vai trò động cơ điện phụ kéo trục chân vịt, tăng công suất hành trình vượt bão hoặc chạy cứu nạn khẩn cấp khi máy chính sự cố.

### Phase 372: Port Berth Allocation & Quay Crane Scheduling Optimization Engine (BAP/QCSP)
- **Điều độ Phân bổ Cầu bến Liên tục (Continuous BAP)**:
  - Kiểm tra an toàn cập cầu: Chiều dài bến tối thiểu $L_{\text{berth\_req}} = \text{LOA} + 30.0\text{ m}$ (khoảng cách an toàn đệm va $15.0\text{ m}$ mỗi bên mũi/lái).
  - Kiểm tra độ sâu và chuẩn mớn nước (Under-Keel Clearance):
    $$d_{\text{water}} \ge d_{\text{ship\_draft}} + \text{UKC}_{\text{min}} \quad (\text{với }\text{UKC}_{\text{min}} = 1.5\text{ m})$$
  - Cửa sổ thủy triều (Tidal Window Gating): Với các luồng hàng hải nước sâu như Cái Mép - Thị Vải hoặc Lạch Huyện, tàu mớn sâu ($> 14.0\text{ m}$) bắt buộc phải cập/rời bến trong khung triều cao $\Delta h_{\text{tide}} \ge d_{\text{draft}} + 1.5\text{ m} - d_{\text{chart}}$.
- **Lập Kế hoạch Điều độ Cần cẩu Cầu tàu (QCSP)**:
  - Ràng buộc không giao cắt (Non-crossing constraint): Khoảng cách tối thiểu giữa 2 cẩu giàn bờ kề nhau $D_{\text{crane}} \ge 35.0\text{ m}$.
  - Năng suất cẩu bờ trung bình $25 - 32\text{ moves/giờ}$.
  - Thời gian giải phóng tàu:
    $$T_{\text{turnaround}} = \frac{\text{Tổng moves}}{\sum \text{Productivity}_{\text{cranes}}} + T_{\text{berthing\_buffer}}$$

### Phase 373: Marine Biofouling Risk Assessment & In-Water Hull Cleaning Compliance Engine
- **Thang đo Mức độ Bám bẩn Vỏ tàu (Level of Fouling - LoF 0 to 5)**:
  - LoF 0: Vỏ tàu sạch nhẵn, không có sinh vật bám.
  - LoF 1: Lớp nhớt vi sinh (Slime/Microfouling), chưa thấy sinh vật macro.
  - LoF 2: Hà bám vôi nhẹ (Light macrofouling, diện tích bao phủ $\le 5\%$).
  - LoF 3: Hà bám trung bình (Medium macrofouling, $5\% < \text{diện tích} \le 15\%$).
  - LoF 4: Hà bám nặng (Heavy macrofouling, $15\% < \text{diện tích} \le 40\%$).
  - LoF 5: Hà bám nghiêm trọng (Severe macrofouling, $> 40\%$).
- **Gia tăng Sức cản & Tổn thất Nhiên liệu (Hydrodynamic Added Resistance)**:
  - Tổn thất lực đẩy $\Delta P \approx 2.5\% \text{ (LoF 1)}$ đến $35.0\% \text{ (LoF 5)}$.
- **Ma trận Cấp phép Vệ sinh Vỏ tàu Dưới nước (In-Water Cleaning IWC)**:
  - LoF $\le 1$: Cho phép chải rửa nhẹ (grooming) không cần hệ thống hút chân không.
  - LoF 2–3: Cho phép vệ sinh tại bến cảng với điều kiện bắt buộc có hệ thống ROV thu gom chân không đạt hiệu suất $\ge 99.0\%$ cho hạt cặn $\ge 5\ \mu\text{m}$ (ngăn chặn phát tán vi sinh vật ngoại lai theo QCVN 08-MT).
  - LoF $\ge 4$: CẤM tuyệt đối vệ sinh trong vùng nước cảng; bắt buộc đưa tàu vào ụ khô (drydocking).

### Phase 374: Port Circular Waste Oil Recovery & MARPOL Annex I Co-Processing Engine
- **Quy trình Tiếp nhận & Sàng lọc An toàn**:
  - Kiểm tra điểm chớp cháy Pensky-Martens kín: $T_{\text{flash}} \ge 60.0^\circ\text{C}$. Nếu $< 60.0^\circ\text{C}$ (nguy cơ nhiễm xăng/dung môi dễ bay hơi), tự động khóa van tiếp nhận, kích hoạt cảnh báo nguy cơ nổ.
- **Tách Nước Ly tâm & Xử lý Nước thải Dầu**:
  - Gia nhiệt phá nhũ tương $\ge 80^\circ\text{C}$ và ly tâm: Hiệu suất tách nước $\ge 95.0\%$.
  - Pha nước thải sau tách phải đạt nồng độ dầu xả thải $\le 15.0\text{ ppm}$ theo MARPOL Annex I.
- **Tái chế Tuần hoàn Nhiên liệu Công nghiệp (Recovered Fuel Oil - RFO)**:
  - Tiêu chuẩn nhiên liệu đốt lò xi măng/lò nung: Nhiệt trị thấp $\text{LHV} \ge 38.0\text{ MJ/kg}$, hàm lượng cặn $\le 0.5\%$, hàm lượng tro $\le 0.15\%$.
  - Tính toán Giảm phát thải Khí nhà kính: Tiết kiệm $1.2\text{ kg CO}_2\text{ eq}$ cho mỗi kg dầu thải RFO được tuần hoàn đồng xử lý thay thế than/dầu FO nguyên chất.

---

## 2. Thiết kế Kiến trúc Module (< 200 LOC per file)

```
src/core/maritime/
├── phase_371_shaft_generator_pto_pti.py      (~130 LOC)
├── phase_372_port_berth_crane_bap_qcsp.py    (~135 LOC)
├── phase_373_biofouling_hull_cleaning.py     (~125 LOC)
└── phase_374_port_waste_oil_coprocessing.py  (~130 LOC)
src/core/
└── maritime_pto_berth_biofoul_waste_engine.py (~130 LOC)
src/cli/commands/
└── maritime_pto_berth_biofoul_waste_command.py (~140 LOC)
scripts/
└── mcp_server.py                             (+ 4 async FastMCP tools)
tests/
├── test_maritime_pto_berth_unit_suite.py     (~140 LOC)
├── test_maritime_biofoul_waste_unit_suite.py (~130 LOC)
└── test_maritime_371_to_374_cli_mcp_suite.py (~110 LOC)
```
