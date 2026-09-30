---
name: marriage
description: Vietnamese Marriage, Matrimonial Property Regimes & Family Law Suite.
---

# 💍 Marriage — Vietnamese Marriage, Matrimonial Property Regimes & Family Law Engine

Autonomous compliance and legal operations engine for Vietnamese marriage registration, matrimonial property regimes (*chế độ tài sản vợ chồng*), prenuptial agreements (*thỏa thuận tài sản trước hôn nhân*), common vs. separate property division, consensual and unilateral divorce petitions, child custody, and statutory child support under the **Law on Marriage and Family 2014 (Law No. 52/2014/QH13)**, **Decree No. 126/2014/NĐ-CP**, **Decree No. 82/2020/NĐ-CP**, and **Civil Code 2015**.

## Statutory Legal Framework

1. **Luật Hôn nhân và Gia đình 2014 (Luật số 52/2014/QH13)**:
   - **Điều kiện kết hôn (Điều 8)**: Nam từ đủ 20 tuổi trở lên, Nữ từ đủ 18 tuổi trở lên; việc kết hôn do nam và nữ tự nguyện quyết định; không bị mất năng lực hành vi dân sự; không thuộc các trường hợp cấm kết hôn theo Điều 5 (kết hôn giả tạo, tảo hôn, cưỡng ép kết hôn, vi phạm chế độ một vợ một chồng, kết hôn trong phạm vi 3 đời).
   - **Chế độ tài sản của vợ chồng (Chương III, Điều 28–50)**:
     - **Tài sản chung (Điều 33)**: Tài sản do vợ, chồng tạo ra, thu nhập do lao động, hoạt động sản xuất, kinh doanh, hoa lợi, lợi tức phát sinh từ tài sản riêng và thu nhập hợp pháp khác trong thời kỳ hôn nhân; quyền sử dụng đất có được sau khi kết hôn là tài sản chung (trừ khi được thừa kế riêng, tặng cho riêng).
     - **Tài sản riêng (Điều 43)**: Tài sản có trước khi kết hôn, tài sản được thừa kế riêng, tặng cho riêng trong thời kỳ hôn nhân, đồ dùng cá nhân, tài sản hình thành từ tài sản riêng.
     - **Thỏa thuận xác lập chế độ tài sản trước hôn nhân (Prenuptial Agreement - Điều 47–50 & Nghị định 126/2014/NĐ-CP)**: Lập bằng văn bản có công chứng hoặc chứng thực trước ngày đăng ký kết hôn.
   - **Ly hôn & Phân chia tài sản (Chương IV, Điều 51–64)**:
     - **Thuận tình ly hôn (Điều 55)**: Hai bên thật sự tự nguyện ly hôn và đã thỏa thuận được về việc chia tài sản, trông nom, nuôi dưỡng, chăm sóc con.
     - **Ly hôn đơn phương (Điều 56)**: Có hành vi bạo lực gia đình hoặc vi phạm nghiêm trọng quyền, nghĩa vụ làm cho hôn nhân lâm vào tình trạng trầm trọng, đời sống chung không thể kéo dài.
     - **Hạn chế quyền yêu cầu ly hôn của chồng (Điều 51 khoản 3)**: Chồng KHÔNG có quyền yêu cầu ly hôn trong trường hợp vợ đang có thai, sinh con hoặc đang nuôi con dưới 12 tháng tuổi.
     - **Nguyên tắc chia tài sản khi ly hôn (Điều 59)**: Tài sản chung chia đôi nhưng có tính đến hoàn cảnh gia đình, công sức đóng góp, lỗi của mỗi bên, bảo vệ lợi ích chính đáng của vợ và con chưa thành niên.
   - **Trông nom, chăm sóc, nuôi dưỡng & Cấp dưỡng con (Điều 81–84, Điều 110–119)**:
     - Con dưới 36 tháng tuổi được giao cho mẹ trực tiếp nuôi dưỡng (trừ trường hợp cha mẹ có thỏa thuận khác hoặc mẹ không đủ điều kiện).
     - Con từ đủ 07 tuổi trở lên phải xem xét và tôn trọng nguyện vọng của con.
     - Nghĩa vụ cấp dưỡng nuôi con định kỳ hàng tháng của bên không trực tiếp nuôi con.

---

## CLI Usage

```bash
# Báo cáo telemetry tổng quan hôn nhân, ly hôn và tài sản gia đình
mekong marriage status
mekong marriage status --json

# Đăng ký kết hôn hợp pháp với kiểm tra tuổi và nguyên tắc một vợ một chồng
mekong marriage register "Nguyễn Văn Hùng" "Trần Thị Mai" 2000-05-15 2002-08-20 001099881122 001199773344 --office "UBND Phường Bến Nghé, Quận 1, TP.HCM" --json

# Lập văn bản thỏa thuận chế độ tài sản trước hôn nhân (Prenuptial Agreement)
mekong marriage prenuptial MARR-2026-001 2026-02-10 "Văn phòng Công chứng Sài Gòn" --notary-cert "CC-HD-2026-88" --terms "Phân định rõ bất động sản có trước hôn nhân và cổ phần doanh nghiệp thuộc tài sản riêng" --json

# Đăng ký tài sản vào danh mục tài sản chung / tài sản riêng
mekong marriage asset MARR-2026-001 "Căn hộ Vinhomes Grand Park 85m2" REAL_ESTATE 4500000000 --ownership COMMON --id "GCN-Q9-2026-99" --json
mekong marriage asset MARR-2026-001 "Xe ô tô Mercedes C300" VEHICLE 1800000000 --ownership HUSBAND_SEPARATE --id "51K-999.88" --json

# Nộp đơn yêu cầu ly hôn (Thuận tình hoặc Đơn phương)
mekong marriage divorce MARR-2026-001 CONSENSUAL BOTH "Bất đồng quan điểm sống, đời sống chung không thể kéo dài" --court "TAND Quận 1, TP.HCM" --json

# Giải quyết quyền nuôi con và nghĩa vụ cấp dưỡng định kỳ
mekong marriage custody DIV-2026-001 "Nguyễn Tuấn Kiệt" 2024-06-10 MOTHER 8000000 --notes "Con dưới 36 tháng tuổi giao mẹ nuôi dưỡng theo Điều 81(3)" --json

# Phân định tài sản chung và thanh toán nghĩa vụ khi ly hôn (Điều 59 Luật HNGĐ)
mekong marriage settle DIV-2026-001 "QD-ST-2026/88" --husband-percent 50 --json

# Tra cứu hồ sơ hôn nhân và gia đình
mekong marriage search "Nguyễn Văn Hùng" --json
mekong marriage list --category marriage --limit 20
```

### CLI Subcommands Reference

| Subcommand | Description |
|---|---|
| `status` | Hiển thị bảng điều hành telemetry tổng quan số lượng kết hôn, chế độ tài sản, ly hôn và nghĩa vụ cấp dưỡng. |
| `register` | Đăng ký kết hôn, thẩm tra tuổi luật định (nam $\ge 20$, nữ $\ge 18$) và nguyên tắc một vợ một chồng. |
| `prenuptial` | Đăng ký chế độ tài sản theo thỏa thuận trước hôn nhân có công chứng theo Điều 47–50 Luật HNGĐ. |
| `asset` | Ghi nhận tài sản vào danh mục tài sản chung vợ chồng hoặc tài sản riêng của vợ / chồng. |
| `divorce` | Nộp đơn yêu cầu ly hôn với kiểm tra rào cản Điều 51(3) bảo vệ phụ nữ mang thai / nuôi con nhỏ. |
| `custody` | Giải quyết quyền trực tiếp nuôi con (ưu tiên mẹ nếu $< 36$ tháng, hỏi ý kiến nếu $\ge 7$ tuổi) và cấp dưỡng. |
| `settle` | Quyết định phân chia tài sản chung và hoàn trả tài sản riêng khi ly hôn theo Điều 59 Luật HNGĐ. |
| `search` | Tra cứu đa tiêu chí hồ sơ hôn nhân theo CCCD, họ tên vợ chồng hoặc số trích lục kết hôn. |
| `list` | Liệt kê danh mục hồ sơ theo phân loại (kết hôn, thỏa thuận tài sản, ly hôn, quyền nuôi con). |

---

## MCP Tools Integration

Tích hợp 7 công cụ MCP chuẩn FastMCP và Stdio JSON-RPC:

- `mekong_marriage_register(husband_name, wife_name, husband_dob, wife_dob, husband_id, wife_id, husband_address, wife_address, registration_date, registration_office, husband_nationality, wife_nationality, property_regime, notes, marriage_id)`: Đăng ký kết hôn.
- `mekong_marriage_prenuptial(marriage_id, agreement_date, notary_office, notary_certificate_number, terms_summary, regime_id)`: Xác lập thỏa thuận chế độ tài sản trước hôn nhân.
- `mekong_marriage_asset(marriage_id, asset_name, asset_category, estimated_value, ownership_type, acquisition_date, identifier_number, notes, asset_id)`: Ghi nhận tài sản gia đình.
- `mekong_marriage_divorce(marriage_id, divorce_type, petitioner, grounds, court_name, filing_date, has_domestic_violence, wife_is_pregnant, nursing_child_under_12m, petition_id)`: Nộp đơn ly hôn.
- `mekong_marriage_custody(petition_id, child_name, child_dob, custodial_parent, monthly_support_vnd, effective_date, notes, order_id)`: Giải quyết quyền nuôi con & cấp dưỡng.
- `mekong_marriage_search(query)`: Tra cứu hồ sơ hôn nhân & gia đình.
- `mekong_marriage_status()`: Trả về trạng thái telemetry và các chỉ số hôn nhân gia đình.
