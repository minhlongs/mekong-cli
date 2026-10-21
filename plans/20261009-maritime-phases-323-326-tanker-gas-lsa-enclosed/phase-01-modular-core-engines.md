# Phase 01: Tái cấu trúc Module Lõi & Mặt tiền Thống nhất

## 1. Mục tiêu & Bối cảnh
- Tách nhỏ module `src/core/maritime_tanker_gas_lsa_enclosed_engine.py` (536 dòng) thành 4 module con chuyên biệt dưới 200 LOC nằm trong thư mục `src/core/maritime/`.
- Giữ file `src/core/maritime_tanker_gas_lsa_enclosed_engine.py` làm Facade re-export toàn bộ symbols để không làm gãy bất kỳ import nào trong hệ thống.

## 2. Cấu trúc File triển khai
1. `src/core/maritime/phase_323_tanker_washing.py` (< 170 dòng):
   - `ChemicalPollutionCategory` (Enum: CAT_X, CAT_Y, CAT_Z, OS)
   - `CrudeOilWashingInput`, `ChemicalTankerPrewashInput`, `TankerWashingResult`
   - `TankerWashingComplianceEngine` (kiểm tra IGS O2 <= 8%, áp suất >= 100 mmWG, cặn cạn, prewash Cat X/Y/Z, xả bờ <= 1000 ppm, xả biển >= 12 NM).
2. `src/core/maritime/phase_324_lng_gas_custody.py` (< 140 dòng):
   - `LngBogInput`, `LngCtmsInput`, `LngGasManagementResult`
   - `LngGasCustodyEngine` (nhiệt hóa hơi BOG, tỷ lệ BOR tự nhiên %/ngày, áp suất MARVS, GCU trigger, chuyển giao năng lượng MMBtu).
3. `src/core/maritime/phase_325_lifeboat_fpd.py` (< 120 dòng):
   - `LifeboatReleaseMode` (Enum: OFF_LOAD, ON_LOAD)
   - `LifeboatFpdInput`, `LifeboatReleaseSafetyResult`
   - `LifeboatFpdSafetyEngine` (hệ số an toàn FPD MBL >= 6.0 lần tải trọng móc, độ mòn cam <= 2.0 mm, cảm biến thủy tĩnh off-load, override 2 tầng on-load).
4. `src/core/maritime/phase_326_enclosed_space.py` (< 130 dòng):
   - `EnclosedSpaceGasInput`, `EnclosedSpaceEntryResult`
   - `EnclosedSpaceSafetyEngine` (4-Gas: O2 [20.8%-22.0%], LEL <= 1.0%, H2S <= 5.0 ppm, CO <= 25.0 ppm, thông gió >= 3 air changes, bích mù cách ly, permit 8 giờ).
5. `src/core/maritime_tanker_gas_lsa_enclosed_engine.py` (< 60 dòng):
   - Facade re-export 100% contracts.

## 3. Checklist Thực hiện
- [x] Tạo thư mục `src/core/maritime/` nếu chưa có.
- [x] Trích xuất logic Phase 323 vào `phase_323_tanker_washing.py`.
- [x] Trích xuất logic Phase 324 vào `phase_324_lng_gas_custody.py`.
- [x] Trích xuất logic Phase 325 vào `phase_325_lifeboat_fpd.py`.
- [x] Trích xuất logic Phase 326 vào `phase_326_enclosed_space.py`.
- [x] Cập nhật `maritime_tanker_gas_lsa_enclosed_engine.py` re-export sạch sẽ.
- [x] Kiểm tra import và độ dài từng file (`wc -l < 200`).
