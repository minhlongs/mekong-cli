# Mekong Enterprise Suite — Documentation & Architecture Guide (Phases 154 - 158)

Mekong Enterprise Suite cung cấp hệ thống điều hành tuân thủ pháp lý, quản trị nhân sự - tiền lương, bảo hộ tài sản trí tuệ, và tự động hóa đối soát thanh toán chuẩn quốc gia cho doanh nghiệp Việt Nam.

## 5 Trụ Cột Điều Hành (5 Enterprise Pillars)

1. **Doanh nghiệp & Đầu tư FDI (`EnterpriseFDIEngine`)**
   - Căn cứ: Luật Doanh nghiệp 2020 (Điều 47, 75) & Luật Đầu tư 2020 (Điều 26).
   - Kiểm tra thời hạn góp vốn 90 ngày kể từ ngày cấp ĐKKD, tỷ lệ góp vốn thực tế, cảnh báo chế tài xử phạt vi phạm hành chính (Nghị định 122/2021/NĐ-CP: 30 - 50 triệu VNĐ).
   - Thẩm định hạn mức sở hữu nước ngoài (FOL) theo cam kết WTO và danh mục ngành nghề tiếp cận thị trường có điều kiện (IT/Phần mềm 100%, Logistics 51%, Fintech 50%). Kích hoạt thủ tục đăng ký góp vốn/mua cổ phần khi FDI > 50%.

2. **Sở hữu Trí tuệ & Nhãn hiệu (`IntellectualPropertyEngine`)**
   - Căn cứ: Luật Sở hữu trí tuệ 2005 (sửa đổi 2022) & Nghị định 65/2023/NĐ-CP.
   - Tra cứu tra cứu chuẩn 45 nhóm Nice quốc tế về phân loại hàng hóa & dịch vụ.
   - Đánh giá định lượng tính phân biệt (Distinctiveness Score 0 - 100). Thuật toán chuẩn hóa tiếng Việt không dấu bóc tách và từ chối các dấu hiệu mô tả chung ("phần mềm", "công ty", "dịch vụ", "chất lượng").

3. **Lao động, Tiền lương & BHXH Bắt buộc (`LaborHRMEngine`)**
   - Căn cứ: Bộ luật Lao động 2019 & Nghị định 74/2024/NĐ-CP.
   - Bảng lương 4 vùng tối thiểu: Vùng I (4.960.000 VNĐ), Vùng II (4.410.000 VNĐ), Vùng III (3.860.000 VNĐ), Vùng IV (3.450.000 VNĐ).
   - Lương cơ sở: 2.340.000 VNĐ.
   - Trần đóng bảo hiểm luật định độc lập: BHXH/BHYT trần 20 lần lương cơ sở (46.800.000 VNĐ); BHTN trần 20 lần lương tối thiểu vùng (Điều 58 Luật Việc làm 2013, trần Vùng I là 99.200.000 VNĐ).
   - Trích nộp bắt buộc: NLĐ 10.5% (BHXH 8%, BHYT 1.5%, BHTN 1%); Doanh nghiệp 23.5% (BHXH 17.5%, BHYT 3%, BHTN 1%, Kinh phí công đoàn 2%).
   - Thuế TNCN lũy tiến 7 bậc sau giảm trừ gia cảnh bản thân (11 triệu) và người phụ thuộc (4.4 triệu/người).

4. **Đối soát VietQR & Ngân hàng (`VietQRReconEngine`)**
   - Căn cứ: Chuẩn Napas 247 & Đặc tả EMVCo Merchant-Presented QR Code.
   - Sinh chuỗi payload TLV với Merchant Account Information (Tag 38, AID `A000000727`), tiền tệ Tag 53 ('704'), và mã kiểm tra checksum CRC16-CCITT (Tag 63, đa thức 0x1021).
   - Xác thực Webhook biến động số dư ngân hàng qua chữ ký HMAC-SHA256 với `hmac.compare_digest` chống timing attacks.
   - Tự động sinh bút toán kế toán đối soát VAS: Nợ TK 1121 (Tiền gửi ngân hàng) / Có TK 131 (Phải thu khách hàng).

5. **Hợp đồng Thương mại & Audit Hub (`EnterpriseAuditEngine`)**
   - Căn cứ: Luật Thương mại 2005 (Điều 301).
   - Thẩm định trần phạt vi phạm hợp đồng tối đa 8% phần giá trị nghĩa vụ hợp đồng bị vi phạm; cảnh báo vô hiệu phần vượt trần.
   - Tổng hòa điểm số 360 độ sức khỏe doanh nghiệp (Enterprise Health Score 0 - 100) và xếp hạng rủi ro (LOW, MEDIUM, HIGH, CRITICAL).

## Hướng Dẫn Sử Dụng CLI

```bash
# Bảng điều khiển trung tâm
mekong enterprise
mekong doanhnghiep

# 1. Thẩm tra góp vốn và điều kiện đầu tư FDI
mekong enterprise corp --committed 2000000000 --contributed 2000000000 --inc-date 2026-01-01 --sector it_software --foreign-pct 0

# 2. Thẩm định khả năng đăng ký nhãn hiệu
mekong enterprise ip --mark "MekongAI" --class 9

# 3. Tính lương Gross-Net và trích nộp bảo hiểm
mekong enterprise labor --gross 30000000 --dependents 1 --region 1

# 4. Sinh mã VietQR động theo chuẩn EMVCo
mekong enterprise recon --bin 970422 --account 0123456789 --amount 500000 --memo "HD-001"

# 5. Kiểm tra mức trần phạt vi phạm hợp đồng (Điều 301 LTM)
mekong enterprise contract --value 1000000000 --penalty-pct 8.0

# 6. Đánh giá sức khỏe pháp lý & tài chính tổng thể
mekong enterprise audit --committed 2000000000 --contributed 2000000000 --mark "MekongAI" --class 9 --employees 10
```

## Tích hợp MCP Protocol (Model Context Protocol)

Các công cụ được đăng ký sẵn qua cả in-process FastMCP server và stdio JSON-RPC server:
- `mekong_enterprise_corp`
- `mekong_enterprise_ip`
- `mekong_enterprise_labor`
- `mekong_enterprise_recon`
- `mekong_enterprise_audit`
