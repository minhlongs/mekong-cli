---
name: guardianship
description: Vietnamese Guardianship, Custodianship & Ward Protection Suite.
---

# 🛡️ Guardianship — Vietnamese Guardianship, Custodianship & Ward Protection Engine

Autonomous compliance and legal operations engine for Vietnamese guardianship registration, custodianship, ward protection, property management, and civil status registration under the **Civil Code 2015 (Luật Dân sự 2015 - Luật số 91/2015/QH13, Điều 46–63)**, **Law on Civil Status 2014 (Luật Hộ tịch 2014, Điều 19–21 & 39–41)**, **Decree No. 126/2014/NĐ-CP**, and **Decree No. 82/2020/NĐ-CP**.

## Statutory Legal Framework

1. **Bộ luật Dân sự 2015 (Chương III Mục 4: Giám hộ, Điều 46–63)**:
   - **Người được giám hộ (Điều 47)**:
     - Người chưa thành niên mồ côi cả cha và mẹ, không xác định được cha mẹ, hoặc cha mẹ mất năng lực hành vi dân sự, bị hạn chế quyền cha mẹ.
     - Người mất năng lực hành vi dân sự.
     - Người có khó khăn trong nhận thức, làm chủ hành vi.
   - **Điều kiện của cá nhân làm người giám hộ (Điều 48)**:
     - Có năng lực hành vi dân sự đầy đủ (từ đủ 18 tuổi).
     - Có tư cách đạo đức tốt và các điều kiện cần thiết để thực hiện quyền, nghĩa vụ.
     - Không phải là người đang bị truy cứu trách nhiệm hình sự hoặc người bị kết án nhưng chưa được xóa án tích về một trong các tội cố ý xâm phạm tính mạng, sức khỏe, danh dự, nhân phẩm, tài sản của người khác.
     - Không phải là người bị Tòa án tuyên bố hạn chế quyền đối với con chưa thành niên.
   - **Người giám sát việc giám hộ (Điều 51)**:
     - Người thân thích của người được giám hộ hoặc do UBND cấp xã cử / Tòa án chỉ định.
     - Đăng ký giám sát tại UBND cấp xã nơi đăng ký việc giám hộ.
     - Theo dõi, kiểm tra người giám hộ trong việc thực hiện giám hộ; xem xét, đồng ý bằng văn bản đối với các giao dịch dân sự có giá trị lớn liên quan đến tài sản của người được giám hộ.
   - **Thứ tự người giám hộ đương nhiên (Điều 52 & 53)**:
     - Đối với người chưa thành niên (Điều 52): Anh ruột là anh cả hoặc chị ruột là chị cả $\to$ Ông nội, bà nội, ông ngoại, bà ngoại $\to$ Bác ruột, chú ruột, cậu ruột, cô ruột, dì ruột.
     - Đối với người mất năng lực hành vi dân sự (Điều 53): Vợ / chồng $\to$ Cha, mẹ $\to$ Con cả (hoặc con tiếp theo thành niên).
   - **Quản lý tài sản của người được giám hộ (Điều 59)**:
     - Trong thời hạn **10 ngày** kể từ ngày cử, chỉ định hoặc phát sinh giám hộ, người giám hộ phải cùng người giám sát kiểm kê tài sản.
     - Giao dịch dân sự có giá trị lớn phải có sự đồng ý của người giám sát việc giám hộ.
     - **Nghiêm cấm tặng cho tài sản**: *"Không được đem tài sản của người được giám hộ tặng cho người khác"* (Điều 59 khoản 3).
   - **Chấm dứt việc giám hộ & Chuyển giao tài sản (Điều 62 & 63)**:
     - Chấm dứt khi: người được giám hộ đã thành niên, khôi phục năng lực hành vi, chết, cha mẹ đã có đủ điều kiện, hoặc được nhận làm con nuôi.
     - Trong thời hạn **03 tháng** kể từ ngày chấm dứt việc giám hộ, người giám hộ thanh toán tài sản và chuyển giao cho người được giám hộ hoặc người thừa kế với sự chứng kiến của người giám sát.

2. **Luật Hộ tịch 2014 (Điều 19–21 & 39–41)**:
   - Đăng ký giám hộ đương nhiên và giám hộ cử tại UBND cấp xã nơi cư trú của người được giám hộ hoặc người giám hộ.
   - Cấp Giấy xác nhận đăng ký giám hộ (`CERT-GH-YYYY-XXXX`).

---

## CLI Usage

```bash
# Bảng điều hành giám sát & bảo vệ người được giám hộ toàn quốc
mekong guardianship status
mekong guardianship status --json

# Đăng ký giám hộ tại UBND cấp xã với kiểm tra điều kiện Điều 48 BLDS 2015
mekong guardianship register "Lê Hoàng Nam" 2012-04-15 079212009988 "Lê Tuấn Hùng" 1998-02-20 079098001122 \
  --ward-address "12 Hai Bà Trưng, Quận 1, TP.HCM" \
  --guardian-address "12 Hai Bà Trưng, Quận 1, TP.HCM" \
  --category MINOR_NO_PARENTS \
  --relationship ELDER_SIBLING \
  --type NATURAL \
  --commune-ubnd "UBND Phường Bến Nghé" --json

# Đăng ký người giám sát việc giám hộ theo quy định tại Điều 51 BLDS 2015
mekong guardianship supervisor GH-XXXX "Lê Văn Đức" 079075003344 \
  --dob 1975-08-10 --address "45 Lê Duẩn, Quận 1, TP.HCM" \
  --relationship CLOSE_RELATIVE --authority "UBND Phường Bến Nghé" --json

# Kiểm kê tài sản của người được giám hộ trong thời hạn 10 ngày (Điều 59.1 BLDS 2015)
mekong guardianship inventory GH-XXXX "Nhà đất 85m2 mặt tiền Hai Bà Trưng" REAL_ESTATE 12000000000 \
  --identifier "GCN-Q1-2026-0012" --is-verified --json

# Thực hiện giao dịch tài sản có kiểm soát bảo vệ và đồng ý của người giám sát (Điều 59.2)
mekong guardianship transact GH-XXXX EXPENSE_CARE 15000000 "Chi phí sinh hoạt và dinh dưỡng hàng tháng cho người được giám hộ" --json
mekong guardianship transact GH-XXXX SALE 12000000000 "Chuyển nhượng nhà đất để chữa bệnh hiểm nghèo" \
  --asset-id AST-XXXX --major --supervisor-consent --json

# Chấm dứt giám hộ và kích hoạt thời hạn 3 tháng chuyển giao tài sản (Điều 62 & 63 BLDS 2015)
mekong guardianship terminate GH-XXXX WARD_ATTAINED_MAJORITY \
  --handover-notes "Người được giám hộ đã đủ 18 tuổi, bàn giao toàn bộ tài sản có người giám sát chứng kiến" --json

# Tra cứu và liệt kê hồ sơ giám hộ
mekong guardianship search "Lê Hoàng Nam" --json
mekong guardianship list --category MINOR_NO_PARENTS --limit 20
```

---

## MCP Tools Integration

Mekong Guardianship exposes 7 native MCP tools with full FastMCP & JSON-RPC parity:
- `mekong_guardianship_register`: Đăng ký giám hộ với kiểm tra năng lực và điều kiện loại trừ.
- `mekong_guardianship_supervisor`: Đăng ký người giám sát việc giám hộ theo Điều 51 BLDS 2015.
- `mekong_guardianship_inventory`: Kiểm kê tài sản người được giám hộ trong hạn 10 ngày.
- `mekong_guardianship_transact`: Thực hiện giao dịch tài sản có xác thực đồng ý của người giám sát và cấm tặng cho.
- `mekong_guardianship_terminate`: Chấm dứt việc giám hộ và thiết lập thời hạn thanh toán, chuyển giao 3 tháng.
- `mekong_guardianship_search`: Tìm kiếm thông tin hồ sơ giám hộ, người giám hộ và người được giám hộ.
- `mekong_guardianship_status`: Thống kê telemetry giám hộ, giám sát và tài sản quản lý.
