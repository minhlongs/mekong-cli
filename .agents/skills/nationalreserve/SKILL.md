---
name: nationalreserve
description: Vietnamese National Reserves, Strategic Stockpiling & Emergency Relief Suite.
---

# mekong nationalreserve — Autonomous Vietnamese National Reserves & Relief Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Dự trữ quốc gia 2012 (Luật số 22/2012/QH13) & Nghị định số 94/2013/NĐ-CP**:
   - Quản lý nhà nước thống nhất đối với hệ thống kho, danh mục và nguồn lực dự trữ quốc gia (DTQG).
   - **Mục tiêu chiến lược (Điều 3)**:
     * Chủ động đáp ứng yêu cầu đột xuất, cấp bách về phòng, chống, khắc phục hậu quả thiên tai, thảm họa, dịch bệnh.
     * Cứu trợ, cứu đói dịp Tết Nguyên đán và kỳ giáp hạt.
     * Phục vụ quốc phòng, an ninh và tham gia bình ổn thị trường khi chỉ số giá tiêu dùng biến động mạnh.
   - **Danh mục 6 nhóm hàng DTQG thiết yếu (Điều 27)**:
     * `GRAIN_FOOD`: Lương thực chiến lược (Gạo tẻ 15% tấm, thóc bảo quản áp suất thấp).
     * `RESCUE_EQUIPMENT`: Vật tư, phương tiện cứu hộ, cứu nạn (Xuồng cao tốc DT4, bè cứu sinh tự thổi, máy bơm nước chữa cháy, nhà bạt cứu sinh).
     * `PETROLEUM_ENERGY`: Xăng dầu, nhiên liệu chuyên dùng quân sự và dân sinh.
     * `MEDICAL_SUPPLIES`: Hóa chất sát trùng, vắc-xin, thuốc phòng chống dịch bệnh nguy hiểm.
     * `AGRICULTURAL_SEEDS`: Hạt giống cây trồng, giống lúa thuần, ngô, rau, hóa chất khử trùng chuồng trại thú y.
     * `DEFENSE_SECURITY`: Khí tài, trang thiết bị đặc chủng của lực lượng vũ trang.
2. **Quy chuẩn kỹ thuật quốc gia (QCVN) & Thời hạn lưu kho bảo quản (Điều 34 & Điều 45)**:
   - Quy chuẩn bảo quản kín trong môi trường khí Nitơ nồng độ cao ($\ge 98\% \text{ N}_2$) hoặc CO2 để kéo dài thời hạn bảo quản hạt lương thực lên đến 24 tháng.
   - Bảo quản thông thường: kiểm định và xuất bán đổi hàng định kỳ 12 tháng một lần nhằm chống suy giảm phẩm chất hạt gạo.
   - Phân loại chất lượng kiểm định: `PASSED`, `WARNING`, `SUBSTANDARD`.
3. **Thẩm quyền và cơ chế xuất cấp cứu trợ khẩn cấp (Điều 35, 36, 37 & 38)**:
   - Thẩm quyền quyết định xuất cấp: Thủ tướng Chính phủ (`PRIME_MINISTER`) hoặc Bộ trưởng Bộ Tài chính (`MINISTER_OF_FINANCE`) được ủy quyền.
   - Cơ chế hoàn bù ngân sách nhà nước: Sau khi xuất cấp cứu trợ, ngân sách trung ương phải bố trí vốn để mua bù đủ số lượng hàng dự trữ quốc gia đã sử dụng.
4. **Lưu trữ SQLite WAL**: Bảng `reserve_warehouses`, `reserve_inventories`, `relief_allocations`, `rotation_plans` tại `~/.mekong/nationalreserve.db` (override qua `MEKONG_NATIONALRESERVE_DB`).

---

## CLI Invocations

```bash
# Báo cáo tổng quan kho tàng, tồn kho chiến lược, viện trợ cứu trợ và cảnh báo xoay vòng
mekong nationalreserve

# Đăng ký kho dự trữ quốc gia chuyên dụng
mekong nationalreserve warehouse --code "KHO-DT-HN01" --name "Kho Dự trữ Quốc gia Đông Anh" --region "NORTH" --unit "Cục Dự trữ Nhà nước khu vực Hà Nội" --storage-type "CONTROLLED_ATMOSPHERE_N2" --capacity 50000

# Nhập kho lô hàng dự trữ quốc gia (gạo tẻ)
mekong nationalreserve intake --code "DTQG-GAO-2026-01" --warehouse "KHO-DT-HN01" --category "GRAIN_FOOD" --name "Gạo tẻ dự trữ quốc gia 15% tấm" --quantity 10000 --unit "TAN" --date "2026-02-01" --months 18 --cost-vnd 14500000

# Cập nhật kết quả kiểm định chất lượng theo QCVN
mekong nationalreserve inspect --code "DTQG-GAO-2026-01" --status "PASSED"

# Xuất cấp cứu trợ khẩn cấp thiên tai bão lũ theo Quyết định của Thủ tướng Chính phủ
mekong nationalreserve relief --code "XUAT-CUUTRO-2026-QB01" --decision "QĐ 189/QĐ-TTg" --authority "PRIME_MINISTER" --purpose "DISASTER_RELIEF" --inventory "DTQG-GAO-2026-01" --locality "Tỉnh Quảng Bình" --quantity 2500 --date "2026-10-15"

# Lập kế hoạch xuất đổi hàng / xoay vòng dự trữ quốc gia
mekong nationalreserve rotate --code "XR-2026-GAO-01" --inventory "DTQG-GAO-2026-01" --year 2026 --type "AUCTION_SALE" --quantity 3000 --deadline "2026-12-31" --proceeds 42000000000 --budget 43500000000

# Nhập hàng bù đắp hoàn tất chu trình xoay vòng
mekong nationalreserve replenish --code "XR-2026-GAO-01" --quantity 3000 --cost-vnd 14500000

# Tra cứu dữ liệu quản lý dự trữ quốc gia
mekong nationalreserve list --type all --limit 20
mekong nationalreserve list --type warehouses
mekong nationalreserve list --type inventories
mekong nationalreserve list --type allocations
mekong nationalreserve list --type rotations

# Báo cáo telemetry chi tiết
mekong nationalreserve status --json
```

---

## MCP Tools Reference

- `mekong_nationalreserve_warehouse`: Register strategic storage depot with capacity and atmospheric storage specifications.
- `mekong_nationalreserve_intake`: Record commodity stock intake with automated preservation and rotation expiry calculation.
- `mekong_nationalreserve_inspect`: Update statutory technical quality inspection per QCVN standards.
- `mekong_nationalreserve_relief`: Execute emergency dispatch & disaster relief under Prime Minister decision.
- `mekong_nationalreserve_rotate`: Schedule statutory stock rotation to prevent commodity obsolescence.
- `mekong_nationalreserve_replenish`: Complete stock rotation cycle by intaking fresh replacement stock.
- `mekong_nationalreserve_list`: Query warehouses, reserve inventories, relief allocations, and rotation plans.
- `mekong_nationalreserve_status`: Telemetry metrics on national reserves, capacity utilization, and relief aid.
