---
name: automotive
description: Vietnamese Automotive Manufacturing, Type Approval (VTA), Emission & EV Compliance Suite.
---

# mekong automotive — Autonomous Vietnamese Automotive Manufacturing, Type Approval & EV Compliance Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Giao thông đường bộ 2008 (Luật số 23/2008/QH12)**:
   - Thống nhất quản lý chất lượng phương tiện cơ giới đường bộ tham gia giao thông.
   - Cơ quan quản lý nhà nước: **Bộ Giao thông Vận tải (Bộ GTVT)**, **Cục Đăng kiểm Việt Nam (Vietnam Register - VR)** và Bộ Công Thương.
2. **Điều kiện sản xuất, lắp ráp ô tô (Nghị định 116/2017/NĐ-CP & Nghị định 17/2020/NĐ-CP)**:
   - **Đường thử nội bộ**: Chiều dài tối thiểu **$800\text{ m}$**, đảm bảo các điều kiện địa hình (đường bằng phẳng, đường dốc ngập nước, đường sỏi đá gập ghềnh, đường cua trơn trượt).
   - **Dây chuyền kiểm tra chất lượng xuất xưởng**: Bắt buộc trang bị đầy đủ các thiết bị kiểm tra tự động:
     * Thiết bị kiểm tra góc trượt ngang bánh xe dẫn hướng (Side Slip Tester).
     * Thiết bị kiểm tra lực phanh (Brake Tester).
     * Thiết bị đo cường độ và độ lệch chùm sáng đèn pha (Headlight Tester).
     * Thiết bị phân tích nồng độ khí thải hoặc đo độ khói khí xả (Emission Analyzer / Opacimeter).
   - **Mạng lưới bảo hành, bảo dưỡng ủy quyền**: Cam kết hệ thống cơ sở bảo hành, bảo dưỡng đáp ứng điều kiện tại các tỉnh thành phố trên toàn quốc.
3. **Chứng nhận chất lượng an toàn kỹ thuật và BVMT kiểu loại (VTA) & Chuẩn khí thải Euro 5 (Thông tư 25/2019/TT-BGTVT & Quyết định 49/2011/QĐ-TTg)**:
   - Áp dụng chuẩn khí thải **Mức 5 (tương đương Euro 5)** bắt buộc từ 01/01/2022:
     * Động cơ xăng: $CO \le 1.00\text{ g/km}$, $THC \le 0.10\text{ g/km}$, $NMHC \le 0.068\text{ g/km}$, $NO_x \le 0.060\text{ g/km}$, $PM \le 0.0045\text{ g/km}$.
     * Động cơ diesel: $CO \le 0.50\text{ g/km}$, $NO_x \le 0.180\text{ g/km}$, $HC + NO_x \le 0.230\text{ g/km}$, $PM \le 0.0045\text{ g/km}$.
     * Xe thuần điện (BEV): Không phát thải trực tiếp (Zero Emission).
4. **Hàm lượng giá trị khu vực RVC & Ưu đãi thuế quan ATIGA Form D**:
   - Công thức tính: $RVC = \frac{FOB - VNM}{FOB} \times 100\%$.
   - Tỷ lệ nội địa hóa nội khối ASEAN đạt **$RVC \ge 40\%$** đủ điều kiện cấp Giấy chứng nhận xuất xứ hàng hóa C/O Form D, hưởng **thuế nhập khẩu ưu đãi $0\%$**.
5. **Tiêu chuẩn an toàn pin và hệ thống điện cao áp xe điện (QCVN 91:2019/BGTVT & QCVN 09:2015/BGTVT)**:
   - Thử nghiệm an toàn pin động lực (LFP, NMC, Solid-State): Quá nạp, ngắn mạch ngoài, ngâm nước sâu chuẩn IP67 (ngập sâu 1m trong 30 phút), va chạm nghiền nén cơ học, chống lan truyền nhiệt giữa các cell pin (Thermal Runaway Prevention).
   - Cơ chế ngắt điện cao áp tự động (HV Cutoff): Contactor ngắt điện cao áp an toàn dưới $60\text{V DC}$ trong vòng $100\text{ ms}$ khi có tín hiệu va chạm từ cảm biến túi khí.
6. **Chu kỳ đăng kiểm phương tiện cơ giới đường bộ (Thông tư 08/2023/TT-BGTVT & Thông tư 16/2021/TT-BGTVT)**:
   - Ô tô chở người dưới 9 chỗ không kinh doanh: Miễn kiểm định lần đầu trong **36 tháng** đối với xe mới; chu kỳ **24 tháng** (xe đến 7 năm); **12 tháng** (xe từ 7 đến 20 năm); **06 tháng** (xe trên 20 năm).
   - Ô tô kinh doanh vận tải: Miễn kiểm định lần đầu trong **24 tháng**; chu kỳ **12 tháng** (xe đến 5 năm); **06 tháng** (xe trên 5 năm).
7. **Lưu trữ SQLite WAL**: Bảng `automotive_manufacturers`, `vehicle_type_approvals`, `ev_battery_audits`, `vehicle_inspections` tại `.mekong/automotive.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan ngành sản xuất ô tô, chứng nhận kiểu loại VTA, pin xe điện và đăng kiểm
mekong automotive

# Thẩm tra điều kiện sản xuất, lắp ráp ô tô theo Nghị định 116/2017/NĐ-CP & Nghị định 17/2020/NĐ-CP
mekong automotive license "Nhà máy Sản xuất Ô tô VinFast" --tax-id "0108877665" --address "Cát Hải, Hải Phòng" --track 850 --side-slip --brake --emission --service-centers 85

# Thẩm định Chứng nhận kiểu loại ô tô (VTA) theo Thông tư 25/2019/TT-BGTVT và chuẩn Euro 5
mekong automotive vta "Mekong E-SUV VF8" --type ELECTRIC_VEHICLE --powertrain ELECTRIC --co 0 --nox 0 --pm 0 --rvc 48.5

# Tính toán tỷ lệ hàm lượng giá trị khu vực RVC theo Hiệp định ATIGA Form D
mekong automotive rvc "Mekong Sedan Lux" 650000000 320000000

# Kiểm toán an toàn pin xe điện và hệ thống điện cao áp theo QCVN 91:2019/BGTVT
mekong automotive battery "Mekong E-SUV VF8" --chemistry LFP --voltage 400 --capacity 87.7 --overcharge --short-circuit --ip67 --thermal --cutoff 35

# Tính toán chu kỳ và hạn đăng kiểm phương tiện cơ giới theo Thông tư 08/2023/TT-BGTVT
mekong automotive inspect "51K-999.88" --category PASSENGER_CAR_UNDER_9 --non-commercial --year 2026

# Tra cứu danh mục hồ sơ ngành ô tô
mekong automotive list manufacturers
mekong automotive list vtas
mekong automotive list batteries
mekong automotive list inspections

# Xuất báo cáo trạng thái hệ thống định dạng JSON
mekong automotive status --json
```

---

## MCP Tools Integration

| Tool Name | Engine Method | Mục Tiêu & Mô Tả Nghiệp Vụ |
|---|---|---|
| `mekong_automotive_license` | `license_manufacturer` | Thẩm tra điều kiện sản xuất, lắp ráp ô tô (đường thử >= 800m, thiết bị đo phanh/trượt/khí thải) NĐ 116. |
| `mekong_automotive_vta` | `audit_type_approval` | Thẩm định chứng nhận an toàn kỹ thuật & BVMT kiểu loại VTA và tiêu chuẩn khí thải Euro 5 (TT 25/2019). |
| `mekong_automotive_rvc` | `calculate_rvc_localization` | Tính toán tỷ lệ nội địa hóa khu vực RVC theo Hiệp định ATIGA Form D (ngưỡng >= 40% thuế 0%). |
| `mekong_automotive_battery` | `audit_ev_battery_safety` | Kiểm toán an toàn pin xe điện và cơ chế ngắt cao áp khi va chạm theo QCVN 91:2019/BGTVT. |
| `mekong_automotive_inspect` | `calculate_inspection_schedule` | Tính toán chu kỳ và thời hạn đăng kiểm phương tiện cơ giới đường bộ theo Thông tư 08/2023/TT-BGTVT. |
| `mekong_automotive_list` | `list_*` | Tra cứu danh mục nhà máy sản xuất, chứng chỉ kiểu loại VTA, kiểm định pin EV và lịch đăng kiểm. |
| `mekong_automotive_status` | `get_status` | Báo cáo telemetry tổng hợp sản xuất ô tô, chứng nhận kiểu loại, thị phần xe điện và an toàn đăng kiểm. |
