---
name: mediation
description: Vietnamese Commercial Mediation, Conciliation & ADR Suite.
---

# /mediation — Vietnamese Commercial Mediation, Conciliation & ADR Suite

Quản lý và giải quyết tranh chấp kinh tế, thương mại bằng Hòa giải thương mại theo Nghị định 22/2017/NĐ-CP, soạn thảo thỏa thuận hòa giải, chỉ định hòa giải viên đạt chuẩn Điều 7, lập Văn bản kết quả hòa giải thành theo Điều 15, thẩm tra thủ tục công nhận kết quả hòa giải thành ngoài Tòa án theo Bộ luật Tố tụng dân sự 2015 (Điều 416-419) và thẩm tra điều kiện thi hành xuyên biên giới theo Công ước Singapore về Hòa giải 2018.

## Căn cứ Pháp lý & Khung Quy chuẩn

1. **Nghị định số 22/2017/NĐ-CP ngày 24/02/2017 của Chính phủ** về hòa giải thương mại.
2. **Bộ luật Tố tụng dân sự 2015 — Chương XXXIII (Điều 416 - Điều 419)**: Thủ tục công nhận kết quả hòa giải thành ngoài Tòa án.
3. **Bộ luật Dân sự 2015**: Quy định về giao dịch dân sự, hợp đồng và tự do thỏa thuận hợp pháp.
4. **Công ước Singapore về Hòa giải 2018 (Singapore Convention on Mediation)**: Công ước Liên Hợp Quốc về thỏa thuận hòa giải quốc tế (iMSAs).
5. **Quy tắc hòa giải của các Trung tâm hòa giải thương mại**: VICMC (Trung tâm Hòa giải Thương mại Quốc tế Việt Nam), VMC (Trung tâm Hòa giải Việt Nam thuộc VIAC).

---

## Tính năng Nghiệp vụ Cốt lõi

### 1. Soạn thảo & Thẩm tra Thỏa thuận Hòa giải (Điều 11 Nghị định 22)
- Thẩm định thỏa thuận hòa giải trước hoặc sau khi xảy ra tranh chấp dưới hình thức văn bản, điều khoản mẫu hoặc trao đổi điện tử.
- Hỗ trợ cơ chế hòa giải qua tổ chức (`VICMC`, `VMC`) hoặc hòa giải viên vụ việc (`AD_HOC`).

### 2. Thụ lý Vụ việc & Bổ nhiệm Hòa giải viên Đạt chuẩn (Điều 7 & 12)
- Thụ lý đơn yêu cầu hòa giải các tranh chấp thương mại (mua bán hàng hóa, dịch vụ phần mềm/IT, EPC, cổ đông góp vốn, logistics, SHTT).
- Thẩm tra tiêu chuẩn hòa giải viên theo Điều 7: bằng đại học trở lên, tối thiểu 02 năm kinh nghiệm thực tế, phẩm chất đạo đức tốt, độc lập và vô tư.
- Tính toán biểu phí dịch vụ hòa giải thương mại theo giá trị vụ việc tranh chấp.

### 3. Lập Văn bản Kết quả Hòa giải Thành (Điều 15 Nghị định 22)
- Soạn thảo Văn bản kết quả hòa giải thành có chữ ký của các bên và hòa giải viên thương mại.
- Thẩm tra tính tự nguyện, năng lực hành vi dân sự, không trốn tránh nghĩa vụ ngân sách nhà nước/thuế, không vi phạm điều cấm của luật và đạo đức xã hội.
- Văn bản kết quả hòa giải thành có hiệu lực ràng buộc các bên theo quy định của pháp luật dân sự (Khoản 5 Điều 15).

### 4. Thẩm tra Công nhận của Tòa án (Điều 416–419 BLTTDS 2015)
- Thẩm tra hồ sơ yêu cầu Tòa án công nhận kết quả hòa giải thành ngoài Tòa án.
- Kiểm tra nghiêm ngặt thời hiệu nộp đơn trong thời hạn 06 tháng kể từ ngày lập văn bản hòa giải thành (Điều 416).
- Quyết định công nhận của Tòa án có hiệu lực thi hành ngay, không bị kháng cáo/kháng nghị, được cưỡng chế theo Luật Thi hành án dân sự.

### 5. Thẩm tra Công ước Singapore về Hòa giải (Singapore Convention 2018)
- Đánh giá khả năng thi hành trực tiếp xuyên biên giới tại các quốc gia thành viên công ước mà không cần qua thủ tục khởi kiện mới.
- Kiểm tra tính chất thương mại quốc tế, loại trừ tranh chấp người tiêu dùng hoặc gia đình, xác nhận hợp chuẩn của hòa giải viên.

### 6. National Commercial Mediation Telemetry & Status
- Báo cáo tổng hợp số thỏa thuận, số vụ việc thụ lý, tỷ lệ hòa giải thành, tổng giá trị tranh chấp và số quyết định công nhận có hiệu lực THADS.

---

## Hướng dẫn Sử dụng CLI (`mekong mediation`)

```bash
# Xem báo cáo tổng quan telemetry hòa giải thương mại quốc gia
mekong mediation

# Soạn thảo và thẩm định thỏa thuận / điều khoản hòa giải mẫu
mekong mediation agreement "Công ty Công nghệ Mekong" "Tập đoàn Đầu tư Alpha" --center "VICMC" --lang "VIETNAMESE"

# Thụ lý vụ việc hòa giải và chỉ định hòa giải viên đạt chuẩn
mekong mediation case "Công ty Phần mềm Sài Gòn" "Công ty Bán lẻ Toàn Cầu" --amount 750000000 --category "TECH_SERVICES" --exp 6

# Lập Văn bản kết quả hòa giải thành theo Điều 15
mekong mediation settle "MED-CAS-88AB12CD" --amount 600000000 --summary "Bên B đồng ý thanh toán đợt cuối và bàn giao mã nguồn trong 20 ngày"

# Thẩm tra thủ tục Tòa án công nhận kết quả hòa giải thành (thời hiệu <= 6 tháng)
mekong mediation recognize "MED-SET-99FE34BA" --court "Tòa án nhân dân Thành phố Hồ Chí Minh" --months 2.5

# Thẩm tra điều kiện thi hành xuyên biên giới theo Công ước Singapore
mekong mediation convention "MED-SET-99FE34BA" --cross-border --commercial --attestation

# Tra cứu hồ sơ hòa giải thương mại
mekong mediation list --category ALL --limit 50 --json

# Xem telemetry hệ thống
mekong mediation status --json
```

---

## Công cụ Native MCP

- `mekong_mediation_agreement`: Soạn thảo và thẩm tra thỏa thuận hòa giải thương mại theo Điều 11 NĐ 22/2017.
- `mekong_mediation_case`: Thụ lý vụ việc hòa giải và bổ nhiệm hòa giải viên thương mại đạt chuẩn Điều 7.
- `mekong_mediation_settle`: Lập Văn bản kết quả hòa giải thành theo Điều 15 Nghị định 22/2017.
- `mekong_mediation_recognize`: Thẩm tra thủ tục Tòa án công nhận kết quả hòa giải thành ngoài Tòa án theo BLTTDS 2015.
- `mekong_mediation_convention`: Thẩm tra điều kiện công nhận xuyên biên giới theo Công ước Singapore về Hòa giải.
- `mekong_mediation_list`: Tra cứu danh mục thỏa thuận, vụ việc, văn bản hòa giải thành và hồ sơ công nhận.
- `mekong_mediation_status`: Báo cáo chỉ số telemetry hoạt động hòa giải thương mại và công nhận Tòa án.
