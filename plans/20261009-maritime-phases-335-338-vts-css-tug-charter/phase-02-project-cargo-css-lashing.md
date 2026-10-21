# Phase 02: Project Cargo & Heavy Lift CSS Lashing Safety

**Mục tiêu:** Xây dựng micro-engine tính toán an toàn chằng buộc hàng siêu trường siêu trọng (OOG/Project Cargo) theo IMO CSS Code Annex 13.

## Yêu cầu Kỹ thuật
1. Tính toán lực trượt ngang ($F_{\text{slide}}$) và lực lật ($M_{\text{tipping}}$) dựa trên gia tốc chuyển động tàu ($a_x, a_y, a_z$).
2. Mô hình ma sát dunnage/đệm lót ($\mu = 0.3$ gỗ/thép, $\mu = 0.1$ thép/thép).
3. Đóng góp lực chằng buộc hiệu dụng của cáp/xích chằng ($MSL \cdot \cos(\alpha) \cdot \cos(\beta)$).
4. Kiểm định hệ số an toàn:
   $$S_F = \frac{\sum F_{\text{lash\_res}} + F_{\text{friction}}}{F_{\text{external}}} \ge 1.25$$
5. File code: `src/core/maritime/phase_336_project_cargo_css_lashing.py` ($< 200\text{ LOC}$).
