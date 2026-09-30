---
name: pubinvestment
description: Vietnamese Public Investment, Capital Allocation, Feasibility & Medium-Term Planning Suite.
---

# mekong pubinvestment — Autonomous Vietnamese Public Investment & Capital Allocation Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Đầu tư công 2019 (Luật số 39/2019/QH14, sửa đổi bổ sung Luật số 03/2022/QH15 và Luật số 29/2023/QH15)**:
   - Thống nhất quản lý nhà nước về đầu tư công; quản lý và sử dụng vốn đầu tư công; quyền, nghĩa vụ và trách nhiệm của cơ quan, tổ chức, cá nhân liên quan.
   - **Phân loại dự án đầu tư công (Điều 6 - 10)**:
     * *Dự án quan trọng quốc gia (Điều 7)*: Tổng mức đầu tư $\ge 10.000\text{ tỷ VND}$ hoặc di dân tái định cư $\ge 20.000$ người; do Quốc hội quyết định chủ trương đầu tư.
     * *Dự án nhóm A (Điều 8)*: Giao thông, năng lượng, công nghiệp $\ge 2.300\text{ tỷ VND}$; nông nghiệp, thủy lợi, hạ tầng đô thị $\ge 1.500\text{ tỷ VND}$; y tế, giáo dục $\ge 1.000\text{ tỷ VND}$; do Thủ tướng Chính phủ quyết định chủ trương đầu tư.
     * *Dự án nhóm B (Điều 9)*: Giao thông $120\text{ tỷ} \le V < 2.300\text{ tỷ VND}$; nông nghiệp $80\text{ tỷ} \le V < 1.500\text{ tỷ VND}$; y tế, giáo dục $60\text{ tỷ} \le V < 1.000\text{ tỷ VND}$; do HĐND cấp tỉnh hoặc Bộ trưởng quyết định chủ trương đầu tư.
     * *Dự án nhóm C (Điều 10)*: Dưới ngưỡng quy định của Nhóm B; thẩm quyền quyết định phân cấp theo luật định.
2. **Kế hoạch đầu tư công trung hạn & hằng năm (Điều 48 - 65)**:
   - Kế hoạch đầu tư công trung hạn 05 năm (MTPIP) phù hợp kế hoạch phát triển KTXH 5 năm.
   - **Thứ tự ưu tiên phân bổ vốn (Điều 51)**:
     * Hạng 1: Thu hồi các khoản vốn ứng trước.
     * Hạng 2: Thanh toán toàn bộ nợ đọng xây dựng cơ bản.
     * Hạng 3: Bố trí vốn đối ứng cho dự án sử dụng vốn ODA và vốn vay ưu đãi.
     * Hạng 4: Dự án chuyển tiếp hoàn thành trong kỳ kế hoạch.
     * Hạng 5: Dự án khởi công mới đáp ứng đủ điều kiện theo luật định.
3. **Thanh toán & Giải ngân vốn đầu tư công (Nghị định số 99/2021/NĐ-CP)**:
   - Thủ tục kiểm soát thanh toán vốn qua hệ thống Kho bạc Nhà nước (KBNN).
   - Đảm bảo giải ngân đúng khối lượng hoàn thành, đúng niên độ ngân sách, tránh thất thoát lãng phí.
4. **Giám sát đánh giá đầu tư & Tháo gỡ điểm nghẽn (Nghị định số 40/2020/NĐ-CP & Thông tư 12/2022/TT-BKHĐT)**:
   - Theo dõi tốc độ giải ngân thực tế (Disbursement Rate).
   - Kiểm soát và xử lý các điểm nghẽn trọng yếu: Giải phóng mặt bằng (GPMB), thủ tục đấu thầu, biến động giá nguyên vật liệu, thủ tục nhà tài trợ ODA.
5. **Lưu trữ SQLite WAL**: Bảng `investment_projects`, `capital_plans`, `disbursement_records`, `bottleneck_assessments` tại `~/.mekong/pubinvestment.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động quản lý đầu tư công, kế hoạch vốn & tỷ lệ giải ngân KBNN
mekong pubinvestment

# Đăng ký dự án đầu tư công và xác định phân nhóm (QTQG, Nhóm A, B, C)
mekong pubinvestment project --code "PRJ-EXPRESSWAY-01" --name "Dự án Xây dựng Tuyến Cao tốc Bắc - Nam đoạn Cần Thơ - Cà Mau" --sector "TRANSPORT_ENERGY_INDUSTRY" --capital 27500000000000 --source "CENTRAL_BUDGET" --agency "Ban Quản lý Dự án Mỹ Thuận - Bộ GTVT" --location "Đồng bằng sông Cửu Long" --start 2026 --end 2029 --resettlement 3500

# Tra cứu nhanh phân loại dự án và thẩm quyền phê duyệt
mekong pubinvestment classify --sector "AGRICULTURE_IRRIGATION_URBAN" --capital 1850000000000

# Giao kế hoạch vốn hằng năm theo thứ tự ưu tiên Điều 51
mekong pubinvestment plan "PRJ-XXXXXXXX" --type ANNUAL --year 2026 --capital 6500000000000 --approver "Thủ tướng Chính phủ" --decision "Quyết định số 1600/QĐ-TTg" --priority 4

# Ghi nhận chứng từ giải ngân vốn qua Kho bạc Nhà nước
mekong pubinvestment disburse "PRJ-XXXXXXXX" --amount 1250000000000 --year 2026 --treasury "Kho bạc Nhà nước Cần Thơ" --voucher "GCT-2026-0881" --contractor "Tổng công ty Xây dựng Trường Sơn" --notes "Nghiệm thu thanh toán khối lượng thi công gói thầu XL-01 đợt 3"

# Đánh giá điểm nghẽn tiến độ dự án (GPMB, mỏ vật liệu, đấu thầu)
mekong pubinvestment bottleneck "PRJ-XXXXXXXX" --type "LAND_CLEARANCE" --severity "HIGH" --delay 4 --measures "Thành lập tổ công tác đặc biệt phối hợp chính quyền địa phương chi trả tiền đền bù" --party "Trung tâm Phát triển Quỹ đất Tỉnh"

# Tra cứu dữ liệu đầu tư công
mekong pubinvestment list --type all --limit 20
mekong pubinvestment list --type projects
mekong pubinvestment list --type plans
mekong pubinvestment list --type disbursements

# Trích xuất dữ liệu máy học / CI
mekong pubinvestment --json
mekong pubinvestment status --json
```

---

## MCP Tools Integration
- `mekong_pubinvestment_project`: Đăng ký dự án đầu tư công và phân nhóm theo tiêu chí luật định.
- `mekong_pubinvestment_classify`: Đánh giá thẩm quyền quyết định chủ trương đầu tư và phê duyệt dự án.
- `mekong_pubinvestment_plan`: Giao kế hoạch vốn đầu tư công trung hạn hoặc hằng năm.
- `mekong_pubinvestment_disburse`: Ghi nhận thanh toán giải ngân vốn Kho bạc Nhà nước.
- `mekong_pubinvestment_bottleneck`: Ghi nhận và phân tích điểm nghẽn tiến độ dự án.
- `mekong_pubinvestment_list`: Liệt kê danh sách dự án, kế hoạch vốn và đợt giải ngân.
- `mekong_pubinvestment_status`: Kiểm tra chỉ số telemetry đầu tư công và tốc độ giải ngân vốn toàn quốc.
