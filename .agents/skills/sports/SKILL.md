---
name: sports
description: Vietnamese Physical Training, Sports, Professional Athletics & Anti-Doping Suite.
---

# /sports — Vietnamese Physical Training, Sports & Anti-Doping Suite

Quản lý và giám sát tuân thủ hoạt động thể dục thể thao, hợp đồng lao động và chuyển nhượng vận động viên (VĐV) chuyên nghiệp, kiểm tra phòng chống Doping theo Bộ luật WADA 2021 và cấp phép cơ sở kinh doanh thể thao mạo hiểm theo Luật Thể dục, thể thao 2006 (sửa đổi, bổ sung 2018).

## Căn cứ Pháp lý & Khung Quy chuẩn

1. **Luật Thể dục, thể thao 2006** (sửa đổi, bổ sung 2018 số 26/2018/QH14).
2. **Nghị định số 36/2019/NĐ-CP** quy định chi tiết thi hành một số điều của Luật Thể dục, thể thao.
3. **Thông tư số 17/2019/TT-BVHTTDL** của Bộ Văn hóa, Thể thao và Du lịch quy định về kiểm tra phòng, chống Doping trong hoạt động thể thao.
4. **Thông tư số 04/2019/TT-BVHTTDL** ban hành danh mục hoạt động thể thao bắt buộc có người hướng dẫn tập luyện và hoạt động thể thao mạo hiểm.
5. **WADA World Anti-Doping Code 2021** & Quy định của Trung tâm Doping và Y học Thể thao Việt Nam (VADC).

---

## Tính năng Nghiệp vụ Cốt lõi

### 1. Hợp đồng Lao động & Chuyển nhượng VĐV Chuyên nghiệp (Điều 32 & 33)
- Hợp đồng lao động VĐV chuyên nghiệp bằng văn bản, thời hạn tối thiểu 06 tháng.
- Mức lương không thấp hơn mức lương tối thiểu vùng, bảo hiểm tai nạn lao động, bệnh nghề nghiệp và BHYT bắt buộc (khoản 2 Điều 32).
- Thỏa thuận chuyển nhượng VĐV ba bên (CLB cũ, CLB mới, VĐV) và hoàn trả chi phí đào tạo hợp lệ (Điều 33).

### 2. Kiểm tra Doping & Chế tài Xử phạt WADA Code (Thông tư 17/2019/TT-BVHTTDL)
- Phân loại danh mục chất cấm WADA 2021 (S0–S9, M1–M3):
  * Chất không đặc biệt (S1, S2, M1, M2, M3): Đình chỉ thi đấu tiêu chuẩn 48 tháng (4 năm).
  * Chất đặc biệt (S6, S7, S8, S9): Đình chỉ thi đấu tiêu chuẩn 24 tháng (2 năm).
- Thẩm định hồ sơ miễn trừ do điều trị y tế TUE (Therapeutic Use Exemption) được VADC phê duyệt.

### 3. Cấp phép Cơ sở Thể thao Mạo hiểm (Thông tư 04/2019/TT-BVHTTDL)
- Thẩm định điều kiện an toàn cho các môn thể thao mạo hiểm: Dù lượn (`PARAGLIDING`), diều bay (`HANG_GLIDING`), leo núi thể thao (`ROCK_CLIMBING`), lặn biển có khí thở (`SCUBA_DIVING`), đua xe địa hình (`OFF_ROAD_MOTOR`), nhảy bungee (`BUNGEE_JUMPING`).
- Yêu cầu bắt buộc 4 tiêu chí: Huấn luyện viên có chứng chỉ, Nhân viên cứu hộ thường trực, Thiết bị kiểm định an toàn định kỳ, Phương án cấp cứu y tế.

### 4. Phê duyệt Tổ chức Giải Thi đấu Thể thao (Điều 37 & 38)
- Thẩm tra điều kiện cơ sở vật chất, hệ thống chiếu sáng thi đấu (tối thiểu 500 lux, 1200+ lux truyền hình), đội ngũ y tế trực cấp cứu và lối thoát hiểm khẩn cấp.

### 5. National Sports Telemetry & Status
- Báo cáo tổng thể hợp đồng VĐV, quỹ lương chuyên nghiệp, thống kê mẫu thử doping WADA, tỷ lệ mẫu sạch và cấp phép thể thao mạo hiểm.

---

## Hướng dẫn Sử dụng CLI (`mekong sports`)

```bash
# Xem báo cáo tổng quan telemetry thể thao và phòng chống doping quốc gia
mekong sports

# Đăng ký và thẩm định hợp đồng lao động VĐV chuyên nghiệp
mekong sports contract "Nguyễn Văn Toàn" --sport "BÓNG ĐÁ" --club "CLB Thép Xanh Nam Định" --salary 60000000 --months 36 --insurance

# Đăng ký chuyển nhượng vận động viên
mekong sports contract "Nguyễn Quang Hải" --sport "BÓNG ĐÁ" --club "CLB Công An Hà Nội" --type "TRANSFER" --salary 100000000 --months 24 --transfer-fee 5000000000 --insurance

# Xử lý kết quả mẫu kiểm tra Doping (Âm tính)
mekong sports doping "Nguyễn Thị Oanh" --sport "ĐIỀN KINH" --sample-type "URINE"

# Xử lý mẫu dương tính WADA có chế tài xử phạt
mekong sports doping "VĐV Nghi Vấn" --sport "CỬ TẠ" --substance "Stanozolol" --wada-class "S1"

# Xử lý mẫu phát hiện chất có miễn trừ điều trị y tế TUE hợp lệ
mekong sports doping "Trần Đình Trọng" --sport "BÓNG ĐÁ" --substance "Prednisolone" --wada-class "S9" --has-tue --tue-approved

# Thẩm định cấp phép cơ sở thể thao mạo hiểm
mekong sports extreme "CLB Dù lượn Đà Lạt Paragliding" --sport-type "PARAGLIDING" --coach --rescue --equipment --medical

# Phê duyệt tổ chức giải thi đấu thể thao quốc gia
mekong sports tournament "Giải Vô địch Quốc gia V.League 1 2026" --sport "BÓNG ĐÁ" --scale "NATIONAL" --organizer "VPF & VFF" --venue "Sân Hàng Đẫy" --lighting 1800 --medical --emergency

# Tra cứu danh mục hồ sơ
mekong sports list --category ALL --limit 50

# Xem trạng thái hệ thống dạng JSON
mekong sports status --json
```

---

## Native MCP Tools

Bộ công cụ MCP thể thao và phòng chống doping quốc gia (FastMCP & JSON-RPC 2.0 stdio):

- `mekong_sports_contract`: Thẩm tra và đăng ký hợp đồng lao động, chuyển nhượng VĐV chuyên nghiệp (Điều 32, 33).
- `mekong_sports_doping`: Đánh giá mẫu kiểm tra doping, nhóm chất cấm WADA, miễn trừ TUE và chế tài đình chỉ thi đấu.
- `mekong_sports_extreme`: Thẩm định điều kiện an toàn và cấp phép cơ sở kinh doanh thể thao mạo hiểm (Thông tư 04/2019).
- `mekong_sports_tournament`: Thẩm định điều kiện kỹ thuật và phê duyệt tổ chức giải thi đấu thể thao (Điều 37, 38).
- `mekong_sports_list`: Tra cứu danh sách hợp đồng VĐV, kết quả doping, giấy phép thể thao mạo hiểm và giải đấu.
- `mekong_sports_status`: Truy xuất dữ liệu telemetry thể thao quốc gia và thống kê WADA.
