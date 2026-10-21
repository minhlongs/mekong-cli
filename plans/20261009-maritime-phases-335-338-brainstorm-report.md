# Báo cáo Brainstorming Chuyên sâu & Thiết kế Kỹ thuật: Maritime Phases 335–338

**Chủ đề:** Hệ thống Điều hành Hàng hải Thông minh, An toàn Chằng buộc Siêu trường Siêu trọng, Năng lượng Cảng Xanh & Trọng tài Hàng hải (VTS/TSS, CSS OOG Lashing, Green Tug Cold Ironing, BIMCO Charterparty)  
**Kiến trúc:** Hybrid Unified Modular Architecture (< 200 LOC sub-modules + Central Facade + Typer CLI + FastMCP)  
**Tiêu chuẩn Quốc tế & Việt Nam:** COLREGs Rule 10, IMO Res. A.1158(32), IALA V-128, CSS Code Annex 13 (IMO Res. A.714(17)), DNV-ST-N001, IEC/IEEE 80005-1/3, BIMCO NYPE 2015 / GENCON 2022, LMAA Terms 2021 & Quy tắc Trọng tài VMAC 2019.

---

## 1. Phân tích Nghiệp vụ & Mô hình Toán học

### Phase 335: VTS & Traffic Separation Schemes (TSS) Management
- **Quy chuẩn COLREGs Rule 10 & IMO Res. A.1158(32)**:
  - Phân luồng giao thông luồng hàng hải (Inbound/Outbound traffic lanes, Separation zone).
  - Cảnh báo phương tiện đi ngược chiều luồng (Wrong-way heading vector $\Delta \theta > 90^\circ$ so với hướng quy định luồng).
  - Độ lệch hành lang luồng (Cross-Track Error - XTE): Cảnh báo khi $|XTE| > W_{\text{lane\_half}}$.
- **Đánh giá Rủi ro Va chạm (CPA & TCPA)**:
  - Khoảng cách tiếp cận gần nhất (Closest Point of Approach - CPA): Ngưỡng an toàn tối thiểu $\text{CPA} < 1.0\text{ NM}$.
  - Thời gian đến điểm tiếp cận gần nhất (Time to CPA - TCPA): Cảnh báo khẩn khi $\text{TCPA} < 15\text{ phút}$.
  - Dịch vụ VTS: Information Service (INS), Traffic Organization Service (TOS), Navigational Assistance Service (NAS).

### Phase 336: Project Cargo & Heavy Lift OOG Lashing Safety (CSS Code)
- **IMO CSS Code Annex 13 & DNV-ST-N001**:
  - Áp dụng hàng thiết bị công trình, siêu trường siêu trọng (Out-of-Gauge - OOG).
  - Gia tốc thiết kế theo vị trí hầm hàng/mặt boong: $a_x$ (dọc), $a_y$ (ngang), $a_z$ (đứng).
- **Cân bằng Lực & Hệ số An toàn Chống Trượt / Chống Lật**:
  - Lực trượt ngang: $F_{\text{slide}} = m \cdot g \cdot a_y - \mu \cdot m \cdot g \cdot (1 - a_z)$.
  - Tải trọng làm việc an toàn của xích/cáp chằng buộc (Maximum Securing Load - MSL): Thép tấm/dầm $MSL = 0.5 \times BL$, xích $MSL = 0.5 \times BL$, cáp thép $MSL = 0.8 \times BL$.
  - Góc chằng buộc hiệu dụng: $F_{\text{lashing\_eff}} = MSL \cdot \cos(\alpha) \cdot \cos(\beta)$.
  - Yêu cầu hệ số an toàn:
    $$S_F = \frac{\sum F_{\text{lash\_res}} + F_{\text{friction}}}{F_{\text{ext}}} \ge 1.25$$

### Phase 337: Green Tug Energy Management & Cold Ironing
- **IEC/IEEE 80005-1/3 High & Low Voltage Shore Connection (HVSC/LVSC)**:
  - Đồng bộ hòa lưới bờ cấp điện cho tàu tại cầu bến (Cold Ironing/OPS).
  - Thuật toán bù tải đỉnh (Peak Shaving) cho trạm ắc quy tàu lai Hybrid/All-Electric:
    $$P_{\text{shore}} = P_{\text{vessel}} - P_{\text{bat\_discharge}}$$
  - Mức dự phòng năng lượng khẩn cấp: Tối thiểu State of Charge $\text{SoC} \ge 20\%$.
  - Định mức năng lượng lực kéo (Bollard Pull Energy Metric):
    $$E_{\text{pull}} = \frac{E_{\text{consumed\_kWh}}}{BP_{\text{ton}} \cdot t_{\text{hour}}} \le 0.15\text{ kWh/(t-pull}\cdot\text{h)}$$
  - Giảm phát thải: $CO_2$ giảm theo hệ số phát thải lưới ($EF_{\text{grid}} \approx 0.72\text{ kg CO}_2/\text{kWh}$) so với MGO ($3.206\text{ t CO}_2/\text{t MGO}$).

### Phase 338: BIMCO Charterparty Performance & Maritime Arbitration
- **Điều khoản Bảo đảm Tốc độ & Tiêu thụ Nhiên liệu (Speed & Consumption Warranty)**:
  - Loại trừ yếu tố thời tiết bất khả kháng (Good Weather Definition):
    $$\text{Beaufort} \le 4 \quad \text{và} \quad \text{Douglas Sea State} \le 3 \quad (\text{Sóng} \le 1.25\text{ m}), \quad \text{Dòng chảy} \le 0.5\text{ kts}$$
  - Thiệt hại do tàu chạy chậm hoặc tiêu thụ nhiên liệu vượt mức bảo đảm:
    $$\Delta \text{Cost} = (\text{Fuel}_{\text{actual}} - \text{Fuel}_{\text{warranted}}) \times P_{\text{bunker}} + \Delta t_{\text{hours}} \times \text{HireRate}_{\text{hourly}}$$
- **Tính toán Thời gian Làm hàng & Phạt/Thưởng (Laytime, Demurrage & Despatch)**:
  - Quy tắc SHINC (Sundays & Holidays Included) vs SHEX (Sundays & Holidays Excluded).
  - Thuận bù trừ laytime (Reversible Laytime): Bù trừ thời gian bốc và thời gian dỡ.
  - Phân định tranh chấp theo thủ tục rút gọn LMAA ICP ($<\$100,000$) hoặc VMAC (Việt Nam).

---

## 2. Thiết kế Kiến trúc Hybrid Modular Facade (<200 LOC/file)

1. **4 Micro-engines trong `src/core/maritime/`**:
   - `phase_335_vts_tss_navigation.py` (~140 LOC)
   - `phase_336_project_cargo_css_lashing.py` (~135 LOC)
   - `phase_337_electric_tug_cold_ironing.py` (~130 LOC)
   - `phase_338_charterparty_arbitration.py` (~140 LOC)

2. **Central Facade**:
   - `src/core/maritime_vts_css_tug_charter_engine.py` (~45 LOC)
   - Re-export toàn diện, đảm bảo backward compatibility và loose coupling.

3. **Typer CLI Command Group**:
   - `src/cli/commands/maritime_vts_css_tug_charter_command.py` (~150 LOC)
   - 4 apps: `vts_app`, `css_app`, `tug_app`, `charter_app`

4. **App Setup & Song ngữ Tiếng Việt**:
   - Đăng ký 4 lệnh gốc: `vts`, `csscargo`, `electug`, `charter`
   - Đăng ký 8 bí danh tiếng Việt: `luonghanghai`, `phanquyvts`, `hangsieutruong`, `changketoog`, `taulaidien`, `dienbencang`, `thuetautrongtai`, `tranhchaphanghai`

5. **FastMCP Endpoints (`scripts/mcp_server.py`)**:
   - `mekong_vts_tss_traffic_monitor`
   - `mekong_css_cargo_lashing_verify`
   - `mekong_electric_tug_energy_assess`
   - `mekong_charterparty_dispute_calculate`

6. **Zero-Mock Test Suite**:
   - `tests/test_maritime_vts_css_tug_charter_suite.py` (18+ tests xanh 100%)

---

## 3. Lộ trình Triển khai Chi tiết

- **Bước 1**: Tạo 4 micro-engines nghiệp vụ trong `src/core/maritime/`.
- **Bước 2**: Tạo Central Facade `src/core/maritime_vts_css_tug_charter_engine.py`.
- **Bước 3**: Tạo Typer CLI commands `src/cli/commands/maritime_vts_css_tug_charter_command.py`.
- **Bước 4**: Tích hợp CLI groups & bilingual aliases vào `src/cli/app_setup.py`.
- **Bước 5**: Tích hợp FastMCP tools vào `scripts/mcp_server.py`.
- **Bước 6**: Xây dựng test suite toàn diện `tests/test_maritime_vts_css_tug_charter_suite.py` và chạy pytest 100% green.
- **Bước 7**: Kiểm tra ruff linting & line counts `< 200 LOC`.
- **Bước 8**: Cập nhật roadmap & project memory.
