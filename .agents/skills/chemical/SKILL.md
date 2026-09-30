---
name: chemical
description: Vietnamese Chemical Safety, Dangerous Goods & Industrial Explosives Suite.
---

# mekong chemical — Autonomous Vietnamese Chemical Safety, Dangerous Goods & Industrial Explosives Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Hóa chất 2007 (Luật số 06/2007/QH12)**:
   - Thống nhất quản lý hoạt động hóa chất, an toàn trong sản xuất, kinh doanh, sử dụng, bảo quản và vận chuyển hóa chất.
   - Thẩm quyền quản lý nhà nước: **Bộ Công Thương (Cục Hóa chất)**, Bộ Công an, Bộ Y tế, Bộ Giao thông Vận tải.
   - Phân loại danh mục hóa chất:
     * Hóa chất sản xuất, kinh doanh có điều kiện (Phụ lục I).
     * Hóa chất hạn chế sản xuất, kinh doanh (Phụ lục II) - Cần Giấy phép của Bộ Công Thương.
     * Hóa chất cấm (Phụ lục III).
     * Hóa chất phải khai báo (Phụ lục V) - Khai báo điện tử qua Cổng thông tin một cửa quốc gia (`vnsw.gov.vn`).
     * Hóa chất phải xây dựng Kế hoạch / Biện pháp phòng ngừa, ứng phó sự cố hóa chất (Phụ lục IV).
   - Phiếu an toàn hóa chất (MSDS / SDS) 16 mục bắt buộc theo chuẩn GHS (Globally Harmonized System).
2. **Nghị định số 113/2017/NĐ-CP & Nghị định số 82/2022/NĐ-CP**:
   - Quy chuẩn kỹ thuật quốc gia về an toàn trong sản xuất, kinh doanh, sử dụng, bảo quản và vận chuyển hóa chất nguy hiểm.
   - **Quy chuẩn kho bãi và bồn bể lưu chứa (TCVN 5507)**:
     * Đê bao chống tràn (bunding): Thể tích đê bao phải đạt tối thiểu $110\%$ thể tích của bồn bể lớn nhất trong đê.
     * Vòi tắm và thiết bị rửa mắt khẩn cấp: Bố trí cách vị trí thao tác nguy hiểm không quá $10\text{ m}$.
     * Hệ thống thông gió phòng nổ tự động và hệ thống tiếp địa tiêu tán tĩnh điện bắt buộc.
   - Khai báo hóa chất nhập khẩu: Khai báo qua Cổng một cửa quốc gia trước khi thông quan, phản hồi tự động cấp mã tiếp nhận hồ sơ NSW.
3. **Nghị định số 34/2024/NĐ-CP & Thỏa thuận vận tải hàng nguy hiểm quốc tế ADR**:
   - Quy định danh mục hàng nguy hiểm, vận chuyển hàng nguy hiểm bằng phương tiện giao thông cơ giới đường bộ.
   - Phân loại 9 nhóm hàng nguy hiểm (Loại 1: Chất nổ; Loại 2: Khí; Loại 3: Chất lỏng dễ cháy; Loại 4: Chất rắn dễ cháy; Loại 5: Chất oxy hóa; Loại 6: Chất độc; Loại 7: Chất phóng xạ; Loại 8: Chất ăn mòn; Loại 9: Hàng nguy hiểm khác).
   - Điều kiện lưu hành: Bắt buộc có Giấy phép vận chuyển hàng nguy hiểm, trang bị đủ bình chữa cháy chuyên dụng, lái xe và người áp tải có Chứng chỉ huấn luyện an toàn vận chuyển hàng nguy hiểm.
4. **Nghị định số 71/2019/NĐ-CP & Nghị định số 17/2022/NĐ-CP**:
   - Xử phạt vi phạm hành chính trong lĩnh vực hóa chất:
     * Vi phạm không khai báo hóa chất nhập khẩu: Phạt tiền 20.000.000 - 30.000.000 VND.
     * Vi phạm kho chứa không có đê bao hoặc không đủ khoảng cách an toàn: Phạt 40.000.000 - 60.000.000 VND.
     * Vận chuyển hàng nguy hiểm không có Giấy phép: Phạt 20.000.000 - 40.000.000 VND (Nghị định 100/2019 & NĐ 123/2021).
5. **Lưu trữ SQLite WAL**: Bảng `chemical_classifications`, `storage_safety_audits`, `import_declarations`, `transport_audits` tại `.mekong/chemical.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động an toàn hóa chất, kho bãi và vận chuyển hàng nguy hiểm
mekong chemical

# Tra cứu và phân loại hóa chất theo Nghị định 113/2017 & 82/2022 và GHS
mekong chemical classify "7664-93-9"
mekong chemical classify "Axit nitric"
mekong chemical classify "NH4NO3"

# Hậu kiểm an toàn bồn bể, kho bãi hóa chất theo TCVN 5507
mekong chemical storage "Kho Hóa chất Mekong Đình Vũ" --chemical "Axit sulfuric" --volume 60000 --bund 115.0 --shower 8.0 --vent --ground

# Khai báo hóa chất nhập khẩu qua Cổng Một cửa Quốc gia (vnsw.gov.vn)
mekong chemical declare "Công ty TNHH Hóa chất Công nghiệp Mekong" --cas "7664-93-9" --qty 12000 --origin "Japan" --gate "Cảng Hải Phòng"

# Thẩm tra điều kiện vận chuyển hàng nguy hiểm đường bộ theo Nghị định 34/2024/NĐ-CP
mekong chemical transport "Đoàn xe Bồn Mekong Logistics" --un "UN 1830" --class 8 --weight 15000 --license --fire-ext --driver-cert

# Tra cứu danh mục hồ sơ an toàn hóa chất
mekong chemical list all
mekong chemical list classifications
mekong chemical list audits
mekong chemical list declarations
mekong chemical list transports

# Báo cáo telemetry an toàn hóa chất dạng JSON
mekong chemical status --json
```

---

## MCP Tools Integration

| Tool Name | Parameters | Description |
|-----------|------------|-------------|
| `mekong_chemical_classify` | `query: str` | Tra cứu, phân loại hóa chất theo Nghị định 113/2017/NĐ-CP, Nghị định 82/2022/NĐ-CP và GHS |
| `mekong_chemical_storage` | `facility_name, chemical_name, volume_liters, bund_capacity_pct, shower_distance_m, has_explosion_proof_ventilation, has_grounding_system` | Hậu kiểm an toàn kho bãi hóa chất theo TCVN 5507 và Nghị định 113/2017 |
| `mekong_chemical_declare` | `importer_name, cas_number, quantity_kg, country_of_origin, border_gate` | Khai báo hóa chất nhập khẩu điện tử qua Cổng Một cửa Quốc gia (vnsw.gov.vn) |
| `mekong_chemical_transport` | `carrier_name, un_number, hazard_class_key, gross_weight_kg, has_dangerous_goods_license, has_fire_extinguishers, driver_hazmat_certified` | Thẩm tra điều kiện vận chuyển hàng nguy hiểm đường bộ theo Nghị định 34/2024/NĐ-CP |
| `mekong_chemical_list` | `category: str = 'all', limit: int = 50` | Tra cứu danh mục hồ sơ an toàn hóa chất, kho chứa, khai báo nhập khẩu và vận chuyển hàng nguy hiểm |
| `mekong_chemical_status` | *(none)* | Báo cáo chỉ số telemetry tổng hợp hệ thống an toàn hóa chất và vận chuyển hàng nguy hiểm |
