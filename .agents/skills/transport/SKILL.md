---
name: transport
description: Vietnamese Road Transport, Logistics, Highway Tolling & Electronic Toll Collection (ETC) Suite.
---

# 🚛 Transport — Vietnamese Road Transport, Logistics, Highway Tolling & ETC

Autonomous operations engine for Vietnamese commercial road transport, transport business licensing, vehicle badge issuance (*phù hiệu xe*), non-stop electronic toll collection (ETC/MLFF), journey monitoring devices (GPS blackbox & dashcam compliance), and vehicle gross weight overload auditing under the Law on Road Traffic 2008 (Law 23/2008/QH12), Law on Road Order and Safety 2024 (Law 36/2024/QH15), Law on Roads 2024 (Law 35/2024/QH15), Decree 10/2020/NĐ-CP, Decree 47/2022/NĐ-CP, Decree 41/2024/NĐ-CP, Decision 19/2020/QĐ-TTg, Decree 119/2024/NĐ-CP, Circular 12/2020/TT-BGTVT, Circular 46/2015/TT-BGTVT, Decree 100/2019/NĐ-CP, and Decree 123/2021/NĐ-CP.

## Statutory Legal Framework

1. **Luật Giao thông đường bộ & Luật Trật tự, an toàn giao thông đường bộ 2024 (Luật số 36/2024/QH15)**:
   - Quy định về điều kiện hoạt động của xe cơ giới tham gia giao thông đường bộ.
   - Kiểm soát thời gian lái xe của người điều khiển xe ô tô kinh doanh vận tải:
     * Thời gian lái xe liên tục không quá 4 giờ ($4.0\text{h}$) và phải nghỉ tối thiểu 15 phút.
     * Tổng thời gian lái xe trong một ngày không quá 10 giờ ($10.0\text{h}$).

2. **Kinh Doanh & Điều Kiện Kinh Doanh Vận Tải (Nghị định 10/2020/NĐ-CP & Nghị định 41/2024/NĐ-CP)**:
   - Cấp Giấy phép kinh doanh vận tải bằng xe ô tô (thời hạn 5 năm).
   - Thẩm định và cấp phù hiệu xe: `XE TUYẾN CỐ ĐỊNH`, `XE HỢP ĐỒNG`, `XE TAXI`, `XE BUÝT`, `XE TẢI`, `XE ĐẦU KÉO`, `XE SIÊU TRƯỜNG SIÊU TRỌNG`.
   - Niên hạn sử dụng phương tiện giao thông đường bộ:
     * Xe ô tô chở người (xe tuyến cố định, hợp đồng, xe buýt): Tối đa 20 năm (taxi tối đa 12 năm tại đô thị đặc biệt).
     * Xe ô tô tải chở hàng và xe đầu kéo container: Tối đa 25 năm.
   - Bắt buộc lắp thiết bị giám sát hành trình (GSHT) và camera truyền dữ liệu hình ảnh về Cục Đường bộ Việt Nam (đối với xe $\ge 9$ chỗ và xe đầu kéo kéo sơ mi rơ moóc).

3. **Thu Phí Điện Tử Không Dừng ETC & MLFF (Quyết định 19/2020/QĐ-TTg & Nghị định 119/2024/NĐ-CP)**:
   - Thẻ định danh RFID e-tag (VETC / ePass) dán trên kính hoặc đèn xe.
   - 5 nhóm phân loại phương tiện tính giá dịch vụ BOT (Thông tư 35/2016/TT-BGTVT):
     * **Class 1**: Xe dưới 12 chỗ, xe tải trọng dưới 2 tấn, xe buýt công cộng.
     * **Class 2**: Xe từ 12 đến 30 chỗ, xe tải từ 2 tấn đến dưới 4 tấn.
     * **Class 3**: Xe từ 31 chỗ trở lên, xe tải từ 4 tấn đến dưới 10 tấn.
     * **Class 4**: Xe tải từ 10 tấn đến dưới 18 tấn, xe chở container 20 feet.
     * **Class 5**: Xe tải từ 18 tấn trở lên, xe chở container 40 feet.

4. **Kiểm Soát Tải Trọng & Xử Phạt Quá Tải (Nghị định 100/2019/NĐ-CP & Nghị định 123/2021/NĐ-CP)**:
   - Tải trọng trục xe và tổng trọng lượng xe theo Thông tư 46/2015/TT-BGTVT.
   - Khung phạt quá tải:
     * $< 10\%$: Dung sai cho phép, không lập biên bản xử phạt.
     * $10\% \le P \le 20\%$: Phạt lái xe 4–6 triệu VND, chủ xe 4–8 triệu VND, bắt buộc hạ tải.
     * $20\% < P \le 50\%$: Phạt lái xe 13–15 triệu VND, tước GPLX 1–3 tháng, chủ xe 14–16 triệu VND.
     * $> 50\%$: Phạt lái xe 40–50 triệu VND, tước GPLX 3–5 tháng, chủ xe 28–32 triệu VND.

---

## CLI Usage

```bash
# Báo cáo telemetry tổng quan mạng lưới vận tải đường bộ
mekong transport status
mekong transport status --json

# Cấp Giấy phép kinh doanh vận tải bằng xe ô tô
mekong transport license "Công ty Cổ phần Xe Khách Phương Trang FUTA Bus Lines" "0303888999" --type PASSENGER_COACH_FIXED --fleet 500 --authority "Sở Giao thông Vận tải TP.HCM" --json

# Thẩm định niên hạn, thiết bị GSHT/Camera và cấp phù hiệu xe
mekong transport badge "51B-299.88" GPKD-PAS-889900 --type PASSENGER_COACH_FIXED --year 2022 --capacity 45.0 --gps --camera --json

# Xử lý giao dịch thu phí đường bộ tự động không dừng (ETC/MLFF)
mekong transport etc "30E-123.45" "E-TAG-VETC-998877" --station "Trạm BOT Pháp Vân - Cầu Giẽ" --class CLASS_1 --provider VETC --balance 500000 --json

# Giám sát hành trình lái xe (kiểm tra liên tục <= 4h và trong ngày <= 10h)
mekong transport gps "51B-299.88" "Nguyễn Văn Hùng" "GPLX-D-798822" --continuous 3.5 --daily 8.0 --rest 20 --camera --gps --json

# Cân tải trọng phương tiện và tính mức xử phạt vi phạm quá tải
mekong transport weight "50H-888.99" --config ARTICULATED_5AXLE --weight 46.5 --json

# Tra cứu dữ liệu giấy phép, phù hiệu xe, giao dịch ETC, biên bản cân tải trọng
mekong transport list licenses --limit 50 --json
mekong transport list badges --json
mekong transport list etc --json
mekong transport list weights --json
```
