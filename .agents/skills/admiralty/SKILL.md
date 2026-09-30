---
name: admiralty
description: Vietnamese Maritime Court, Admiralty Jurisdiction, Vessel Arrest, Maritime Liens & General Average Suite.
---

# /admiralty — Vietnamese Maritime Court, Admiralty Jurisdiction, Vessel Arrest, Maritime Liens & General Average Suite

Hệ thống quản lý và thực thi nghiệp vụ tư pháp hàng hải, bắt giữ tàu biển để bảo đảm khiếu nại hàng hải theo Pháp lệnh số 05/2008/PL-UBTVQH12, xác lập và xếp hạng Quyền cầm giữ hàng hải (Maritime Liens) theo Điều 41-42 Bộ luật Hàng hải Việt Nam 2015 (ưu tiên thanh toán trước thế chấp tàu biển), phân định trách nhiệm đâm va tàu thuyền theo COLREGS 1972 & Điều 286-291, và tính toán phân bổ tổn thất chung (General Average) theo Quy tắc York-Antwerp 2016 (YAR 2016) & Điều 300-307.

## Căn cứ Pháp lý & Khung Quy chuẩn

1. **Bộ luật Hàng hải Việt Nam 2015 (Luật số 95/2015/QH13)**:
   - Chương II: Đăng ký tàu biển và Cờ quốc tịch tàu biển Việt Nam (Điều 17–36).
   - Chương III: Thế chấp tàu biển và hiệu lực đối kháng bên thứ ba (Điều 37–40).
   - Chương IV: Quyền cầm giữ hàng hải (Maritime Liens - Điều 41–43): Thứ tự 5 bậc ưu tiên và thời hiệu 01 năm.
   - Chương X: Tai nạn hàng hải & Đâm va tàu thuyền (Điều 286–291): Phân bổ trách nhiệm bồi thường theo tỷ lệ lỗi.
   - Chương XI: Cứu hộ hàng hải (Điều 292–299): Nguyên tắc No Cure - No Pay và bồi hoàn đặc biệt SCOPIC.
   - Chương XII: Tổn thất chung (General Average - Điều 300–307): Hi sinh vì tổn thất chung và chi phí tổn thất chung.
2. **Pháp lệnh Thủ tục bắt giữ tàu biển 2008 (Pháp lệnh số 05/2008/PL-UBTVQH12)**:
   - Thẩm quyền bắt giữ tàu biển của Tòa án nhân dân cấp tỉnh (Điều 7).
   - Điều 11: 9 nhóm khiếu nại hàng hải làm căn cứ yêu cầu bắt giữ tàu biển.
   - Điều 14: Biện pháp bảo đảm tài chính bắt buộc của người nộp đơn (tối thiểu 15% giá trị khiếu nại để phòng ngừa bắt giữ tàu sai trái).
   - Điều 15: Thời hạn bắt giữ tàu biển tối đa 30 ngày.
   - Thả tàu biển khi nhận được bảo đảm thay thế (Thư bảo lãnh LOU từ P&I Club hoặc bảo lãnh ngân hàng).
3. **Quy tắc York-Antwerp 2016 (YAR 2016)**:
   - Quy tắc phân bổ tổn thất chung quốc tế giữa giá trị tàu biển, giá trị hàng hóa và tiền cước vận chuyển chịu rủi ro.
4. **Quy tắc quốc tế phòng ngừa đâm va tàu thuyền trên biển (COLREGS 1972)**:
   - Quy tắc 14 (Tình huống đối đầu), Quy tắc 15 (Tình huống cắt hướng), Quy tắc 19 (Tầm nhìn xa bị hạn chế).

---

## Tính năng Nghiệp vụ Cốt lõi

### 1. Đăng ký Tàu biển Quốc gia (Chương II)
- Quản lý số hiệu IMO chuẩn hóa quốc tế gồm 7 chữ số.
- Thẩm tra dung tích toàn phần (Gross Tonnage - GT) và trọng tải toàn phần (Deadweight - DWT).
- Phân loại chủng loại tàu: `CONTAINER`, `BULK_CARRIER`, `OIL_TANKER`, `CHEMICAL_GAS_CARRIER`, `GENERAL_CARGO`.

### 2. Thẩm tra Đơn Bắt Giữ Tàu Biển (Pháp lệnh 05/2008)
- Tiếp nhận yêu cầu bắt giữ tàu biển để bảo đảm giải quyết 9 nhóm khiếu nại hàng hải luật định (Khoản 1 Điều 11).
- Kiểm tra tính đầy đủ của biện pháp bảo đảm tài chính (Counter-Security): Tối thiểu 15% giá trị khiếu nại nộp tại Kho bạc Nhà nước hoặc bảo lãnh ngân hàng theo Điều 14.
- Quản lý lệnh bắt giữ, thời hạn tố tụng 30 ngày (Điều 15), và quy trình thả tàu biển khi có bảo lãnh P&I LOU.

### 3. Thẩm định Quyền Cầm Giữ Hàng Hải (Maritime Liens - Điều 41, 42)
- Xếp hạng thứ tự ưu tiên thanh toán 5 bậc luật định (ưu tiên thanh toán trước cả thế chấp tàu biển):
  1. Hạng 1: Tiền lương, chi phí hồi hương, tiền đóng BHXH của thuyền viên.
  2. Hạng 2: Bồi thường tính mạng, thương tích thuyền viên, hành khách.
  3. Hạng 3: Tiền công cứu hộ hàng hải.
  4. Hạng 4: Phí luồng lạch, hoa tiêu, cầu bến neo đậu cảng biển.
  5. Hạng 5: Tổn thất vật chất trực tiếp do đâm va hoặc tai nạn hàng hải.
- Kiểm tra thời hiệu tố tụng chặt chẽ: Tự động phát hiện khiếu nại hết thời hiệu 01 năm (365 ngày) theo Điều 42.

### 4. Phân định Trách nhiệm Đâm Va Tàu Thuyền (Điều 286–291)
- Áp dụng nguyên tắc chia lỗi theo tỷ lệ phần trăm dựa trên vi phạm COLREGS 1972.
- Tính toán trách nhiệm gánh chịu thiệt hại và số tiền bồi thường ròng giữa hai tàu (Net settlement calculation).

### 5. Phân bổ Tổn thất chung (General Average - YAR 2016 & Điều 300–307)
- Tổng hợp hi sinh vì tổn thất chung (GA Sacrifice) và chi phí tổn thất chung (GA Expenditure).
- Tính tỷ lệ đóng góp tổn thất chung (%) dựa trên tổng giá trị chịu phân bổ (Vessel + Cargo + Freight).
- Xác định nghĩa vụ đóng góp tổn thất chung chính xác cho Chủ tàu, Chủ hàng và Người vận chuyển.

---

## Hướng dẫn Sử dụng CLI (`mekong admiralty`)

```bash
# 1. Đăng ký tàu biển thương mại vào hệ thống
mekong admiralty vessel IMO9345678 "Mekong Star" --flag VIETNAM --gt 14200 --dwt 21000 --type CONTAINER --owner "Tổng công ty Hàng hải Việt Nam"

# 2. Nộp đơn yêu cầu bắt giữ tàu biển và thẩm tra bảo đảm tài chính 15%
mekong admiralty arrest IMO9345678 "Công ty Nhiên liệu Hàng hải Hải Phòng" --claim-type PORT_NAVIGATION_DUES --amount 150000 --counter-security 30000 --court "TAND TP Hải Phòng" --port "Khu bến cảng Lạch Huyện"

# 3. Thẩm định và xếp hạng quyền cầm giữ hàng hải (Maritime Liens)
mekong admiralty lien IMO9345678 "Thuyền bộ Tàu Mekong Star" --category CREW_WAGES --amount 50000 --incident-date 2026-03-01

# 4. Phân định trách nhiệm bồi thường do đâm va tàu thuyền
mekong admiralty collision IMO9345678 IMO9123456 "2026-07-15" --colregs "RULE_15_CROSSING_GIVE_WAY_FAILED" --fault-a 75.0 --damage-a 200000 --damage-b 600000

# 5. Phân bổ tổn thất chung (General Average) theo York-Antwerp Rules
mekong admiralty ga IMO9345678 "2026-08-10" --sacrifice 400000 --expenditure 200000 --vessel-val 15000000 --cargo-val 20000000 --freight-val 2500000

# 6. Tra cứu danh mục hồ sơ tư pháp hàng hải
mekong admiralty list --category ALL --limit 50

# 7. Xem báo cáo telemetry hoạt động tư pháp hàng hải quốc gia
mekong admiralty status
```

---

## Danh mục MCP Tools (`mekong-core`)

| MCP Tool | Mô tả Chức năng |
|---|---|
| `mekong_admiralty_vessel` | Đăng ký tàu biển thương mại vào Sổ đăng ký tàu biển quốc gia theo Chương II. |
| `mekong_admiralty_arrest` | Thẩm tra đơn yêu cầu bắt giữ tàu biển và ký quỹ bảo đảm tài chính $\ge 15\%$ (Điều 14 Pháp lệnh 05/2008). |
| `mekong_admiralty_lien` | Xác lập và xếp hạng 5 bậc ưu tiên quyền cầm giữ hàng hải và kiểm tra thời hiệu 01 năm (Điều 41-42). |
| `mekong_admiralty_collision` | Phân định trách nhiệm bồi thường đâm va tàu thuyền và tính số tiền thanh toán ròng (Điều 286-291). |
| `mekong_admiralty_ga` | Tính toán phân bổ tổn thất chung (General Average) theo Quy tắc York-Antwerp 2016 & Điều 300-307. |
| `mekong_admiralty_list` | Tra cứu danh mục tàu biển, lệnh bắt giữ, quyền cầm giữ và hồ sơ đâm va hàng hải. |
| `mekong_admiralty_status` | Tổng hợp chỉ số telemetry hoạt động tư pháp hàng hải, bắt giữ tàu biển và xử lý khiếu nại toàn quốc. |
