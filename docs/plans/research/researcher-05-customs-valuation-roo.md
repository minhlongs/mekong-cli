# Researcher Report: Vietnam Customs Valuation & Rules of Origin (ROO) Engine (Phase 167)

**Author:** Researcher Subagent  
**Date:** 2026-10-07  
**Scope:** Luật Hải quan 2014, Nghị định 08/2015/NĐ-CP, Nghị định 59/2018/NĐ-CP, Thông tư 39/2015/TT-BTC, Thông tư 60/2019/TT-BTC & Các Hiệp Định Thương Mại Tự Do (FTAs).

---

## 1. Cơ Sở Pháp Lý & Các Phương Pháp Xác Định Trị Giá Hải Quan

### 1.1. Sáu (06) Phương Pháp Xác Định Trị Giá Hải Quan Tuần Tự (Thông tư 39/2015/TT-BTC)
Hải quan Việt Nam áp dụng tuần tự 6 phương pháp xác định trị giá tính thuế đối với hàng nhập khẩu:
1. **Phương pháp 1: Trị giá giao dịch của hàng hóa nhập khẩu (Transaction Value)**
   - Trị giá hải quan = Giá thực tế đã thanh toán hoặc sẽ thanh toán + Các khoản điều chỉnh cộng - Các khoản điều chỉnh trừ.
   - Điều chỉnh cộng: Chi phí hoa hồng bán hàng, phí bao bì, cước vận chuyển quốc tế (F), bảo hiểm quốc tế (I), tiền bản quyền, khoản trợ cấp.
   - Điều chỉnh trừ: Chi phí vận chuyển sau nhập khẩu, thuế/phí tại Việt Nam, chi phí xây dựng/lắp đặt/bảo trì sau nhập khẩu.
2. **Phương pháp 2: Trị giá giao dịch của hàng hóa nhập khẩu giống hệt (Identical Goods)**
3. **Phương pháp 3: Trị giá giao dịch của hàng hóa nhập khẩu tương tự (Similar Goods)**
4. **Phương pháp 4: Trị giá khấu trừ (Deductive Value)**
   - Trị giá tính thuế = Đơn giá bán tại thị trường VN - Hoa hồng/lợi nhuận/chi phí chung - Chi phí vận chuyển/bảo hiểm nội địa - Thuế nhập khẩu & các loại thuế tại VN.
5. **Phương pháp 5: Trị giá tính toán (Computed Value)**
   - Trị giá tính thuế = Chi phí nguyên vật liệu và sản xuất + Chi phí chung và lợi nhuận của nhà sản xuất nước ngoài + Chi phí vận chuyển và bảo hiểm đến cửa khẩu nhập.
6. **Phương pháp 6: Phương pháp suy luận (Fallback Method)**
   - Áp dụng linh hoạt các phương pháp trên dựa trên tài liệu sẵn có hợp pháp.

---

## 2. Quy Tắc Xuất Xứ Hàng Hóa (Rules of Origin - ROO) & Tính Toán RVC

### 2.1. Công thức Hàm lượng Giá trị Khu vực (Regional Value Content - RVC)
Theo các hiệp định ATIGA (Form D), ACFTA (Form E), CPTPP, EVFTA:

1. **Công thức Gián tiếp (Build-down method):**
   $$RVC = \frac{FOB - VNM}{FOB} \times 100\%$$
   - $FOB$: Giá giao lên tàu của sản phẩm xuất khẩu (FOB price).
   - $VNM$: Giá trị nguyên liệu không có xuất xứ (Value of Non-originating Materials) bao gồm nguyên liệu nhập khẩu từ nước ngoài khối FTA hoặc nguyên liệu không xác định được xuất xứ.

2. **Công thức Trực tiếp (Build-up method):**
   $$RVC = \frac{VOM}{FOB} \times 100\%$$
   - $VOM$: Giá trị nguyên liệu có xuất xứ từ các nước thành viên (Value of Originating Materials) + Chi phí nhân công trực tiếp + Chi phí sản xuất chung + Chi phí khác và Lợi nhuận.

3. **Ngưỡng Xuất Xứ Chuẩn:**
   - Hầu hết các FTA truyền thống (ATIGA, ACFTA, AKFTA): Ngưỡng $RVC \ge 40\%$.
   - Hiệp định thế hệ mới (CPTPP, EVFTA): Ngưỡng linh hoạt $RVC \ge 45\% - 50\%$ hoặc kết hợp tiêu chí CTC.

### 2.2. Chuyển Đổi Mã Số Hàng Hóa (Change in Tariff Classification - CTC)
- **CC (Change in Chapter):** Chuyển đổi mã hàng ở cấp 2 chữ số.
- **CTH (Change in Tariff Heading):** Chuyển đổi mã hàng ở cấp 4 chữ số.
- **CTSH (Change in Tariff Sub-heading):** Chuyển đổi mã hàng ở cấp 6 chữ số.
- **De Minimis:** Tỷ lệ nguyên liệu không đáp ứng CTC không được vượt quá 10% giá FOB của thành phẩm.

---

## 3. Thời Hiệu Kiểm Tra Sau Thông Quan (Post-Clearance Audit)
- **Căn cứ:** Điều 77 Luật Hải quan 2014.
- **Thời hiệu:** 05 năm kể từ ngày đăng ký tờ khai hải quan.
- **Quy trình:** Kiểm tra tại trụ sở cơ quan hải quan hoặc kiểm tra tại trụ sở người khai hải quan.
