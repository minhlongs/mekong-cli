# Mekong Enterprise Suite — Architecture & Technical Specifications

**Version**: 1.0.0 (Phase 154 - 158)  
**Author**: Antigravity Platform Engine  
**Standards**: 100% Python Standard Library, Zero Third-Party Vendor Locks  

---

## 1. Overview & 5 Core Subsystems

Mekong Enterprise Suite is an integrated legal, financial, and operational intelligence platform designed for Vietnamese one-person companies, SMEs, and foreign-invested enterprises (FDI).

```
┌────────────────────────────────────────────────────────────────────────┐
│                      MEKONG ENTERPRISE SUITE                           │
├─────────────────┬─────────────────┬──────────────────┬─────────────────┤
│ 1. Doanh nghiệp │ 2. Sở hữu       │ 3. Lao động &    │ 4. Đối soát     │
│    & Đầu tư FDI │    Trí tuệ      │    Tiền lương    │    VietQR & Bank│
│ (DN & FDI Law)  │ (IP & Trademark)│ (Labor & BHXH)   │ (EMVCo Recon)   │
├─────────────────┴─────────────────┴──────────────────┴─────────────────┤
│ 5. Hợp đồng Thương mại & Đánh giá Tuân thủ Doanh nghiệp Tổng thể      │
│    (Commercial Contracts & Unified Enterprise Health Audit Engine)     │
└────────────────────────────────────────────────────────────────────────┘
```

### Subsystem 1: Doanh nghiệp & Đầu tư (DN & FDI)
- **Legal Base**: Luật Doanh nghiệp số 59/2020/QH14, Luật Đầu tư số 61/2020/QH14, Nghị định 01/2021/NĐ-CP, Nghị định 31/2021/NĐ-CP.
- **Key Capabilities**:
  - Đánh giá cơ cấu vốn, tiến độ góp vốn điều lệ (hạn 90 ngày).
  - Kiểm tra tỷ lệ sở hữu nhà đầu tư nước ngoài (Foreign Ownership Limit) theo cam kết WTO, CPTPP, EVFTA.
  - Quản trị biểu quyết Hội đồng thành viên (HĐTV), Đại hội đồng cổ đông (ĐHĐCĐ).
  - Thủ tục chi nhánh, văn phòng đại diện, địa điểm kinh doanh.

### Subsystem 2: Sở hữu Trí tuệ (IP & Trademark)
- **Legal Base**: Luật Sở hữu trí tuệ số 50/2005/QH11 (sửa đổi 2022 số 07/2022/QH15), Nghị định 65/2023/NĐ-CP.
- **Key Capabilities**:
  - Tra cứu nhãn hiệu theo 45 nhóm Bảng phân loại Nice (Nice Classification 12th).
  - Thuật toán đánh giá tính phân biệt và rủi ro từ chối bảo hộ (Distinctiveness Scoring).
  - Quản lý hồ sơ bản quyền phần mềm / tác phẩm ứng dụng.
  - Rà soát xâm phạm nhãn hiệu và ước tính thiệt hại bồi thường theo luật định.

### Subsystem 3: Lao động, Tiền lương & BHXH (Labor & HR)
- **Legal Base**: Bộ luật Lao động số 45/2019/QH14, Luật BHXH số 58/2014/QH13, Nghị định 74/2024/NĐ-CP (Lương tối thiểu vùng).
- **Key Capabilities**:
  - Quản lý 3 loại hợp đồng lao động: Không xác định thời hạn, Xác định thời hạn (tối đa 36 tháng, 2 lần), Thử việc (30/60/180 ngày).
  - Lương tối thiểu vùng I (4.960.000đ), II (4.410.000đ), III (3.860.000đ), IV (3.450.000đ).
  - Trích đóng bảo hiểm bắt buộc: NLĐ 10.5% (8% BHXH + 1.5% BHYT + 1% BHTN); Doanh nghiệp 23.5% (17.5% BHXH + 3% BHYT + 1% BHTN + 2% Công đoàn). Trần đóng 20 lần mức lương cơ sở (46.800.000đ).
  - Thuế TNCN lũy tiến 7 bậc (giảm trừ bản thân 11tr, người phụ thuộc 4.4tr).

### Subsystem 4: Đối soát VietQR & Giao dịch Ngân hàng (VietQR Recon)
- **Technical Base**: Napas 247 VietQR Standard (EMVCo QR Code Specification), Webhook HMAC-SHA256 signature verification.
- **Key Capabilities**:
  - Sinh chuỗi payload VietQR động theo chuẩn EMVCo Merchant-Presented QR Code.
  - Xác thực chữ ký số HMAC-SHA256 của Webhook ngân hàng (SePay, Casso, VietQR API).
  - Thuật toán Fuzzy Matching & trích xuất mã hóa đơn từ nội dung chuyển khoản tự do.
  - Tự động chuyển đổi trạng thái hóa đơn (UNPAID -> PARTIAL -> SETTLED -> OVERPAID) và sinh định khoản kế toán Nợ 112 / Có 131.

### Subsystem 5: Hợp đồng Thương mại & Enterprise Health Audit
- **Legal Base**: Luật Thương mại 2005, Bộ luật Dân sự 2015.
- **Key Capabilities**:
  - Thẩm định điều khoản hợp đồng mua bán, dịch vụ, NDA: rà soát mức phạt vi phạm (tối đa 8% theo Điều 301 LTM).
  - Enterprise Health Index: chấm điểm toàn diện 5 trụ cột (Pháp lý DN, Bản quyền SHTT, Tuân thủ Lao động, Đối soát Tài chính, An toàn Hợp đồng) từ 0 - 100 điểm với đề xuất khắc phục cụ thể.
