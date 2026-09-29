---
name: tourism
description: Vietnamese Tourism, Hospitality, Travel Licensing & Star Rating Suite.
---

# 🏖️ Tourism — Vietnamese Tourism, Hospitality, Travel Licensing & Star Rating

Autonomous operations engine for Vietnamese tourism, domestic and international travel agency licensing with statutory bank escrow, hotel and resort star ratings (1-5 stars under TCVN 4391:2015), tour guide certification, high-risk adventure tourism safety audits, and booking revenue telemetry under the Law on Tourism 2017 (Law 09/2017/QH14), Decree 168/2017/NĐ-CP, Decree 94/2021/NĐ-CP, and TCVN 4391:2015.

## Statutory Legal Framework

1. **Luật Du lịch 2017 (Luật số 09/2017/QH14)**:
   - Quy định về tài nguyên du lịch, quy hoạch phát triển du lịch, kinh doanh dịch vụ lữ hành, vận tải khách du lịch, lưu trú du lịch, hướng dẫn viên du lịch.
   - Thẩm quyền quản lý của Cục Du lịch Quốc gia Việt Nam (Bộ Văn hóa, Thể thao và Du lịch) và Sở Du lịch các tỉnh/thành phố.

2. **Kinh Doanh Dịch Vụ Lữ Hành & Tiền Ký Quỹ Bắt Buộc (Nghị định 168/2017/NĐ-CP)**:
   - **Lữ hành nội địa (`DOMESTIC_TRAVEL`)**:
     * Tiền ký quỹ tại ngân hàng: 100,000,000 VND.
     * Người phụ trách điều hành tốt nghiệp trung cấp chuyên ngành lữ hành trở lên.
     * Thẩm quyền cấp phép: Sở Du lịch cấp tỉnh.
   - **Lữ hành quốc tế (`INTERNATIONAL_INBOUND` / `INTERNATIONAL_OUTBOUND` / `INTERNATIONAL_FULL`)**:
     * Ký quỹ phục vụ khách quốc tế đến VN (Inbound): 250,000,000 VND.
     * Ký quỹ phục vụ khách VN ra nước ngoài (Outbound) hoặc cả hai: 500,000,000 VND.
     * Người phụ trách tốt nghiệp cao đẳng chuyên ngành lữ hành trở lên.
     * Thẩm quyền cấp phép: Cục Du lịch Quốc gia Việt Nam.

3. **Tiêu Chuẩn Xếp Hạng Sao Khách Sạn & Resort (TCVN 4391:2015)**:
   - **1 sao**: $\ge 10$ phòng, tiện nghi cơ bản.
   - **2 sao**: $\ge 20$ phòng, phục vụ ăn sáng.
   - **3 sao**: $\ge 50$ phòng, nhà hàng, phòng họp, thang máy từ 3 tầng.
   - **4 sao**: $\ge 80$ phòng, 2 nhà hàng, hồ bơi, gym, spa, phòng hội nghị đa năng.
   - **5 sao**: $\ge 100$ phòng, ẩm thực quốc tế, hồ bơi vô cực, dịch vụ quản gia, phòng tổng thống.

4. **Cấp Thẻ Hướng Dẫn Viên Du Lịch (Điều 58, 59 Luật Du lịch 2017)**:
   - Thẻ hướng dẫn viên nội địa (`DOMESTIC`): Tốt nghiệp trung cấp hướng dẫn du lịch trở lên.
   - Thẻ hướng dẫn viên quốc tế (`INTERNATIONAL`): Tốt nghiệp cao đẳng hướng dẫn du lịch hoặc cử nhân chuyên ngành khác + chứng chỉ ngoại ngữ B2/IELTS.
   - Thẻ hướng dẫn viên tại điểm (`ON_SITE`): Bồi dưỡng nghiệp vụ tại điểm tham quan di tích/danh thắng.

5. **An Toàn Du Lịch Mạo Hiểm (Nghị định 168/2017/NĐ-CP)**:
   - Thẩm định điều kiện an toàn đối với các sản phẩm du lịch có nguy cơ cao: Dù lượn, lặn biển scuba diving, chèo thuyền vượt thác (rafting), leo núi, thám hiểm hang động (caving như Sơn Đoòng), zipline.
   - Yêu cầu huấn luyện viên chứng chỉ chuyên nghiệp, trang bị định vị/bảo hộ, phương án sơ cấp cứu khẩn cấp và bảo hiểm tai nạn du lịch mức tối thiểu 100,000,000 VND/người.

---

## CLI Usage

```bash
# Báo cáo telemetry tổng quan ngành du lịch, lữ hành & khách sạn
mekong tourism status
mekong tourism status --json

# Thẩm định và cấp giấy phép kinh doanh lữ hành
mekong tourism license "Saigontourist Group" "0300625211" --type INTERNATIONAL_FULL --escrow 500000000 --bank Vietcombank --responsible "Nguyễn Văn Hùng" --json

# Thẩm định xếp hạng sao khách sạn / resort theo TCVN 4391
mekong tourism rating "Vinpearl Resort & Spa Phú Quốc" --type RESORT --rooms 120 --province "Kiên Giang" --star 5_STAR --pool --restaurant --conference --json

# Cấp thẻ hành nghề hướng dẫn viên du lịch
mekong tourism guide "Trần Thanh Tâm" --type INTERNATIONAL --language "Tiếng Anh (IELTS 7.5)" --qualification "Cử nhân Hướng dẫn Du lịch" --json

# Thẩm định an toàn tour du lịch mạo hiểm
mekong tourism adventure "Thám hiểm Hang Sơn Đoòng 4N3Đ" --type CAVING_EXPEDITION --location "Vườn Quốc gia Phong Nha - Kẻ Bàng, Quảng Bình" --instructor --gear --rescue --insurance 100000000 --json

# Đặt tour du lịch và tính doanh thu
mekong tourism booking "John Smith" --nationality "United States" --type INBOUND --pax 6 --price 12000000 --date 2026-11-10 --duration 7 --json

# Tra cứu danh mục
mekong tourism list licenses --json
mekong tourism list accommodations --json
mekong tourism list guides --json
mekong tourism list adventure --json
mekong tourism list bookings --json
```

---

## MCP Tools Integration

Mekong CLI provides dual FastMCP and pure-Python JSON-RPC 2.0 stdio tools:
- `mekong_tourism_license`: Issue commercial domestic or international travel operator license with bank escrow.
- `mekong_tourism_rating`: Audit hotel & resort star rating compliance (1-5 stars) under TCVN 4391:2015.
- `mekong_tourism_guide`: Issue certified tour guide card for domestic, international, or on-site tour guides.
- `mekong_tourism_adventure`: Audit safety requirements for high-risk adventure tourism products under Decree 168/2017/NĐ-CP.
- `mekong_tourism_booking`: Record tour booking and calculate revenue metrics.
- `mekong_tourism_list`: Query travel licenses, rated accommodations, tour guides, adventure audits, or bookings.
- `mekong_tourism_status`: Retrieve Vietnamese tourism, hospitality & travel industry telemetry and compliance metrics.
