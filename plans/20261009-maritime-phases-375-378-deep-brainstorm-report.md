# Báo cáo Brainstorming Chuyên sâu & Thiết kế Kỹ thuật: Maritime Phases 375–378 & Refactor Kiến trúc

**Chủ đề:** Tối ưu Định tuyến Thời tiết & Khử cacbon CII, Kiểm soát Thu hồi Khí VOC Tàu dầu, Tối ưu Bãi Container & Điều độ Cẩu bãi RTG/YC, Tuần hoàn Nước ngưng HVAC & Nước xám Sinh hoạt Tàu biển  
**Kiến trúc:** Hybrid Modular Facade Pattern (< 200 LOC sub-modules + Central Facade + Typer CLI + FastMCP Tools)  
**Tiêu chuẩn Quốc tế & Quy chuẩn Việt Nam:**
- **IMO Res. MEPC.328(76), ISO 15016:2015 & IMO Res. MEPC.336(76)** (Operational Carbon Intensity Indicator CII calculation, Voyage Weather Routing wave/wind added resistance modeling, speed reduction vs fuel consumption, AER/cii rating A to E).
- **MARPOL Annex VI Reg 15, IMO MSC/Circ.585 & OCIMF Vapor Emission Control (VEC) Systems** (Crude oil volatile organic compounds recovery, vapor balancing between shore terminal and cargo tanks, closed-loop pressure relief valves, LEL explosive limit monitors <= 50% LEL).
- **UNCTAD Container Terminal Handbook, IAPH Smart Port Guidelines & Quyết định 1579/QĐ-TTg** (Container yard block stacking, reshuffling penalty minimization, Rubber-Tyred Gantry / Yard Crane dispatch, dwell time and dangerous goods segregation IMDG block allocation).
- **IMO Res. MEPC.227(64), WHO Guide to Ship Sanitation & QCVN 14:2008/BTNMT Cột A** (Air conditioning condensate recovery, greywater filtration & UV/ozonation, technical freshwater reuse for deck washing, boiler feed, and sanitary flush, zero discharge in marine protected areas).

---

## 1. Phân tích Nghiệp vụ & Mô hình Tính toán Kỹ thuật

### Phase 375: Voyage Weather Routing & CII Dynamic Decarbonization Optimization Engine
- **Mô hình Kháng lực Khí tượng (Added Resistance in Waves & Wind - ISO 15016)**:
  - Kháng lực gió khí quyển:
    $$R_{\text{wind}} = \frac{1}{2} \rho_{\text{air}} A_{\text{trans}} C_X(\theta_{\text{rel}}) V_{\text{rel}}^2$$
    Trong đó: $\rho_{\text{air}} \approx 1.225\text{ kg/m}^3$, $A_{\text{trans}}$ là diện tích cản gió mặt trước, $C_X$ là hệ số cản theo góc gió tương đối $\theta_{\text{rel}}$, $V_{\text{rel}}$ là tốc độ gió biểu kiến.
  - Kháng lực sóng đại dương (JONSWAP / Pierson-Moskowitz spectrum):
    $$R_{\text{wave}} = 2 \rho_{\text{sea}} g \int_0^\infty \int_{-\pi}^\pi S(\omega, \theta) \left( \frac{R_{\text{wave}}(\omega)}{H_s^2 / 4} \right) d\theta d\omega$$
    Thực tế chuẩn hóa: $\Delta P_{\text{weather}} = P_{\text{calm}} \cdot (1 + \alpha_{\text{Beaufort}} \cdot \text{BF}^2)$.
- **Tối ưu hóa Chỉ số Cường độ Cacbon Tàu biển (CII & Attained CII)**:
  - Chỉ số Carbon Intensity thực tế theo hải trình:
    $$\text{CII}_{\text{attained}} = \frac{\sum (F_j \times C_{F, j})}{\text{DWT} \times D_{\text{travel}}} \times 10^6 \quad (\text{g CO}_2\text{ / (DWT}\cdot\text{nm)})$$
  - So sánh với giá trị tham chiếu yêu cầu $\text{CII}_{\text{required}} = a \cdot \text{DWT}^{-c} \cdot (1 - Z / 100)$.
  - Phân hạng năng lượng:
    - Hạng A: $\text{Ratio} \le d_1$ (Superior)
    - Hạng B: $d_1 < \text{Ratio} \le d_2$ (Minor superior)
    - Hạng C: $d_2 < \text{Ratio} \le d_3$ (Standard compliant)
    - Hạng D: $d_3 < \text{Ratio} \le d_4$ (Minor inferior - Cảnh báo kế hoạch SEEMP III)
    - Hạng E: $\text{Ratio} > d_4$ (Inferior - Bắt buộc lập CAP hành động khắc phục).
- **Thuật toán Khuyến nghị Tốc độ Tối ưu (Speed Optimization)**:
  - Giảm tốc độ kinh tế (Just-In-Time arrival) để giảm lượng tiêu thụ nhiên liệu lập phương ($P \propto V^3$) khi gặp vùng biển bão.

---

### Phase 376: Oil Tanker VOC Emission Recovery & Vapor Balancing Engine
- **Cơ chế Phát thải VOC trên Tàu Dầu (Crude Oil Volatile Organic Compounds)**:
  - Quá trình bơm hàng (loading) và hành trình không tải (laden/ballast voyage) sinh ra hơi hydrocacbon nhẹ (Methane, Ethane, Propane, Butane, Pentane).
  - Áp suất hơi bồn chứa $P_{\text{tank}}$ so với giá trị cài đặt P/V valve ($+14.0\text{ kPa}$ áp dương, $-3.5\text{ kPa}$ áp âm).
- **Cân bằng Khí Khép kín (Vapor Balancing - IMO MSC/Circ.585)**:
  - Kết nối hệ thống hồi hơi VEC từ tàu về bồn bờ (shore terminal) hoặc giữa hai tàu trong hoạt động sang mạn (STS Transfer).
  - Tốc độ hồi hơi tối đa theo lưu lượng nạp hàng:
    $$Q_{\text{vapor\_req}} = 1.25 \times Q_{\text{loading\_rate}} \quad (\text{m}^3\text{/h})$$
- **Hệ thống Thu hồi Hơi Ngưng tụ (Condensation & Absorption Recovery Unit - VRCU)**:
  - Nén và làm lạnh sâu hơi hydrocacbon ngưng tụ tái nạp lại bồn hàng:
    $$\Delta M_{\text{VOC\_recovered}} = V_{\text{vapor}} \cdot \rho_{\text{VOC}} \cdot \eta_{\text{recovery}} \quad (\text{kg})$$
  - Giảm thiểu khí nhà kính và ozone tầng thấp: Tương đương giảm $2.8\text{ kg CO}_2\text{ eq / kg VOC}$.
- **Khóa Liên động An toàn (Safety Interlocks)**:
  - Nồng độ oxy trong dòng hồi hơi $O_2 \le 8.0\%\text{ vol}$ (theo MARPOL/SOLAS bồn dầu phải trơ hóa bằng khí trơ inert gas).
  - Giới hạn áp suất bồn không vượt quá $80\%\text{ P/V setting}$. Báo động rò rỉ khí độc $H_2S \ge 5\text{ ppm}$.

---

### Phase 377: Port Container Terminal Automated Yard Stacking & YC/RTG Dispatch Engine
- **Mô hình Khối Bãi Container (Yard Block Stacking Logic)**:
  - Khối bãi chuẩn $6 \times 4 \times 5$ (6 hàng bays, 4 luồng rows, 5 tầng tiers).
  - Giảm thiểu đảo chuyển bãi (Reshuffling Minimization):
    Container có thời gian xuất bãi sớm hơn phải xếp ở trên container xuất bãi muộn hơn.
    $$N_{\text{reshuffle\_penalty}} = \sum_{i=1}^n \max(0, \text{Tier}_i - \text{Tier}_{\text{target}})$$
- **Phân bổ Khối Hàng Nguy hiểm IMDG & Container Lạnh (Reefer Stacking)**:
  - IMDG Segregation theo Bộ luật IMDG: Cách ly tối thiểu 1 bay cho hàng hóa chất dễ cháy Class 3 và chất oxy hóa Class 5.1.
  - Reefer plug capacity: Tỷ lệ tải ổ cắm điện lạnh không vượt quá $90\%$ công suất trạm biến áp bãi cảng.
- **Điều độ Cẩu Khung Bãi (RTG / Yard Crane Dispatch - QCSP Coupling)**:
  - Ghép nối tiến độ giải phóng tàu từ cẩu bờ (Quay Crane):
    $$\text{Tốc độ tiếp nhận bãi } Q_{\text{yard\_req}} \ge \sum Q_{\text{QC}} \quad (\text{moves/h})$$
  - Phân bổ số lượng cẩu RTG cho mỗi Block: Tối thiểu 1 RTG phục vụ 2 Quay Cranes để tránh nghẽn luồng xe kéo bãi (Internal Movement Vehicles - IMV).
  - Tối ưu quãng đường di chuyển rùa cẩu (Gantry Travel Distance):
    $$D_{\text{travel}} = \sum |x_{k+1} - x_k| + |y_{k+1} - y_k|$$

---

### Phase 378: Shipboard HVAC Condensate & Greywater Circular Reclamation Engine
- **Thu hồi Nước ngưng Dàn lạnh HVAC (Air Conditioning Condensate Harvesting)**:
  - Khối lượng nước ngưng sinh ra từ luồng không khí nhiệt đới (Mekong Delta / Biển Đông):
    $$\dot{m}_{\text{cond}} = \dot{m}_{\text{air}} \times (w_{\text{in}} - w_{\text{out}}) \quad (\text{kg/h})$$
    Trong điều kiện khí hậu Việt Nam ($T=34^\circ\text{C}$, $\text{RH}=85\% \to T_{\text{supply}}=18^\circ\text{C}$, $\text{RH}=95\%$), tàu container tạo ra từ $3.0\text{ đến }8.0\text{ m}^3\text{ nước ngưng/ngày}$.
  - Nước ngưng HVAC có độ dẫn điện cực thấp ($\text{TDS} < 30\text{ ppm}$), lý tưởng tái sử dụng làm nước cấp nồi hơi phụ (Boiler Feed Water) hoặc rửa buồng lái/sàn tàu.
- **Tái sinh Nước xám Sinh hoạt (Greywater Recycling - QCVN 14:2008/BTNMT)**:
  - Phân loại nước xám: Nước thải từ vòi sen, bồn rửa tay, giặt ủi (không chứa chất thải đen toilet).
  - Quy trình xử lý đa tầng:
    Lọc thô $\to$ Bể lọc cát/than hoạt tính $\to$ Màng vi lọc UF ($0.02\ \mu\text{m}$) $\to$ Khử trùng UV/Ozone.
  - Tiêu chuẩn nước tái sử dụng:
    $\text{BOD}_5 \le 20\text{ mg/L}$, $\text{TSS} \le 10\text{ mg/L}$, $\text{Coliform} \le 100\text{ MPN/100mL}$, độ đục $\le 2.0\text{ NTU}$.
- **Cân bằng Nước Bền vững & Lợi ích Kinh tế**:
  - Giảm phụ thuộc vào nước ngọt cấp từ cảng (Bunkering fresh water cost: $5 - 10\text{ USD/m}^3$).
  - Khóa liên động cấm xả nước xám chưa qua xử lý trong khu vực bảo tồn biển và lãnh hải nội thủy 3 hải lý.

---

## 2. Thiết kế Kiến trúc Mã nguồn (Hybrid Modular Facade)

Tất cả các tệp mã nguồn và kiểm thử tuân thủ nghiêm ngặt chuẩn `< 200 dòng/tệp`:

| Module Path | Mục đích & Nghiệp vụ | Dự kiến LOC |
|-------------|----------------------|-------------|
| `src/core/maritime/phase_375_voyage_weather_routing_cii.py` | Tính toán kháng lực sóng gió ISO 15016, mô phỏng CII rating A-E & tối ưu tốc độ JIT | ~140 LOC |
| `src/core/maritime/phase_376_voc_vapor_recovery_balancing.py` | Quản lý hơi hydrocacbon VOC MARPOL VI, tỷ lệ cân bằng hơi VEC, giảm phát thải GHG | ~135 LOC |
| `src/core/maritime/phase_377_container_yard_rtg_dispatch.py` | Tối ưu xếp bãi container, hạn chế reshuffle, điều độ cẩu bãi RTG & an toàn IMDG | ~140 LOC |
| `src/core/maritime/phase_378_hvac_condensate_greywater_reuse.py` | Thu hồi nước ngưng HVAC, tái sinh nước xám QCVN 14 cột A & cấp nước tuần hoàn tàu biển | ~135 LOC |
| `src/core/maritime_voyage_voc_yard_greywater_engine.py` | Facade trung tâm tổng hợp đánh giá multi-domain `run_all` cho Phases 375–378 | ~145 LOC |
| `src/cli/commands/maritime_voyage_voc_yard_greywater_command.py` | 4 Typer sub-apps với 8 alias lệnh song ngữ Anh - Việt | ~165 LOC |
| `src/cli/app_setup.py` | Đăng ký 8 command groups vào Typer app root | ~35 dòng diff |
| `scripts/mcp_server.py` | Đăng ký 4 FastMCP async tool endpoints | ~80 dòng diff |
| `tests/test_maritime_voyage_voc_unit_suite.py` | 8 zero-mock unit tests cho Weather Routing CII & VOC Recovery | ~150 LOC |
| `tests/test_maritime_yard_greywater_unit_suite.py` | 8 zero-mock unit tests cho Container Yard RTG & HVAC Greywater Reuse | ~150 LOC |
| `tests/test_maritime_375_to_378_cli_mcp_suite.py` | 4 zero-mock integration tests cho Central Facade, Typer CLI & FastMCP Tools | ~165 LOC |

---

## 3. Danh mục Lệnh CLI Song ngữ Anh - Việt & FastMCP Endpoints

### 8 Lệnh Typer CLI:
1. `weathercii` / `dinhhuongcii`: Đánh giá định tuyến thời tiết, dự báo CII và tối ưu tốc độ hành trình.
2. `vocvapor` / `thuhoikhivoc`: Kiểm soát phát thải hơi hydrocacbon VOC, cân bằng hơi tàu - bờ và tín chỉ GHG.
3. `yardstack` / `dieudobaicont`: Tối ưu xếp bãi container, tính reshuffle penalty và điều độ cẩu RTG.
4. `greywater` / `tuanhoannuocxam`: Tính toán thu hồi nước ngưng HVAC, tái sinh nước xám và cân bằng nước ngọt tàu.

### 4 FastMCP Tools:
1. `mekong_maritime_weather_cii_evaluate`: Tối ưu hải trình theo sóng gió và phân hạng năng lượng CII IMO.
2. `mekong_maritime_voc_recovery_evaluate`: Đánh giá an toàn cân bằng hơi VEC và thu hồi hơi VOC bồn dầu.
3. `mekong_maritime_yard_rtg_dispatch_evaluate`: Đánh giá hiệu suất bãi container và năng suất cẩu RTG.
4. `mekong_maritime_greywater_reuse_evaluate`: Đánh giá chất lượng nước ngưng HVAC và nước xám tái sinh.

---

## 4. Kế hoạch Triển khai (Execution Roadmap)

- **Bước 1: Triển khai 4 Micro-Engine Lõi** (`src/core/maritime/phase_375_*.py` đến `phase_378_*.py`) với các công thức toán học và tiêu chuẩn IMO/QCVN.
- **Bước 2: Triển khai Facade Trung tâm** (`src/core/maritime_voyage_voc_yard_greywater_engine.py`) với hàm `run_all`.
- **Bước 3: Triển khai Typer CLI & Tích hợp FastMCP** với 8 bí danh lệnh Anh - Việt và 4 FastMCP tools.
- **Bước 4: Thiết lập Bộ Kiểm thử Toàn diện** (3 test suites, 20 zero-mock unit & integration tests).
- **Bước 5: Chạy Ruff Lint & Pytest Verification** đảm bảo 100% pass và `< 200 LOC/tệp`.
- **Bước 6: Cập nhật Bộ nhớ & Tài liệu Dự án** (`MEMORY.md`, `project-changelog.md`, `development-roadmap.md`).
