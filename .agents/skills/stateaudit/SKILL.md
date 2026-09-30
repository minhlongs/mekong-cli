---
name: stateaudit
description: Vietnamese State Audit, Supreme Audit Institution (SAV / KTNN) & Public Financial Oversight Suite.
---

# mekong stateaudit — Autonomous Vietnamese State Audit & Public Financial Oversight Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Kiểm toán nhà nước 2015 (Luật số 81/2015/QH13) & Luật sửa đổi 2019 (Luật số 55/2019/QH14)**:
   - Cơ quan kiểm toán tối cao của Nhà nước Việt Nam (State Audit of Vietnam - KTNN), do Quốc hội thành lập, hoạt động độc lập và chỉ tuân theo pháp luật (Điều 118 Hiến pháp 2013).
   - **3 Loại hình kiểm toán nhà nước bắt buộc (Điều 10)**:
     * `FINANCIAL_AUDIT`: Kiểm toán báo cáo tài chính, quyết toán ngân sách nhà nước (NSNN), báo cáo tài chính doanh nghiệp nhà nước.
     * `COMPLIANCE_AUDIT`: Kiểm toán việc tuân thủ pháp luật, nội quy, quy chế về thu - chi ngân sách, quản lý vốn đầu tư công, mua sắm đấu thầu và tài sản công.
     * `PERFORMANCE_AUDIT`: Kiểm toán hoạt động đánh giá tính kinh tế, hiệu quả và hiệu lực (3E: Economy, Efficiency, Effectiveness) trong quản lý, sử dụng tài chính công và tài sản công.
   - **Thẩm quyền kiểm toán (Điều 55)**:
     * Các Bộ, cơ quan trung ương, UBND/HĐND 63 tỉnh/thành phố, Tập đoàn/Tổng công ty Nhà nước, Ban Quản lý dự án công trình trọng điểm quốc gia.
2. **Xử lý tài chính và kiến nghị kiểm toán (Điều 37 & Điều 48)**:
   - **4 Nhóm kiến nghị xử lý tài chính bắt buộc**:
     * `REVENUE_INCREASE`: Tăng thu ngân sách nhà nước (truy thu thuế, phí, lệ phí trốn lậu, tiền cấp quyền khai thác khoáng sản).
     * `EXPENDITURE_DISALLOWANCE`: Giảm chi ngân sách nhà nước (xuất toán, giảm trừ thanh quyết toán công trình xây lắp do áp sai định mức, nghiệm thu khống).
     * `REIMBURSEMENT`: Thu hồi nộp lại ngân sách nhà nước (các khoản tạm ứng quá hạn, chi sai chế độ, sử dụng nguồn vốn sai mục đích).
     * `OTHER_FINANCIAL_REMEDIATION`: Xử lý tài chính khác (ghi thu - ghi chi, điều chỉnh hạch toán kế toán, trích lập quỹ đúng quy định).
   - **Kiến nghị xử lý trách nhiệm**:
     * `DISCIPLINARY_ACTION`: Xử lý kỷ luật hành chính, khiển trách, cách chức cá nhân sai phạm.
     * `CRIMINAL_REFERRAL`: Chuyển hồ sơ sang Cơ quan Cảnh sát Điều tra Bộ Công an (C03) khi phát hiện dấu hiệu tội phạm tham ô, tham nhũng, lãng phí nghiêm trọng.
3. **Theo dõi và đôn đốc thực hiện kết luận kiểm toán (Nghị định số 162/2021/NĐ-CP)**:
   - Đơn vị được kiểm toán có nghĩa vụ thi hành đầy đủ, kịp thời các kiến nghị của KTNN và báo cáo kết quả thực hiện.
   - Phân loại tiến độ: `PENDING`, `PARTIALLY_IMPLEMENTED`, `FULLY_IMPLEMENTED`, `OVERDUE`.
4. **Lưu trữ SQLite WAL**: Bảng `audit_engagements`, `audit_findings`, `audit_recommendations`, `recommendation_settlements` tại `~/.mekong/stateaudit.db` (override qua `MEKONG_STATEAUDIT_DB`).

---

## CLI Invocations

```bash
# Báo cáo tổng quan tình hình kiểm toán nhà nước, kiến nghị tài chính và tỷ lệ thu hồi ngân sách
mekong stateaudit

# Đăng ký quyết định kiểm toán nhà nước đối với đơn vị được kiểm toán
mekong stateaudit engagement --code "KTNN-2026-BXD-01" --decision "QĐ 112/QĐ-KTNN" --entity "Bộ Xây dựng" --type "MINISTRY" --audit-type "COMPLIANCE_AUDIT" --year 2025 --lead "Nguyễn Văn Kiểm" --start "2026-03-01" --end "2026-04-30"

# Ghi nhận phát hiện sai phạm kiểm toán (áp sai định mức dự toán xây lắp)
mekong stateaudit finding --code "FIND-2026-001" --engagement "KTNN-2026-BXD-01" --domain "PUBLIC_INVESTMENT" --desc "Áp sai đơn giá vật liệu và định mức ca máy tại Dự án Cao tốc Bắc - Nam đoạn A-B" --violation "Khoản 2 Điều 132 Luật Xây dựng 2014 & Thông tư 12/2021/TT-BXD" --severity "HIGH" --evidence "Hồ sơ nghiệm thu thanh toán đợt 3 và biên bản đối chiếu hiện trường"

# Ban hành kiến nghị xử lý tài chính (giảm trừ thanh quyết toán công trình)
mekong stateaudit recommend --code "REC-2026-001" --finding "FIND-2026-001" --type "EXPENDITURE_DISALLOWANCE" --desc "Giảm trừ thanh toán giá trị khối lượng xây lắp nghiệm thu sai quy định" --agency "Ban QLDA Thăng Long" --deadline "2026-08-31" --amount 18500000000

# Ghi nhận thực hiện nộp hoàn trả ngân sách hoặc giảm trừ quyết toán
mekong stateaudit settle --id "SETTLE-2026-001" --code "REC-2026-001" --date "2026-07-15" --voucher "GNT-2026-KBNN-889" --amount 18500000000 --evidence "Giấy nộp tiền vào NSNN tại Kho bạc Nhà nước Hà Nội"

# Kết luận hoặc công bố báo cáo kiểm toán chính thức
mekong stateaudit conclude --code "KTNN-2026-BXD-01" --status "CONCLUDED"

# Tra cứu dữ liệu kiểm toán nhà nước
mekong stateaudit list --type all --limit 20
mekong stateaudit list --type engagements
mekong stateaudit list --type findings
mekong stateaudit list --type recommendations
mekong stateaudit list --type settlements

# Báo cáo telemetry chi tiết
mekong stateaudit status --json
```

---

## MCP Tools Reference

- `mekong_stateaudit_engagement`: Register State Audit mission dossier under Auditor General decision.
- `mekong_stateaudit_finding`: Record compliance defects, budget leaks, and statutory infractions.
- `mekong_stateaudit_recommend`: Issue statutory audit recommendation for fiscal recovery or accountability action.
- `mekong_stateaudit_settle`: Record implementation and reimbursement of audit recommendations with treasury vouchers.
- `mekong_stateaudit_conclude`: Mark audit mission as concluded or officially published.
- `mekong_stateaudit_list`: Query audit missions, findings, recommendations, and settlements.
- `mekong_stateaudit_status`: Aggregate telemetry metrics on state audits, fiscal recoveries, and criminal referrals.
