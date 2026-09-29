---
name: publishing
description: Vietnamese Publishing, Printing, Distribution & Legal Depository Suite.
---

# mekong publishing — Autonomous Vietnamese Publishing, Printing, Distribution & Legal Depository Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Xuất bản 2012 (Luật số 19/2012/QH13)** (sửa đổi, bổ sung):
   - Thống nhất quản lý nhà nước về hoạt động xuất bản, in ấn và phát hành xuất bản phẩm tại Việt Nam.
   - Thẩm quyền quản lý: **Bộ Thông tin và Truyền thông (Bộ TTTT)**, **Cục Xuất bản, In và Phát hành**.
   - Điều 10 (Nội dung và hành vi bị cấm trong hoạt động xuất bản): Tuyên truyền chống Nhà nước; xuyên tạc lịch sử, phủ nhận thành tựu cách mạng; kích động chiến tranh xâm lược, chia rẽ khối đại đoàn kết; tiết lộ bí mật nhà nước; tuyên truyền văn hóa phẩm đồi trụy; xuyên tạc chủ quyền lãnh thổ quốc gia.
   - Điều 22 (Điều kiện thành lập nhà xuất bản): Phải có vốn thành lập (vốn điều lệ) tối thiểu **5.000.000.000 VND**; diện tích trụ sở làm việc tối thiểu **200 m²**; có tổng giám đốc (giám đốc), tổng biên tập đủ tiêu chuẩn nghiệp vụ.
   - Điều 25 & 26 (Cấp mã số chuẩn quốc tế ISBN & Quyết định xuất bản): Tác phẩm xuất bản phải được cấp mã **ISBN-13** chuẩn quốc tế (tiền tố quốc gia 978-604 cho Việt Nam) có checksum EAN-13 hợp lệ, và Tổng giám đốc (Giám đốc) ký quyết định xuất bản trước khi đưa bản thảo vào in.
   - Điều 28 (Nộp lưu chiểu và nộp xuất bản phẩm cho Thư viện Quốc gia):
     * Xuất bản phẩm in hoặc điện tử phải được nộp lưu chiểu ít nhất **03 bản** cho cơ quan quản lý nhà nước về xuất bản (Bộ TTTT / Sở TTTT) và **02 bản** cho Thư viện Quốc gia Việt Nam.
     * **Thời hạn phong tỏa đọc thẩm định 10 ngày (Embargo)**: Xuất bản phẩm chỉ được phát hành ra công chúng sau **10 ngày** kể từ ngày nộp lưu chiểu đầy đủ theo quy định pháp luật.
2. **Nghị định số 195/2013/NĐ-CP & Nghị định số 119/2020/NĐ-CP (Điều kiện in ấn và xuất bản điện tử)**:
   - Cơ sở in xuất bản phẩm phải có Giấy phép hoạt động in, có Giấy chứng nhận đủ điều kiện an ninh, trật tự, công nghệ thiết bị in phù hợp và người đứng đầu có nghiệp vụ in.
   - Xuất bản phẩm điện tử: Phải có máy chủ đặt tại Việt Nam, giải pháp kỹ thuật DRM chống sao chép trái phép, sử dụng chữ ký số và tuân thủ định dạng lưu trữ tiêu chuẩn.
3. **Nghị định số 119/2020/NĐ-CP & Nghị định số 14/2022/NĐ-CP (Xử phạt vi phạm hành chính trong hoạt động xuất bản)**:
   - Xử phạt 10.000.000 - 20.000.000 VND đối với hành vi phát hành xuất bản phẩm khi chưa hết thời hạn 10 ngày đọc thẩm định lưu chiểu.
   - Xử phạt 30.000.000 - 50.000.000 VND đối với hành vi xuất bản tác phẩm không có mã ISBN hoặc phát hành xuất bản phẩm không có quyết định xuất bản.
   - Xử phạt 70.000.000 - 100.000.000 VND và tịch thu, tiêu hủy đối với xuất bản phẩm chứa nội dung cấm theo Điều 10 Luật Xuất bản.
4. **Lưu trữ SQLite WAL**: Bảng `publishers`, `isbn_allocations`, `legal_depositories`, `release_decisions`, `printing_facilities` tại `.mekong/publishing.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động xuất bản, in ấn, cấp ISBN và lưu chiểu sách
mekong publishing

# Đăng ký thành lập hoặc thẩm định điều kiện Nhà xuất bản (Luật Xuất bản Điều 22)
mekong publishing publisher "Nhà xuất bản Tri Thức Mới" --director "Nguyễn Văn An" --capital 6000000000 --area 250 --location "Hà Nội"

# Đăng ký và cấp mã số sách chuẩn quốc tế ISBN-13 (tiền tố 978-604)
mekong publishing isbn "Kỷ Nguyên Trí Tuệ Nhân Tạo" --publisher "Nhà xuất bản Tri Thức Mới" --author "Lê Minh Tuấn" --genre science --year 2026

# Đăng ký nộp lưu chiểu xuất bản phẩm (Điều 28: tối thiểu 3 bản nhà nước + 2 bản Thư viện Quốc gia)
mekong publishing deposit "PUB-NXBTTM-001" "978-604-0-12345-6" --state-copies 3 --library-copies 2

# Quyết định phát hành và kiểm toán thời hạn phong tỏa thẩm định 10 ngày (10-day reading embargo)
mekong publishing release "PUB-NXBTTM-001" "978-604-0-12345-6" --copies 5000 --price 185000 --days-since-deposit 12

# Kiểm tra phát hành vi phạm thời hạn phong tỏa (dưới 10 ngày)
mekong publishing release "PUB-NXBTTM-001" "978-604-0-12345-6" --copies 5000 --price 185000 --days-since-deposit 5

# Thẩm định điều kiện cấp phép cơ sở in ấn xuất bản phẩm (Nghị định 195/2013)
mekong publishing printing "Xí nghiệp In Quân Đội" --press-types "offset,digital" --security-clearance --certified-manager

# Tra cứu danh mục hồ sơ xuất bản
mekong publishing list publishers
mekong publishing list isbns
mekong publishing list deposits
mekong publishing list releases
```

---

## Integration Parity Matrix

| Workflow | CLI Command | MCP Tool | Pure-Python Engine Function |
|----------|-------------|----------|-----------------------------|
| Publisher Licensing | `mekong publishing publisher` | `mekong_publishing_license` | `PublishingEngine.register_publisher()` |
| ISBN-13 Allocation | `mekong publishing isbn` | `mekong_publishing_isbn` | `PublishingEngine.allocate_isbn()` |
| Legal Depository | `mekong publishing deposit` | `mekong_publishing_deposit` | `PublishingEngine.record_legal_depository()` |
| Release Embargo Audit | `mekong publishing release` | `mekong_publishing_release` | `PublishingEngine.audit_release_decision()` |
| Printing Facility Review | `mekong publishing printing` | `mekong_publishing_printing` | `PublishingEngine.review_printing_facility()` |
| Record Listing | `mekong publishing list` | `mekong_publishing_list` | `PublishingEngine.list_records()` |
| Dashboard Telemetry | `mekong publishing status` | `mekong_publishing_status` | `PublishingEngine.get_publishing_dashboard()` |
