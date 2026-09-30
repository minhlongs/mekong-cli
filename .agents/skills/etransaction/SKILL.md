---
name: etransaction
description: Vietnamese Electronic Transactions, Digital Signatures, Trust Services & Data Messages Suite.
---

# mekong etransaction — Autonomous Vietnamese Electronic Transactions & Digital Trust Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Giao dịch điện tử 2023 (Luật số 20/2023/QH15 - Có hiệu lực thi hành từ ngày 01/07/2024)**:
   - Thống nhất khung pháp lý quốc gia về thông điệp dữ liệu, chữ ký điện tử, dịch vụ tin cậy và hợp đồng điện tử.
   - **Giá trị pháp lý của thông điệp dữ liệu như văn bản (Điều 9)**: Thông tin trong thông điệp dữ liệu có giá trị như văn bản nếu thông tin đó có thể truy cập và sử dụng được để tham chiếu khi cần thiết.
   - **Giá trị pháp lý của thông điệp dữ liệu như bản gốc (Điều 10)**: Có giá trị như bản gốc khi nội dung được bảo đảm toàn vẹn từ khi được khởi tạo lần đầu dưới dạng một thông điệp dữ liệu hoàn chỉnh và có thể truy cập được.
   - **Giá trị pháp lý của thông điệp dữ liệu làm chứng cứ (Điều 11)**: Thông điệp dữ liệu có giá trị làm chứng cứ theo quy định của Luật này và pháp luật về tố tụng (Bộ luật Tố tụng Dân sự 2015 Điều 95).
   - **Chuyển đổi giữa văn bản giấy và thông điệp dữ liệu (Điều 12)**: Phải đáp ứng điều kiện về tính toàn vẹn, có dấu hiệu khẳng định đã chuyển đổi, thông tin của cơ quan/tổ chức thực hiện chuyển đổi.
2. **Chữ ký điện tử & Chữ ký số (Điều 21 - 25 & Nghị định số 130/2018/NĐ-CP)**:
   - Phân loại chữ ký điện tử (Điều 21):
     * *Chữ ký điện tử thông thường*: Click-wrap, OTP SMS, email xác nhận.
     * *Chữ ký điện tử chuyên dùng*: Do cơ quan, tổ chức tạo lập để sử dụng nội bộ.
     * *Chữ ký số (Qualified PKI)*: Chữ ký điện tử sử dụng thuật toán mã hóa khóa không đối xứng, gắn với chứng thư chữ ký số do Tổ chức cung cấp dịch vụ chứng thực chữ ký số công cộng (VNPT-CA, Viettel-CA, FPT-CA, BKAV-CA...) hoặc chứng thực chuyên dùng cấp.
   - Điều kiện bảo đảm an toàn cho chữ ký số (Điều 22): Dữ liệu tạo chữ ký gắn duy nhất với người ký, thuộc quyền kiểm soát của người ký, mọi thay đổi sau thời điểm ký đều bị phát hiện.
3. **Dịch vụ tin cậy (Điều 28 - 32)**:
   - Dịch vụ cấp dấu thời gian (RFC 3161 compliant time-stamping service).
   - Dịch vụ chứng thực thông điệp dữ liệu.
   - Dịch vụ chứng thực chữ ký số công cộng.
4. **Hợp đồng điện tử & Chứng thực CeCA (Điều 34 - 38 & Nghị định số 52/2024/NĐ-CP)**:
   - Giao kết và thực hiện hợp đồng điện tử: Thông báo, chấp nhận đề nghị, ký kết điện tử đa bên.
   - Tổ chức cung cấp dịch vụ chứng thực hợp đồng điện tử (CeCA - Certified e-Contract Authority) được Bộ Công Thương cấp phép: Gắn con dấu xác thực hợp đồng điện tử, bảo đảm tính chống chối bỏ và giá trị thi hành pháp lý cao nhất.
5. **Lưu trữ SQLite WAL**: Bảng `data_messages`, `electronic_signatures`, `trust_tokens`, `electronic_contracts` tại `~/.mekong/etransaction.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan hoạt động giao dịch điện tử, chữ ký số, dịch vụ tin cậy
mekong etransaction

# Khởi tạo thông điệp dữ liệu điện tử pháp lý (Điều 9-11)
mekong etransaction message "Biên bản Bàn giao Thiết bị CNTT & Tài sản Số" --content '{"asset_id":"SRV-9901","serial":"DELL-R750-88","status":"ACCEPTANCE_PASSED"}' --originator "Công ty TNHH Công nghệ Alpha" --recipient "Tập đoàn Viễn thông Beta" --format json --original --retention 10

# Xác minh tính toàn vẹn và giá trị chứng cứ của thông điệp dữ liệu
mekong etransaction verify-msg "MSG-XXXXXXXX"

# Chuyển đổi văn bản giấy sang dữ liệu điện tử (Điều 12)
mekong etransaction convert --paper-ref "Số 108/BB-BCT ngày 15/03/2026" --converted-by "Văn phòng Công chứng Sài Gòn" --content "Bản số hóa hợp đồng chuyển nhượng quyền sử dụng đất..." --title "Bản điện tử chuyển đổi Giấy chuyển nhượng QSDĐ" --recipient "Ngân hàng TMCP Ngoại thương Việt Nam"

# Tạo chữ ký số công cộng (QUALIFIED PKI) theo Luật GDĐT 2023 & NĐ 130/2018/NĐ-CP
mekong etransaction sign "MSG-XXXXXXXX" --signer "Nguyễn Văn An - Giám đốc Điều hành" --role "legal_representative" --type QUALIFIED --ca "VNPT-CA" --serial "5404BFA6C723810E" --valid-until "2028-12-31T23:59:59Z"

# Xác minh tính hợp lệ và chứng thư của chữ ký số
mekong etransaction verify-sig "SIG-XXXXXXXX"

# Cấp dấu thời gian RFC 3161 hoặc chứng thư tin cậy
mekong etransaction trust "MSG-XXXXXXXX" --type TIMESTAMP --authority "Vietnam National Timestamp Authority" --license "BTTTT-TRUST-088/GP"

# Khởi tạo hợp đồng điện tử đa bên (Điều 34-38)
mekong etransaction contract --number "CTR-2026-CLOUD-01" --title "Hợp đồng Cung cấp Dịch vụ Điện toán Đám mây & AI Sandbox" --party-a "Công ty TNHH Giải pháp Đám mây Mekong" --party-b "Công ty CP Bán lẻ Toàn Cầu" --value 360000000 --currency VND --content "Điều khoản cung cấp hạ tầng GPU & cam kết SLA 99.99%..."

# Ký hợp đồng điện tử
mekong etransaction sign-contract "CTR-XXXXXXXX" --party "Công ty TNHH Giải pháp Đám mây Mekong" --role "legal_representative" --type QUALIFIED --ca "VNPT-CA"
mekong etransaction sign-contract "CTR-XXXXXXXX" --party "Công ty CP Bán lẻ Toàn Cầu" --role "legal_representative" --type QUALIFIED --ca "Viettel-CA"

# Gắn dấu xác thực CeCA của Bộ Công Thương lên hợp đồng đã ký kết hoàn tất (Nghị định 52/2024/NĐ-CP)
mekong etransaction ceca "CTR-XXXXXXXX" --authority "CeCA-Vietnam-Post" --license "BCT-CeCA-008/GP"

# Tra cứu dữ liệu giao dịch điện tử
mekong etransaction list --type all --limit 20
mekong etransaction list --type contracts
mekong etransaction list --type messages
mekong etransaction list --type signatures

# Trích xuất dữ liệu máy học / CI
mekong etransaction --json
mekong etransaction status --json
```

---

## MCP Tools Integration
- `mekong_etransaction_message_create`: Khởi tạo và lưu trữ thông điệp dữ liệu pháp lý theo Luật GDĐT 2023.
- `mekong_etransaction_message_verify`: Xác minh tính toàn vẹn và hiệu lực pháp lý của thông điệp dữ liệu.
- `mekong_etransaction_sign`: Ký điện tử / ký số PKI có chứng thực CA hợp lệ.
- `mekong_etransaction_verify_signature`: Giám định tính hợp lệ của chữ ký điện tử / chữ ký số.
- `mekong_etransaction_trust_issue`: Cấp dấu thời gian hoặc chứng thư dịch vụ tin cậy.
- `mekong_etransaction_contract_manage`: Khởi tạo, ký kết hoặc chứng thực CeCA hợp đồng điện tử.
- `mekong_etransaction_status`: Kiểm tra telemetry và độ tuân thủ quy định pháp luật.
