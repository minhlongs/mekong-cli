# Phase 04: BIMCO Charterparty & Arbitration Settlement

**Mục tiêu:** Xây dựng micro-engine phân tích tranh chấp hợp đồng thuê tàu BIMCO và tính toán thời gian làm hàng/phạt thưởng theo thông lệ LMAA và VMAC.

## Yêu cầu Kỹ thuật
1. Lọc dữ liệu thời tiết thuận lợi (Good Weather Exclusion): loại trừ khi $\text{Beaufort} > 4$ hoặc $\text{Douglas Sea State} > 3$.
2. Tính toán thiệt hại vi phạm tốc độ và tiêu thụ nhiên liệu (Speed & Fuel Warranty underperformance claim).
3. Tính toán Laytime, thời gian dôi nhật và tiền phạt/thưởng (Demurrage & Despatch, Reversible Laytime).
4. Phân định tranh chấp theo thủ tục rút gọn LMAA ICP hoặc VMAC.
5. File code: `src/core/maritime/phase_338_charterparty_arbitration.py` ($< 200\text{ LOC}$).
