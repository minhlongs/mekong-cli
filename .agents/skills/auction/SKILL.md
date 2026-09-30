---
name: auction
description: Vietnamese Property Auction, Distressed Asset Liquidation & Judicial Asset Disposal Suite.
---

# /auction — Vietnamese Property Auction, Distressed Asset Liquidation & Judicial Asset Disposal Suite

Hệ thống quản lý và thẩm tra đấu giá tài sản theo Luật Đấu giá tài sản 2016 (sửa đổi, bổ sung 2024 bởi Luật số 37/2024/QH15), thẩm tra chứng chỉ hành nghề đấu giá viên theo Điều 10 & 14, niêm yết tài sản đấu giá và quy chế tiền đặt trước (5-20%, 10-20% với đất dự án), đăng ký người tham gia đấu giá theo Điều 38, lập Biên bản cuộc đấu giá theo Điều 44, và phân tích rủi ro thông đồng, dìm giá hoặc dàn xếp bỏ cọc gắn với chế tài hình sự Điều 218 Bộ luật Hình sự 2015.

## Căn cứ Pháp lý & Khung Quy chuẩn

1. **Luật Đấu giá tài sản 2016 (Luật số 01/2016/QH14)**.
2. **Luật sửa đổi, bổ sung một số điều của Luật Đấu giá tài sản 2024 (Luật số 37/2024/QH15 có hiệu lực từ 01/01/2025)**:
   - Tăng cường quy định ngăn ngừa bỏ cọc, thổi giá tài sản đấu giá.
   - Nâng tỷ lệ tiền đặt trước đối với quyền sử dụng đất thực hiện dự án đầu tư lên 10% đến 20% giá khởi điểm.
3. **Nghị định số 62/2017/NĐ-CP & Nghị định số 47/2023/NĐ-CP**:
   - Quy định chi tiết một số điều và biện pháp thi hành Luật Đấu giá tài sản.
   - Quy chế vận hành Cổng thông tin đấu giá tài sản quốc gia.
4. **Luật Quản lý, sử dụng tài sản công 2017 & Luật Đất đai 2024**: Quy định đấu giá tài sản công và quyền sử dụng đất.
5. **Luật Các tổ chức tín dụng 2024 & Nghị quyết 42/2017/QH14**: Xử lý nợ xấu và tài sản bảo đảm của ngân hàng.
6. **Bộ luật Hình sự 2015 (Điều 218)**: Tội vi phạm quy định về hoạt động bán đấu giá tài sản (thông đồng dìm giá, ép giá, hối lộ để trúng đấu giá).

---

## Tính năng Nghiệp vụ Cốt lõi

### 1. Quản lý Hồ sơ Đấu giá viên (Điều 10, 14)
- Thẩm tra Chứng chỉ hành nghề đấu giá do Bộ Tư pháp cấp (mã hiệu BTP).
- Kiểm tra tổ chức hành nghề đấu giá (Trung tâm dịch vụ bán đấu giá tài sản hoặc Doanh nghiệp đấu giá tài sản).
- Kiểm tra điều kiện duy trì hành nghề thực tế.

### 2. Niêm yết & Quy chế Tài sản Đấu giá (Điều 35, 39)
- Hỗ trợ 6 nhóm tài sản theo luật định:
  - `PUBLIC_PROPERTY`: Tài sản công nhà nước (xe công vụ, trụ sở công).
  - `LAND_USE_RIGHT`: Quyền sử dụng đất (giao đất, cho thuê đất, dự án đầu tư).
  - `DISTRESSED_DEBT`: Tài sản bảo đảm xử lý nợ xấu ngân hàng/VAMC.
  - `ENFORCEMENT_ASSET`: Tài sản kê biên thi hành án dân sự.
  - `CONFISCATED_GOODS`: Tang vật, phương tiện tịch thu sung quỹ nhà nước.
  - `MINING_SPECTRUM_VEHICLE`: Quyền khai thác khoáng sản, tần số, biển số xe.
- Thẩm tra tỷ lệ tiền đặt trước:
  - Đất dự án: Bắt buộc từ 10% đến 20% giá khởi điểm (Luật 37/2024/QH15).
  - Tài sản khác: Từ 5% đến 20% giá khởi điểm (Điều 39).
- Thẩm tra thời hạn niêm yết thông báo công khai: Tối thiểu 30 ngày đối với bất động sản, 15 ngày đối với động sản (Điều 35).

### 3. Đăng ký & Thẩm tra Người tham gia Đấu giá (Điều 38)
- Thẩm tra việc nộp đủ và đúng hạn tiền đặt trước vào tài khoản thanh toán riêng của tổ chức đấu giá.
- Sàng lọc các đối tượng bị cấm tham gia theo Khoản 4 Điều 38 (người không có năng lực hành vi dân sự, người có thẩm quyền bán tài sản, quan hệ thân thuộc với đấu giá viên...).

### 4. Tổ chức Phiên Đấu giá & Biên bản Điều 44
- Hỗ trợ 4 hình thức đấu giá:
  - `ONLINE_PORTAL`: Đấu giá trực tuyến qua Cổng đấu giá tài sản quốc gia.
  - `DIRECT_VOTING`: Bỏ phiếu trực tiếp tại cuộc đấu giá.
  - `INDIRECT_VOTING`: Bỏ phiếu gián tiếp qua bưu chính.
  - `ORAL_BIDDING`: Đấu giá trực tiếp bằng lời nói.
- Thẩm tra giá trúng đấu giá ($\ge$ Giá khởi điểm), bước giá và chữ ký bắt buộc của các bên trên Biên bản đấu giá Điều 44.

### 5. Thẩm tra Chống Dìm Giá & Thông Đồng (Điều 218 BLHS)
- Thuật toán phân tích bất thường: Nhận diện trùng lặp địa chỉ IP/mạng LAN giữa các đối thủ, trả giá giống hệt nhau hoặc đồng loạt bỏ cuộc ở các vòng cuối để một bên trúng giá sàn.
- Đưa ra khuyến nghị chuyển cơ quan điều tra nếu phát hiện vi phạm Điều 218 BLHS.

---

## Hướng dẫn Sử dụng CLI (`mekong auction`)

```bash
# Xem báo cáo tổng quan telemetry đấu giá tài sản toàn quốc
mekong auction

# Đăng ký và thẩm tra hồ sơ Đấu giá viên
mekong auction auctioneer "Đấu giá viên Lê Hoàng Long" --cert "BTP-ĐGV-2024/09" --org "Công ty Đấu giá Hợp danh Á Châu" --date "2024-03-10"

# Niêm yết tài sản đấu giá với thẩm tra tỷ lệ tiền đặt trước và thời hạn thông báo
mekong auction asset "Khu đất dự án thương mại dịch vụ 5,000m2 tại KĐT Mới Cầu Giấy" --type "LAND_USE_RIGHT" --owner "Sở Tài nguyên và Môi trường Hà Nội" --price 120000000000 --step 500000000 --deposit 15 --notice 30

# Đăng ký tham gia đấu giá và kiểm tra nộp tiền đặt trước
mekong auction bidder "AST-12AB34CD" "Công ty Cổ phần Đầu tư Bất động sản Thăng Long" "0109988776" --deposit 18000000000

# Ghi nhận kết quả phiên đấu giá và lập Biên bản Điều 44
mekong auction session "AST-12AB34CD" "AUC-55EE66FF" "BID-77GG88HH" 135000000000 --format "ONLINE_PORTAL" --protocol

# Thẩm tra dấu hiệu thông đồng dìm giá hoặc bỏ cọc
mekong auction audit "AST-12AB34CD" --bids '[{"amount_vnd": 120000000000, "withdrawn": false}, {"amount_vnd": 120000000000, "withdrawn": true}]' --ips '["192.168.1.100", "192.168.1.100"]'

# Tra cứu danh mục hồ sơ đấu giá
mekong auction list --category ALL --limit 50 --json

# Xem telemetry hệ thống đấu giá toàn quốc
mekong auction status --json
```

---

## Công cụ Native MCP

- `mekong_auction_auctioneer`: Đăng ký và thẩm tra tư cách hành nghề Đấu giá viên theo Điều 10 & 14.
- `mekong_auction_asset`: Niêm yết và thẩm tra quy chế tài sản đấu giá theo Điều 35 & 39.
- `mekong_auction_bidder`: Đăng ký và thẩm tra điều kiện nộp tiền đặt trước của người tham gia theo Điều 38.
- `mekong_auction_session`: Lập Biên bản cuộc đấu giá và công nhận kết quả trúng giá theo Điều 44.
- `mekong_auction_audit`: Thẩm tra rủi ro thông đồng dìm giá hoặc dàn xếp bỏ cọc theo Điều 218 BLHS.
- `mekong_auction_list`: Tra cứu danh mục đấu giá viên, tài sản niêm yết, người đăng ký và biên bản phiên đấu giá.
- `mekong_auction_status`: Báo cáo chỉ số telemetry hoạt động đấu giá tài sản toàn quốc.
