---
name: telecom
description: Vietnamese Telecommunications Law 2023, Radio Spectrum Auctions, 5G Rollout Commitments, BTS EMF Radiation Safety & OTT Services Compliance.
---

# 📡 Telecom — Vietnamese Telecommunications Law 2023, Radio Spectrum Auctions, BTS EMF & OTT Services

Autonomous operations engine for Vietnamese telecommunications infrastructure, radio frequency spectrum auction valuation, base transceiver station (BTS) EMF radiation safety audits, OTT messaging/voice service regulatory compliance, and national numbering resource allocations.

## Statutory Legal Framework

1. **Luật Viễn thông 2023 (Luật số 24/2023/QH15)**:
   - Quản lý mở rộng bao gồm Dịch vụ Trung tâm Dữ liệu (IDC TIA-942), Điện toán đám mây (Cloud Computing) và Dịch vụ OTT Viễn thông (OTT messaging, VoIP như Zalo, Telegram, Viber, Skype, WhatsApp).
   - Quy định an toàn thông tin cá nhân người dùng, bảo mật bí mật thư tín và cơ chế chia sẻ cơ sở hạ tầng viễn thông thụ động (cột ăng-ten, nhà trạm, cống bể cáp).

2. **Luật Tần số Vô tuyến điện 2009 / Sửa đổi 2022 & Nghị định 63/2023/NĐ-CP**:
   - Khung pháp lý và phương pháp xác định giá khởi điểm đấu giá quyền sử dụng băng tần số vô tuyến điện:
     - Khối băng tần 4G/5G chủ lực: `B7_2600` (2500 - 2690 MHz), `C2_3700` (3700 - 3800 MHz), `C3_3800` (3800 - 3900 MHz), `N28_700` (703 - 733 MHz / 758 - 788 MHz), `B3_1800` (1710 - 1785 MHz / 1805 - 1880 MHz).
     - Thời hạn cấp quyền sử dụng băng tần: tối đa **15 năm**.
     - Tỷ lệ tiền đặt trước (tiền cọc) tham gia đấu giá: từ **5.0%** đến **20.0%** giá khởi điểm.
     - Cam kết triển khai mạng lưới bắt buộc:
       - Sau 2 năm: Tối thiểu 3.000 trạm phát sóng 5G.
       - Sau 5 năm: Độ phủ dân số tối thiểu 80% - 85% và cung cấp dịch vụ viễn thông di động băng rộng tại các khu vực cam kết.

3. **Tiêu chuẩn Kỹ thuật An toàn Bức xạ Điện từ Trạm BTS (QCVN 08:2020/BTTTT & QCVN 101:2020/BTTTT)**:
   - Đánh giá mật độ công suất bức xạ sóng vô tuyến điện $S$ tại các khu vực dân cư xung quanh trạm thu phát sóng:
     $$S = \frac{P \cdot G}{4\pi R^2}$$
     Trong đó:
     - $P$: Công suất phát sóng (Watts).
     - $G$: Hệ số tăng ích ăng-ten ($G = 10^{\text{dBi}/10}$).
     - $R$: Khoảng cách từ ăng-ten tới ranh giới công trình dân cư lân cận (mét).
   - Ngưỡng giới hạn phơi nhiễm công cộng tối đa cho phép: **$S \le 2.0\text{ W/m}^2$** (hoặc $200\text{ }\mu\text{W/cm}^2$).

4. **Quản lý Dịch vụ OTT Viễn thông & Định danh Người dùng (Nghị định 147/2024/NĐ-CP & Luật Viễn thông 2023)**:
   - Nghĩa vụ thông báo cung cấp dịch vụ OTT tới Cục Viễn thông (VNTA - Bộ TTTT).
   - Xác thực số điện thoại / định danh danh tính người dùng (KYC).
   - Mã hóa đầu cuối bảo vệ dữ liệu (End-to-end Encryption) và cơ chế lưu trữ nhật ký truy vết phục vụ an ninh quốc gia.
   - Hiện diện lưu trữ dữ liệu tại Việt Nam theo Luật An ninh mạng 2018 và Nghị định 53/2022/NĐ-CP.

5. **Quy hoạch & Phân bổ Kho số Viễn thông (Thông tư 25/2015/TT-BTTTT & Thông tư 48/2016/TT-BTTTT)**:
   - Phân bổ dải số: Tổng đài Chăm sóc khách hàng toàn quốc `1900` (thu cước), `1800` (miễn cước người gọi), dải số di động mạng Viettel, VNPT VinaPhone, MobiFone, Vietnamobile (block $100.000$ đến $1.000.000$ thuê bao).
   - Tính phí sử dụng và phí duy trì kho số viễn thông hàng tháng nộp ngân sách nhà nước.

---

## Typer CLI Commands

```bash
# 1. Bảng điều khiển tổng quan hạ tầng viễn thông & tần số vô tuyến
mekong telecom
mekong telecom --json

# 2. Định giá khởi điểm & phương án đấu giá quyền sử dụng băng tần (Nghị định 63/2023/NĐ-CP)
mekong telecom spectrum B7_2600 --years 15 --deposit 10.0
mekong telecom spectrum C2_3700 --years 15 --deposit 15.0 --json

# 3. Thẩm định điều kiện pháp lý & an toàn dịch vụ OTT viễn thông (Luật Viễn thông 2023)
mekong telecom ott "Zalo Messaging" "VNG Corporation" --users 75000000 --features "MESSAGING,VOIP,FILE_TRANSFER" --kyc --encryption --vnta-notify --local-data
mekong telecom ott "GlobalChat App" "GlobalTech Ltd" --users 1500000 --json

# 4. Kiểm định an toàn bức xạ điện từ trạm BTS theo QCVN 08:2020/BTTTT
mekong telecom bts "BTS-Q1-SGN-01" "Phường Bến Nghé, Quận 1, TP.HCM" --power 80.0 --gain 18.0 --height 35.0 --distance 25.0
mekong telecom bts "BTS-HN-08" "Cầu Giấy, Hà Nội" --power 120.0 --gain 21.0 --distance 18.0 --json

# 5. Phân bổ và quản lý tài nguyên kho số viễn thông (1900, 1800, Mobile)
mekong telecom number "1900-8888" "VIETNAMESE_ENTERPRISE" "CUSTOMER_CARE_HOTLINE" --size 1 --unit-fee 5000000
mekong telecom number "098-BLOCK" "VIETTEL_TELECOM" "MOBILE_CELLULAR" --size 1000000 --unit-fee 100 --json

# 6. Truy vấn danh mục đấu giá, hồ sơ OTT, trạm BTS hoặc kho số
mekong telecom list spectrum
mekong telecom list ott --json
mekong telecom list bts
mekong telecom list numbers --json

# 7. Báo cáo đo kiểm viễn thông
mekong telecom status
mekong telecom status --json
```

---

## FastMCP & JSON-RPC Tools

- `mekong_telecom_spectrum(band_code, license_years, deposit_pct, custom_reserve_price_vnd)`
- `mekong_telecom_ott(service_name, provider_name, registered_users, service_features, kyc_verified, end_to_end_encryption, vnta_notified, local_data_presence)`
- `mekong_telecom_bts(station_id, location, tx_power_watts, antenna_gain_dbi, antenna_height_m, distance_residential_m)`
- `mekong_telecom_number(prefix, assigned_operator, service_purpose, block_size, monthly_unit_fee_vnd)`
- `mekong_telecom_list(item_type, limit)`
- `mekong_telecom_status()`
