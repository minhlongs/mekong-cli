---
name: disaster
description: Vietnamese Meteorology, Hydrology, Hydroelectric Reservoir Dam Safety & Natural Disaster Prevention Suite.
---

# mekong disaster — Autonomous Vietnamese Meteorology, Dam Safety & Natural Disaster Prevention Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Phòng, chống thiên tai 2013 (sửa đổi, bổ sung 2020 - Luật số 60/2020/QH14)**:
   - Thống nhất quản lý phòng ngừa, ứng phó, khắc phục hậu quả thiên tai trên toàn quốc.
   - Cơ quan thường trực quốc gia: **Ban Chỉ đạo Quốc gia về Phòng, chống thiên tai** (Cục Quản lý đê điều và Phòng chống thiên tai - Bộ NN&PTNT).
   - Nguyên tắc cơ bản: Phương châm "4 tại chỗ" (Chỉ huy tại chỗ, lực lượng tại chỗ, phương tiện/vật tư tại chỗ, hậu cần tại chỗ).
2. **Luật Khí tượng thủy văn 2015 (Luật số 90/2015/QH13)**:
   - Quản lý mạng lưới quan trắc khí tượng thủy văn chuyên dùng phục vụ vận hành hồ chứa, công trình ven biển, hàng không và phòng chống lụt bão.
   - Thẩm quyền quản lý nhà nước: **Tổng cục Khí tượng Thủy văn (Bộ Tài nguyên và Môi trường)**.
3. **Nghị định số 114/2018/NĐ-CP (Quản lý an toàn đập, hồ chứa nước)**:
   - Phân cấp an toàn đập:
     * **Đập quan trọng đặc biệt**: Dung tích trữ $\ge 1\text{ tỷ m}^3$ hoặc hạ du là thành phố, khu đô thị trọng điểm. Chu kỳ kiểm định 5 năm/lần.
     * **Đập lớn**: Chiều cao đập $\ge 15\text{m}$ hoặc dung tích trữ từ $3\text{ triệu m}^3$ đến dưới $1\text{ tỷ m}^3$. Chu kỳ kiểm định 5 năm/lần.
     * **Đập vừa**: Chiều cao từ $10\text{m}$ đến dưới $15\text{m}$ hoặc dung tích từ $500.000\text{ m}^3$ đến dưới $3\text{ triệu m}^3$. Chu kỳ kiểm định 7 năm/lần.
     * **Đập nhỏ**: Chiều cao dưới $10\text{m}$ và dung tích trữ dưới $500.000\text{ m}^3$. Chu kỳ kiểm định 10 năm/lần.
   - Bắt buộc lập và phê duyệt Phương án ứng phó với tình huống khẩn cấp cho vùng hạ du (Điều 23).
   - Đập lớn và đặc biệt quan trọng bắt buộc lắp đặt hệ thống quan trắc KTTV tự động và camera giám sát xả lũ.
4. **Quy trình vận hành liên hồ chứa (Quyết định của Thủ tướng Chính phủ)**:
   - Các lưu vực trọng điểm: Sông Hồng, Sông Cả, Sông Mã, Sông Vu Gia - Thu Bồn, Sông Ba, Sông Sê San, Sông Srêpôk, Sông Đồng Nai.
   - Thời gian phát lệnh và thông báo xả lũ: Tối thiểu $\ge 4.0\text{ giờ}$ trước khi mở cửa xả tràn (trường hợp khẩn cấp $\ge 2.0\text{ giờ}$).
   - Kích hoạt hệ thống còi báo động, loa truyền thanh cảnh báo dân cư hạ du.
5. **Quyết định số 18/2021/QĐ-TTg (Dự báo, cảnh báo và cấp độ rủi ro thiên tai)**:
   - Phân loại 5 cấp độ rủi ro thiên tai: Cấp 1 (Nhỏ), Cấp 2 (Trung bình), Cấp 3 (Lớn), Cấp 4 (Rất lớn), Cấp 5 (Thảm họa).
6. **Nghị định số 78/2021/NĐ-CP (Quỹ Phòng, chống thiên tai)**:
   - Mức đóng góp của doanh nghiệp: $0.02\%$ trên tổng vốn/tài sản (Tối thiểu $500.000\text{ VND}$, tối đa $100.000.000\text{ VND}$).
   - Người lao động: Mức đóng chuẩn theo luật định ($90.000\text{ VND}$/người/năm).
7. **Lưu trữ SQLite WAL**: Bảng `reservoir_dam_audits`, `reservoir_flood_discharges`, `natural_disaster_risk_assessments`, `disaster_prevention_fund_calculations` tại `.mekong/disaster.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan phòng chống thiên tai, an toàn đập hồ chứa và quỹ PCTT
mekong disaster

# Thẩm định cấp công trình và kiểm định an toàn đập theo Nghị định 114/2018/NĐ-CP
mekong disaster dam "Thủy điện Hòa Bình" --basin "Lưu vực Sông Đà - Sông Hồng" --height 128.0 --capacity 9450000000 --population 250000 --inspection 4 --plan --monitoring

# Giám sát và kiểm tra quy trình xả lũ hồ chứa liên hồ (chuẩn thông báo trước >= 4.0h)
mekong disaster discharge "Thủy điện Sông Tranh 2" --basin "Lưu vực Sông Vu Gia - Thu Bồn" --level 175.5 --flood-level 173.0 --inflow 3200 --discharge 2800 --warning-hours 4.5 --siren --inter-res

# Đánh giá cấp độ rủi ro thiên tai (Cấp 1-5 theo Quyết định 18/2021/QĐ-TTg)
mekong disaster risk "Bão Yagi Siêu bão Số 3" --type TYPHOON --provinces 8 --wind 16 --rain 450 --flood 4 --population 500000

# Tính toán mức đóng góp bắt buộc Quỹ Phòng chống thiên tai (Nghị định 78/2021/NĐ-CP)
mekong disaster fund "Công ty CP Tập đoàn Mekong Tech" --capital 35000000000 --employees 120

# Tra cứu lịch sử thẩm định và dữ liệu phòng chống thiên tai
mekong disaster list all --limit 20
```

---

## FastMCP & JSON-RPC Tools
- `mekong_disaster_dam(dam_name, river_basin, dam_height_m, reservoir_capacity_m3, downstream_population, last_inspection_years_ago, has_emergency_plan, automatic_monitoring)`
- `mekong_disaster_discharge(dam_name, river_basin, current_water_level_m, flood_control_water_level_m, inflow_rate_m3s, discharge_rate_m3s, advance_warning_hours, siren_system_active, inter_reservoir_compliance)`
- `mekong_disaster_risk(event_name, disaster_type, affected_provinces_count, wind_level_beaufort, rainfall_24h_mm, river_flood_level, downstream_population_at_risk)`
- `mekong_disaster_fund(enterprise_name, total_capital_vnd, employee_count, is_exempt, exemption_reason)`
- `mekong_disaster_list(category, limit)`
- `mekong_disaster_status()`
