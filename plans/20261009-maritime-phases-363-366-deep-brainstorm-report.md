# Báo cáo Brainstorming Chuyên sâu & Thiết kế Kỹ thuật: Maritime Phases 363–366 & Refactor Kiến trúc

**Chủ đề:** Giám sát Xuồng Cứu sinh Tự rơi & Phao HRU, Hệ thống Quản trị Năng lượng Máy phát điện Tàu biển PMS & Ngăn ngừa Blackout, Tái sử dụng Bùn nạo vét Luồng Cảng biển & Thẩm định Vetting Tàu lai dắt Cảng biển OCIMF OVID  
**Kiến trúc:** Hybrid Modular Facade Pattern (< 200 LOC sub-modules + Central Facade + Typer CLI + FastMCP Tools)  
**Tiêu chuẩn Quốc tế & Quy chuẩn Hàng hải:**
- **SOLAS III/Reg 13 & 33**, **LSA Code Ch. IV/VI** & **IMO Res. MSC.81(70)** (Free-fall lifeboat structural acceleration limits, entry angle, hydrostatic release unit HRU activation depth).
- **SOLAS II-1/Reg 53**, **IEC 60092-202** & **DNV/ABS Marine Power Rules** (Marine Electrical Power Management System PMS, active/reactive load sharing, non-essential preferential tripping stages 1-3, under-frequency blackout protection).
- **London Convention/Protocol (1996)** & **QCVN 43:2017/BTNMT** (Dredged sediment heavy metals, TBT, PAH contamination criteria, geotechnical beneficial reuse solids >= 60%, unconfined compressive strength UCS >= 50 kPa).
- **OCIMF OVID Guidelines**, **IMCA M 149 / CMID**, **DNV Towing Gear Rules** & **STCW Code III/3** (Port tug vetting, certified continuous bollard pull, towing winch static brake holding >= 80% MBL, escort steering/braking forces F_y/F_x).

---

## 1. Phân tích Nghiệp vụ & Mô hình Tính toán Kỹ thuật

### Phase 363: Free-Fall Lifeboat Launch & Hydrostatic Release Unit (HRU) Engine
- **Mô hình Thủy động lực học Phóng Xuồng Tự rơi (MSC.81(70) & LSA Code)**:
  - Khi kích hoạt thả tự do, xuồng trượt theo máng phóng dốc nghiêng $\theta_{\text{ramp}} \approx 30^\circ - 35^\circ$ với gia tốc trọng trường.
  - Vận tốc tiếp nước $V_{\text{entry}} = \sqrt{2 g H_{\text{drop}}}$.
  - Góc tiếp nước của sống xuồng (water entry angle): $\alpha_{\text{entry}} \in [50.0^\circ, 65.0^\circ]$. Nếu $\alpha < 50^\circ$, xuồng va đập dẹt gây chấn thương cột sống; nếu $\alpha > 65^\circ$, nguy cơ lặn sâu mất kiểm soát.
  - Giới hạn gia tốc hãm tác động lên đầu và cột sống thuyền viên:
    $$a_{\text{headward}} \le 15.0\,g \quad (\approx 147.15\text{ m/s}^2)$$
  - Cơ chế phao tự nổi HRU (Hydrostatic Release Unit):
    - Hoạt động bằng màng nhạy áp lực nước biển tự cắt dây chằng hoặc nhả chốt:
    - Khoảng độ sâu kích hoạt tiêu chuẩn bắt buộc: $h_{\text{act}} \in [1.5\text{ m}, 4.0\text{ m}]$.
    - Cảnh báo: Sóng đánh mạnh dưới 1.5m không được nhả chốt; chìm quá 4.0m mà chưa nhả là lỗi cơ khí nghiêm trọng.

### Phase 364: Marine Generator PMS & Blackout Prevention Engine
- **Cân bằng Phụ tải & Điều khiển Lưới điện Tàu biển (IEC 60092-202 & SOLAS II-1/53)**:
  - Phân bổ tải tác dụng $P$ (kW) và phản kháng $Q$ (kVAR) giữa các Diesel Generator (DG):
    $$\Delta P_{\text{imbalance}} = |P_1 - P_2| / P_{\text{rated}} \le 10\%$$
  - Ngưỡng tự động khởi động máy phát dự phòng:
    $$P_{\text{grid}} \ge 85.0\% \cdot \sum P_{\text{running\_MCR}}$$
  - Cơ chế sa thải phụ tải ưu tiên (Preferential Tripping):
    - Cấp 1 (Tải không thiết yếu: Điều hòa không khí, làm mát sinh hoạt, máy pha cà phê).
    - Cấp 2 (Tải phụ trợ: Máy sấy khí boong, quạt thông gió hầm hàng, bơm dằn phụ).
    - Cấp 3 (Tải công nghiệp phụ: Bơm chuyển nhiên liệu, máy nén khí phụ).
  - Khóa bảo vệ chống Blackout (Mất điện toàn tàu):
    - Ngắt trip khẩn cấp bảo vệ khi tần số $f \le 57.0\text{ Hz}$ ($60\text{ Hz}$ nominal) hoặc điện áp $U \le 0.85\,U_n$ duy trì kéo dài $t > 0.5\text{ s}$.
    - Khởi động máy phát sự cố (Emergency Generator) và đóng điện bảng điện chính trong vòng $\le 45\text{ s}$.

### Phase 365: Port Dredging Sediment Quality & Beneficial Reuse Engine
- **Đánh giá Độc chất Trầm tích Nạo vét (QCVN 43:2017/BTNMT & London Protocol 1996)**:
  - Hợp chất hữu cơ thiếc chống hà TBT (Tributyltin): Giới hạn nghiêm ngặt $\le 0.001\text{ mg/kg}$ trọng lượng khô. Nếu phát hiện $> 0.001\text{ mg/kg}$, cấm tuyệt đối đổ ra biển mở.
  - Tổng hydrocacbon thơm đa vòng ($\sum 16\text{-PAH}$): Giới hạn $\le 10.0\text{ mg/kg}$ cho Trầm tích Loại 1 (Class 1).
  - Kim loại nặng: As ($\le 20$), Cd ($\le 1.5$), Pb ($\le 50$), Hg ($\le 0.4$), Cu ($\le 65$), Zn ($\le 200\text{ mg/kg}$).
- **Cơ chế San lấp Tái sử dụng Có ích (Beneficial Reuse Gate)**:
  - Tách nước bùn nạo vét đạt hàm lượng chất rắn khô (Solids Content): $\ge 60.0\%$.
  - Ổn định hóa / rắn hóa bằng vôi/xi măng đạt cường độ nén nở hông (UCS - Unconfined Compressive Strength) sau 28 ngày:
    $$\text{UCS}_{28d} \ge 50.0\text{ kPa}$$
  - Đủ điều kiện làm lõi đê biển, tôn tạo bãi chứa container hậu cần cảng biển.

### Phase 366: OCIMF OVID Tug Vetting & Towing Winch Safety Engine
- **Quy chuẩn Thẩm định Tàu lai dắt OCIMF OVID & IMCA M 149**:
  - Lực kéo tĩnh liên tục (Certified Continuous Bollard Pull - BP, tính bằng tấn hoặc kN).
  - Khả năng giữ phanh của tời kéo (Towing Winch Brake Holding Capacity):
    $$\text{Brake Holding} \ge 80.0\% \cdot \text{MBL}_{\text{towline}}$$
    Trong đó $\text{MBL}_{\text{towline}}$ là tải trọng đứt gãy thiết kế nhỏ nhất của dây kéo chính.
  - Khóa nhả khẩn cấp dây kéo dưới tải trọng cao (Quick Release): Thời gian nhả $< 3.0\text{ s}$ khi tàu lai có nguy cơ bị lật úp do góc nghiêng gantry vắt ngang.
  - Lực kéo hộ tống động lực học (Escort Tug Forces) tại tốc độ 10 hải lý/giờ: Lực bẻ lái ngang $F_y$ (Steering Force) và Lực hãm dọc $F_x$ (Braking Force).
  - Năng lực thuyền viên: Bắt buộc thuyền trưởng và máy trưởng có xác nhận STCW III/3 chuyên dùng cho tàu kéo.

---

## 2. Kiến trúc Module & Phân bổ Tệp (< 200 LOC)

```
src/
├── core/
│   ├── maritime/
│   │   ├── phase_363_lsa_lifeboat_hru_release.py       (~115 LOC)
│   │   ├── phase_364_marine_generator_pms_blackout.py   (~120 LOC)
│   │   ├── phase_365_dredging_sediment_beneficiation.py (~110 LOC)
│   │   └── phase_366_ovid_tug_winch_vetting.py          (~125 LOC)
│   └── maritime_lsa_pms_dredge_tug_engine.py            (~120 LOC)
├── cli/
│   └── commands/
│       └── maritime_lsa_pms_dredge_tug_command.py       (~145 LOC)
```

Kiểm thử Zero-mock:
```
tests/
├── test_maritime_lsa_pms_unit_suite.py                 (~120 LOC)
├── test_maritime_dredge_tug_unit_suite.py               (~115 LOC)
└── test_maritime_363_to_366_cli_mcp_suite.py           (~130 LOC)
```

Toàn bộ tuân thủ triệt để:
1. Zero mock logic.
2. Tất cả các tệp đều $< 200$ LOC.
3. 8 bí danh tiếng Việt trực quan.
4. FastMCP integration đầy đủ.
