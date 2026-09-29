---
name: standards
description: Vietnamese Technical Standards, Metrology, CR Mark & Product Quality Compliance Suite.
---

# mekong standards — Autonomous Vietnamese Technical Standards, Metrology, CR Mark & Product Quality Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Tiêu chuẩn và Quy chuẩn kỹ thuật 2006 (Luật số 68/2006/QH11)**:
   - Thống nhất quản lý hoạt động xây dựng, công bố và áp dụng tiêu chuẩn, quy chuẩn kỹ thuật trên toàn quốc.
   - Thẩm quyền quản lý: **Bộ Khoa học và Công nghệ (Bộ KH&CN)**, **Tổng cục Tiêu chuẩn Đo lường Chất lượng (STAMEQ)**.
   - Phân định rõ ràng:
     * **Tiêu chuẩn quốc gia (TCVN)**: Tự nguyện áp dụng (voluntary), trừ khi được viện dẫn bắt buộc trong quy chuẩn kỹ thuật.
     * **Quy chuẩn kỹ thuật quốc gia (QCVN)**: Bắt buộc áp dụng (mandatory) đối với sản phẩm, hàng hóa có nguy cơ gây hại sức khỏe, tính mạng con người, môi trường.
   - Hoạt động đánh giá sự phù hợp: Công bố hợp chuẩn (TCVN) và công bố hợp quy (QCVN).
2. **Luật Chất lượng sản phẩm, hàng hóa 2007 (Luật số 05/2007/QH12)**:
   - Phân loại sản phẩm thành 2 nhóm:
     * **Nhóm 1**: Không có khả năng gây mất an toàn (quản lý theo tiêu chuẩn cơ sở TCCS hoặc TCVN).
     * **Nhóm 2**: Có khả năng gây mất an toàn (phải chứng nhận hợp quy, công bố hợp quy và gắn **Dấu Hợp Quy CR** trước khi lưu thông trên thị trường).
   - Kiểm tra nhà nước về chất lượng hàng hóa nhập khẩu (State quality inspection for imported goods).
   - Truy xuất nguồn gốc và quy trình thu hồi, tiêu hủy sản phẩm khuyết tật không đạt chất lượng.
3. **Luật Đo lường 2011 (Luật số 04/2011/QH13)**:
   - Quản lý phương tiện đo nhóm 2: Các loại cân thương mại, cột đo xăng dầu, công tơ điện, đồng hồ nước, máy đo nồng độ cồn... sử dụng trong thương mại, thanh toán, an toàn.
   - Yêu cầu bắt buộc: Phải được phê duyệt mẫu, kiểm định ban đầu, kiểm định định kỳ, và tem niêm phong / kẹp chì kiểm định còn nguyên vẹn.
4. **Thông tư số 28/2012/TT-BKHCN & Thông tư số 02/2017/TT-BKHCN (Bộ KH&CN)**:
   - Quy định về công bố hợp chuẩn, công bố hợp quy và phương thức đánh giá sự phù hợp (Phương thức 1 đến 8).
   - Quy chuẩn dấu hợp quy CR: Chiều cao tối thiểu 5mm, kèm mã số tổ chức chứng nhận được chỉ định và số đăng ký bản công bố hợp quy.
5. **Nghị định số 119/2017/NĐ-CP & Nghị định số 126/2021/NĐ-CP**:
   - Xử phạt 15.000.000 - 30.000.000 VND đối với hành vi không dán dấu hợp quy CR hoặc dấu CR không đúng quy chuẩn.
   - Xử phạt 30.000.000 - 50.000.000 VND đối với hành vi đưa hàng hóa Nhóm 2 lưu thông mà chưa công bố hợp quy.
   - Phạt vi phạm gian lận đo lường hoặc sử dụng phương tiện đo hết hạn kiểm định / đứt chì niêm phong.
6. **Lưu trữ SQLite WAL**: Bảng `standards_catalog`, `conformity_declarations`, `cr_mark_verifications`, `measuring_instruments`, `quality_inspections` tại `.mekong/standards.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động tiêu chuẩn, quy chuẩn, dấu hợp quy CR và đo lường
mekong standards

# Tra cứu danh mục tiêu chuẩn quốc gia (TCVN) và quy chuẩn kỹ thuật (QCVN)
mekong standards lookup "an toàn điện" --type QCVN
mekong standards lookup "ISO 9001"

# Đăng ký bản công bố hợp chuẩn hoặc công bố hợp quy (Thông tư 28/2012/TT-BKHCN)
mekong standards declare "Nồi cơm điện tử" "QCVN 04:2009/BKHCN" --manufacturer "Công ty Mekong Home" --type HOP_QUY --report-no "TR-2026-088" --cert-body "QUATEST 3" --group-2

# Hậu kiểm tuân thủ quy chuẩn dán Dấu Hợp Quy CR trên sản phẩm hàng hóa Nhóm 2
mekong standards cr "Nồi cơm điện tử" --has-cr --height 6.0 --cert-code "VN01" --dec-code "DKHQ-2026-088" --group-2

# Kiểm tra phương tiện đo Nhóm 2 (cột đo xăng dầu, cân thương mại, công tơ điện)
mekong standards instrument "Cột đo xăng dầu Tatsuno" "SN-88992" --type FUEL_DISPENSER --last-date "2025-08-01" --validity-months 12 --seal

# Kiểm tra chất lượng nhà nước cho lô hàng nhập khẩu (Luật Chất lượng sản phẩm hàng hóa 2007)
mekong standards inspect "LOT-2026-IMPORT-01" "Thép cuộn xây dựng" --origin "Hàn Quốc" --sample 200 --defective 0

# Tra cứu danh mục hồ sơ
mekong standards list standards
mekong standards list declarations
mekong standards list cr_marks
mekong standards list instruments
mekong standards list inspections
```

---

## Integration Parity Matrix

| Workflow | CLI Command | MCP Tool | Pure-Python Engine Function |
|----------|-------------|----------|-----------------------------|
| Standards Lookup | `mekong standards lookup` | `mekong_standards_lookup` | `StandardsEngine.lookup_standard()` |
| Conformity Declaration | `mekong standards declare` | `mekong_standards_declare` | `StandardsEngine.register_conformity_declaration()` |
| CR Mark Audit | `mekong standards cr` | `mekong_standards_cr` | `StandardsEngine.verify_cr_marking()` |
| Metrology Verification | `mekong standards instrument` | `mekong_standards_instrument` | `StandardsEngine.audit_measuring_instrument()` |
| Quality Inspection | `mekong standards inspect` | `mekong_standards_inspect` | `StandardsEngine.record_quality_inspection()` |
| Record Listing | `mekong standards list` | `mekong_standards_list` | `StandardsEngine.list_records()` |
| Dashboard Telemetry | `mekong standards status` | `mekong_standards_status` | `StandardsEngine.get_status()` |
