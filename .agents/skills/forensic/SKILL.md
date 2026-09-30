---
name: forensic
description: Vietnamese Judicial Expertise, Forensic Assessment & Electronic Evidence Suite.
---

# /forensic — Vietnamese Judicial Expertise, Forensic Assessment & Electronic Evidence Suite

Quản lý và thực hiện hoạt động giám định tư pháp theo Luật Giám định tư pháp 2012 (sửa đổi 2020), thẩm tra tiêu chuẩn giám định viên tư pháp theo Điều 7, tiếp nhận quyết định trưng cầu giám định của Tòa án/VKS/CQĐT theo Điều 25-26, lập Kết luận giám định tư pháp hợp chuẩn Điều 32 gắn với chế tài hình sự Điều 382 BLHS, và bảo toàn tính toàn vẹn chuỗi chứng cứ kỹ thuật số (Chain of Custody) theo Điều 99, 107 BLTTHS 2015.

## Căn cứ Pháp lý & Khung Quy chuẩn

1. **Luật Giám định tư pháp 2012 (sửa đổi, bổ sung 2020, Luật số 56/2020/QH14)**.
2. **Nghị định số 157/2020/NĐ-CP & Nghị định số 85/2013/NĐ-CP** quy định chi tiết và biện pháp thi hành Luật Giám định tư pháp.
3. **Bộ luật Tố tụng hình sự 2015**:
   - Điều 87: Kết luận giám định là nguồn chứng cứ pháp lý.
   - Điều 99, 107: Thu thập, bảo quản dữ liệu điện tử, phương tiện điện tử và niêm phong vật chứng.
   - Điều 205–214: Trưng cầu giám định, quyền và nghĩa vụ của người giám định.
4. **Bộ luật Tố tụng dân sự 2015 (Điều 102)**: Trưng cầu giám định, yêu cầu giám định của đương sự.
5. **Bộ luật Hình sự 2015 (Điều 382)**: Tội cung cấp tài liệu sai sự thật hoặc khai báo gian dối trong tố tụng tư pháp.
6. **Pháp lệnh số 02/2012/UBTVQH13**: Chi phí giám định, định giá tài sản trong tố tụng.

---

## Tính năng Nghiệp vụ Cốt lõi

### 1. Quản lý Hồ sơ Giám định viên Tư pháp (Điều 7 & 18)
- Thẩm tra điều kiện bổ nhiệm Giám định viên tư pháp: bằng đại học trở lên, tối thiểu 05 năm kinh nghiệm thực tế trong lĩnh vực chuyên môn (Khoản 1 Điều 7).
- Hỗ trợ 5 lĩnh vực trọng điểm:
  - `FINANCIAL_ACCOUNTING`: Tài chính - kế toán, thuế, sai phạm tài chính.
  - `DIGITAL_EVIDENCE`: Kỹ thuật số, dữ liệu điện tử, mã độc, viễn thông.
  - `CONSTRUCTION_QUALITY`: Chất lượng công trình, sự cố xây dựng, tổng mức đầu tư.
  - `INTELLECTUAL_PROPERTY`: Sở hữu trí tuệ, sao chép mã nguồn, nhãn hiệu, sáng chế.
  - `DOCUMENT_SIGNATURE`: Kỹ thuật hình sự tài liệu, chữ ký, con dấu, giả mạo.

### 2. Tiếp nhận Trưng cầu Giám định Tư pháp (Điều 25–26)
- Tiếp nhận Quyết định trưng cầu giám định của cơ quan tiến hành tố tụng hoặc Đơn yêu cầu giám định của đương sự.
- Ước tính chi phí và tạm ứng chi phí giám định theo Pháp lệnh 02/2012/UBTVQH13.

### 3. Ban hành Kết luận Giám định Tư pháp (Điều 32)
- Soạn thảo bản Kết luận giám định tư pháp chuẩn hóa với phương pháp khoa học kỹ thuật, thiết bị kiểm định và kết luận chuyên môn.
- Kiểm tra cam đoan chịu trách nhiệm hình sự về tính trung thực theo Điều 382 BLHS 2015.
- Kiểm tra nghiêm ngặt nguy cơ xung đột lợi ích theo Điều 34 Luật Giám định tư pháp.

### 4. Bảo toàn Chuỗi Chứng cứ Điện tử (Chain of Custody)
- Quản lý quá trình trích xuất và bảo toàn dữ liệu nhị phân nguyên gốc (Bit-stream image) với mã băm mật mã SHA-256.
- Thẩm tra việc sử dụng thiết bị chống ghi chuyên dụng (Hardware Write-Blocker) và tối thiểu 02 người chứng kiến theo Điều 107 BLTTHS 2015.

### 5. National Forensic Telemetry & Status
- Báo cáo tổng thể số lượng giám định viên, quyết định trưng cầu, tỷ lệ kết luận hợp chuẩn và số lượng vật chứng điện tử bảo toàn.

---

## Hướng dẫn Sử dụng CLI (`mekong forensic`)

```bash
# Xem báo cáo tổng quan telemetry giám định tư pháp toàn quốc
mekong forensic

# Đăng ký và thẩm tra hồ sơ Giám định viên tư pháp
mekong forensic expert "KS. Nguyễn Thế Vinh" --domain "DIGITAL_EVIDENCE" --degree "Kỹ sư An toàn Thông tin" --exp 8 --card "GĐTP-09/2024/BTP"

# Tiếp nhận quyết định trưng cầu giám định
mekong forensic solicit "TAND TP Hà Nội" "Vụ án số 12/2026/HS-ST" --target "Giám định mã độc tống tiền Ransomware trên máy chủ" --domain "DIGITAL_EVIDENCE" --value 5000000000

# Ban hành Kết luận giám định tư pháp chuẩn hóa Điều 32
mekong forensic conclude "REQ-99AA12BB" "JEX-11CC22DD" --method "Phân tích tĩnh và động phần mềm" --verdict "Phát hiện mã độc khai thác lỗ hổng Zero-day gây thất thoát dữ liệu" --sworn

# Xác lập chuỗi bảo toàn chứng cứ kỹ thuật số (Chain of Custody)
mekong forensic custody "Ổ cứng máy chủ dữ liệu Seagate Exos 16TB SN: WZX1928" --device "Máy chủ Dell R750" --data "Raw forensic image payload hash" --write-blocker --witnesses 2

# Tra cứu hồ sơ giám định tư pháp
mekong forensic list --category ALL --limit 50 --json

# Xem telemetry hệ thống
mekong forensic status --json
```

---

## Công cụ Native MCP

- `mekong_forensic_expert`: Đăng ký và thẩm tra Giám định viên tư pháp theo Điều 7 Luật GĐTP.
- `mekong_forensic_solicit`: Tiếp nhận trưng cầu giám định tư pháp và tính phí theo Điều 25-26.
- `mekong_forensic_conclude`: Ban hành Kết luận giám định tư pháp chuẩn hóa Điều 32 & Điều 382 BLHS.
- `mekong_forensic_custody`: Thẩm tra chuỗi bảo quản chứng cứ kỹ thuật số theo Điều 99, 107 BLTTHS 2015.
- `mekong_forensic_list`: Tra cứu danh mục giám định viên, trưng cầu, bản kết luận và chuỗi vật chứng.
- `mekong_forensic_status`: Báo cáo chỉ số telemetry hoạt động giám định tư pháp toàn quốc.
