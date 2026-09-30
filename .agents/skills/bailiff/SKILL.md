---
name: bailiff
description: Vietnamese Bailiff, Evidence Protocol (Vi Bằng) & Civil Enforcement Suite.
---

# /bailiff — Vietnamese Bailiff, Evidence Protocol (Vi Bằng) & Civil Enforcement Suite

Hệ thống Thừa phát lại chuyên nghiệp, lập Vi bằng ghi nhận chứng cứ trực tiếp, tống đạt văn bản tố tụng của Tòa án/VKS/THADS, xác minh điều kiện thi hành án và trực tiếp tổ chức thi hành án dân sự theo Nghị định số 08/2020/NĐ-CP và Luật Thi hành án dân sự 2014.

## Căn cứ Pháp lý & Khung Quy chuẩn

1. **Nghị định số 08/2020/NĐ-CP** ngày 08/01/2020 của Chính phủ về tổ chức và hoạt động của Thừa phát lại:
   - Thẩm quyền lập Vi bằng (Điều 36-41).
   - Các trường hợp cấm lập Vi bằng (Điều 37).
   - Tống đạt văn bản của Tòa án, Viện kiểm sát nhân dân, cơ quan thi hành án dân sự (Điều 32-35).
   - Xác minh điều kiện thi hành án (Điều 43-50).
   - Trực tiếp tổ chức thi hành bản án, quyết định theo yêu cầu của đương sự (Điều 51-56).
2. **Thông tư số 05/2020/TT-BTP** của Bộ Tư pháp quy định chi tiết thi hành Nghị định 08/2020/NĐ-CP.
3. **Luật Thi hành án dân sự 2008** (sửa đổi, bổ sung 2014, Luật số 64/2014/QH13).
4. **Bộ luật Tố tụng dân sự 2015**: Giá trị chứng cứ của Vi bằng (Điều 95) và quy định về tống đạt văn bản tố tụng (Chương X).

---

## Tính năng Nghiệp vụ Cốt lõi

### 1. Lập Vi Bằng Chứng Cứ Trực Tiếp (Điều 36–41 Nghị định 08/2020/NĐ-CP)
- Ghi nhận sự kiện, hành vi có thật theo yêu cầu:
  - Hiện trạng nhà đất, ranh giới quyền sử dụng đất, hiện trạng công trình xây dựng trước khi thi công.
  - Giao nhận tiền, giao nhận tài sản, bàn giao mặt bằng nhà xưởng.
  - Hành vi xâm phạm quyền tác giả, nhãn hiệu, sở hữu trí tuệ trên môi trường mạng internet/mạng xã hội.
  - Phân chia di sản thừa kế, giao nhận di chúc.
  - Vi phạm hợp đồng kinh tế, chậm tiến độ, không thực hiện nghĩa vụ cam kết.
- Tự động thẩm tra các trường hợp cấm theo Điều 37 (không thay thế công chứng mua bán đất không có sổ đỏ, không xâm phạm bí mật đời tư).
- Kiểm tra thủ tục đăng ký Sở Tư pháp trong thời hạn luật định 03 ngày làm việc (Điều 39 khoản 4).

### 2. Tống Đạt Văn Bản Tố Tụng (Điều 32–35)
- Nhận ủy thác tống đạt từ Tòa án nhân dân, Viện kiểm sát nhân dân và Cơ quan Thi hành án dân sự.
- Các phương thức tống đạt: Tống đạt trực tiếp có ký nhận, niêm yết công khai (khi đương sự vắng mặt), tống đạt qua chính quyền/tổ dân phố.

### 3. Xác Minh Điều Kiện Thi Hành Án (Điều 43–50)
- Xác minh tài sản của người phải thi hành án:
  - Truy vấn tài khoản và số dư tại các ngân hàng thương mại.
  - Xác minh quyền sử dụng đất, quyền sở hữu nhà ở tại Văn phòng đăng ký đất đai.
  - Xác minh phương tiện cơ giới (ô tô, xe máy) tại cơ quan đăng ký xe.
- Kết luận chính thức về việc đương sự có điều kiện thi hành án hay chưa có điều kiện thi hành án.

### 4. Trực Tiếp Tổ Chức Thi Hành Án Dân Sự (Điều 51–56)
- Thừa phát lại trực tiếp ra quyết định thi hành án, đôn đốc tự nguyện chấp hành trong thời hạn 10 ngày.
- Lập kế hoạch cưỡng chế kê biên, phong tỏa tài khoản, khấu trừ thu nhập (phối hợp lực lượng công an nhân dân khi cần thiết).

---

## Hướng dẫn Sử dụng CLI (`mekong bailiff`)

```bash
# Xem báo cáo tổng quan telemetry hoạt động Thừa phát lại toàn quốc
mekong bailiff

# Lập Vi bằng ghi nhận hiện trạng nhà đất liền kề
mekong bailiff protocol "Công ty CP Đầu tư Xây dựng Hà Nội" --desc "Ghi nhận hiện trạng nứt tường công trình liền kề trước khi đào móng" --category PROPERTY_STATUS --location "Số 20 Phố Huế, Hoàn Kiếm, Hà Nội" --media 8 --doj-reg

# Lập Vi bằng ghi nhận vi phạm nhãn hiệu trên mạng xã hội
mekong bailiff protocol "Tập đoàn Thời trang Sun" --desc "Ghi nhận bài đăng bán hàng giả mạo nhãn hiệu Sun trên Facebook và TikTok" --category INTERNET_IP_INFRINGEMENT --media 12 --doj-reg

# Tống đạt văn bản tố tụng của Tòa án
mekong bailiff serve "Nguyễn Văn Tuấn" --doc "Quyết định đưa vụ án ra xét xử" --agency "TAND Quận Ba Đình" --address "Số 8 Đội Cấn, Ba Đình, Hà Nội" --method DIRECT_DELIVERY --fee 150000

# Xác minh điều kiện thi hành án của người phải thi hành án
mekong bailiff verify "Công ty TNHH Thương mại Minh Phát" --judgment "Bản án số 15/2026/KDTM-ST" --accounts 3 --balance 450000000 --real-estate 1 --vehicles 2

# Trực tiếp tổ chức thi hành án dân sự
mekong bailiff enforce "Trần Đình Hùng" --amount 800000000 --judgment "Quyết định số 05/2026/QĐST-DS" --collected 250000000 --voluntary

# Tra cứu danh mục hồ sơ Thừa phát lại
mekong bailiff list --category ALL --limit 50

# Xem trạng thái hệ thống dạng JSON
mekong bailiff status --json
```

---

## Native MCP Tools

Bộ công cụ MCP Thừa phát lại quốc gia (FastMCP & JSON-RPC 2.0 stdio):

- `mekong_bailiff_protocol`: Lập và đăng ký Vi bằng chứng cứ theo Nghị định 08/2020/NĐ-CP.
- `mekong_bailiff_serve`: Tống đạt văn bản tố tụng của Tòa án, VKS, cơ quan THADS.
- `mekong_bailiff_verify`: Xác minh tài sản và điều kiện thi hành án của đương sự.
- `mekong_bailiff_enforce`: Tổ chức thi hành bản án, quyết định dân sự.
- `mekong_bailiff_list`: Tra cứu danh sách Vi bằng, hồ sơ tống đạt, xác minh và thi hành án.
- `mekong_bailiff_status`: Tổng hợp chỉ số telemetry Vi bằng, tống đạt và thu hồi tiền thi hành án.
