---
name: publicdebt
description: Vietnamese Public Debt, Sovereign Bonds, ODA On-Lending & Debt Safety Red Lines Suite.
---

# mekong publicdebt — Autonomous Vietnamese Public Debt & Sovereign Credit Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật Quản lý nợ công 2017 (Luật số 20/2017/QH14) & Nghị định số 94/2018/NĐ-CP**:
   - Thống nhất quản lý an toàn nợ công, bảo đảm an ninh tài chính quốc gia và cân đối vĩ mô.
   - **Phân loại 3 cấu phần nợ công (Điều 4)**:
     * *Nợ Chính phủ (Government Debt)*: Phát hành Trái phiếu Chính phủ (TPCP), công trái xây dựng Tổ quốc, vay ODA và vay ưu đãi nước ngoài, phát hành trái phiếu quốc tế (Sovereign Eurobond).
     * *Nợ được Chính phủ bảo lãnh (Government-Guaranteed Debt)*: Doanh nghiệp vay vốn phục vụ các công trình, dự án trọng điểm quốc gia, ngân hàng chính sách nhà nước (VDB, NHCSXH).
     * *Nợ chính quyền địa phương (Local Government Debt)*: Trái phiếu chính quyền địa phương (TP. Hà Nội, TP.HCM...), vay lại từ nguồn vốn vay ODA và ưu đãi nước ngoài của Chính phủ.
   - **Chỉ tiêu an toàn nợ công & Giới hạn đỏ (Điều 19 & Nghị quyết Quốc hội)**:
     * Nợ công không quá **60%** GDP.
     * Nợ Chính phủ không quá **50%** GDP.
     * Nợ nước ngoài của quốc gia không quá **50%** GDP.
     * Nghĩa vụ trả nợ trực tiếp của Chính phủ (không bao gồm cho vay lại) không quá **25%** tổng thu ngân sách nhà nước hằng năm.
2. **Cho vay lại vốn vay ODA và vay ưu đãi nước ngoài (Nghị định số 97/2018/NĐ-CP)**:
   - Cơ chế cho vay lại đối với UBND cấp tỉnh và doanh nghiệp nhà nước (DNNN).
   - Phí cho vay lại từ $0,25\%$ đến $0,5\%$/năm để bù đắp chi phí quản lý và dự phòng rủi ro.
   - Thẩm định năng lực tài chính, tài sản bảo đảm và phân loại rủi ro tín dụng đơn vị vay lại (`LOW`, `MEDIUM`, `HIGH`).
3. **Cấp và quản lý bảo lãnh Chính phủ (Nghị định số 91/2018/NĐ-CP)**:
   - Phí bảo lãnh Chính phủ từ $0,25\%$ đến $2,0\%$/năm trên dư nợ bảo lãnh.
   - Bắt buộc lập Quỹ tích lũy trả nợ (Debt Service Escrow Reserve Fund) để bảo đảm khả năng trả nợ thay khi bên được bảo lãnh gặp khó khăn.
4. **Lưu trữ SQLite WAL**: Bảng `debt_instruments`, `debt_service_schedules`, `onlending_agreements`, `debt_safety_assessments` tại `~/.mekong/publicdebt.db` (override qua `MEKONG_PUBLICDEBT_DB`).

---

## CLI Invocations

```bash
# Báo cáo tổng quan tình hình nợ công, nợ Chính phủ và chỉ tiêu an toàn
mekong publicdebt

# Đăng ký công cụ nợ công / Trái phiếu Chính phủ / Hiệp định vay ODA
mekong publicdebt instrument --code "TPCP-2026-10Y-01" --category "GOVERNMENT_DEBT" --type "TREASURY_BOND" --creditor "Kho bạc Nhà nước" --borrower "Chính phủ Việt Nam" --amount 15000000000000 --currency "VND" --rate 3.85 --tenor 10 --issue-date "2026-01-15"

# Lập lịch trình thanh toán gốc, lãi và phí nghĩa vụ trả nợ công
mekong publicdebt schedule --code "TPCP-2026-10Y-01" --period "2026-K1" --due-date "2026-07-15" --principal 0 --interest 288750000000 --fees 1500000000

# Thực hiện thanh toán trả nợ từ Quỹ tích lũy trả nợ hoặc NSNN
mekong publicdebt repay "SCHED-A1B2C3D4" --amount 290250000000

# Ký hợp đồng cho vay lại vốn ODA cho dự án cơ sở hạ tầng địa phương
mekong publicdebt onlend --code "CVL-2026-HCM-METRO2" --parent-debt "WB-ODA-VN01" --borrower "UBND TP. Hồ Chí Minh" --project "Tuyến Metro số 2 Bến Thành - Tham Lương" --amount 8500000000000 --fee 0.25 --risk "LOW"

# Đánh giá chỉ tiêu an toàn nợ công và kiểm tra giới hạn đỏ Quốc hội
mekong publicdebt safety --year 2026 --gdp 12500000000000000 --revenue 2100000000000000

# Tra cứu dữ liệu quản lý nợ công
mekong publicdebt list --type all --limit 20
mekong publicdebt list --type instruments
mekong publicdebt list --type schedules
mekong publicdebt list --type onlending
mekong publicdebt list --type assessments

# Báo cáo trạng thái telemetry nợ công
mekong publicdebt status --json
```

---

## MCP Tools Integration (Dual Parity)

- `mekong_publicdebt_instrument`: Đăng ký công cụ nợ công, trái phiếu Chính phủ hoặc khoản vay ODA.
- `mekong_publicdebt_schedule`: Lập lịch trình trả nợ gốc, lãi và phí quản lý nợ công.
- `mekong_publicdebt_repay`: Xác nhận trích quỹ tích lũy trả nợ thanh toán nghĩa vụ nợ.
- `mekong_publicdebt_onlend`: Ký kết hợp đồng cho vay lại vốn vay ODA cho địa phương/DNNN.
- `mekong_publicdebt_safety`: Đánh giá 4 chỉ tiêu an toàn nợ công theo trần luật định (60%, 50%, 50%, 25%).
- `mekong_publicdebt_list`: Tra cứu danh sách công cụ nợ, lịch trả nợ, cho vay lại, an toàn nợ.
- `mekong_publicdebt_status`: Tổng hợp chỉ số nợ công, nợ Chính phủ và cảnh báo an ninh tài chính.
