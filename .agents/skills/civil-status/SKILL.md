---
name: civil-status
description: Vietnamese Civil Registration, Vital Statistics & Identification Registry Suite.
---

# /civil-status — Vietnamese Civil Registration, Vital Statistics & Identification Registry Suite

Hệ thống số hóa đăng ký hộ tịch, thống kê sinh tử và quản lý căn cước công dân quốc gia theo Luật Hộ tịch 2014, Luật Hôn nhân và gia đình 2014, Luật Căn cước 2023 (Luật số 26/2023/QH15) và Đề án 06/CP (VNeID mức 2).

## Căn cứ Pháp lý & Khung Quy chuẩn

1. **Luật Hộ tịch 2014** (Luật số 60/2014/QH13): Đăng ký khai sinh, kết hôn, khai tử, giám hộ, nhận cha mẹ con và cấp số định danh cá nhân khi khai sinh.
2. **Nghị định số 123/2015/NĐ-CP**: Hướng dẫn thi hành một số điều của Luật Hộ tịch.
3. **Thông tư số 04/2020/TT-BTP**: Quy định chi tiết thi hành Luật Hộ tịch và Nghị định 123/2015/NĐ-CP.
4. **Luật Hôn nhân và gia đình 2014** (Luật số 52/2014/QH13 - Điều kiện kết hôn Điều 8).
5. **Luật Căn cước 2023** (Luật số 26/2023/QH15 thay thế Luật Căn cước công dân 2014): Thẻ Căn cước gắn chip, sinh trắc học mống mắt, vân tay, khuôn mặt và định danh điện tử VNeID Mức 2.
6. **Nghị định số 70/2024/NĐ-CP**: Quy định chi tiết một số điều và biện pháp thi hành Luật Căn cước.

---

## Tính năng Nghiệp vụ Cốt lõi

### 1. Đăng ký Khai sinh & Cấp Số Định danh Cá nhân (Điều 13–16 Luật Hộ tịch)
- Tiếp nhận đăng ký khai sinh trong thời hạn luật định 60 ngày.
- Tự động sinh **Số định danh cá nhân (12 chữ số)** chuẩn quốc gia:
  - 3 số đầu: Mã tỉnh, thành phố trực thuộc trung ương hoặc mã quốc gia.
  - 1 số tiếp theo: Mã thế kỷ và giới tính (Thế kỷ 20: Nam 0, Nữ 1; Thế kỷ 21: Nam 2, Nữ 3).
  - 2 số tiếp theo: Hai số cuối của năm sinh.
  - 6 số cuối: Số ngẫu nhiên duy nhất trong kho dữ liệu dân cư.
- Cấp Giấy khai sinh bản chính và đồng bộ CSDL Dân cư.

### 2. Đăng ký Kết hôn & Thẩm định Hôn nhân Hợp pháp (Điều 17–18 Luật Hộ tịch & Điều 8 Luật HN&GĐ)
- Thẩm định độ tuổi kết hôn hợp pháp: Nam từ đủ 20 tuổi trở lên, Nữ từ đủ 18 tuổi trở lên.
- Kiểm tra Giấy xác nhận tình trạng hôn nhân (chứng minh độc thân hợp pháp) và nguyên tắc tự nguyện hoàn toàn.
- Cấp Giấy chứng nhận kết hôn chính thức.

### 3. Đăng ký Khai tử & Khóa Dữ liệu Dân cư (Điều 32–34 Luật Hộ tịch)
- Tiếp nhận khai tử trong thời hạn 15 ngày kể từ ngày người chết qua đời.
- Thẩm tra Giấy báo tử của cơ sở khám bệnh, chữa bệnh hoặc văn bản của cơ quan công an / chính quyền.
- Khóa trạng thái công dân trên Cơ sở dữ liệu quốc gia về dân cư.

### 4. Cấp Thẻ Căn cước & Kích hoạt VNeID Mức 2 (Luật Căn cước 2023)
- Thu nhận bắt buộc sinh trắc học: mống mắt (iris), vân tay 10 ngón và ảnh khuôn mặt kỹ thuật số đối với công dân từ đủ 14 tuổi.
- Tính toán chính xác thời hạn thẻ Căn cước theo các mốc tuổi luật định (25, 40, 60 tuổi; trên 60 tuổi có giá trị vĩnh viễn theo Điều 21).
- Kích hoạt tài khoản định danh điện tử VNeID Mức 2.

### 5. Cấp Bản sao Trích lục Hộ tịch Điện tử (Điều 63 Luật Hộ tịch)
- Cấp bản sao trích lục khai sinh, kết hôn, khai tử từ sổ bộ hộ tịch điện tử toàn quốc.

---

## Hướng dẫn Sử dụng CLI (`mekong civil-status`)

```bash
# Xem báo cáo tổng quan telemetry hộ tịch và căn cước quốc gia
mekong civil-status

# Đăng ký khai sinh và cấp số định danh cá nhân 12 số
mekong civil-status birth "Trần Bảo An" --dob "2026-09-01" --gender "NAM" --mother "Nguyễn Thị Mai" --father "Trần Văn Hùng" --province "Hà Nội" --place "Bệnh viện Phụ sản Hà Nội" --notice

# Đăng ký kết hôn
mekong civil-status marriage "Lê Hoàng Long" "Phạm Quỳnh Anh" --groom-dob "1998-05-15" --groom-pid "001098012345" --bride-dob "2000-08-20" --bride-pid "001100067890" --single-cert --consent

# Đăng ký khai tử
mekong civil-status death "Nguyễn Văn Hưởng" --pid "001050012345" --dod "2026-09-20" --cause "Bệnh lý tự nhiên" --place "Bệnh viện Bạch Mai" --notice

# Cấp thẻ Căn cước gắn chip và VNeID Mức 2
mekong civil-status identity "Nguyễn Minh Khang" --pid "001098055667" --dob "1998-10-12" --gender "NAM" --iris --fingerprint --face

# Cấp bản sao trích lục hộ tịch
mekong civil-status extract BIRTH "CS-BRT-A1B2C3D4" --applicant "Trần Văn Hùng" --purpose "Bổ sung hồ sơ nhập học"

# Tra cứu danh mục hồ sơ hộ tịch
mekong civil-status list --category ALL --limit 50

# Xem trạng thái hệ thống dạng JSON
mekong civil-status status --json
```

---

## Native MCP Tools

Bộ công cụ MCP Hộ tịch & Căn cước công dân quốc gia (FastMCP & JSON-RPC 2.0 stdio):

- `mekong_civil_status_birth`: Đăng ký khai sinh và cấp số định danh cá nhân 12 số.
- `mekong_civil_status_marriage`: Đăng ký kết hôn và cấp Giấy chứng nhận kết hôn.
- `mekong_civil_status_death`: Đăng ký khai tử và khóa dữ liệu công dân trên CSDL dân cư.
- `mekong_civil_status_identity`: Thẩm định cấp Thẻ Căn cước chip và VNeID Mức 2 (Luật Căn cước 2023).
- `mekong_civil_status_extract`: Cấp bản sao trích lục hộ tịch điện tử (Điều 63 Luật Hộ tịch).
- `mekong_civil_status_list`: Tra cứu danh sách đăng ký khai sinh, kết hôn, khai tử, căn cước và trích lục.
- `mekong_civil_status_status`: Tổng hợp chỉ số thống kê sinh tử, tăng tự nhiên dân số và thẻ căn cước.
