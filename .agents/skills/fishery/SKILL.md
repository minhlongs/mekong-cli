---
name: fishery
description: Vietnamese Fisheries Law 2017, VMS Fleet Tracking, eCDT Catch Documentation & European IUU Yellow Card Compliance.
---

# 🐟 Fishery — Vietnamese Fisheries, VMS Fleet Tracking & EU IUU Yellow Card Compliance

Autonomous operations engine for Vietnamese commercial marine fisheries, Vessel Monitoring System (VMS) continuous 24/7 positioning, electronic Catch Documentation and Traceability (eCDT VN), designated landing port inspection, and European Union IUU (Illegal, Unreported, and Unregulated) Yellow Card removal compliance under Decree 37/2024/NĐ-CP and Decree 26/2019/NĐ-CP.

## Statutory Legal Framework

1. **Luật Thủy sản 2017 (Luật số 18/2017/QH14) & Nghị định 26/2019/NĐ-CP, Nghị định 37/2024/NĐ-CP**:
   - Khung pháp lý tổng thể chống khai thác hải sản bất hợp pháp (IUU Fishing) theo khuyến nghị của Ủy ban Châu Âu (EC):
     - **Bắt buộc lắp đặt thiết bị giám sát hành trình (VMS)**: Áp dụng với 100% tàu cá có chiều dài lớn nhất ($L_{\max}$) từ **15 mét trở lên**.
     - Vận hành thiết bị VMS liên tục 24/24 giờ từ khi rời cảng đến khi cập cảng.
     - Cảnh báo tự động khi mất tín hiệu kết nối quá **06 giờ** trên biển hoặc quá **10 ngày** tại cảng không báo cáo.
     - Kiểm soát ranh giới vùng biển cho phép khai thác: Cảnh báo nghiêm cấm vượt ranh giới vùng biển Việt Nam sang vùng biển nước ngoài.
     - Xử phạt nghiêm khắc các hành vi vi phạm IUU theo Nghị định 38/2024/NĐ-CP.

2. **Hệ thống Truy xuất Nguồn gốc Thủy sản Khai thác Điện tử (eCDT VN)**:
   - Quy trình số hóa chuỗi cung ứng hải sản từ tàu khai thác đến nhà máy chế biến và xuất khẩu:
     - **Statement of Catch (SC)**: Giấy xác nhận nguyên liệu thủy sản bốc dỡ qua cảng cá chỉ định (Designated Port).
     - **Catch Certificate (CC)**: Giấy chứng nhận nguồn gốc thủy sản khai thác xuất khẩu sang thị trường EU, Hoa Kỳ, Nhật Bản.
     - Mã hóa định danh duy nhất (eCDT QR hash) liên kết hồ sơ tàu, nhật ký khai thác và chứng chỉ xuất xưởng.

3. **An toàn Thực phẩm & Kiểm định Nhà máy Chế biến (Thông tư 48/2013/TT-BNNPTNT & EU Regulation 2017/625)**:
   - Cấp mã số cơ sở chế biến thủy sản xuất khẩu đi thị trường châu Âu (EU Approval Code `DL-xxx`).
   - Kiểm tra hệ thống quản lý an toàn thực phẩm HACCP ($\ge 80/100$ điểm).
   - Kiểm soát nghiêm ngặt dư lượng kháng sinh cấm:
     - Chloramphenicol $\le 0.1\text{ ppb}$ (ngưỡng không phát hiện).
     - Dẫn xuất Nitrofuran (AOZ, AMOZ, AHD, SEM) $\le 0.5\text{ ppb}$.
     - Kiểm soát kim loại nặng (Chì, Thủy ngân, Cadimi).

---

## Typer CLI Commands

```bash
# 1. Bảng điều khiển tổng quan hạm đội tàu cá & giám sát IUU
mekong fishery
mekong fishery --json

# 2. Đăng ký tàu cá vào VNFishbase & thẩm định điều kiện VMS
mekong fishery vessel "VN-98765-TS" "Nguyễn Văn Thuyền" --port PORT_TAC_CAU --length 19.2 --power 500 --vms "VMS-VN-98765" --zone SOUTHWEST_GULF

# 3. Giám sát hải trình VMS & cảnh báo vi phạm ranh giới biển
mekong fishery vms "VN-98765-TS" 9.5 103.8 --speed 8.5 --heading 140 --zone SOUTHWEST_GULF

# 4. Cấp chứng nhận nguồn gốc thủy sản khai thác eCDT (CC/SC)
mekong fishery cert "VN-98765-TS" --species YELLOWFIN_TUNA --volume 14000 --port PORT_QUY_NHON --market EU_MARKET

# 5. Kiểm nghiệm an toàn thực phẩm nhà máy HACCP & kháng sinh
mekong fishery quality "DL-482" "Nhà máy Thủy sản Minh Phú" "LOT-2026-0929" --species WHITELEG_SHRIMP --haccp 96.0 --chloramphenicol 0.0

# 6. Truy vấn danh mục
mekong fishery list vessels
mekong fishery list vms
mekong fishery list certs
mekong fishery list quality
mekong fishery list --type certs --json

# 7. Trạng thái hệ thống telemetry
mekong fishery status --json
```

---

## MCP Tools Integration

- `mekong_fishery_vessel(vessel_plate, owner_name, home_port, length_meters, engine_power_hp, vms_device_id, assigned_zone, license_valid_years)`
- `mekong_fishery_vms(vessel_plate, latitude, longitude, speed_knots, heading_degrees, is_signal_active, disconnection_hours, assigned_zone)`
- `mekong_fishery_cert(vessel_plate, species_code, catch_volume_kg, landing_port, destination_market, certificate_type)`
- `mekong_fishery_quality(facility_eu_code, facility_name, lot_number, species_code, haccp_score, chloramphenicol_ppb, nitrofurans_ppb, heavy_metal_pass)`
- `mekong_fishery_list(item_type, limit)`
- `mekong_fishery_status()`
