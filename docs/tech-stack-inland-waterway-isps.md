# Tech Stack & Domain Architecture — Phases 187-190

## 1. Domain Components
- **Phase 187: Vietnam Inland Waterway Navigation & Bridge Clearance**:
  - `InlandWaterwayNavEngine`: Phân cấp kỹ thuật đường thủy (Circular 46/2016/TT-BGTVT), tính toán Air Draft Clearance dưới cầu tĩnh không thấp và Under Keel Clearance (UKC) luồng cạn theo mùa lũ/kiệt.
- **Phase 188: Container Feeder Barging & Mekong Transit Freight**:
  - `FeederBargingFreightEngine`: Tính biểu cước sà lan tuyến TP.HCM - Cái Mép / Cần Thơ / Phnom Penh theo Thông tư 39/2023/TT-BGTVT và Hiệp định Vận tải thủy Việt Nam - Campuchia, bao gồm phụ phí DG container và phí ĐTNĐ (TT 248/2016/TT-BTC).
- **Phase 189: Maritime Search & Rescue (SAR) & Wreck Removal**:
  - `MaritimeSARWreckEngine`: Tính toán hộp tìm kiếm cứu nạn (IAMSAR datum drift & search radius), thời hạn 30 ngày lập phương án trục vớt tài sản chìm đắm (Nghị định 05/2017/NĐ-CP) và quyền lưu giữ hàng hải theo Điều 284 Bộ luật Hàng hải.
- **Phase 190: Port Facility & Ship Security (ISPS Code)**:
  - `PortFacilitySecurityISPSEngine`: Bộ máy đánh giá cấp độ an ninh ISPS Level 1/2/3, quy tắc chênh lệch cấp độ an ninh giữa Tàu và Bến cảng, và điều kiện bắt buộc ký Tuyên bố An ninh (Declaration of Security - DoS).

## 2. Purity & Performance Invariants
- 100% Python Standard Library in `src/core/inland_waterway_isps_engine.py` (zero external dependencies).
- AST dependency verification gate in `tests/test_inland_waterway_isps_suite.py`.
- Deterministic math, zero floating-point accumulation leaks, clean dataclass encapsulation.
