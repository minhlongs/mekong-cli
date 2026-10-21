# Hướng dẫn Thiết kế Giao diện & Trực quan hóa Dữ liệu: Maritime Phases 335–338

## 1. Màu sắc & Chỉ báo Trạng thái (Design Tokens)
- **Cảnh báo Nguy cấp (Critical Alert)**: Đỏ (#EF4444) — Đi ngược luồng TSS, $S_F < 1.25$ mất an toàn lashing, $\text{CPA} < 0.5\text{ NM}$, $\text{SoC} < 20\%$.
- **Cảnh báo Suy giảm (Warning/Degraded)**: Vàng Hổ phách (#F59E0B) — Chênh lệch tốc độ hợp đồng, sụt áp trạm sạc bờ, $1.25 \le S_F < 1.5$.
- **Tuân thủ Hoàn toàn (Compliant/Normal)**: Xanh Lục (#10B981) — Đúng luồng hành hải, $S_F \ge 1.5$, hòa lưới an toàn, thời gian làm hàng đạt chuẩn.
- **Dữ liệu Hàng hải (Maritime Theme)**: Xanh Đại dương (#0284C7), Nền tối (#0F172A).

## 2. Bố cục Thông tin (Layout)
- **VTS Radar Monitor**: Hiển thị bảng vector mục tiêu (Target Vectors), khoảng cách CPA (hải lý) và thời gian TCPA (phút).
- **CSS Lashing Matrix**: Bảng phân bổ lực trượt/lật, góc chằng buộc và hệ số an toàn $S_F$.
- **Cold Ironing Gauge**: Thanh đo tỷ lệ nạp/xả trạm ắc quy, công suất tiêu thụ lưới bờ và lượng $CO_2$ cắt giảm.
- **Charterparty Settlement**: Bảng quyết toán thời gian làm hàng (Laytime Timeline), phân định thưởng/phạt và điều khoản loại trừ thời tiết xấu.
