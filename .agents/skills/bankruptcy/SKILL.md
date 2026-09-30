---
name: bankruptcy
description: Vietnamese Corporate Insolvency, Bankruptcy, Debt Restructuring & Asset Liquidation Suite.
---

# /bankruptcy — Vietnamese Corporate Insolvency, Bankruptcy, Debt Restructuring & Asset Liquidation Suite

Hệ thống quản lý và thẩm tra thủ tục phá sản doanh nghiệp theo Luật Phá sản 2014 và Nghị định số 22/2015/NĐ-CP, thẩm tra chứng chỉ hành nghề Quản tài viên theo Điều 12, tiếp nhận và kiểm tra điều kiện thụ lý đơn yêu cầu mở thủ tục phá sản (quá hạn thanh toán nợ >= 03 tháng theo Khoản 1 Điều 4), lập danh sách chủ nợ theo Điều 64-67, tổ chức Hội nghị chủ nợ và thông qua nghị quyết phục hồi kinh doanh theo Điều 75-86 (túc số >= 51% nợ không bảo đảm theo Điều 79), và tính toán phân chia tài sản thanh lý theo đúng thứ tự ưu tiên luật định tại Điều 54.

## Căn cứ Pháp lý & Khung Quy chuẩn

1. **Luật Phá sản 2014 (Luật số 51/2014/QH13)**:
   - Khoản 1 Điều 4: Định nghĩa doanh nghiệp mất khả năng thanh toán khi không thực hiện nghĩa vụ thanh toán khoản nợ trong thời hạn 03 tháng kể từ ngày đến hạn.
   - Điều 5: Quyền và nghĩa vụ nộp đơn yêu cầu mở thủ tục phá sản (Chủ nợ không bảo đảm, người lao động/công đoàn, người đại diện theo pháp luật, cổ đông sở hữu >= 20%).
   - Điều 12, 13: Tiêu chuẩn Quản tài viên và Doanh nghiệp quản lý, thanh lý tài sản.
   - Điều 54: Thứ tự phân chia tài sản khi Tòa án ra quyết định tuyên bố doanh nghiệp phá sản.
   - Điều 79, 89: Điều kiện hợp lệ của Hội nghị chủ nợ (>= 51% nợ không bảo đảm) và thời hạn phục hồi hoạt động kinh doanh (tối đa 03 năm).
2. **Nghị định số 22/2015/NĐ-CP**:
   - Quy định chi tiết thi hành một số điều của Luật Phá sản về Quản tài viên và hành nghề quản lý, thanh lý tài sản.
3. **Nghị quyết số 03/2016/NQ-HĐTP**:
   - Hướng dẫn áp dụng một số quy định của Luật Phá sản của Hội đồng Thẩm phán TANDTC.
4. **Bộ luật Dân sự 2015 & Luật Doanh nghiệp 2020**: Nghĩa vụ tài sản và quyền sở hữu trong giải thể, phá sản.

---

## Tính năng Nghiệp vụ Cốt lõi

### 1. Quản lý Hồ sơ Quản tài viên (Điều 12, 13)
- Thẩm tra Chứng chỉ hành nghề Quản tài viên do Bộ Tư pháp cấp (mã hiệu BTP-QTV).
- Kiểm tra điều kiện thâm niên chuyên môn (tối thiểu 05 năm kinh nghiệm đối với luật sư, kiểm toán viên, cử nhân luật/tài chính).
- Quản lý doanh nghiệp quản lý, thanh lý tài sản (công ty hợp danh, DNTN).

### 2. Thẩm tra Đơn Yêu cầu Mở Thủ tục Phá sản (Điều 4, 5, 40–42)
- Xác minh điều kiện mất khả năng thanh toán: Khoản nợ quá hạn thanh toán $\ge 90$ ngày (03 tháng) theo Khoản 1 Điều 4.
- Kiểm tra tư cách hợp pháp của người nộp đơn (chủ nợ, người lao động, đại diện theo pháp luật, cổ đông $\ge 20\%$).
- Xác định thẩm quyền thụ lý của Tòa án nhân dân cấp tỉnh / cấp huyện.

### 3. Lập Danh sách Chủ nợ & Yêu cầu Đòi nợ (Điều 64–67)
- Tiếp nhận và phân loại yêu cầu đòi nợ trong thời hạn 30 ngày:
  - `SECURED`: Nợ có bảo đảm bằng tài sản (xử lý ưu tiên theo Điều 53).
  - `PARTIALLY_SECURED`: Nợ có bảo đảm một phần.
  - `UNSECURED`: Nợ không có bảo đảm (tham gia biểu quyết và phân chia theo tỷ lệ).

### 4. Hội nghị Chủ nợ & Kế hoạch Phục hồi (Điều 75–86)
- Thẩm tra túc số hợp lệ của Hội nghị chủ nợ: Bắt buộc đại diện cho ít nhất 51% tổng số nợ không có bảo đảm tham gia (Điều 79).
- Giám sát Nghị quyết Hội nghị: Thông qua phương án phục hồi kinh doanh (`RESTRUCTURING_PLAN` - tối đa 03 năm theo Điều 89) hoặc yêu cầu tuyên bố phá sản (`DECLARE_BANKRUPTCY`).

### 5. Phân chia Tài sản Thanh lý Phá sản (Điều 54)
- Thuật toán phân bổ dòng tiền thanh lý tài sản tự động theo đúng thứ tự luật định:
  1. Chi phí phá sản (thù lao Quản tài viên, chi phí định giá, niêm yết, bán tài sản).
  2. Nợ lương, trợ cấp thôi việc, bảo hiểm xã hội (BHXH, BHYT) đối với người lao động.
  3. Khoản nợ mới phát sinh sau khi mở thủ tục phá sản nhằm phục hồi kinh doanh.
  4. Nghĩa vụ tài chính đối với Nhà nước (thuế, phí) & Nợ không có bảo đảm theo tỷ lệ.
  5. Giá trị còn lại thuộc về chủ sở hữu / cổ đông doanh nghiệp.

---

## Hướng dẫn Sử dụng CLI (`mekong bankruptcy`)

```bash
# Xem báo cáo tổng quan telemetry phá sản & tái cơ cấu nợ toàn quốc
mekong bankruptcy

# Đăng ký và thẩm tra hồ sơ Quản tài viên
mekong bankruptcy practitioner "Luật sư Quản tài viên Phạm Hồng Sơn" --cert "BTP-QTV-112/2021" --org "Công ty Hợp danh Quản lý Tài sản Mekong" --profession "LUAT_SU" --years 9

# Nộp đơn yêu cầu mở thủ tục phá sản (quá hạn >= 90 ngày)
mekong bankruptcy petition "Công ty Cổ phần Xây dựng & Địa ốc Tân Bình" "0301987654" "Ngân hàng TMCP Đầu tư Á Châu" --role "UNSECURED_CREDITOR" --days 120 --debt 15000000000 --court "TAND TP.HCM"

# Tiếp nhận và xác minh Giấy đòi nợ của chủ nợ
mekong bankruptcy claim "PET-12AB34CD" "Công ty TNHH Thép Việt Nhật" "0102030405" --type "UNSECURED" --amount 2500000000

# Tổ chức Hội nghị chủ nợ (kiểm tra túc số >= 51% nợ không bảo đảm)
mekong bankruptcy meeting "PET-12AB34CD" 18000000000 25000000000 --resolution "RESTRUCTURING_PLAN" --years 2.5

# Tính toán phân chia tài sản thanh lý theo thứ tự ưu tiên Điều 54
mekong bankruptcy distribute "PET-12AB34CD" 8000000000 300000000 1200000000 --new-debts 500000000 --tax 1000000000 --unsecured 10000000000

# Tra cứu danh mục hồ sơ phá sản
mekong bankruptcy list --category ALL --limit 50 --json

# Xem telemetry hệ thống phá sản doanh nghiệp toàn quốc
mekong bankruptcy status --json
```

---

## Công cụ Native MCP

- `mekong_bankruptcy_practitioner`: Đăng ký và thẩm tra Quản tài viên theo Điều 12 Luật Phá sản.
- `mekong_bankruptcy_petition`: Tiếp nhận và thẩm tra đơn mở thủ tục phá sản theo Điều 4, 5.
- `mekong_bankruptcy_claim`: Đăng ký và xác minh yêu cầu đòi nợ của chủ nợ theo Điều 64-67.
- `mekong_bankruptcy_meeting`: Thẩm tra túc số và Nghị quyết Hội nghị chủ nợ theo Điều 75-86.
- `mekong_bankruptcy_distribute`: Phân chia tài sản thanh lý theo thứ tự ưu tiên luật định tại Điều 54.
- `mekong_bankruptcy_list`: Tra cứu hồ sơ Quản tài viên, đơn yêu cầu, chủ nợ, hội nghị và phân chia tài sản.
- `mekong_bankruptcy_status`: Báo cáo chỉ số telemetry hoạt động giải quyết phá sản doanh nghiệp toàn quốc.
