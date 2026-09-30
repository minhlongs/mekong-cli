---
name: geodesy
description: Vietnamese Geodesy, National Coordinates (VN-2000), Map Sovereignty & Cadastral GIS Suite.
---

# mekong geodesy — Autonomous Vietnamese Geodesy, Map Sovereignty & Cadastral GIS Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Đo đạc và bản đồ 2018 (Luật số 27/2018/QH14)**:
   - Thống nhất quản lý hoạt động đo đạc cơ bản, đo đạc chuyên ngành, xây dựng hạ tầng dữ liệu không gian địa lý quốc gia (NSDI).
   - Cơ quan quản lý nhà nước: **Bộ Tài nguyên và Môi trường (Cục Đo đạc, Bản đồ và Thông tin địa lý Việt Nam)**.
   - **Hệ quy chiếu và Hệ tọa độ quốc gia VN-2000 (Quyết định số 83/2000/QĐ-TTg)**:
     * Ellipsoid WGS-84: Bán trục lớn $a = 6378137\text{ m}$, độ dẹt $\alpha = 1/298.257223563$.
     * Lưới chiếu UTM / Transverse Mercator: Múi chiếu 3 độ ($k_0 = 0.9999$) cho đo đạc địa chính tỷ lệ lớn, hoặc múi 6 độ ($k_0 = 0.9996$) cho bản đồ địa hình tỷ lệ nhỏ.
     * Điểm gốc tọa độ quốc gia đặt tại Viện Khoa học Đo đạc và Bản đồ, Hà Nội.
     * Quy định kinh tuyến trục (Central Meridian) riêng cho từng tỉnh/thành phố (Hà Nội: $105^\circ$, TP.HCM: $105^\circ 45'$, Đà Nẵng: $107^\circ 45'$).
   - **Bảo vệ Chủ quyền lãnh thổ trên bản đồ (Điều 6)**:
     * Nghiêm cấm xuất bản, phát hành, lưu hành, truyền đưa sản phẩm đo đạc bản đồ không thể hiện hoặc thể hiện sai lệch địa giới hành chính, chủ quyền biên giới quốc gia, hai quần đảo Hoàng Sa và Trường Sa, hoặc có đường chín đoạn (đường lưỡi bò) phi pháp.
   - **Cấp Giấy phép hoạt động đo đạc và bản đồ (Điều 51, 52 & Nghị định 27/2019/NĐ-CP)**:
     * Người phụ trách kỹ thuật có bằng đại học chuyên ngành đo đạc bản đồ và kinh nghiệm $\ge 5$ năm.
     * Tối thiểu 02 nhân sự kỹ thuật có chứng chỉ hành nghề đo đạc bản đồ.
     * Thiết bị đo đạc (máy toàn đạc điện tử, máy định vị vệ tinh GNSS RTK hai tần số) có giấy kiểm định, hiệu chuẩn còn hiệu lực.
2. **Thông tư số 25/2014/TT-BTNMT & Thông tư số 09/2021/TT-BTNMT (Quy chuẩn Bản đồ Địa chính)**:
   - Quy định sai số trung phương vị trí điểm góc ranh thửa đất so với điểm khống chế đo vẽ:
     * Khu vực đô thị: Tỷ lệ 1:500 ($\le 0.07\text{ m}$), 1:1000 ($\le 0.10\text{ m}$), 1:2000 ($\le 0.20\text{ m}$).
     * Khu vực nông thôn: Tỷ lệ 1:1000 ($\le 0.15\text{ m}$), 1:2000 ($\le 0.30\text{ m}$), 1:5000 ($\le 0.70\text{ m}$).
3. **Nghị định số 18/2020/NĐ-CP & Nghị định số 04/2022/NĐ-CP**:
   - Phạt 30.000.000 - 50.000.000 VND và tịch thu tang vật, phương tiện, cấm lưu hành đối với hành vi xuất bản bản đồ vi phạm chủ quyền lãnh thổ biển đảo Việt Nam.
4. **Lưu trữ SQLite WAL**: Bảng `coordinate_conversions`, `map_sovereignty_audits`, `geodesy_licenses`, `cadastral_surveys` tại `.mekong/geodesy.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động đo đạc bản đồ, tọa độ VN-2000 và chủ quyền biển đảo
mekong geodesy

# Chuyển đổi và kiểm tra tọa độ trắc địa phẳng VN-2000 từ kinh vĩ độ WGS-84
mekong geodesy coord MOC-HN-001 --lat 21.028511 --lon 105.854444 --zone 3 --province "HÀ NỘI"

# Thẩm định tính toàn vẹn chủ quyền lãnh thổ biển đảo trên bản đồ (Điều 6 Luật Đo đạc và bản đồ)
mekong geodesy sovereignty "Bản đồ Địa lý Du lịch Việt Nam 2026" --publisher "Nhà xuất bản Bản đồ" --hoang-sa --truong-sa --no-nine-dash --type DIGITAL_WEB

# Thẩm tra điều kiện cấp Giấy phép hoạt động đo đạc và bản đồ (Điều 51, 52)
mekong geodesy license "Công ty CP Trắc địa Bản đồ Mekong Geo" --director "KS. Nguyễn Thành Long" --exp 6 --surveyors 3 --calibrated --scope CADASTRAL_AND_TOPOGRAPHIC

# Kiểm tra sai số đo đạc ranh thửa đất bản đồ địa chính theo Thông tư 25/2014/TT-BTNMT
mekong geodesy cadastral THUA-45-TO-12 --province "HÀ NỘI" --scale "1:500" --area URBAN --error 0.05

# Tra cứu danh mục điểm tọa độ, thẩm định bản đồ, giấy phép hoặc đo đạc địa chính
mekong geodesy list coordinates
mekong geodesy list sovereignty
mekong geodesy list licenses
mekong geodesy list surveys

# Telemetry dạng JSON cho hệ thống tự động
mekong geodesy status --json
```

---

## MCP Tools Integration

- `mekong_geodesy_coord`: Chuyển đổi và kiểm tra tọa độ trắc địa phẳng VN-2000 (Múi 3°/6°, kinh tuyến trục địa phương) theo Quyết định 83/2000/QĐ-TTg.
- `mekong_geodesy_sovereignty`: Thẩm định tính toàn vẹn chủ quyền biển đảo (Hoàng Sa, Trường Sa, loại trừ đường 9 đoạn phi pháp) trên bản đồ số/in.
- `mekong_geodesy_license`: Thẩm tra điều kiện cấp Giấy phép hoạt động đo đạc bản đồ theo Điều 51-52 Luật Đo đạc và bản đồ.
- `mekong_geodesy_cadastral`: Kiểm tra sai số đo đạc ranh thửa đất địa chính theo Thông tư 25/2014/TT-BTNMT.
- `mekong_geodesy_list`: Tra cứu danh mục hồ sơ tọa độ, thẩm định bản đồ, giấy phép hoặc đo đạc địa chính.
- `mekong_geodesy_status`: Báo cáo chỉ số telemetry tổng hợp hệ thống đo đạc bản đồ và GIS quốc gia.
