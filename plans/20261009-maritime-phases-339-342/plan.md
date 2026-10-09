# Kế hoạch Triển khai: Maritime Phases 339–342

**Mục tiêu:** Xây dựng trọn vẹn 4 phân hệ hàng hải kỹ thuật cao đạt chuẩn quốc tế IMO/SOLAS/MARPOL/LOF, tuân thủ nghiêm ngặt Hybrid Modular Facade (<200 LOC/file) và 100% Zero-Mock Test Suite.

## Danh sách Phân hệ & Tiến độ
- [ ] **Phase 339:** IMO Polar Code & PWOM Navigation Risk (`src/core/maritime/phase_339_polar_code_polaris_rio.py`)
- [ ] **Phase 340:** Cargo Hold Washwater & Cleaning MARPOL HME (`src/core/maritime/phase_340_hold_washwater_marpol_hme.py`)
- [ ] **Phase 341:** PCTC Ro-Ro Car Carrier EV Lithium-ion Fire Safety (`src/core/maritime/phase_341_pctc_ev_fire_safety.py`)
- [ ] **Phase 342:** Lloyd's Open Form LOF 2024 & SCOPIC Clause Salvage (`src/core/maritime/phase_342_salvage_lof_scopic_compensation.py`)
- [ ] **Central Facade:** `src/core/maritime_polar_wash_ev_salvage_engine.py` (<50 LOC)
- [ ] **CLI Apps:** `src/cli/commands/maritime_polar_wash_ev_salvage_command.py` + 8 Vietnamese aliases trong `src/cli/app_setup.py`
- [ ] **FastMCP Endpoints:** 4 async tool handlers trong `scripts/mcp_server.py`
- [ ] **Zero-Mock Test Suite:** `tests/test_maritime_polar_wash_ev_salvage_suite.py` (18+ tests xanh 100%)
- [ ] **Tài liệu & Bộ nhớ:** Cập nhật `docs/development-roadmap.md` và lưu bộ nhớ `MEMORY.md`

## Chiến lược Thực thi Song song
1. Tạo 4 micro-engines độc lập.
2. Tạo Central Facade kết nối.
3. Đăng ký CLI và FastMCP.
4. Viết và kiểm thử test suite toàn diện.
