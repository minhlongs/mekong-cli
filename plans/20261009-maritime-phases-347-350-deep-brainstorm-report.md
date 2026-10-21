# Báo cáo Brainstorming Chuyên sâu & Thiết kế Kỹ thuật: Maritime Phases 347–350

**Chủ đề:** Hệ thống Bảo vệ Vỏ tàu, Giảm phát thải Khí xả Động cơ, An toàn Neo đậu Cảng & Vận đơn Điện tử Chuyển nhượng Quyền sở hữu (ICCP Cathodic Protection, Engine SCR & ME-GI NOx, Port Anchorage Windlass Holding Power & e-BL MLETR Title Transfer)
**Kiến trúc:** Hybrid Modular Facade Pattern (< 200 LOC per file, Zero-Mock Tests, Typer CLI với 8 bí danh tiếng Việt, 4 FastMCP Tools)
**Tiêu chuẩn Quốc tế & Việt Nam:** DNV-RP-B401 / NACE SP0176, IMO MARPOL Annex VI Reg 13 (NOx Tier III) / MEPC.198(62), IACS UR A1 / OCIMF MEG4 / MSC.1/Circ.1175, UNCITRAL MLETR 2017 / BIMCO e-BL / DCSA API / Bộ luật Hàng hải VN 2015.

---

## 1. Phân tích Kỹ thuật & Công thức Nghiệp vụ

### Phase 347: Impressed Current Cathodic Protection (ICCP) & Sacrificial Anode Engine
- **Điện thế Bảo vệ Thân tàu qua Điện cực So sánh $\text{Ag/AgCl}$ (NACE SP0176, DNV-RP-B401)**:
  - Cửa sổ điện thế an toàn: $-800\text{ mV}$ đến $-1050\text{ mV}$ (so với điện cực Bạc/Bạc Clorua trong nước biển).
  - Vùng thiếu bảo vệ (Under-protection): $E > -800\text{ mV}$ (ví dụ $-720\text{ mV}$ gây ăn mòn điện hóa rỉ sét vỏ thép, tốc độ ăn mòn tăng vọt $> 0.1\text{ mm/năm}$).
  - Vùng thừa bảo vệ (Over-protection): $E < -1050\text{ mV}$ (ví dụ $-1150\text{ mV}$ sinh khí hydro cực âm bóc tách lớp sơn màng mỏng Cathodic Disbondment và gây giòn hydro cho thép cường độ cao).
- **Mật độ Dòng Bảo vệ & Công suất Cưỡng bức ICCP**:
  - Diện tích ướt thân tàu: $A_{\text{wetted}} = 1.025 \times L_{bp} \times (C_b \times B + 1.7 \times d)$.
  - Nhu cầu dòng điện: $I_{\text{req}} = A_{\text{wetted}} \times j_{\text{design}} \times f_c \times 10^{-3}\ (\text{Ampere})$, trong đó $j_{\text{design}} = 20 - 45\text{ mA/m}^2$, $f_c$ là hệ số suy thoái lớp phủ ($0.05 - 0.20$).
- **Khối lượng Anode Kẽm/Nhôm Hy sinh Dự phòng**:
  - $M_{\text{anode}} = \frac{I_{\text{req}} \times 8760 \times T_{\text{years}}}{\epsilon \times u}\ (\text{kg})$, với dung lượng điện hóa $\epsilon = 780\text{ Ah/kg}$ (Zn) hoặc $2000\text{ Ah/kg}$ (Al), hệ số tiêu hao hữu dụng $u = 0.85$.

### Phase 348: Marine Engine SCR & Dual-Fuel ME-GI NOx Tier III Compliance Engine
- **Giới hạn Phát thải NOx Tier III (IMO MARPOL Annex VI Reg 13)**:
  - Áp dụng khi tàu hoạt động trong vùng kiểm soát phát thải NOx-ECA (Bắc Mỹ, Biển Baltic, Biển Bắc).
  - Động cơ tốc độ chậm ($n < 130\text{ rpm}$): $\text{NOx} \le 3.4\text{ g/kWh}$.
  - Động cơ tốc độ trung bình ($130 \le n < 2000\text{ rpm}$): $\text{NOx} \le 9.0 \times n^{-0.2}\text{ g/kWh}$.
- **Hệ thống Xúc tác Khử Chọn lọc SCR (Selective Catalytic Reduction)**:
  - Cửa sổ nhiệt độ khí xả: $T_{\text{exhaust}} \ge 300^\circ\text{C}$ (ngưỡng tối thiểu ngăn hình thành amoni bisunfat $\text{NH}_4\text{HSO}_4$ gây tắc nghẽn tổ ong xúc tác).
  - Dung dịch khử Urea AUS 40 ($40\%$ urea trong nước): Phương trình phản ứng $(\text{NH}_2)_2\text{CO} + \text{H}_2\text{O} \to 2\text{NH}_3 + \text{CO}_2$.
  - Tỷ lệ phun Urea định lượng: $\dot{m}_{\text{urea}} = \frac{\Delta\text{NOx} \times P_{\text{eng}} \times M_{\text{urea}}}{2 \times M_{\text{NO}_2} \times 0.40 \times \eta_{\text{SCR}}}\ (\text{kg/h})$.
- **Kiểm soát Trượt Khí Mê-tan (Methane Slip) Động cơ Hai Nhiên liệu (Dual-Fuel ME-GI / X-DF)**:
  - Ngưỡng rò rỉ khí chưa cháy: $\le 2.5\text{ g/kWh}$. Nếu vượt ngưỡng, cảnh báo phạt GHG và tự động điều chỉnh thời điểm phun mồi nhiên liệu pilot.

### Phase 349: Port Anchorage Windlass Holding Power & Ground Tackle Scope Engine
- **Trang Thiết bị Số EN (IACS UR A1 Equipment Number)**:
  - $\text{EN} = \Delta^{2/3} + 2.0 \cdot B \cdot a + 0.1 \cdot A_{\text{lat}}$.
  - Xác định cỡ neo, cấp xích neo (Grade U2/U3) và tải trọng thử đứt/kéo của tời neo (Windlass brake holding load $\ge 80\%$ MBL xích neo).
- **Lực Giữ Của Neo & Xích (Catenary Ground Tackle Holding Power)**:
  - Lực giữ mỏ neo: $H_{\text{anchor}} = W_{\text{anchor}} \times k_{\text{holding}}$ ($k = 3 - 4$ cho neo thường, $10 - 15$ cho neo sức bám cao HHP).
  - Lực ma sát xích nằm trên đáy biển: $H_{\text{chain}} = L_{\text{bottom}} \times w_{\text{chain\_submerged}} \times \mu_{\text{seabed}}$ ($\mu = 0.5 - 0.75$).
  - Tỷ lệ xả xích an toàn (Chain Scope Ratio): $S = L_{\text{cable}} / d_{\text{depth}}$ (Tối thiểu $4:1$ vùng nước êm, $6:1 - 7:1$ khi có gió giật sóng lớn).
- **Cảnh báo Trôi Neo (Dragging Anchor Alert)**:
  - Tính tổng lực cản môi trường: $F_{\text{env}} = F_{\text{wind}} + F_{\text{current}}$.
  - Ngưỡng an toàn: Nếu $F_{\text{env}} > 0.75 \times (H_{\text{anchor}} + H_{\text{chain}})$, phát cảnh báo nguy cơ trôi neo khẩn cấp.

### Phase 350: Electronic Bill of Lading (e-BL) Title Transfer & MLETR Blockchain Engine
- **Tiêu chuẩn UNCITRAL MLETR 2017 & DCSA e-BL Data Model**:
  - Đảm bảo tính độc nhất vô nhị (Singularity) và kiểm soát độc quyền (Exclusive Control) của chứng từ chuyển nhượng điện tử.
  - Vòng đời trạng thái: `ISSUED` $\to$ `ENDORSED` $\to$ `TRANSFERRED` $\to$ `PLEDGED` $\to$ `ACCOMPLISHED` / `SURRENDERED`.
- **Phân loại Vận đơn & Cơ chế Ký số / Chuyển quyền (Endorsement)**:
  - Vận đơn Đích danh (Straight BL): Không thể chuyển nhượng, chỉ giao hàng cho đúng Người nhận đích danh.
  - Vận đơn Theo lệnh (To Order / To Order of Shipper): Chuyển nhượng bằng Ký hậu số (Digital Endorsement - Blank hoặc Special).
  - Vận đơn Vô danh (Bearer BL): Chuyển nhượng bằng chuyển giao quyền kiểm soát (Token Transfer).
- **Chuỗi Hash Xác thực & Thẩm tra Giải phóng Hàng (Release Verification)**:
  - Băm SHA-256 từng giao dịch chuyển giao quyền sở hữu `hash = SHA256(prev_hash + actor + timestamp + action)`.
  - Nghiêm cấm cấp phát chứng từ giấy song song (No Paper Duplicate), loại bỏ rủi ro Thư bảo lãnh nhận hàng (Letter of Indemnity - LOI) và gian lận thương mại hàng hải.

---

## 2. Thiết kế Kiến trúc Hybrid Modular Facade (< 200 LOC/file)

1. `src/core/maritime/phase_347_iccp_cathodic_protection.py` (< 200 LOC)
2. `src/core/maritime/phase_348_engine_scr_megi_nox.py` (< 200 LOC)
3. `src/core/maritime/phase_349_anchorage_windlass_holding.py` (< 200 LOC)
4. `src/core/maritime/phase_350_ebl_mletr_transfer.py` (< 200 LOC)
5. `src/core/maritime_iccp_scr_anchor_ebl_engine.py` (Facade trung tâm < 200 LOC)
6. `src/cli/commands/maritime_iccp_scr_anchor_ebl_command.py` (Typer CLI < 200 LOC)
7. Đăng ký CLI trong `src/cli/app_setup.py` (8 bí danh tiếng Việt)
8. Đăng ký 4 FastMCP Tools trong `scripts/mcp_server.py`
9. Test Suites zero-mock:
   - `tests/test_maritime_iccp_scr_anchor_ebl_unit_suite.py` (< 200 LOC)
   - `tests/test_maritime_iccp_scr_anchor_ebl_cli_mcp_suite.py` (< 200 LOC)
