---
title: "Phases 327-330: BWM USCG, FuelEU Decarb, Lifting Gear & OPRC Oil Spill Suite"
status: completed
created: 2026-10-09
author: Claude Fable 5 & Antigravity
architecture: Hybrid Unified Modular (< 200 LOC sub-modules + Central Facade)
---

# Kế hoạch Triển khai Chi tiết: Hàng hải & Cảng biển Phases 327–330

## 1. Mục tiêu Tổng quan
Triển khai hoàn chỉnh 4 phân hệ kỹ thuật hàng hải và cảng biển quốc tế theo kiến trúc **Hybrid "Cả 3"**:
- **Phase 327**: Quản lý Nước dằn & Trầm tích (IMO D-2 vs USCG Type Approval CMF/FDA, UVT & TRO Neutralization).
- **Phase 328**: Giảm phát thải Hàng hải (EU ETS Maritime MRV Surrender, FuelEU GHG Pooling, Methanol/Ammonia Dual-Fuel Bunkering).
- **Phase 329**: Thiết bị Nâng Cảng biển & Cáp thép (ILO 152 & QCVN 23:2010 SWL Proof Load Testing, ISO 4309 Wire Rope Discard).
- **Phase 330**: Ứng phó Sự cố Tràn dầu Quốc gia (OPRC 1990 Tier 1-3, NEBA Chemical Dispersant Matrix, Booming & Skimmer Capacity).

## 2. Danh sách các Phase Kỹ thuật
- [x] [Phase 01: Thiết kế Lõi Modular & Central Facade](phase-01-modular-core-engines.md)
- [x] [Phase 02: Tích hợp CLI Commands & Bilingual Aliases](phase-02-cli-commands-wiring.md)
- [x] [Phase 03: Đăng ký FastMCP Tools trong MCP Server](phase-03-fastmcp-tools.md)
- [x] [Phase 04: Bộ kiểm thử Đơn vị & Tích hợp 100% Zero-Mock](phase-04-unit-integration-tests.md)
- [x] [Phase 05: Cập nhật Roadmap & Persistent Memory](phase-05-roadmap-docs-sync.md)

## 3. Tiêu chí Thành công (Definition of Done)
1. Toàn bộ các file trong `src/core/maritime/` dưới 200 LOC.
2. File mặt tiền `src/core/maritime_ballast_decarb_lifting_spill_engine.py` re-export đầy đủ.
3. 4 nhóm lệnh CLI (`ballast`, `decarb`, `lifting`, `spill`) và 8 alias tiếng Việt hoạt động trơn tru.
4. 4 tools FastMCP tích hợp đầy đủ schema, xử lý lỗi an toàn.
5. Kiểm thử `pytest tests/test_maritime_ballast_decarb_lifting_spill_suite.py` đạt 100% pass với $\ge 20$ bài test zero-mock.
6. `ruff check` không phát hiện lỗi cú pháp hay kiểu dữ liệu.
