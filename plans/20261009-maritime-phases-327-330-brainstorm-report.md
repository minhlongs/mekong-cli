# Báo cáo Brainstorming Chuyên sâu & Thiết kế Kỹ thuật: Maritime Phases 327–330

**Chủ đề:** Hệ thống Tuân thủ & An toàn Kỹ thuật Hàng hải - Cảng biển (BWM USCG, FuelEU Decarb, Lifting Gear & OPRC Oil Spill)
**Kiến trúc:** Hybrid Unified Modular Architecture (< 200 LOC sub-modules + Central Facade + Typer CLI + FastMCP)
**Tiêu chuẩn Quốc tế & Việt Nam:** BWM Code (IMO D-2 & USCG 46 CFR 162.060), EU ETS & FuelEU Maritime (EU 2023/1805), ILO 152 & QCVN 23:2010/BGTVT, OPRC 1990 & Quyết định 12/2021/QĐ-TTg.

---

## 1. Phân tích Kỹ thuật & Công thức Nghiệp vụ

### Phase 327: Advanced Ballast Water & Sediment Management
- **Quy chuẩn IMO BWM D-2 vs USCG Type Approval (46 CFR 162.060)**:
  - Sinh vật $\ge 50\ \mu\text{m}$: $< 10\text{ vi sinh sống}/m^3$.
  - Sinh vật $10 - 50\ \mu\text{m}$: $< 10\text{ vi sinh sống}/ml$.
  - Vi sinh vật chỉ thị: *Vibrio cholerae* $< 1\text{ cfu}/100\text{ ml}$, *E. coli* $< 250\text{ cfu}/100\text{ ml}$, *Intestinal Enterococci* $< 100\text{ cfu}/100\text{ ml}$.
  - Tiêu chuẩn USCG FDA/CMF: Phân biệt sống/chết tuyệt đối qua huỳnh quang màng tế bào.
- **Hệ thống Xử lý UV & Khử Clo (TRO)**:
  - Độ thấu quang tối thiểu $\text{UVT} \ge 50\%$.
  - Điện phân muối biển (Electrochlorination): Phải trung hòa bằng Natri Thiosulfate khi tổng chất oxy hóa tồn dư $\text{TRO} > 0.1\text{ mg/L}$ trước khi xả mạn.
- **Quản lý Trầm tích Két dằn (Sediment)**:
  - Bắt buộc xử lý cặn tại ụ tàu/cơ sở tiếp nhận; giới hạn cặn vét khô $< 5\%$ dung tích két nhằm chống tái nhiễm khuẩn.

### Phase 328: Maritime Decarbonization & Alternative Fuels
- **EU ETS Maritime MRV (Directive 2023/959)**:
  - Áp dụng tàu $\ge 5,000\text{ GT}$. Tỷ lệ nộp hạn ngạch (Phase-in): $40\%$ (2024), $70\%$ (2025), $100\%$ (2026+).
  - Phạm vi: $100\%$ chuyến nội khối EU/EEA, $50\%$ chuyến quốc tế đến/từ cảng EU.
- **FuelEU Maritime GHG Intensity Pooling (Regulation 2023/1805)**:
  - Mức giảm cường độ phát thải GHG (Baseline $91.16\text{ gCO}_2\text{eq/MJ}$): Năm 2025 giảm $-2.0\%$, Năm 2030 giảm $-6.0\%$.
  - Cơ chế Pooling (Điều 28): Hợp nhất đội tàu; bù trừ thặng dư (surplus) của tàu xanh cho tàu thâm hụt (deficit).
- **An toàn Tiếp nhận Nhiên liệu Xanh (Methanol & Ammonia Dual-Fuel Bunkering)**:
  - Ngưỡng rò rỉ khí độc/cháy: Methanol $< 200\text{ ppm}$ (TWA), Ammonia $< 25\text{ ppm}$ (TWA) và $< 50\text{ ppm}$ (STEL).
  - Thổi khí trơ $N_2$ tẩy rửa: Nồng độ $O_2$ trong đường ống phải hạ $< 2.0\%$ thể tích trước khi nạp nhiên liệu.
  - Vùng an toàn (Safety Zone Radius): Bán kính cách ly $5\text{ m} - 15\text{ m}$ tùy áp suất truyền dẫn.

### Phase 329: Port Lifting Appliances & Cargo Handling Gear
- **ILO Convention 152 & QCVN 23:2010/BGTVT (Thử tải Kiểm định)**:
  - Tải trọng làm việc an toàn (SWL):
    - $\text{SWL} \le 20\text{ Tấn} \implies \text{Proof Load} = 1.25 \times \text{SWL}$.
    - $20\text{ Tấn} < \text{SWL} \le 50\text{ Tấn} \implies \text{Proof Load} = \text{SWL} + 5\text{ Tấn}$.
    - $\text{SWL} > 50\text{ Tấn} \implies \text{Proof Load} = 1.10 \times \text{SWL}$.
- **Tiêu chuẩn Loại bỏ Cáp Thép (ISO 4309 Wire Rope Discard)**:
  - Số sợi đứt trên một bước bện (lay length) vượt ngưỡng cho phép.
  - Đường kính cáp giảm $\ge 7\%$ so với đường kính danh định.
  - Ăn mòn rỗ bề mặt làm suy giảm tiết diện chịu lực.
- **Chu kỳ Đăng kiểm Cảng vụ**: Chứng nhận kiểm định tải trọng hàng năm (Annual) và đại tu định kỳ 5 năm (Quadrennial thorough survey).

### Phase 330: National Marine Oil Spill Response & NEBA
- **Phân cấp Ứng phó Tràn dầu OPRC 1990 & Quyết định 12/2021/QĐ-TTg**:
  - Cấp 1 (Tier 1): $< 20\text{ tấn}$ (hoặc $< 7\text{ tấn}$ tại bến cảng cơ sở) - Cơ sở tự ứng phó.
  - Cấp 2 (Tier 2): $20 - 500\text{ tấn}$ - Ứng phó khu vực / hiệp đồng cấp tỉnh.
  - Cấp 3 (Tier 3): $> 500\text{ tấn}$ - Quốc gia / Quốc tế chỉ đạo khẩn cấp.
- **Ma trận Đánh giá Lợi ích Môi trường Ròng (NEBA) Phun chất Phân tán**:
  - Độ sâu luồng nước $\ge 10\text{ m}$.
  - Khoảng cách xa bờ $\ge 3\text{ Hải lý}$.
  - Độ nhớt dầu $< 10,000\text{ cSt}$ (dầu còn khả năng phân tán, chưa nhũ tương hóa quá mức).
- **Tính toán Quây phao & Thu gom Dầu**:
  - Chiều dài phao quây: $L = 3 \times \text{LOA}$ tàu bị nạn.
  - Lực căng neo phao: $T = k \cdot v^2 \cdot h$.
  - Công suất thu gom thực tế của máy hút dầu (Skimmer): $R_{net} = E \times (v \cdot w \cdot h)$.

---

## 2. Thiết kế Kiến trúc Hybrid "Cả 3"

1. **Micro-modules `< 200 LOC` trong `src/core/maritime/`**:
   - `phase_327_ballast_water_uscg.py` (~130 LOC)
   - `phase_328_decarb_fueleu_fuels.py` (~140 LOC)
   - `phase_329_lifting_appliances.py` (~120 LOC)
   - `phase_330_oil_spill_oprc_neba.py` (~130 LOC)
2. **Central Facade**:
   - `src/core/maritime_ballast_decarb_lifting_spill_engine.py` (~60 LOC): Re-export toàn bộ dataclasses và evaluation engines.
3. **Typer CLI Command Group**:
   - `src/cli/commands/maritime_ballast_decarb_lifting_spill_command.py` (~220 LOC): 4 Apps: `ballast_app`, `decarb_app`, `lifting_app`, `spill_app`.
   - 8 Bí danh tiếng Việt: `nuocdan`, `bwmuscg`, `giamphatthai`, `fueleu`, `thietbinang`, `cauport`, `trandau`, `oprcneba`.
4. **FastMCP Tools trong `scripts/mcp_server.py`**:
   - `mekong_ballast_water_uscg_evaluate`
   - `mekong_maritime_decarb_fueleu_evaluate`
   - `mekong_port_lifting_gear_inspect`
   - `mekong_oil_spill_oprc_neba_evaluate`
5. **Zero-Mock Test Suite**:
   - `tests/test_maritime_ballast_decarb_lifting_spill_suite.py` ($\ge 20$ test cases).
