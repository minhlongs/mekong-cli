# Hướng dẫn Thiết kế Giao diện & Trực quan hóa Dữ liệu: Maritime Phases 399–402

## 1. Màu sắc & Chỉ báo Trạng thái (Design Tokens)
- **Cảnh báo Nguy cấp (Critical Emergency / Trip)**: Đỏ (#EF4444) — Quá nhiệt dầu thủy lực chân vịt mũi ($> 85^\circ\text{C}$), HRU quá hạn bảo dưỡng, rò rỉ áp suất lò đốt, áp suất hơi khoang hàng vượt ngưỡng nguy hại ($> +0.14\text{ bar}$) hoặc nồng độ Oxy VECS $\ge 8.0\%$.
- **Cảnh báo Thận trọng (Warning / Lockout)**: Vàng Hổ phách (#F59E0B) — Hiện tượng xâm thực chân vịt ($\sigma < 0.40$), nhiệt độ lò sơ cấp chưa đủ sấy rác ($< 850^\circ\text{C}$), báo mức cao khoang hàng $95\%$, chênh áp lưới lọc chặn lửa $\Delta P > 0.05\text{ bar}$.
- **Tuân thủ Hoàn toàn (Compliant / Nominal Safe)**: Xanh Lục (#10B981) — Lực đẩy chân vịt danh định, chốt thủy tĩnh cắt dây an toàn hoạt động tự do, khí thải lò đốt đạt chuẩn MEPC.244(66), kiểm soát hơi kín thu hồi VECS an toàn.
- **Giao diện Hàng hải (Maritime Automation Theme)**: Xanh Biển (#0284C7), Nền Thép Đậm (#0F172A), Viền Bảng Kim Loại (#334155).

## 2. Bố cục Thông tin & CLI Dashboards
- **Phase 399 Bow Thruster**: Bảng lực đẩy ngang (Lateral Thrust kN), chỉ số xâm thực ($\sigma$), phụ tải động cơ kW và trạng thái nhiệt độ dầu thủy lực.
- **Phase 400 Liferaft HRU**: Sơ đồ áp suất thủy tĩnh kích hoạt cắt dây, lực kéo đứt mắt yếu (Weak Link Breaking Force), chiều dài dây chằng và niên hạn kiểm định.
- **Phase 401 Waste Incinerator**: Đồng hồ nhiệt độ 2 buồng đốt (Sơ cấp $850^\circ\text{C}$ / Thứ cấp $1100^\circ\text{C}$), nồng độ CO, $O_2$, khói Ringelmann và khóa an toàn nạp rác.
- **Phase 402 Tanker VECS**: Áp suất đường ống hơi (Vapor Manifold P/V), nồng độ $O_2$ (< 8.0%), mức ngắt bơm hàng tự động (High-High 98%) và tình trạng van chống cháy nổ.
