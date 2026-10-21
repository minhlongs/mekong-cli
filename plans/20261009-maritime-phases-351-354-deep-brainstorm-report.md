# Báo cáo Brainstorming Chuyên sâu & Thiết kế Kỹ thuật: Maritime Phases 351–354

**Chủ đề:** Tính toán Ổn định & Ứng suất Tàu hàng rời, Mô phỏng Trôi dạt Hóa chất Độc hại HNS, Hệ thống Làm mát Trung tâm Nước biển & Xác thực Chứng nhận Hàng hải Điện tử  
**Kiến trúc:** Hybrid Modular Facade Pattern (< 200 LOC sub-modules + Facade + Typer CLI + FastMCP)  
**Tiêu chuẩn Quốc tế & Việt Nam:**  
- SOLAS XII/11 & IACS UR S1/S1A (Bending Moment & Shear Force permissible limits).
- IMO 2008 Intact Stability Code (2008 IS Code, Res. MSC.267(85)) — GM >= 0.15m, Area under GZ curve.
- OPRC-HNS Protocol 2000, CEDRE SEACARAMB & IMO MEPC/OPRC-HNS guidelines for chemical drift.
- ISO 28523 / TEMA / DNV rules for Central Cooling & Marine Growth Prevention System (MGPS).
- IMO FAL.5/Circ.39/Rev.2 (Guidelines for the use of electronic certificates) & W3C DID / Verifiable Credentials.

---

## 1. Phân tích Nghiệp vụ & Mô hình Tính toán

### Phase 351: Bulk Carrier Loading Computer, Stability & Hull Stress Engine
- **Tiêu chuẩn SOLAS XII/11 & IACS UR S1/S1A**:
  - Tàu chở xô hàng rời có nguy cơ nứt gãy thân tàu do ứng suất uốn quá mức (Still Water Bending Moment - SWBM) hoặc lực cắt quá mức (Still Water Shear Force - SWSF) khi xếp hàng xen kẽ (alternate hold loading).
  - Tỷ lệ ứng suất cho phép tại các mặt cắt sườn:
    $$\% \text{SWBM} = \frac{M_{\text{calc}}}{M_{\text{permissible}}} \times 100\% \le 100\%$$
    $$\% \text{SWSF} = \frac{F_{\text{calc}}}{F_{\text{permissible}}} \times 100\% \le 100\%$$
- **Ổn định ban đầu và đường cong cánh tay đòn hồi phục GZ (2008 IS Code)**:
  - Chiều cao tâm nghiêng ban đầu hiệu chỉnh mặt thoáng chất lỏng:
    $$GM_{\text{fluid}} = KM - KG - \sum \frac{\rho_i \cdot i_{xx}}{\Delta} \ge 0.15\text{ m}$$
  - Cánh tay đòn hồi phục:
    $$GZ(\theta) = GM_{\text{fluid}} \cdot \sin(\theta) + \overline{MS}(\theta) - KG \cdot \sin(\theta)$$
  - Yêu cầu diện tích dưới đường cong $GZ$:
    $$\text{Area}_{0^\circ \to 30^\circ} \ge 0.055\text{ m}\cdot\text{rad}, \quad \text{Area}_{0^\circ \to 40^\circ} \ge 0.090\text{ m}\cdot\text{rad}, \quad \text{Area}_{30^\circ \to 40^\circ} \ge 0.030\text{ m}\cdot\text{rad}$$
    $$GZ_{\text{max}} \ge 0.20\text{ m at } \theta \ge 30^\circ$$

### Phase 352: HNS Chemical Spill Drift Trajectory & Hazard Zone Engine
- **Quy chuẩn OPRC-HNS Protocol 2000 & CEDRE**:
  - Hóa chất độc hại và nguy hiểm (Hazardous & Noxious Substances - HNS) phân loại theo đặc tính SEACARAMB:
    - **G** (Gas), **E** (Evaporator), **F** (Floater), **D** (Dissolver), **S** (Sinker), cùng các tổ hợp kép (e.g., **FED**, **FE**, **FD**).
- **Véctơ trôi dạt hóa chất bề mặt (Surface Drift Mechanics)**:
  - Véctơ vận tốc trôi:
    $$\vec{V}_{\text{drift}} = \vec{V}_{\text{current}} + \alpha \cdot \vec{V}_{\text{wind}}$$
    Trong đó $\alpha \approx 0.03$ ($3\%$ tốc độ gió, góc lệch leeway $0^\circ - 15^\circ$ theo Coriolis).
  - Tọa độ dự báo sau $\Delta t$ giờ:
    $$\Delta \text{Lat} = \frac{V_{y} \cdot \Delta t}{60}, \quad \Delta \text{Lon} = \frac{V_{x} \cdot \Delta t}{60 \cdot \cos(\text{Lat})}$$
- **Vùng nguy hiểm cách ly khẩn cấp (Emergency Response Isolation Zone)**:
  - Xác định bán kính cách ly ban đầu theo độ bay hơi/độc tính khí:
    $$R_{\text{iso}} = R_0 \cdot \sqrt{\frac{Q_{\text{spill\_ton}}}{10.0}} \quad (\text{hải lý})$$

### Phase 353: Central Seawater Cooling & MGPS Bio-Fouling Prevention Engine
- **Hệ thống làm mát trung tâm (Central Cooling Water System - CCWS)**:
  - Bộ trao đổi nhiệt tấm Titanium (Plate Heat Exchangers - PHE):
    $$Q = \dot{m}_{\text{SW}} \cdot C_{p,\text{SW}} \cdot (T_{\text{SW,out}} - T_{\text{SW,in}}) = \dot{m}_{\text{FW}} \cdot C_{p,\text{FW}} \cdot (T_{\text{FW,in}} - T_{\text{FW,out}})$$
  - Chênh lệch nhiệt độ trung bình logarit (LMTD):
    $$\Delta T_{\text{lm}} = \frac{(T_{\text{FW,in}} - T_{\text{SW,out}}) - (T_{\text{FW,out}} - T_{\text{SW,in}})}{\ln\left(\frac{T_{\text{FW,in}} - T_{\text{SW,out}}}{T_{\text{FW,out}} - T_{\text{SW,in}}}\right)}$$
  - Tiết kiệm năng lượng: Tàu chạy tốc độ cao ($V > 12\text{ hải lý/h}$) kích hoạt họng hút nước biển tự nhiên (Seawater Scoop Injection) hoặc bơm VFD biến tần, giảm $30 - 60\%$ điện năng tiêu thụ bơm.
- **Hệ thống chống sinh vật biển bám (Marine Growth Prevention System - MGPS)**:
  - Điện phân anode đồng (Cu) và nhôm (Al) trong hộp hút nước biển (sea chest):
    - Nồng độ ion Cu tối ưu: $2 - 5\ \mu\text{g/L}$ ($0.002 - 0.005\text{ mg/L}$) để tiêu diệt ấu trùng hà và tảo mà không vượt ngưỡng ô nhiễm môi trường.
    - Anode nhôm tạo kết tủa $Al(OH)_3$ phủ một lớp màng chống ăn mòn bên trong đường ống thép.

### Phase 354: Marine E-Certificates & W3C Verifiable Credentials Engine
- **Tiêu chuẩn IMO FAL.5/Circ.39/Rev.2**:
  - Hướng dẫn công nhận giấy chứng nhận điện tử của tàu (Class Certificate, Safety Construction, Load Line, Marpol I/VI, MLC, SMC/ISPS).
  - 4 thuộc tính bắt buộc của E-Certificate:
    1. Cơ quan phát hành ủy quyền (Recognized Organization - RO/Đăng kiểm).
    2. Mã định danh duy nhất (Unique Tracking Number - UTN).
    3. Chữ ký số / Con dấu điện tử toàn vẹn (Digital Signature / Cryptographic Hash).
    4. Cổng xác thực trực tuyến công khai (Verification Link / QR Portal).
- **Mô hình W3C Verifiable Credentials (VC) & Data Integrity**:
  - Chuỗi băm SHA-256 xác thực chống làm giả:
    $$\text{ProofHash} = \text{SHA256}(\text{UTN} \parallel \text{IMO} \parallel \text{IssueDate} \parallel \text{ExpiryDate} \parallel \text{IssuerRO})$$
  - Kiểm tra trạng thái hiệu lực: Đang hiệu lực (ACTIVE), Hết hạn (EXPIRED), Bị đình chỉ (SUSPENDED), hoặc Bị thu hồi (REVOKED).

---

## 2. Kiến trúc Module & Phân bổ File (<200 LOC/file)

1. `src/core/maritime/phase_351_bulk_loading_stability.py` (~140 LOC)
2. `src/core/maritime/phase_352_hns_chemical_spill_drift.py` (~135 LOC)
3. `src/core/maritime/phase_353_central_cooling_mgps.py` (~130 LOC)
4. `src/core/maritime/phase_354_marine_ecert_verification.py` (~135 LOC)
5. `src/core/maritime_loading_hns_cool_ecert_engine.py` (~50 LOC) — Facade trung tâm
6. `src/cli/commands/maritime_loading_hns_cool_ecert_command.py` (~150 LOC) — Typer CLI với 8 bí danh
7. `scripts/mcp_server.py` — Đăng ký 4 FastMCP tools
8. `tests/test_maritime_loading_hns_cool_ecert_unit_suite.py` (~150 LOC)
9. `tests/test_maritime_loading_hns_cool_ecert_cli_mcp_suite.py` (~140 LOC)
