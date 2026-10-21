# Báo cáo Nghiên cứu Kỹ thuật: Maritime Phases 343–346

## 1. Mục tiêu & Phạm vi Nghiên cứu
- **Phase 343: ECDIS Passage Planning & Safety Contour**
  - Nghiên cứu SOLAS V/34 & IMO Res. A.893(21).
  - Thuật toán tính độ sâu an toàn (Safety Depth) có xét đến mớn nước tĩnh (Static Draft), hiệu ứng ngồi đáy (Ship Squat), dự phòng dưới ky tàu (UKC), độ cao thủy triều và dung sai vùng độ tin cậy hải đồ CATZOC (Zone of Confidence A1/A2/B/C/U).
  - Xác lập giới hạn lệch tim luồng Cross Track Limit (XTL) và hình nón cảnh báo chống mắc cạn tự động (Look-Ahead anti-grounding safety cone).
- **Phase 344: Bunkering Coriolis MFM Mass Balance & Protest**
  - Nghiên cứu tiêu chuẩn Singapore SS 648:2019 và ISO 22192 cho hệ thống đo lưu lượng khối lượng Coriolis MFM.
  - Ma trận phát hiện hiện tượng bọt khí xâm thực ăn gian thể tích (Cappuccino Effect) qua chỉ số Drive Gain (> 80%) và biến động tỷ trọng.
  - Đối soát chênh lệch khối lượng cấp dầu so với đo két thủ công (Vessel Sounding), ngưỡng phát hành Notice of Protest (NoP) khi độ lệch vượt quá MPE $\pm 0.5\%$.
- **Phase 345: Marine Auxiliary Boiler Water Chemical Treatment**
  - Nghiên cứu tiêu chuẩn xử lý nước nồi hơi tàu biển ISO 5814 và BS 2486.
  - Kiểm soát các chỉ tiêu: Độ cứng ($0\text{ ppm}$), Clorua ($Cl^- \le 300\text{ ppm}$), Độ kiềm $P\text{-Alk}$ ($100 - 300\text{ ppm}$), pH ($9.5 - 11.0$), Dư lượng khử oxy Hydrazine ($0.05 - 0.2\text{ ppm}$) và Phosphate tồn dư ($20 - 40\text{ ppm}$).
  - Công thức tính toán tỷ lệ xả đáy (Blowdown Rate) ngăn ngừa nồng độ Clorua tăng cao gây nứt ăn mòn ứng suất.
- **Phase 346: Port Agency Disbursements Account (PDA/FDA) Reconciliation**
  - Nghiên cứu hợp đồng đại lý chuẩn FONASBA và biểu phí cảng biển theo Thông tư 39/2023/TT-BGTVT và Nghị định 58/2017/NĐ-CP.
  - Mô hình đối soát ngân sách: Tạm ứng (Cash Advance) vs Quyết toán thực tế (FDA) gồm phí trọng tải, bảo đảm hàng hải, hoa tiêu, lai dắt, cầu bến, bốc dỡ và phí đại lý ủy thác.
  - Cảnh báo chênh lệch ngân sách từng khoản mục $> 5\%$ và xác thực mã băm SHA-256 biên bản quyết toán.

## 2. Tiêu chí Kỹ thuật & Ràng buộc Kiến trúc
- Tuân thủ nghiêm ngặt nguyên tắc **KISS, YAGNI, DRY**.
- Mỗi file mã nguồn và test phải tuyệt đối **dưới 200 dòng (LOC < 200)**.
- Mô hình kiến trúc: **Hybrid Modular Facade**:
  - Sub-modules độc lập trong `src/core/maritime/`
  - Central Facade re-export trong `src/core/`
  - Command CLI Typer với 8 bí danh tiếng Việt
  - FastMCP tool endpoints trong `scripts/mcp_server.py`
  - 100% kiểm thử zero-mock, không dùng dữ liệu giả lập hay thư viện mock ngoài chuẩn.
