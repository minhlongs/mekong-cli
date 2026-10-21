# Phase 04: Bộ kiểm thử Đơn vị & Tích hợp 100% Zero-Mock

## 1. Mục tiêu
Xây dựng `tests/test_maritime_ballast_decarb_lifting_spill_suite.py` với tối thiểu 20 bài test zero-mock, kiểm tra đầy đủ các kịch bản thành công, cảnh báo và từ chối nghiêm ngặt theo luật hàng hải.

## 2. Các nhóm Test Cases
1. **Phase 327 (BWM & Sediment)**:
   - Đạt chuẩn IMO D-2 & USCG CMF/FDA.
   - Thất bại do nồng độ vi sinh vượt chuẩn.
   - Thất bại do UVT < 50% hoặc TRO > 0.1 mg/L chưa trung hòa.
   - Cặn đáy vượt ngưỡng 5%.
2. **Phase 328 (Decarbonization & Alternative Fuels)**:
   - Tính toán hạn ngạch EU ETS 2024 (40%) và 2026 (100%).
   - FuelEU Maritime GHG intensity compliance & pooling giữa tàu thặng dư và thâm hụt.
   - Bunkering an toàn Methanol/Ammonia (O2 < 2%, leak < ngưỡng, khoảng cách an toàn).
   - Từ chối bunkering do rò rỉ khí hoặc chưa thổi sạch N2.
3. **Phase 329 (Lifting Gear & Wire Rope)**:
   - Tính tải trọng Proof Load cho SWL <= 20T, 20-50T, > 50T.
   - Loại bỏ cáp thép do đứt sợi hoặc mòn đường kính >= 7%.
   - Hết hạn kiểm định 5 năm (Quadrennial thorough survey).
4. **Phase 330 (Oil Spill OPRC & NEBA)**:
   - Phân cấp Tier 1, 2, 3 chính xác theo sản lượng tràn.
   - NEBA cho phép phun chất phân tán (sâu >= 10m, xa >= 3 NM, độ nhớt < 10,000 cSt).
   - NEBA từ chối phun do gần bờ, nước nông hoặc độ nhớt quá cao.
   - Tính toán chiều dài phao quây và công suất thu gom skimmer.
5. **Facade & Hash integrity**:
   - Re-export đầy đủ và SHA-256 64-hex tamper-evident audit trail.

## 3. Checklist Thực hiện
- [x] Viết `tests/test_maritime_ballast_decarb_lifting_spill_suite.py`.
- [x] Chạy `pytest tests/test_maritime_ballast_decarb_lifting_spill_suite.py -v`.
- [x] 100% tests Passed.
