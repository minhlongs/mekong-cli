---
name: taxadmin
description: Vietnamese Tax Administration, Electronic Invoices & Tax Audit Compliance Suite.
---

# mekong taxadmin — Autonomous Vietnamese Tax Administration & E-Invoicing Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Quản lý thuế 2019 (Luật số 38/2019/QH14) & Nghị định số 126/2020/NĐ-CP**:
   - Thống nhất quản lý thu thuế, phí, lệ phí và các khoản thu khác thuộc ngân sách nhà nước.
   - **Đăng ký thuế & Mã số thuế (MST) (Điều 30-35)**:
     * Cấu trúc MST 10 chữ số cho doanh nghiệp, tổ chức có tư cách pháp nhân.
     * Cấu trúc MST 13 chữ số cho chi nhánh, văn phòng đại diện, đơn vị phụ thuộc.
   - **Xác định nghĩa vụ thuế & Tiền chậm nộp (Điều 42-59)**:
     * Nguyên tắc tự khai, tự tính, tự nộp thuế và tự chịu trách nhiệm trước pháp luật.
     * Trường hợp cơ quan thuế ấn định số thuế phải nộp (Điều 50-52) khi NNT không đăng ký, không khai, không nộp sổ sách chứng từ hoặc có dấu hiệu gian lận.
     * Mức tính tiền chậm nộp: **0,03%/ngày** trên số tiền thuế chậm nộp (Điều 59).
   - **Cưỡng chế thi hành quyết định hành chính thuế (Điều 124-125)**:
     * 7 biện pháp cưỡng chế áp dụng tuần tự:
       1. Trích tiền từ tài khoản, phong tỏa tài khoản ngân hàng.
       2. Khấu trừ một phần tiền lương hoặc thu nhập.
       3. Dừng làm thủ tục hải quan đối với hàng hóa xuất nhập khẩu.
       4. Ngừng sử dụng hóa đơn (vô hiệu hóa hóa đơn điện tử).
       5. Kê biên tài sản, bán đấu giá tài sản kê biên.
       6. Thu tiền, tài sản từ bên thứ ba đang nắm giữ.
       7. Thu hồi giấy chứng nhận đăng ký kinh doanh/giấy phép thành lập.
     * Tạm hoãn xuất cảnh đối với cá nhân, người đại diện pháp luật của doanh nghiệp nợ thuế (Điều 66).
2. **Hóa đơn điện tử & Chứng từ điện tử (Nghị định số 123/2020/NĐ-CP & Thông tư số 78/2021/TT-BTC)**:
   - Triển khai toàn diện hóa đơn điện tử có mã của cơ quan thuế và không có mã của cơ quan thuế.
   - Hóa đơn điện tử khởi tạo từ máy tính tiền có kết nối chuyển dữ liệu điện tử với cơ quan thuế.
   - Xử lý hóa đơn điện tử có sai sót theo Điều 19: Thông báo theo Mẫu 04/SS-HĐĐT, lập hóa đơn điều chỉnh hoặc hóa đơn thay thế.
3. **Thanh tra, kiểm tra thuế & Xử phạt vi phạm hành chính (Nghị định 125/2020/NĐ-CP)**:
   - Kiểm tra thuế tại trụ sở cơ quan thuế và thanh tra thuế tại trụ sở người nộp thuế.
   - Mức xử phạt hành vi khai sai dẫn đến thiếu số thuế: **20%** số tiền thuế khai thiếu.
   - Mức xử phạt hành vi trốn thuế: Phạt từ **1 lần đến 3 lần** số tiền thuế trốn.
4. **Lưu trữ SQLite WAL**: Bảng `taxpayers`, `tax_assessments`, `electronic_invoices`, `tax_audits` tại `~/.mekong/taxadmin.db` (override qua `MEKONG_TAXADMIN_DB`).

---

## CLI Invocations

```bash
# Báo cáo tổng quan tình hình thu nộp ngân sách, phát hành HĐĐT và cưỡng chế thuế
mekong taxadmin

# Đăng ký thông tin người nộp thuế vào Hệ thống Đăng ký thuế quốc gia
mekong taxadmin taxpayer --code "0108999888" --name "Công ty Cổ phần Công nghệ Mekong AI" --rep "Nguyễn Văn A" --type "ENTERPRISE" --office "Cục Thuế TP. Hà Nội"

# Xác định nghĩa vụ thuế, tính tiền chậm nộp 0.03%/ngày và kiểm tra biện pháp cưỡng chế
mekong taxadmin assess --code "0108999888" --type "CIT" --period "2026-Q1" --declared 250000000 --due-date "2026-04-30" --paid 50000000

# Phát hành Hóa đơn điện tử có mã của cơ quan thuế (Nghị định 123/2020/NĐ-CP)
mekong taxadmin invoice --code "1C26TAA-0000001" --type "VAT_INVOICE" --seller "0108999888" --buyer-tax "0100109106" --buyer-name "Tập đoàn Viễn thông Quân đội" --amount 500000000 --vat-rate 10.0

# Xử lý hóa đơn điện tử sai sót (Điều 19 Nghị định 123/2020/NĐ-CP)
mekong taxadmin adjust "1C26TAA-0000001" --action "ADJUST" --new-code "1C26TAA-0000002" --diff 20000000 --reason "Điều chỉnh tăng do ghi thiếu khối lượng dịch vụ"

# Ghi nhận kết luận kiểm tra, thanh tra thuế và xử phạt vi phạm hành chính
mekong taxadmin audit --code "0108999888" --type "FIELD_EXAMINATION" --decision "QĐ-TT-2026-088" --year 2026 --underdeclared 120000000 --no-evasion --days 45 --reason "Hạch toán chi phí không có đầy đủ hóa đơn hợp lệ"

# Tra cứu dữ liệu quản lý thuế
mekong taxadmin list --type all --limit 20
mekong taxadmin list --type taxpayers
mekong taxadmin list --type assessments
mekong taxadmin list --type invoices
mekong taxadmin list --type audits

# Báo cáo trạng thái telemetry quản lý thuế
mekong taxadmin status --json
```

---

## MCP Tools Integration (Dual Parity)

- `mekong_taxadmin_taxpayer`: Đăng ký người nộp thuế vào hệ thống đăng ký thuế quốc gia.
- `mekong_taxadmin_assess`: Xác định nghĩa vụ thuế, tính tiền chậm nộp và biện pháp cưỡng chế.
- `mekong_taxadmin_invoice`: Phát hành hóa đơn điện tử có mã/không có mã CQT.
- `mekong_taxadmin_adjust`: Xử lý sai sót hóa đơn điện tử (Mẫu 04/SS-HĐĐT, điều chỉnh, thay thế).
- `mekong_taxadmin_audit`: Ghi nhận kết luận thanh tra, kiểm tra thuế và xử phạt hành chính.
- `mekong_taxadmin_list`: Tra cứu danh sách NNT, nghĩa vụ thuế, hóa đơn, kết luận thanh tra.
- `mekong_taxadmin_status`: Báo cáo chỉ số thu nộp ngân sách, phát hành HĐĐT và cưỡng chế thuế.
