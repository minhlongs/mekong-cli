# Báo cáo Nghiên cứu Kỹ thuật & Chuẩn hóa: Maritime Phases 339–342

**Phạm vi:** Nghiên cứu nghiệp vụ chuyên sâu, công thức toán học và tiêu chuẩn quốc tế cho:
- **Phase 339:** IMO Polar Code & PWOM Navigation Risk (POLARIS RIO, MSC.1/Circ.1519, MDLT/PST).
- **Phase 340:** Cargo Hold Washwater & Cleaning Management (MARPOL Annex V HME, MEPC.295(71)).
- **Phase 341:** PCTC Ro-Ro Car Carrier EV Lithium-ion Fire Safety (SOLAS II-2, MSC.1/Circ.1615, Off-gas detection).
- **Phase 342:** Lloyd's Open Form LOF 2024 & SCOPIC Clause Salvage Arbitration (Salvage Convention 1989, P&I Club tariff).

---

## 1. Phase 339: IMO Polar Code & POLARIS Risk Index Outcome (RIO)
- **Chuẩn áp dụng:** IMO Res. MSC.385(94), Polar Code Part I-A & IMO MSC.1/Circ.1519.
- **Hệ thống Đánh giá Rủi ro Băng tuyết POLARIS:**
  - $RIO = \sum_{i=1}^{n} (C_i \times RIV_{i, ship})$
  - $C_i$: Nồng độ của loại băng thứ $i$ tính theo phần mười (tenths, $0 \le C_i \le 10$, $\sum C_i \le 10$).
  - $RIV_{i, ship}$: Giá trị chỉ số rủi ro phụ thuộc vào Cấp tàu phá băng (Polar Class PC1–PC7 hoặc tàu thông thường) và loại băng (Ice-free, Medium first-year, Thick first-year, Multi-year ice).
  - Phân loại quyết định:
    - $RIO \ge 0$: **Bình thường (Normal Operation)** — Cho phép hành hải tự do không cần hộ tống.
    - $-10 \le RIO < 0$: **Hạn chế (Elevated Operational Risk)** — Cho phép với tốc độ giảm an toàn ($v \le 5\text{ kts}$) hoặc có tàu phá băng hộ tống.
    - $RIO < -10$: **Cấm hoạt động (Operation Subject to Special Consideration / Prohibited)** — Vượt ngưỡng giới hạn kết cấu thân tàu.
- **Nhiệt độ phục vụ cực (PST):**
  - $PST = MDLT - 10^\circ C$ (MDLT: Nhiệt độ trung bình thấp nhất trong ngày của tháng lạnh nhất).
  - Yêu cầu vật liệu thép chống giòn lạnh, thiết bị sấy ấm cứu sinh và lương thực sinh tồn $\ge 5\text{ ngày}$.

---

## 2. Phase 340: Automated Cargo Hold Cleaning & MARPOL Annex V HME
- **Chuẩn áp dụng:** MARPOL 73/78 Annex V (MEPC.201(62), MEPC.295(71)), IMSBC Code.
- **Phân loại cặn hàng hóa (Cargo Residues):**
  - HME (Harmful to the Marine Environment): Phân loại độc hại thủy sinh cấp 1, độc mãn tính, hoặc chứa chất sinh ung thư/đột biến (CMR).
  - Non-HME (Không gây hại môi trường biển): Cặn than, ngũ cốc, cát thạch anh đã rửa sạch.
- **Quy tắc xả nước rửa hầm hàng (Hold Washwater Discharge Criteria):**
  - Cặn HME: **CẤM XẢ TUYỆT ĐỐI** ra biển toàn cầu. Toàn bộ nước rửa phải gom vào két lắng và xả cho phương tiện tiếp nhận cảng (Port Reception Facility - PRF).
  - Cặn Non-HME:
    - Ngoài vùng đặc biệt: Cho phép xả khi tàu đang hành trình cách bờ gần nhất $\ge 12\text{ hải lý}$.
    - Trong vùng đặc biệt: Chỉ được xả nếu cảng xuất phát và cảng đích không có cơ sở tiếp nhận, cách bờ $\ge 12\text{ NM}$, và ghi nhật ký rác thải (Garbage Record Book Part II).
- **Tính toán làm sạch & tẩy rửa:**
  - Lượng hóa chất tẩy rửa (Chemical Dosage): $V_{\text{chem}} = V_{\text{wash}} \times \text{PPM} \times 10^{-6}$.
  - Trung hòa kiềm/axit: pH nước xả trước khi bơm phải nằm trong dải $6.5 \le pH \le 8.5$.

---

## 3. Phase 341: PCTC Car Carrier EV Lithium-ion Fire Safety
- **Chuẩn áp dụng:** SOLAS II-2 Reg 20, IMO MSC.1/Circ.1615, EMSA Ro-Ro EV Fire Safety Guidance.
- **Giám sát Khí thoát thoát nhiệt (Off-Gas Detection Matrix):**
  - Pin Lithium-ion trước khi bốc cháy giải phóng hỗn hợp khí nguy hiểm: CO, $H_2$, HF (Hydrofluoric acid), VOCs.
  - Ngưỡng cảnh báo sớm: $CO > 30\text{ ppm}$, $H_2 > 200\text{ ppm}$, hoặc gia tốc nhiệt độ bề mặt $dT/dt \ge 1.0^\circ C/\text{giây}$.
- **Hệ thống Chữa cháy & Cách ly Cục bộ:**
  - Chăn chống cháy chuyên dụng (Fire Blanket): Khả năng chịu nhiệt $\ge 1,000^\circ C$, ngăn chặn ngọn lửa lan sang xe bên cạnh (Stowage spacing $\le 0.3\text{ m}$).
  - Lưu lượng nước làm mát ranh giới (Boundary Deluge Cooling): $Q_{\text{deluge}} \ge 10\text{ L/phút/m}^2$ trên boong xe kín.
  - Trạng thái sạc khuyến nghị (State of Charge - SoC): $\text{SoC} \le 30\% - 50\%$ khi xếp dỡ lên tàu.

---

## 4. Phase 342: Lloyd's Open Form (LOF 2024) & SCOPIC Clause Compensation
- **Chuẩn áp dụng:** International Convention on Salvage 1989 (Articles 13 & 14), LOF 2024, SCOPIC 2024 Agreement.
- **Thù lao cứu hộ Article 13 (No Cure - No Pay):**
  - Căn cứ: Giá trị tài sản cứu thoát (Salved Value = Vỏ tàu + Nhiên liệu + Hàng hóa + Tiền cước).
  - Tỷ lệ cứu hộ truyền thống: $5\% - 30\%$ salved value tùy theo mức độ rủi ro, thời tiết và nỗ lực ngăn ngừa ô nhiễm môi trường.
- **Điều khoản SCOPIC (Special Compensation P&I Club Clause):**
  - Chi phí nhân lực & thiết bị theo biểu giá cố định (Tariff Rates): Tàu lai dắt công suất lớn, salvage master, thợ lặn, máy bơm nổi.
  - Tiền thưởng khuyến khích chuẩn (Standard Uplift): $25\%$ trên tổng chi phí biểu giá SCOPIC.
  - Cơ chế Giảm trừ (Article 14 Discount Penalty):
    - Nếu Nhà cứu hộ kích hoạt SCOPIC nhưng Thù lao Article 13 sau đó cao hơn chi phí SCOPIC, Thù lao Article 13 bị phạt giảm $25\%$ của phần chênh lệch ($0.25 \times (\text{Award}_{\text{Art13}} - \text{SCOPIC})$).

---

## 5. Kết luận & Hướng Triển khai
- Áp dụng kiến trúc **Hybrid Modular Facade** (<200 LOC/file) cho 4 micro-engines, 1 central facade, 4 Typer CLI apps kèm 8 alias tiếng Việt, và 4 FastMCP async endpoints.
- Đảm bảo 100% zero-mock testing cho toàn bộ các tình huống tính toán số học.
