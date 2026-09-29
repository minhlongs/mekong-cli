---
name: advertising
description: Vietnamese Advertising, Media & Digital Marketing Compliance Suite.
---

# mekong advertising — Autonomous Vietnamese Advertising, Media & Digital Marketing Compliance Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Quảng cáo 2012 (Luật số 16/2012/QH13)**:
   - Thống nhất quản lý nhà nước về hoạt động quảng cáo trên toàn lãnh thổ Việt Nam.
   - Thẩm quyền quản lý: **Bộ Văn hóa, Thể thao và Du lịch (Bộ VHTTDL)**, **Bộ Thông tin và Truyền thông (Bộ TTTT)**, **Bộ Y tế (Bộ YT)**.
   - Điều 8 (Hành vi cấm): Quảng cáo không đúng hoặc gây nhầm lẫn về khả năng kinh doanh, tính năng, số lượng, chất lượng, giá cả; sử dụng các từ ngữ "nhất", "duy nhất", "tốt nhất", "số một" hoặc tương tự mà không có tài liệu hợp pháp chứng minh.
   - Điều 22 (Thời lượng quảng cáo phát thanh/truyền hình): Tối đa không quá 10% tổng thời lượng phát sóng trong một ngày của tổ chức phát sóng; không quá 5% thời lượng phát sóng đối với kênh truyền hình trả tiền; không được ngắt một chương trình phim quá 02 lần, mỗi lần không quá 05 phút.
2. **Nghị định số 181/2013/NĐ-CP (Hướng dẫn thi hành Luật Quảng cáo)**:
   - Quy định cấp Giấy xác nhận nội dung quảng cáo (XNNDQC) cho các sản phẩm, hàng hóa, dịch vụ đặc biệt (thuốc chữa bệnh, thực phẩm chức năng / bảo vệ sức khỏe, mỹ phẩm, trang thiết bị y tế, hóa chất diệt khuẩn...).
   - Bắt buộc các câu khuyến cáo chuyên ngành (ví dụ: *"Thực phẩm này không phải là thuốc và không có tác dụng thay thế thuốc chữa bệnh"* đối với TPBVSK).
3. **Nghị định số 70/2021/NĐ-CP (Quảng cáo xuyên biên giới)**:
   - Điều chỉnh hoạt động cung cấp dịch vụ quảng cáo xuyên biên giới tại Việt Nam (Facebook, Google, TikTok, YouTube).
   - Nghĩa vụ tuân thủ: Phải ngăn chặn, gỡ bỏ nội dung quảng cáo vi phạm pháp luật trong vòng **24 giờ** kể từ khi nhận được yêu cầu từ Bộ TTTT hoặc cơ quan có thẩm quyền.
   - Trách nhiệm kê khai nộp thuế nhà thầu nước ngoài (FCT) và đảm bảo các giải pháp kỹ thuật ngăn chặn việc chèn quảng cáo vào nội dung vi phạm pháp luật.
4. **Quy chuẩn kỹ thuật Quốc gia về Biển quảng cáo ngoài trời (QCVN 17:2018/BXD)**:
   - Bảng quảng cáo đứng độc lập trên hành lang an toàn đường cao tốc, quốc lộ: diện tích một mặt tối đa **120 m²**, chiều cao tối đa **15 m**, tĩnh không mặt đáy tối thiểu **5 m**.
   - Bảng quảng cáo độc lập trong khu vực đô thị: diện tích một mặt tối đa **40 m²**, chiều cao tối đa **10 m**, tĩnh không tối thiểu **4 m**.
   - Bảng quảng cáo gắn vào tường công trình: diện tích tối đa **20 m²**, chiều cao tối đa **8 m**, không vượt quá chiều cao tường, không che chắn ban công, lối thoát nạn.
   - Băng-rôn (treo ngang/dọc): thời hạn treo tối đa không quá **15 ngày**.
5. **Nghị định số 38/2021/NĐ-CP (Xử phạt vi phạm hành chính trong lĩnh vực văn hóa và quảng cáo)**:
   - Xử phạt từ 10.000.000 - 20.000.000 VND đối với hành vi sử dụng từ "nhất", "duy nhất", "tốt nhất", "số 1" không có tài liệu hợp pháp.
   - Xử phạt từ 50.000.000 - 70.000.000 VND đối với hành vi quảng cáo sai sự thật hoặc gây nhầm lẫn công dụng ("chữa khỏi hoàn toàn", "trị dứt điểm").
   - Xử phạt từ 10.000.000 - 15.000.000 VND đối với hành vi không đọc hoặc không ghi rõ câu khuyến cáo bắt buộc đối với thực phẩm chức năng.
6. **Lưu trữ SQLite WAL**: Bảng `ad_content_approvals`, `ad_content_checks`, `cross_border_takedowns`, `ooh_billboard_permits`, `broadcast_ad_slots` tại `.mekong/advertising.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động quảng cáo, thẩm định nội dung, OOH và xuyên biên giới
mekong advertising

# Quét và kiểm tra tính hợp pháp nội dung quảng cáo (từ cấm, khuyến cáo bắt buộc)
mekong advertising check "Trà sâm Mekong trị dứt điểm mất ngủ, tốt nhất thị trường" --type supplement

# Cấp Giấy xác nhận nội dung quảng cáo (XNNDQC) cho sản phẩm đặc biệt (NĐ 181/2013)
mekong advertising approval "Cao atiso Mekong Detox" --category supplement --applicant "Công ty Dược Mekong" --license "DK-8899/2026/BYT"

# Thẩm định biển quảng cáo ngoài trời OOH và băng-rôn theo QCVN 17:2018/BXD
mekong advertising billboard highway --area 110 --height 14 --clearance 5.5

# Giám sát quy trình gỡ bỏ quảng cáo vi phạm xuyên biên giới 24h theo Nghị định 70/2021/NĐ-CP
mekong advertising takedown Facebook --ad-id "AD-FB-2026-9901" --violation "Quảng cáo cờ bạc trái phép"

# Giám sát thời lượng quảng cáo phát thanh truyền hình theo Điều 22 Luật Quảng cáo 2012
mekong advertising broadcast terrestrial --program-min 90 --ad-min 8.5 --breaks 2 --max-break 4.5

# Tra cứu danh mục hồ sơ kiểm tra quảng cáo hoặc giấy phép
mekong advertising list checks
mekong advertising list approvals
mekong advertising list takedowns
mekong advertising list billboards

# Báo cáo telemetry chỉ số tuân thủ quảng cáo
mekong advertising status
```

---

## MCP Tools Integration

- `mekong_advertising_check`: Quét và kiểm tra nội dung quảng cáo, phát hiện từ cấm ("nhất", "số 1"), thiếu câu khuyến cáo bắt buộc và ước tính khung phạt tiền.
- `mekong_advertising_approval`: Cấp Giấy xác nhận nội dung quảng cáo (XNNDQC) cho sản phẩm đặc biệt (dược phẩm, mỹ phẩm, thực phẩm bảo vệ sức khỏe).
- `mekong_advertising_billboard`: Thẩm định quy chuẩn xây dựng và lắp đặt biển bảng quảng cáo ngoài trời OOH và băng-rôn (QCVN 17:2018/BXD).
- `mekong_advertising_takedown`: Giám sát xử lý gỡ bỏ quảng cáo vi phạm xuyên biên giới trong thời hạn 24 giờ (NĐ 70/2021/NĐ-CP).
- `mekong_advertising_broadcast`: Kiểm tra tỷ lệ thời lượng quảng cáo phát thanh, truyền hình và thời lượng ngắt phim (Luật Quảng cáo 2012).
- `mekong_advertising_list`: Tra cứu danh mục hồ sơ thẩm định maket quảng cáo, giấy phép XNNDQC hoặc vụ việc gỡ bỏ xuyên biên giới.
- `mekong_advertising_status`: Báo cáo chỉ số telemetry tổng hợp hệ thống giám sát và tuân thủ quảng cáo quốc gia.
