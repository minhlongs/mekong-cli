---
name: enforcement
description: Vietnamese Civil Judgment Enforcement, Asset Attachment & Debt Recovery Suite.
---

# mekong enforcement — Autonomous Vietnamese Civil Judgment Enforcement & Asset Attachment Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Thi hành án dân sự 2008 (sửa đổi, bổ sung 2014 - Luật số 64/2014/QH13)**:
   - Thống nhất quản lý thi hành bản án, quyết định dân sự, thương mại, lao động của Tòa án và phán quyết của Trọng tài thương mại trên toàn lãnh thổ Việt Nam.
   - Thẩm quyền tổ chức thi hành án: Cơ quan thi hành án dân sự (Cục THADS cấp tỉnh, Chi cục THADS cấp huyện) và Văn phòng Thừa phát lại theo luật định.
   - **Thời hiệu yêu cầu thi hành án (Điều 30)**: $05\text{ năm}$ kể từ ngày bản án, quyết định có hiệu lực pháp luật.
   - **Thời hạn tự nguyện thi hành án (Điều 45)**: $10\text{ ngày}$ kể từ ngày người phải thi hành án nhận được thông báo hợp lệ.
2. **Xác minh điều kiện thi hành án (Điều 44 & 44a)**:
   - Chấp hành viên xác minh tài sản, thu nhập, tài khoản ngân hàng, cổ phần, vốn góp tại cơ quan đăng ký đất đai, tổ chức tín dụng, cơ quan đăng ký kinh doanh.
   - Phân loại: Có điều kiện thi hành án (Solvent) hoặc Chưa có điều kiện thi hành án (Insolvent / Suspended).
   - Biện pháp ngăn chặn tạm thời: Tạm hoãn xuất cảnh (Điều 44a) đối với người phải thi hành án chưa hoàn thành nghĩa vụ.
3. **Biện pháp cưỡng chế thi hành án (Điều 71 - 100)**:
   - Phong tỏa và khấu trừ tiền trong tài khoản tại ngân hàng, TCTD (Điều 76).
   - Khấu trừ thu nhập: Tối đa $30\%$ tiền lương hàng tháng, tối đa $50\%$ đối với các khoản thu nhập khác (Điều 78).
   - Kê biên, xử lý tài sản của người phải thi hành án (Điều 88-100), bao gồm cả tài sản đang do bên thứ ba giữ.
   - Kê biên, phong tỏa phần vốn góp, cổ phần, chứng khoán (Điều 92).
   - Kê biên nhà ở, quyền sử dụng đất, công trình xây dựng (Điều 95 & 110).
4. **Thứ tự phân bổ tiền và tài sản thi hành án (Điều 47)**:
   - Tiền thu được từ việc cưỡng chế, bán đấu giá tài sản kê biên được thanh toán theo thứ tự ưu tiên luật định:
     * Hạng 1: Chi phí cưỡng chế thi hành án và chi phí bảo quản tài sản.
     * Hạng 2: Tiền cấp dưỡng; tiền lương, tiền công lao động, trợ cấp thôi việc, bảo hiểm xã hội, bồi thường thiệt hại tính mạng, sức khỏe.
     * Hạng 3: Án phí, lệ phí Tòa án.
     * Hạng 4: Các khoản tiền phạt, tiền tịch thu sung quỹ nhà nước, nghĩa vụ tài chính khác đối với Nhà nước.
     * Hạng 5: Nghĩa vụ thi hành án có biện pháp bảo đảm (cầm cố, thế chấp đã đăng ký hợp pháp).
     * Hạng 6: Các khoản nghĩa vụ thi hành án không có bảo đảm (thanh toán theo tỷ lệ số tiền được thi hành nếu không đủ).
5. **Nghị định số 62/2015/NĐ-CP & Nghị định số 33/2020/NĐ-CP**:
   - Quy định chi tiết thủ tục cưỡng chế, thẩm định giá và đấu giá tài sản thi hành án.
6. **Lưu trữ SQLite WAL**: Bảng `judgment_dossiers`, `debtor_verifications`, `coercive_measures`, `proceeds_distributions` tại `.mekong/enforcement.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động thi hành án dân sự, kê biên tài sản & thu hồi nợ
mekong enforcement

# Lập hồ sơ yêu cầu thi hành án dân sự / thương mại / phán quyết trọng tài
mekong enforcement dossier "Bản án số 15/2026/KDTM-ST Tranh chấp Hợp đồng Tín dụng" --creditor "Ngân hàng Thương mại CP Sài Gòn" --debtor "Công ty CP Đầu tư & Xây dựng Hải Đăng" --claim 18500000000 --type COURT_COMMERCIAL --agency "Cục THADS TP. Hồ Chí Minh"

# Xác minh điều kiện thi hành án và áp dụng biện pháp ngăn chặn (tạm hoãn xuất cảnh)
mekong enforcement verify "DOS-1700000001" --assets 9500000000 --solvent --bank-frozen --exit-ban

# Ra quyết định cưỡng chế thi hành án (Kê biên BĐS / Phong tỏa tài khoản / Khấu trừ lương)
mekong enforcement coerce "DOS-1700000001" --measure ASSET_DISTRAINT --target "Quyền sử dụng đất và nhà xưởng tại KCN Hiệp Phước, Nhà Bè" --value 15000000000

# Phân bổ thanh toán tiền thi hành án theo thứ tự ưu tiên Điều 47 Luật THADS
mekong enforcement distribute "DOS-1700000001" --recovered 12000000000 --costs 250000000 --wages 600000000 --court-fees 120000000 --state-fines 50000000 --secured 8000000000 --unsecured 5000000000

# Tra cứu danh mục hồ sơ thi hành án
mekong enforcement list all
mekong enforcement list dossiers
mekong enforcement list verifications
mekong enforcement list measures
mekong enforcement list distributions

# Báo cáo telemetry thi hành án dạng JSON
mekong enforcement status --json
```

---

## MCP Tools Integration

| Tool Name | Parameters | Description |
|-----------|------------|-------------|
| `mekong_enforcement_dossier` | `judgment_title, creditor_name, debtor_name, total_claim_vnd, judgment_type, enforcement_agency, judgment_date` | Lập hồ sơ thụ lý thi hành bản án, quyết định Tòa án hoặc phán quyết Trọng tài thương mại theo Điều 36 |
| `mekong_enforcement_verify` | `dossier_id, verified_assets_vnd, is_solvent, bank_account_frozen, salary_garnished, exit_ban_imposed, notes` | Xác minh điều kiện thi hành án và áp dụng biện pháp ngăn chặn tạm hoãn xuất cảnh theo Điều 44 & 44a |
| `mekong_enforcement_coerce` | `dossier_id, measure_type, target_description, estimated_value_vnd` | Ra quyết định áp dụng biện pháp cưỡng chế thi hành án (Kê biên tài sản, phong tỏa tài khoản, khấu trừ thu nhập) theo Điều 71 |
| `mekong_enforcement_distribute` | `dossier_id, recovered_amount_vnd, enforcement_costs_vnd, wages_and_alimony_vnd, court_fees_vnd, state_fines_vnd, secured_claims_vnd, unsecured_claims_vnd` | Phân bổ số tiền thi hành án thu hồi được theo thứ tự 6 bậc ưu tiên luật định tại Điều 47 Luật THADS |
| `mekong_enforcement_list` | `category: str = 'all', limit: int = 50` | Tra cứu danh mục hồ sơ thi hành án, kết quả xác minh điều kiện, biện pháp cưỡng chế và phân bổ dòng tiền |
| `mekong_enforcement_status` | *(none)* | Báo cáo chỉ số telemetry tổng hợp hệ thống thi hành án dân sự, thu hồi tài sản và cưỡng chế quốc gia |
