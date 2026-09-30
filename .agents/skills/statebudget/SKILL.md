---
name: statebudget
description: Vietnamese State Budget, Fiscal Discipline, Public Treasury Accounts & Budget Allocations Suite.
---

# mekong statebudget — Autonomous Vietnamese State Budget & Public Treasury Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Ngân sách nhà nước 2015 (Luật số 83/2015/QH13, có hiệu lực từ năm ngân sách 2017)**:
   - Thống nhất quản lý nền tài chính quốc gia, bảo đảm kỷ luật tài khóa, phân cấp nguồn thu, nhiệm vụ chi giữa các cấp ngân sách.
   - **Hệ thống ngân sách nhà nước (Điều 6)**:
     * *Ngân sách trung ương (NSTW)*: Chi quốc phòng, an ninh, đối ngoại, chi đầu tư phát triển quốc gia, các chương trình mục tiêu quốc gia...
     * *Ngân sách địa phương (NSĐP)*: Ngân sách cấp tỉnh, ngân sách cấp huyện, ngân sách cấp xã.
   - **Dự phòng ngân sách & Quỹ dự trữ tài chính**:
     * *Dự phòng ngân sách (Điều 10)*: Mức bố trí từ $2\%$ đến $4\%$ tổng chi ngân sách mỗi cấp để xử lý thiên tai, dịch bệnh, nhiệm vụ đột xuất.
     * *Quỹ dự trữ tài chính (Điều 11)*: Thành lập tại trung ương và cấp tỉnh, mức khống chế tối đa $25\%$ dự toán chi ngân sách hằng năm.
2. **Kiểm soát chi & Cam kết chi qua Kho bạc Nhà nước (Thông tư số 342/2016/TT-BTC & Nghị định 11/2020/NĐ-CP)**:
   - Tất cả các khoản chi ngân sách chỉ được thanh toán khi có trong dự toán ngân sách được giao và đáp ứng các điều kiện luật định.
   - Quản lý cam kết chi (Spending Commitment Control) đối với các hợp đồng kinh tế theo quy định của Bộ Tài chính, tránh phát sinh nợ đọng ngân sách.
   - Phân biệt rõ tạm ứng ngân sách (Advance) và thanh toán thực tế (Actual Payout), thời hạn thu hồi tạm ứng.
3. **Kỷ luật tài khóa & Các hành vi bị cấm (Điều 18 & 70-73)**:
   - Nghiêm cấm chi ngoài dự toán, chi không đúng chế độ, tiêu chuẩn, định mức, chia nhỏ hợp đồng để trốn tránh đấu thầu.
   - Kiểm tra, thanh tra, kiểm toán báo cáo quyết toán ngân sách nhà nước bởi Kiểm toán Nhà nước.
4. **Lưu trữ SQLite WAL**: Bảng `budget_estimates`, `spending_commitments`, `treasury_payouts`, `fiscal_audits` tại `~/.mekong/statebudget.db` (override qua `MEKONG_STATEBUDGET_DB`).

---

## CLI Invocations

```bash
# Báo cáo tổng quan tình hình dự toán, cam kết chi và tỷ lệ thực chi ngân sách nhà nước
mekong statebudget

# Lập và phê duyệt dự toán chi ngân sách nhà nước
mekong statebudget estimate --code "DT-2026-BYT-01" --year 2026 --level "CENTRAL_BUDGET" --type "REGULAR_EXPENDITURE" --sector "HEALTHCARE_AND_POPULATION" --unit "Bệnh viện Bạch Mai" --amount 1850000000000 --approver "Quốc hội" --decision "Nghị quyết số 105/2025/QH15" --contingency 3.0

# Đăng ký cam kết chi qua Kho bạc Nhà nước cho hợp đồng kinh tế
mekong statebudget commit "DT-2026-BYT-01" --code "CKC-2026-0042" --contract "HĐ-MUA-THIET-BI-Y-TE-01" --beneficiary "Công ty Thiết bị Y tế MedTech VN" --amount 450000000000 --treasury "Kho bạc Nhà nước TP. Hà Nội"

# Thực hiện xuất chi ngân sách qua Kho bạc Nhà nước (Giấy rút dự toán / Lệnh chi tiền)
mekong statebudget payout "DT-2026-BYT-01" --voucher "LCT-2026-981" --amount 150000000000 --category "ACTUAL_PAYOUT" --treasury "Kho bạc Nhà nước TP. Hà Nội" --account "711-KBNN-BACHMAI" --notes "Thanh toán đợt 1 hợp đồng cung cấp vật tư y tế"

# Ghi nhận kết luận thanh tra, kiểm toán tài khóa ngân sách nhà nước
mekong statebudget audit --year 2026 --unit "UBND Huyện X" --violation "UNAUTHORIZED_EXPENDITURE" --severity "HIGH" --amount 12500000000 --measures "Thu hồi nộp trả ngân sách nhà nước và kiến nghị xử lý trách nhiệm người đứng đầu" --agency "Kiểm toán Nhà nước Khu vực I"

# Tra cứu dữ liệu ngân sách
mekong statebudget list --type all --limit 20
mekong statebudget list --type estimates
mekong statebudget list --type commitments
mekong statebudget list --type payouts
mekong statebudget list --type audits

# Báo cáo trạng thái telemetry ngân sách
mekong statebudget status --json
```

---

## MCP Tools Integration (Dual Parity)

- `mekong_statebudget_estimate`: Lập và phê duyệt dự toán ngân sách nhà nước.
- `mekong_statebudget_commit`: Đăng ký kiểm soát cam kết chi hợp đồng qua Kho bạc Nhà nước.
- `mekong_statebudget_payout`: Ghi nhận chứng từ xuất chi ngân sách nhà nước qua KBNN.
- `mekong_statebudget_audit`: Ghi nhận kết luận kiểm tra, kiểm toán kỷ luật tài khóa.
- `mekong_statebudget_list`: Tra cứu danh sách dự toán, cam kết chi, chứng từ chi, kiểm toán.
- `mekong_statebudget_status`: Tổng hợp chỉ số chấp hành ngân sách và kỷ luật tài khóa toàn quốc.
