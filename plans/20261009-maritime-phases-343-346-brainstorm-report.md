# Báo cáo Brainstorming Chuyên sâu & Tái cấu trúc: Maritime Phases 343–346

**Chủ đề:** Hệ thống Điều hướng Hải đồ Điện tử, Đo lường Cấp dầu MFM, Hóa nghiệm Nồi hơi & Quyết toán Đại lý Cảng
**Kiến trúc:** Hybrid Modular Facade (< 200 LOC per file) + Typer CLI + FastMCP + Zero-Mock Testing
**Quy chuẩn Quốc tế & Việt Nam:** IMO Res. A.893(21), SOLAS V/34, SS 648:2019, ISO 22192, ISO 5814, BS 2486, FONASBA Standard Port Agency Agreement, Nghị định 58/2017/NĐ-CP & Thông tư 39/2023/TT-BGTVT.

---

## 1. Phân tích Nghiệp vụ Chuyên sâu & Công thức Kỹ thuật

### Phase 343: ECDIS Passage Planning & Narrow Channel Pilotage (IMO Res. A.893(21), SOLAS V/34)
- **4 Giai đoạn Passage Plan**: Appraisal (Đánh giá), Planning (Lập kế hoạch), Execution (Thực thi), Monitoring (Giám sát).
- **Phân hạng CATZOC (Bathymetric Zone of Confidence)**:
  - A1: Sai số độ sâu $\pm (0.5\text{ m} + 1\%d)$, vị trí $\pm 5\text{ m}$.
  - A2: Sai số độ sâu $\pm (1.0\text{ m} + 2\%d)$, vị trí $\pm 20\text{ m}$.
  - B: Sai số độ sâu $\pm (1.0\text{ m} + 2\%d)$, vị trí $\pm 50\text{ m}$.
  - C: Sai số độ sâu $\pm (2.0\text{ m} + 5\%d)$, vị trí $\pm 500\text{ m}$.
- **Công thức Đường đẳng sâu An toàn (Safety Contour & Depth)**:
  $$\text{Safety Depth} = \text{Draft} + \text{Squat} + \text{UKC}_{\text{company}} - \text{Height of Tide} + \text{CATZOC Allowance}$$
  - $\text{Safety Contour}$: Làm tròn lên đường đẳng sâu kế tiếp khả dụng trên hải đồ điện tử ENC ($10\text{ m}, 15\text{ m}, 20\text{ m}$).
- **Hành lang Luồng hẹp (Cross Track Limit - XTL/XTE)**:
  - Luồng hẹp hàng hải (Sài Gòn - Vũng Tàu, Lạch Huyện): $XTL \le 50\text{ m}$.
  - Đoạn tiếp cận cảng: $XTL \le 100\text{ m}$; Vùng biển mở: $XTL \ge 500\text{ m}$.
  - Khung thời gian nhìn trước (Look-Ahead anti-grounding cone): vector $\ge 6\text{ phút}$.

### Phase 344: Bunkering MFM Mass Flow Metering Management (SS 648:2019, ISO 22192)
- **Nguyên lý Coriolis & Dung sai Đo lường**:
  - Đo trực tiếp khối lượng dòng chảy (Mass Flow $M$) độc lập với tỷ trọng và nhiệt độ.
  - Sai số cho phép tối đa (Maximum Permissible Error - MPE): $\pm 0.5\%$.
- **Cảnh báo Nhiễm khí / Hiệu ứng Bọt khí (Cappuccino Effect Detection)**:
  - Giám sát độ khuếch đại dao động ống Coriolis (Drive Gain): nếu $\text{Drive Gain} > 80\%$ hoặc gia tốc độ nhớt/tỷ trọng dao động đột ngột $> 2\%$, phát hiện hiện tượng sục khí ăn gian thể tích.
- **Đối soát Chênh lệch Khối lượng & Kháng nghị (Notice of Protest - NoP)**:
  $$\Delta M = M_{\text{MFM (Barge)}} - M_{\text{Sounding (Vessel)}}$$
  $$\text{Chênh lệch \%} = \frac{|\Delta M|}{M_{\text{MFM}}} \times 100\%$$
  - Nếu chênh lệch $> 0.5\%$: Kích hoạt cảnh báo tranh chấp, lập biên bản NoP tự động.
  - Tuân thủ hàm lượng lưu huỳnh BDN: $S \le 0.50\%$ (VLSFO toàn cầu) hoặc $S \le 0.10\%$ (ECA).

### Phase 345: Marine Boiler Water Treatment & Auxiliary Boiler Safety (ISO 5814, BS 2486)
- **Hóa nghiệm Nước Nồi hơi & Ngưỡng An toàn**:
  - Độ cứng (Hardness): $0\text{ ppm CaCO}_3$ (chống đóng cặn ống lửa/nước).
  - Clorua (Chloride $Cl^-$): Nồi hơi phụ $\le 300\text{ ppm}$; Nồi hơi ống nước cao áp $\le 30\text{ ppm}$.
  - Kiềm Phenolphthalein ($P\text{-Alkalinity}$): $100 - 300\text{ ppm CaCO}_3$; Độ pH chuẩn: $9.5 - 11.0$.
  - Khử oxy hòa tan ($O_2$ Scavenging): Dư lượng Hydrazine $N_2H_4: 0.05 - 0.2\text{ ppm}$ hoặc DEHA.
  - Dự trữ Phosphate ($\text{PO}_4^{3-}$): $20 - 40\text{ ppm}$ để kết tủa bùn cặn trôi nổi.
- **Tính toán Tỷ lệ Xả đáy Nồi hơi (Boiler Blowdown Rate)**:
  $$\text{Blowdown } \% = \frac{Cl^-_{\text{feedwater}}}{Cl^-_{\text{target}} - Cl^-_{\text{feedwater}}} \times 100\%$$
  - Phân tách xả bề mặt (Surface blowdown - hạ TDS/Clorua) và xả đáy (Bottom blowdown - tống bùn).

### Phase 346: Port Agency Disbursements Account & FONASBA Reconciliation
- **Quy trình Quyết toán Đại lý Cảng**:
  - Dự toán ban đầu (Proforma Disbursement Account - PDA).
  - Chi phí thực tế cuối cùng (Final Disbursement Account - FDA).
- **Hạng mục Đối soát Chi phí Cảng biển (Thông tư 39/2023/TT-BGTVT)**:
  - Phí trọng tải (Tonnage dues), Phí bảo đảm hàng hải (Maritime safety dues).
  - Phí hoa tiêu (Pilotage dues), Phí tàu lai dắt (Towage dues per HP/hour).
  - Phí cầu bến (Berthage dues), Bốc dỡ hàng hóa (Stevedoring), Nước ngọt & Thu gom rác thải.
- **Đối soát Số dư Tạm ứng & Phí Đại lý (FONASBA Standard Agreement)**:
  $$\text{Số dư Hoàn trả / Truy thu} = \text{Tiền Tạm ứng (Advance)} - \text{Tổng Chi phí FDA} - \text{Phí Đại lý (Agency Fee)}$$
  - Ngưỡng cảnh báo biến động chi phí: Chênh lệch từng hạng mục $> 5\%$ so với PDA yêu cầu giải trình và chứng từ gốc (vouchers).

---

## 2. Chiến lược Tái cấu trúc & Kiểm soát Kích thước Codebase (< 200 LOC)

1. **Phân tách Sub-module Chuyên biệt**:
   - `src/core/maritime/phase_343_ecdis_passage_planning.py` (~110 LOC)
   - `src/core/maritime/phase_344_bunkering_mfm_flow.py` (~115 LOC)
   - `src/core/maritime/phase_345_boiler_water_treatment.py` (~110 LOC)
   - `src/core/maritime/phase_346_port_agency_disbursements.py` (~115 LOC)
2. **Central Facade Thống nhất**:
   - `src/core/maritime_ecdis_mfm_boiler_agency_engine.py` (~45 LOC)
3. **Typer CLI Command Group**:
   - `src/cli/commands/maritime_ecdis_mfm_boiler_agency_command.py` (~135 LOC)
   - 8 Bí danh tiếng Việt: `ecdis`, `haidodientu`, `mfmbunker`, `dodaucoriolis`, `noihoint`, `hoanoihotau`, `portagency`, `quyettoancangg`.
4. **FastMCP Async Endpoints trong `scripts/mcp_server.py`**:
   - `mekong_ecdis_passage_plan_evaluate`
   - `mekong_bunkering_mfm_mass_balance_check`
   - `mekong_boiler_water_chemistry_evaluate`
   - `mekong_port_agency_fda_reconcile`
5. **Kiểm thử Zero-Mock Độc lập**:
   - `tests/test_maritime_ecdis_mfm_boiler_agency_unit_suite.py` (< 200 LOC)
   - `tests/test_maritime_ecdis_mfm_boiler_agency_cli_mcp_suite.py` (< 200 LOC)
