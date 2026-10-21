# Phase 01: Thiết kế Lõi Modular & Central Facade

## 1. Mục tiêu
Xây dựng 4 micro-modules kỹ thuật độc lập trong `src/core/maritime/` và một facade duy nhất `src/core/maritime_ballast_decarb_lifting_spill_engine.py` re-export đầy đủ để đảm bảo tính module hóa và tương thích ngược.

## 2. Danh sách files
1. `src/core/maritime/phase_327_ballast_water_uscg.py` (146 LOC):
   - Đánh giá IMO D-2 vs USCG CMF/FDA standards.
   - Kiểm tra UV Transmittance (>= 50%) và TRO Neutralization (Tro <= 0.1 mg/L).
   - Kiểm tra cặn đáy két dằn (sediment stripping < 5% volume).
2. `src/core/maritime/phase_328_decarb_fueleu_fuels.py` (152 LOC):
   - Tính toán nghĩa vụ nộp hạn ngạch EU ETS Maritime MRV theo phase-in schedule.
   - Tính toán tuân thủ FuelEU GHG Intensity và Pooling thặng dư/thâm hụt.
   - Kiểm định an toàn tra nạp nhiên liệu Methanol/Ammonia (N2 purge O2 < 2%, leak ppm, safety radius).
3. `src/core/maritime/phase_329_lifting_appliances.py` (127 LOC):
   - Tính toán tải trọng thử Proof Load theo ILO 152 & QCVN 23:2010/BGTVT.
   - Đánh giá tiêu chuẩn loại bỏ cáp thép ISO 4309 (đứt sợi, giảm đường kính >= 7%, rỗ ăn mòn).
   - Kiểm tra chu kỳ đăng kiểm hàng năm và 5 năm.
4. `src/core/maritime/phase_330_oil_spill_oprc_neba.py` (118 LOC):
   - Phân cấp sự cố tràn dầu OPRC 1990 Tier 1-3.
   - Ma trận NEBA cho việc sử dụng chất phân tán (độ sâu >= 10m, cách bờ >= 3 NM, độ nhớt < 10,000 cSt).
   - Tính toán chiều dài phao quây L = 3x LOA và công suất thu gom máy hút dầu skimmer.
5. `src/core/maritime_ballast_decarb_lifting_spill_engine.py` (43 LOC): Facade re-exporting all.

## 3. Checklist Thực hiện
- [x] Tạo `phase_327_ballast_water_uscg.py`.
- [x] Tạo `phase_328_decarb_fueleu_fuels.py`.
- [x] Tạo `phase_329_lifting_appliances.py`.
- [x] Tạo `phase_330_oil_spill_oprc_neba.py`.
- [x] Cập nhật `src/core/maritime/__init__.py`.
- [x] Tạo `src/core/maritime_ballast_decarb_lifting_spill_engine.py`.
- [x] Kiểm tra LOC từng file (< 200 LOC: 146, 152, 127, 118, 43 LOC).
