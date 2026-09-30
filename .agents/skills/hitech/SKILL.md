---
name: hitech
description: Vietnamese High-Tech Enterprise, Science & Technology Parks & Tech Transfer Compliance Suite.
---

# mekong hitech — Autonomous Vietnamese High-Tech Enterprise, Science & Technology Parks & Tech Transfer Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Công nghệ cao 2008 (Luật số 21/2008/QH12)**:
   - Thống nhất cơ chế chính sách ưu đãi, hỗ trợ phát triển công nghệ cao, sản phẩm công nghệ cao và ươm tạo doanh nghiệp công nghệ cao.
   - Thẩm quyền quản lý: **Bộ Khoa học và Công nghệ (Bộ KH&CN)**, Ban Quản lý Khu công nghệ cao.
   - Tiêu chí công nhận Doanh nghiệp Công nghệ cao (Doanh nghiệp CNC) theo **Quyết định số 10/2021/QĐ-TTg**:
     * Tỷ lệ doanh thu từ sản phẩm công nghệ cao đạt tối thiểu **70%** tổng doanh thu thuần hàng năm.
     * Tỷ lệ chi tiêu nghiên cứu & phát triển (R&D) tại Việt Nam: Tối thiểu **2.0%** (doanh nghiệp siêu nhỏ/nhỏ), **1.0%** (doanh nghiệp vừa/lớn), hoặc **0.5%** (doanh nghiệp quy mô lớn/FDI đặc biệt).
     * Tỷ lệ lao động có trình độ cao đẳng trở lên trực tiếp làm R&D: Tối thiểu **5.0%** (hoặc **2.5%** với doanh nghiệp quy mô lớn).
     * Bắt buộc có Giấy chứng nhận hệ thống quản lý chất lượng đạt tiêu chuẩn **ISO 9001** hoặc tương đương.
2. **Ưu đãi thuế Thu nhập doanh nghiệp (TNDN / CIT) theo Luật Thuế TNDN & Luật Công nghệ cao**:
   - Thuế suất ưu đãi **10%** trong thời hạn **15 năm**.
   - **Miễn thuế 4 năm** đầu kể từ khi có thu nhập chịu thuế.
   - **Giảm 50% số thuế phải nộp trong 9 năm** tiếp theo (thuế suất thực tế 5%).
   - Miễn thuế nhập khẩu đối với hàng hóa tạo tài sản cố định, nguyên liệu, vật tư phục vụ R&D.
3. **Luật Chuyển giao công nghệ 2017 (Luật số 07/2017/QH14)**:
   - Phân loại công nghệ: Khuyến khích chuyển giao, Hạn chế chuyển giao, và **Cấm chuyển giao**.
   - **Đăng ký bắt buộc hợp đồng chuyển giao công nghệ (Điều 31)**:
     * Chuyển giao công nghệ từ nước ngoài vào Việt Nam (Inward Foreign).
     * Chuyển giao công nghệ từ Việt Nam ra nước ngoài (Outward Foreign).
     * Chuyển giao công nghệ trong nước có sử dụng vốn nhà nước hoặc ngân sách nhà nước.
   - Nghị định số 76/2018/NĐ-CP: Hướng dẫn chi tiết thẩm định giá công nghệ và giám định công nghệ dự án đầu tư.
   - Nghị định số 51/2019/NĐ-CP: Xử phạt hành chính từ 30.000.000 đến 50.000.000 VND đối với hành vi không đăng ký hợp đồng chuyển giao công nghệ bắt buộc; phạt từ 80.000.000 đến 100.000.000 VND và tịch thu phương tiện đối với chuyển giao công nghệ cấm.
4. **Nghị định số 10/2024/NĐ-CP (Khu công nghệ cao)**:
   - Quy định về thành lập, mở rộng và hoạt động của Khu công nghệ cao quốc gia (Hòa Lạc, TP.HCM - SHTP, Đà Nẵng).
   - Tiêu chuẩn tiếp nhận dự án đầu tư:
     * Suất vốn đầu tư tối thiểu: $\ge 100$ tỷ VND/ha (hoặc $\ge 4$ triệu USD/ha).
     * Cam kết lộ trình chuyển giao công nghệ, đào tạo nhân lực công nghệ cao và liên kết nghiên cứu với các trường đại học, viện nghiên cứu Việt Nam.
5. **Lưu trữ SQLite WAL**: Bảng `hitech_enterprises`, `tech_transfer_contracts`, `hitech_park_projects`, `tax_incentive_evaluations` tại `.mekong/hitech.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan doanh nghiệp CNC, hợp đồng chuyển giao công nghệ và KCNC
mekong hitech

# Thẩm định điều kiện cấp Giấy chứng nhận Doanh nghiệp Công nghệ cao (QĐ 10/2021/QĐ-TTg)
mekong hitech enterprise "Công ty CP Bán dẫn Viễn thông Mekong" --rev 200000000000 --hitech-rev 160000000000 --rd 5000000000 --employees 300 --rd-employees 25 --scale MEDIUM --iso

# Đăng ký hợp đồng chuyển giao công nghệ (Điều 31 Luật Chuyển giao công nghệ 2017)
mekong hitech transfer "Chuyển giao thiết kế chip AI Mekong 4nm" --transferor "Tokyo Semi Corp" --transferee "Mekong Tech JSC" --tech "Quy trình quang khắc EUV 4nm" --direction INWARD_FOREIGN --value 1200000 --category ENCOURAGED

# Thẩm định dự án đầu tư vào Khu công nghệ cao quốc gia (Nghị định 10/2024/NĐ-CP)
mekong hitech park "Nhà máy vi cơ điện tử Mekong MEMS" --park "Khu Công Nghệ Cao TP. Hồ Chí Minh (SHTP)" --area 4.0 --capital 500000000000 --export 85.0 --tech-transfer

# Tính toán số thuế TNDN tiết kiệm theo gói ưu đãi công nghệ cao (10% trong 15 năm, miễn 4, giảm 9)
mekong hitech tax "Công ty CP Bán dẫn Viễn thông Mekong" --profit 80000000000 --year 3 --hitech

# Tra cứu danh mục hồ sơ và dự án
mekong hitech list enterprises
mekong hitech list contracts
mekong hitech list parks
mekong hitech list taxes

# Giám sát trạng thái và xuất JSON headless
mekong hitech status --json
```

---

## MCP Tools Integration
- `mekong_hitech_audit`: Thẩm định tiêu chuẩn Doanh nghiệp Công nghệ cao theo Quyết định 10/2021/QĐ-TTg.
- `mekong_hitech_transfer`: Đăng ký hợp đồng chuyển giao công nghệ theo Điều 31 Luật Chuyển giao công nghệ 2017.
- `mekong_hitech_park`: Thẩm định dự án đầu tư vào Khu công nghệ cao theo Nghị định 10/2024/NĐ-CP.
- `mekong_hitech_tax`: Tính toán ưu đãi miễn, giảm thuế TNDN (10% trong 15 năm, miễn 4 giảm 9).
- `mekong_hitech_list`: Tra cứu danh mục doanh nghiệp, hợp đồng, dự án KCNC và tính thuế.
- `mekong_hitech_status`: Báo cáo chỉ số telemetry tổng hợp hệ sinh thái công nghệ cao.
