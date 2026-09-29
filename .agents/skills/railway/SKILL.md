---
name: railway
description: Vietnamese Railway Transport, High-Speed Rail (HSR 350 km/h) & Urban Metro Suite.
---

# 🚄 Railway — Vietnamese Railway Transport, High-Speed Rail & Urban Metro

Autonomous operations engine for Vietnamese railway transport, North-South High-Speed Railway (HSR 350 km/h), urban metro networks, rail safety corridor compliance, rolling stock lifespan limits, freight & passenger tariff calculations, and train driver licensing under the Law on Railways 2017 (Law 06/2017/QH14), Resolution 172/2024/QH15, Decree 56/2018/NĐ-CP, Decree 65/2018/NĐ-CP, Decree 01/2022/NĐ-CP, and Circular 33/2018/TT-BGTVT.

## Statutory Legal Framework

1. **Luật Đường sắt 2017 (Luật số 06/2017/QH14) & Nghị quyết 172/2024/QH15**:
   - **Đường sắt tốc độ cao trên trục Bắc - Nam (HSR)**: Chiều dài tuyến $1,541\text{ km}$, 23 ga hành khách, khổ đường đôi tiêu chuẩn $1,435\text{ mm}$, điện khí hóa toàn tuyến, tốc độ thiết kế $350\text{ km/h}$.
   - **Khổ đường ray theo quy chuẩn**:
     * Khổ tiêu chuẩn (`STANDARD_1435MM`): $1,435\text{ mm}$ (Áp dụng cho HSR Bắc - Nam và tuyến Metro mới).
     * Khổ hẹp truyền thống (`METRE_1000MM`): $1,000\text{ mm}$ (Tuyến đường sắt Bắc - Nam hiện hữu và tuyến nhánh).
     * Khổ lồng kết hợp (`DUAL_GAUGE`): $1,000\text{ mm}$ & $1,435\text{ mm}$ (Tuyến liên vận quốc tế sang Trung Quốc).

2. **Hành Lang An Toàn Giao Thông Đường Sắt (Nghị định 56/2018/NĐ-CP)**:
   - Đường sắt tốc độ cao ($v \ge 200\text{ km/h}$): Khoảng cách đệm an toàn $\ge 20\text{ m}$ tính từ mép ray ngoài cùng, bắt buộc dựng rào cách ly hoàn toàn.
   - Đường sắt trên cao (Metro cầu cạn): Phạm vi bảo vệ công trình $\ge 5\text{ m}$ từ mép dầm ngoài cùng.
   - Đường sắt hầm ngầm: Phạm vi an toàn $\ge 3\text{ m}$ từ vỏ hầm.
   - Đường sắt quốc gia thông thường: $\ge 15\text{ m}$ (khu vực ngoài đô thị) hoặc $\ge 7.5\text{ m}$ (trong đô thị).

3. **Niên Hạn Sử Dụng Phương Tiện Giao Thông Đường Sắt (Nghị định 65/2018/NĐ-CP & Nghị định 01/2022/NĐ-CP)**:
   - Đầu máy diesel, đầu máy điện và toa xe chở khách: Tối đa 40 năm.
   - Toa xe chở hàng: Tối đa 45 năm.
   - Đoàn tàu động lực phân tán EMU cao tốc: Tối đa 30 năm (theo tiêu chuẩn UIC/EN).

4. **Sát Hạch & Cấp Giấy Phép Lái Tàu (Thông tư 33/2018/TT-BGTVT)**:
   - Độ tuổi từ 21 đến 55 (nữ) / 60 (nam), đạt sức khỏe Loại 1 ngành giao thông đường sắt.
   - Thời gian tập sự thực hành lái phụ tối thiểu $\ge 24\text{ tháng}$ đối với tàu điện metro/đầu máy diesel, $\ge 36\text{ tháng}$ đối với tàu cao tốc.

---

## CLI Usage

```bash
# Báo cáo tổng quan ngành đường sắt & metro
mekong railway status
mekong railway status --json

# Đăng ký tuyến đường sắt & thông số thiết kế
mekong railway line "Tuyến Đường Sắt Tốc Độ Cao Bắc - Nam" HSR-BN-01 --category HIGH_SPEED_RAIL --gauge STANDARD_1435MM --length 1541.0 --stations 23 --speed 350.0 --electrified --json

# Thẩm định hành lang an toàn giao thông đường sắt
mekong railway corridor RLN-12345678 --structure AT_GRADE --speed 350.0 --buffer 22.0 --json

# Đăng ký phương tiện đường sắt & kiểm tra niên hạn lưu hành
mekong railway stock HSR-EMU-350-01 --type EMU_TRAINSET --maker "Hitachi Rail" --year 2024 --gauge STANDARD_1435MM --json

# Tính cước vận tải hàng hóa đường sắt theo tấn-km
mekong railway freight "Công ty CP Thép Hòa Phát Dung Quất" --type HEAVY_INDUSTRIAL --weight 500.0 --distance 850.0 --json

# Thẩm định sát hạch điều kiện cấp giấy phép lái tàu
mekong railway driver "Nguyễn Văn Hùng" --type HIGH_SPEED_EMU --age 36 --exp 48 --health 1 --json

# Tra cứu dữ liệu tuyến, hành lang, phương tiện, cước, lái tàu
mekong railway list lines --limit 50 --json
mekong railway list corridor --json
mekong railway list stock --json
mekong railway list freight --json
mekong railway list drivers --json
```

---

## MCP Tools

| MCP Tool | Description |
|---|---|
| `mekong_railway_line` | Register railway line infrastructure, category, gauge, and speed specifications. |
| `mekong_railway_corridor` | Audit railway safety corridor buffer clearance under Decree 56/2018/NĐ-CP. |
| `mekong_railway_stock` | Register rolling stock (locomotive/car) and verify statutory lifespan limits under Decree 65/2018. |
| `mekong_railway_freight` | Calculate statutory rail freight tariff charges based on ton-km and cargo classification. |
| `mekong_railway_driver` | Verify train driver license eligibility, assistant driving practice, and health grade. |
| `mekong_railway_list` | Query registered railway lines, corridor audits, rolling stock, freight bills, or drivers. |
| `mekong_railway_status` | Retrieve aggregate Vietnamese railway, high-speed rail, and urban metro telemetry. |
