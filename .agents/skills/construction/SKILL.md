---
name: construction
description: Vietnamese Construction Law 2020, Building Permits, FIDIC Contracts & QCVN 06:2022 Fire Safety.
---

# 🏗️ Construction — Vietnamese Construction Law 2020, Building Permits, FIDIC Contracts & QCVN 06:2022 Fire Safety

Autonomous operations engine for Vietnamese civil, industrial and infrastructure construction engineering, building permit appraisals under amended Article 89 Law on Construction, international FIDIC contract administration (Decree 37/2015/NĐ-CP & Decree 50/2021/NĐ-CP), national technical regulation QCVN 06:2022/BXD fire safety audits, and project quality acceptance for commercial commissioning (Decree 06/2021/NĐ-CP).

## Statutory Legal Framework

1. **Luật Xây dựng 2014 & Luật số 62/2020/QH14 (Sửa đổi, bổ sung một số điều của Luật Xây dựng)**:
   - **Phân cấp công trình xây dựng** (Nghị định 06/2021/NĐ-CP & Thông tư 06/2021/TT-BXD):
     - **Cấp Đặc biệt**: Chiều cao $\ge 200\text{ m}$, vượt nhịp $\ge 100\text{ m}$, hoặc tổng mức đầu tư $\ge 10.000\text{ tỷ VND}$ (Bộ Xây dựng quản lý).
     - **Cấp I**: Chiều cao $75 - 200\text{ m}$, số tầng nổi $25 - 50$ tầng, GFA $\ge 30.000\text{ m}^2$ (Sở Xây dựng cấp tỉnh quản lý).
     - **Cấp II**: Chiều cao $28 - 75\text{ m}$, số tầng nổi $8 - 24$ tầng, GFA $\ge 10.000\text{ m}^2$.
     - **Cấp III**: Chiều cao $6 - 28\text{ m}$, số tầng nổi $2 - 7$ tầng (UBND Quận/Huyện quản lý).
     - **Cấp IV**: Công trình 1 tầng, kết cấu đơn giản, nhà tạm.
   - **Thẩm định cấp phép xây dựng & Miễn GPXD theo Điều 89**:
     - *Khoản 2a*: Công trình bí mật nhà nước, an ninh quốc phòng khẩn cấp.
     - *Khoản 2d*: Công trình thuộc dự án đầu tư xây dựng trong Khu công nghiệp, khu chế xuất đã có quy hoạch chi tiết 1/500 được duyệt.
     - *Khoản 2h*: Nhà ở riêng lẻ tại nông thôn dưới 7 tầng không thuộc quy hoạch đô thị.
     - Các công trình không thuộc diện miễn trừ bắt buộc phải có Giấy phép Xây dựng và nghiệm thu PCCC trước khi khởi công.

2. **Hợp đồng Xây dựng Quốc tế FIDIC & Nghị định 37/2015/NĐ-CP, Nghị định 50/2021/NĐ-CP**:
   - **FIDIC Red Book (Conditions of Contract for Construction)**: Chủ đầu tư chịu trách nhiệm thiết kế, thanh toán theo đo đạc khối lượng thực tế (BOQ). Tạm ứng chuẩn 10%, bảo lãnh thực hiện hợp đồng 5%, giữ lại bảo hành 5%.
   - **FIDIC Yellow Book (Plant and Design-Build)**: Nhà thầu thiết kế và thi công chìa khóa trao tay một phần, thanh toán trọn gói theo mốc tiến độ (Milestones). Tạm ứng chuẩn 15%, bảo lãnh hợp đồng 10%, giữ lại 5%.
   - **FIDIC Silver Book (EPC / Turnkey Projects)**: Tổng thầu EPC chịu toàn bộ rủi ro thiết kế, thi công, công nghệ và giá cố định. Tạm ứng chuẩn 20%, bảo lãnh hợp đồng 10%, giữ lại 5%.
   - Khống chế trần phạt vi phạm tiến độ (Liquidated Damages) theo Nghị định 37/2015 tối đa không quá 12% giá trị hợp đồng.

3. **Quy chuẩn Kỹ thuật Quốc gia QCVN 06:2022/BXD & Sửa đổi 1:2023/BXD về An toàn Cháy**:
   - Quy định bậc chịu lửa công trình (Bậc I đến V):
     - **Bậc I**: Cột chịu lực REI 150 phút, sàn ngăn cháy REI 90 phút, khoảng cách thoát nạn tối đa 40 mét.
     - **Bậc II**: Cột chịu lực REI 120 phút, sàn ngăn cháy REI 60 phút, khoảng cách thoát nạn tối đa 35 mét.
     - **Bậc III**: Cột chịu lực REI 90 phút, sàn ngăn cháy REI 45 phút, khoảng cách thoát nạn tối đa 30 mét.
   - Nghiệm thu thẩm duyệt PCCC là điều kiện tiên quyết để nghiệm thu hoàn thành công trình đưa vào sử dụng.

4. **Nghiệm thu Chất lượng & Đưa Công trình vào Sử dụng (Nghị định 06/2021/NĐ-CP)**:
   - Nghiệm thu từng giai đoạn (Móng, Kết cấu, Hoàn thiện, Bàn giao tổng thể).
   - Yêu cầu kiểm tra an toàn kết cấu đạt $\ge 90.0\%$ và tuân thủ tuyệt đối hồ sơ bản vẽ hoàn công (as-built drawings).

---

## Typer CLI Commands

```bash
# 1. Bảng điều khiển tổng quan dự án xây dựng & thẩm định
mekong construction
mekong construction --json

# 2. Đăng ký dự án xây dựng & xác định cấp công trình
mekong construction project "Tòa tháp Tài chính Landmark Saigon" --type CIVIL_COMMERCIAL --investment 3500000000000 --area 85000 --height 180 --floors 45 --province "TP. Hồ Chí Minh"

# 3. Thẩm định cấp phép xây dựng & miễn trừ GPXD Điều 89
mekong construction permit "PRJ-9876ABCD" --industrial-park
mekong construction permit "PRJ-9876ABCD" --pccc-approved

# 4. Thiết lập hợp đồng FIDIC & điều khoản bảo lãnh tài chính
mekong construction fidic "PRJ-9876ABCD" "Gói thầu Tổng thầu EPC Cơ điện & Xây dựng" --type FIDIC_YELLOW_BOOK --employer "Vinhomes JSC" --contractor "Coteccons" --value 250000000000

# 5. Thẩm duyệt an toàn Phòng cháy chữa cháy theo QCVN 06:2022
mekong construction pccc "PRJ-9876ABCD" --tier TIER_I --column-rei 150 --floor-rei 90 --evac-dist 32.5

# 6. Nghiệm thu hoàn thành đưa vào sử dụng
mekong construction accept "PRJ-9876ABCD" --stage FINAL_COMMISSIONING --inspector "Apave Vietnam" --soundness 99.0 --as-built

# 7. Tra cứu danh mục
mekong construction list projects
mekong construction list permits
mekong construction list fidic
mekong construction list pccc
mekong construction list acceptances
mekong construction status
```

---

## FastMCP & JSON-RPC 2.0 Tools

- `mekong_construction_project`: Đăng ký dự án & phân cấp công trình xây dựng theo NĐ 06/2021.
- `mekong_construction_permit`: Thẩm định cấp phép và miễn GPXD theo Điều 89 Luật Xây dựng 2020.
- `mekong_construction_fidic`: Thiết lập hợp đồng FIDIC Red/Yellow/Silver và cơ cấu tài chính tạm ứng, bảo lãnh.
- `mekong_construction_pccc`: Thẩm duyệt an toàn PCCC theo chuẩn QCVN 06:2022/BXD.
- `mekong_construction_accept`: Nghiệm thu chất lượng công trình theo NĐ 06/2021/NĐ-CP.
- `mekong_construction_list`: Tra cứu danh mục dự án, giấy phép, FIDIC, PCCC và nghiệm thu.
- `mekong_construction_status`: Lấy chỉ số tổng hợp toàn bộ hệ thống quản lý xây dựng.
