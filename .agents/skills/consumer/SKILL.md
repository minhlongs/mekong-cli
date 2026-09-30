---
name: consumer
description: Vietnamese Consumer Rights Protection, Digital Platform Transparency & Product Recall Suite.
---

# mekong consumer — Autonomous Vietnamese Consumer Rights Protection, Digital Platform Transparency & Product Recall Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Bảo vệ quyền lợi người tiêu dùng 2023 (Luật số 19/2023/QH15, có hiệu lực từ 01/07/2024)**:
   - Thống nhất nguyên tắc bảo vệ quyền lợi người tiêu dùng, trách nhiệm của tổ chức, cá nhân kinh doanh đối với người tiêu dùng trong các giao dịch truyền thống và giao dịch trên không gian mạng.
   - Cơ quan quản lý nhà nước chuyên ngành: **Ủy ban Cạnh tranh Quốc gia (Bộ Công Thương)** và Ủy ban nhân dân các cấp, phối hợp cùng **Hội Bảo vệ quyền lợi người tiêu dùng Việt Nam (VICOPRO)**.
2. **Giao dịch từ xa & Nền tảng số (Điều 37-40 Luật BVQLNTD 2023)**:
   - Bắt buộc các nền tảng số lớn, sàn thương mại điện tử, mạng xã hội bán hàng:
     * Công khai thông tin tổ chức, quy chế hoạt động, chính sách đổi trả/hoàn tiền tối thiểu $\ge 7\text{ ngày}$.
     * Cung cấp tùy chọn minh bạch cho phép người tiêu dùng tắt tính năng gợi ý hành vi, quảng cáo mục tiêu (Targeted Advertising).
     * Nghiêm cấm các giao diện thao túng tâm lý (Dark patterns): tự động tick chọn mua thêm hàng, ép buộc cài đặt phần mềm ngoài ý muốn.
     * Xác minh danh tính $100\%$ người bán hàng trên các nền tảng thương mại điện tử trung gian.
3. **Kiểm soát Hợp đồng theo mẫu & Điều kiện giao dịch chung (Điều 23-28)**:
   - Quyết định số 07/2024/QĐ-TTg của Thủ tướng Chính phủ ban hành Danh mục hàng hóa, dịch vụ thiết yếu phải đăng ký hợp đồng theo mẫu (Điện lực, nước sạch, viễn thông, chung cư, bảo hiểm, ngân hàng, vận chuyển hành khách hàng không).
   - Vô hiệu hóa tuyệt đối các điều khoản bất công (Điều 25): Điều khoản loại trừ trách nhiệm bồi thường của bên bán, điều khoản hạn chế quyền khiếu nại khởi kiện ra Tòa án, điều khoản cho phép đơn phương tăng giá mà không thỏa thuận trước.
4. **Quy trình Thu hồi Sản phẩm có Khuyết tật (Product Recall - Điều 32-34)**:
   - **Khuyết tật Nhóm A** (có nguy cơ gây thiệt hại cho tính mạng, sức khỏe con người): Bắt buộc công bố công khai trên thông tin đại chúng trong vòng $24\text{ giờ}$ và áp dụng mọi biện pháp khẩn cấp thu hồi, tiêu hủy hoặc sửa chữa.
   - **Khuyết tật Nhóm B** (khuyết tật thông thường không đe dọa tính mạng): Triển khai thu hồi và báo cáo tiến độ theo luật định.
   - Báo cáo định kỳ kết quả thu hồi tới Bộ Công Thương và cơ quan chuyên môn.
5. **Giải quyết Tranh chấp Người tiêu dùng & Thủ tục rút gọn (Điều 70-71)**:
   - Áp dụng **Thủ tục rút gọn tại Tòa án nhân dân** đối với các vụ án bảo vệ quyền lợi người tiêu dùng có giá trị giao dịch dưới $\le 100.000.000\text{ VND}$ (Điều 70).
   - **Miễn nộp tiền tạm ứng án phí, lệ phí Tòa án** cho người tiêu dùng khi nộp đơn khởi kiện bảo vệ quyền lợi hợp pháp (Khoản 1 Điều 71).
6. **Lưu trữ SQLite WAL**: Bảng `platform_compliance_audits`, `standard_contract_reviews`, `defective_product_recalls`, `consumer_dispute_cases` tại `.mekong/consumer.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan công tác bảo vệ quyền lợi người tiêu dùng và nền tảng số
mekong consumer

# Thẩm định tính tuân thủ của nền tảng số và sàn TMĐT (Điều 37-40 Luật BVQLNTD 2023)
mekong consumer platform "Shopee Vietnam" --type E_COMMERCE_MARKETPLACE --algo --no-dark --dispute --return-days 15 --verify-rate 100.0

# Rà soát hợp đồng theo mẫu và điều kiện giao dịch chung (Điều 25)
mekong consumer contract "Hợp đồng Cung cấp Dịch vụ Viễn thông Di động" --industry TELECOM --ncc --no-exclude-liability --no-restrict-dispute --no-unilateral-price

# Quản lý và giám sát chương trình thu hồi sản phẩm khuyết tật (Điều 32-34)
mekong consumer recall "Xe máy điện Pin Lithium X" --defect-type GROUP_A_LIFE_THREATENING --batch "BAT-2026-X1" --distributed 5000 --recalled 4850 --announce --report

# Đánh giá hồ sơ tranh chấp người tiêu dùng và thủ tục rút gọn tại Tòa án (Điều 70-71)
mekong consumer dispute "Nguyễn Thị Mai" --merchant "Công ty TNHH Bán lẻ Siêu Tốc" --value 18500000 --method SUMMARY_COURT_PROCEEDING --invoice --refused

# Tra cứu lịch sử thẩm định nền tảng, hợp đồng mẫu, thu hồi sản phẩm và tranh chấp
mekong consumer list all --limit 20
```

---

## Native MCP Tools Parity

- `mekong_consumer_platform`: Audit digital platform and e-commerce intermediary compliance under Articles 37-40 Law on Consumer Rights Protection 2023.
- `mekong_consumer_contract`: Review standard-form contracts and general terms & conditions for void clauses under Article 25 Law 19/2023/QH15.
- `mekong_consumer_recall`: Manage and monitor defective product recall under Articles 32-34 Law on Consumer Rights Protection 2023.
- `mekong_consumer_dispute`: Evaluate consumer dispute and simplified summary court proceeding eligibility under Articles 70-71 Law 19/2023/QH15.
- `mekong_consumer_list`: Query stored digital platform audits, standard contract reviews, product recalls, or consumer disputes.
- `mekong_consumer_status`: Retrieve national consumer rights protection, digital platform compliance, and dispute resolution telemetry.
