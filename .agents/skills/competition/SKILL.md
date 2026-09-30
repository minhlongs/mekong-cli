---
name: competition
description: Vietnamese Competition, Antitrust, Anti-Monopoly & Economic Concentration Suite.
---

# mekong competition — Autonomous Vietnamese Competition, Antitrust & Economic Concentration Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Cạnh tranh 2018 (Luật số 23/2018/QH14)**:
   - Thống nhất quản lý hành vi hạn chế cạnh tranh, tập trung kinh tế và cạnh tranh không lành mạnh trên toàn bộ lãnh thổ Việt Nam.
   - Thẩm quyền quản lý nhà nước: **Ủy ban Cạnh tranh Quốc gia (NCC - National Competition Commission)** thuộc Bộ Công Thương.
   - Nguyên tắc tiếp cận theo tác động (Effect-based approach) kết hợp quy tắc mặc nhiên vi phạm (Per se illegal).
2. **Nghị định số 35/2020/NĐ-CP**:
   - Quy định chi tiết một số điều của Luật Cạnh tranh.
   - **Ngưỡng thông báo tập trung kinh tế (Điều 13)**:
     * Tổng tài sản tại Việt Nam của doanh nghiệp hoặc nhóm doanh nghiệp liên kết $\ge 3.000\text{ tỷ VND}$ (ngành ngân hàng/tổ chức tín dụng $\ge 12.000\text{ tỷ VND}$).
     * Tổng doanh thu bán ra hoặc mua vào tại Việt Nam $\ge 3.000\text{ tỷ VND}$ (ngành ngân hàng $\ge 10.000\text{ tỷ VND}$).
     * Giá trị giao dịch của thương vụ sáp nhập $\ge 1.000\text{ tỷ VND}$ (đối với giao dịch trong nước).
     * Thị phần kết hợp của các doanh nghiệp tham gia trên thị trường liên quan $\ge 20\%$.
   - **Đánh giá tác động hạn chế cạnh tranh (Điều 14 & 15)**:
     * Đánh giá thị phần kết hợp và mức độ tập trung thị trường thông qua Chỉ số Herfindahl-Hirschman (HHI).
     * Giao dịch có nguy cơ gây tác động hạn chế cạnh tranh đáng kể nếu Post-HHI $> 1800$ và $\Delta\text{HHI} > 200$.
     * Thị phần kết hợp $\ge 50\%$ bị xem xét cấm giao dịch trừ khi đáp ứng các điều kiện miễn trừ theo luật định.
3. **Vị trí thống lĩnh thị trường (Điều 24)**:
   - Doanh nghiệp có vị trí thống lĩnh nếu có sức mạnh thị trường đáng kể hoặc có thị phần:
     * Doanh nghiệp đơn lẻ (CR1) $\ge 30\%$.
     * Nhóm 02 doanh nghiệp (CR2) $\ge 50\%$.
     * Nhóm 03 doanh nghiệp (CR3) $\ge 65\%$.
     * Nhóm 04 doanh nghiệp (CR4) $\ge 75\%$.
   - Hành vi lạm dụng bị cấm: Bán dưới giá thành toàn bộ để triệt hạ đối thủ (Predatory Pricing), áp đặt giá mua/bán, phân biệt đối xử, ngăn cản gia nhập thị trường.
4. **Thỏa thuận hạn chế cạnh tranh & Cartel (Điều 11 & 12)**:
   - Thỏa thuận ngang giữa các đối thủ cạnh tranh nhằm: Ấn định giá, phân chia thị trường, hạn chế sản lượng hoặc thông thầu bị cấm tuyệt đối (Per se violation).
   - Mức xử phạt: Lên tới $5\%$ tổng doanh thu của doanh nghiệp vi phạm trong năm tài chính liền kề (Điều 111).
5. **Chính sách khoan hồng (Leniency Program - Điều 112)**:
   - Doanh nghiệp tự nguyện khai báo hành vi thỏa thuận hạn chế cạnh tranh trước khi cơ quan có quyết định điều tra được hưởng chính sách khoan hồng:
     * Doanh nghiệp đầu tiên (1st): Miễn $100\%$ tiền phạt.
     * Doanh nghiệp thứ hai (2nd): Giảm $60\%$ tiền phạt.
     * Doanh nghiệp thứ ba (3rd): Giảm $40\%$ tiền phạt.
     * Tối đa 03 doanh nghiệp đầu tiên nộp đơn hợp tác đầy đủ.
6. **Lưu trữ SQLite WAL**: Bảng `economic_concentrations`, `market_dominance_assessments`, `anti_competitive_agreements`, `leniency_applications` tại `.mekong/competition.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động giám sát cạnh tranh, M&A và chống độc quyền
mekong competition

# Thẩm định ngưỡng thông báo tập trung kinh tế M&A theo Điều 33 & Nghị định 35/2020
mekong competition merger "Thương vụ Sáp nhập Nền tảng Bán lẻ Mekong & Saigon Mall" --buyer "Tập đoàn Bán lẻ A" --target "Chuỗi Siêu thị B" --assets 3500000000000 --revenue 4200000000000 --value 1500000000000 --share 26.5 --pre-hhi 1300 --post-hhi 1750

# Đánh giá vị trí thống lĩnh thị trường (CR1 >= 30%, CR2 >= 50%, CR3 >= 65%, CR4 >= 75%)
mekong competition dominance "Công ty Nền tảng Siêu ứng dụng Mekong" --share 34.5 --cr-shares "34.5,22.0,18.0,12.0" --essential-facility

# Rà soát dấu hiệu thỏa thuận hạn chế cạnh tranh / Cartel cấm theo Điều 11 & 12
mekong competition agreement "Biên bản Họp thống nhất Giá bán Tối thiểu Xi măng Miền Trung" --parties 4 --type PRICE_FIXING --horizontal --revenue 150000000000

# Nộp đơn tự thú hưởng chính sách khoan hồng (miễn giảm đến 100% tiền phạt theo Điều 112)
mekong competition leniency "Công ty CP Xi măng Thống Nhất" --violation "AGR-XIMANG-2026" --order 1 --confess --evidence

# Tra cứu danh mục hồ sơ cạnh tranh
mekong competition list all
mekong competition list concentrations
mekong competition list dominance
mekong competition list agreements
mekong competition list leniency

# Báo cáo telemetry cạnh tranh dạng JSON
mekong competition status --json
```

---

## MCP Tools Integration

| Tool Name | Parameters | Description |
|-----------|------------|-------------|
| `mekong_competition_merger` | `merger_name, acquiring_entity, target_entity, total_assets_vnd, total_revenue_vnd, transaction_value_vnd, combined_market_share_pct, pre_hhi, post_hhi, is_credit_institution` | Thẩm định ngưỡng thông báo tập trung kinh tế M&A và tác động cạnh tranh theo Nghị định 35/2020 |
| `mekong_competition_dominance` | `enterprise_name, market_share_pct, cr_group_shares, has_essential_facility, financial_superiority` | Đánh giá vị trí thống lĩnh thị trường (CR1, CR2, CR3, CR4) theo Điều 24 Luật Cạnh tranh 2018 |
| `mekong_competition_agreement` | `agreement_title, parties_count, agreement_type, is_horizontal, annual_revenue_vnd` | Rà soát thỏa thuận hạn chế cạnh tranh, thỏa thuận phân chia thị trường, ấn định giá và cartel cấm |
| `mekong_competition_leniency` | `enterprise_name, violation_id, submission_order, self_confessed, submitted_evidence` | Thẩm định đơn xin hưởng chính sách khoan hồng (miễn giảm đến 100% tiền phạt) theo Điều 112 |
| `mekong_competition_list` | `category: str = 'all', limit: int = 50` | Tra cứu danh mục hồ sơ thẩm định sáp nhập M&A, vị trí thống lĩnh, thỏa thuận cạnh tranh và khoan hồng |
| `mekong_competition_status` | *(none)* | Báo cáo chỉ số telemetry tổng hợp hệ thống giám sát cạnh tranh và chống độc quyền quốc gia |
