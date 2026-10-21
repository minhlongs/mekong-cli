---
title: "Phases 323-326: Tanker Washing, LNG BOG/CTMS, Lifeboat FPD & Enclosed Space Safety Suite"
status: completed
created: 2026-10-09
author: Claude Fable 5 & Antigravity
architecture: Hybrid Unified Modular (< 200 LOC sub-modules + Central Facade)
---

# Kế hoạch Triển khai Chi tiết: Hàng hải Phases 323–326

## 1. Mục tiêu Tổng quan
Triển khai hoàn chỉnh 4 phân hệ kỹ thuật an toàn hàng hải quốc tế theo kiến trúc **Hybrid "Cả 3"** (Micro-modular < 200 LOC, Facade tương thích ngược, CLI 39-group & FastMCP):
- **Phase 323**: MARPOL Annex I COW (Crude Oil Washing) & IBC Code Chemical Tanker Prewash.
- **Phase 324**: IGC Code LNG/LPG BOG & GIIGNL Custody Transfer Measurement System (CTMS).
- **Phase 325**: SOLAS III/20 & IMO MSC.1/Circ.1392 / Circ.1327 Lifeboat FPD Safety Release.
- **Phase 326**: IMO Res. A.1050(27) & MSC.1/Circ.1401 Enclosed Space 4-Gas Clearance & Permit.

## 2. Danh sách các Phase Kỹ thuật
- [x] [Phase 01: Tái cấu trúc Module Lõi & Facade](phase-01-modular-core-engines.md)
- [x] [Phase 02: Xây dựng CLI Typer Commands & Đăng ký App Setup](phase-02-cli-commands-wiring.md)
- [x] [Phase 03: Tích hợp FastMCP Tools trong MCP Server](phase-03-fastmcp-tools.md)
- [x] [Phase 04: Bộ kiểm thử Đơn vị & Tích hợp 100% Zero-Mock](phase-04-unit-integration-tests.md)
- [x] [Phase 05: Đồng bộ Tài liệu Roadmap & Persistent Memory](phase-05-roadmap-docs-sync.md)

## 3. Tiêu chí Thành công (Definition of Done)
1. Toàn bộ các file code con trong `src/core/maritime/` dưới 200 LOC.
2. File mặt tiền `src/core/maritime_tanker_gas_lsa_enclosed_engine.py` re-export 100% contracts.
3. 4 nhóm lệnh CLI (`cow`, `bog`, `lifeboat`, `enclosed`) và 8 alias tiếng Việt hoạt động trơn tru.
4. 4 tools FastMCP tích hợp đầy đủ schema, xử lý lỗi an toàn.
5. Kiểm thử `pytest tests/test_maritime_tanker_gas_lsa_enclosed_suite.py` đạt 100% pass với $\ge 20$ bài test.
6. `ruff check` và `mypy` không phát hiện lỗi cú pháp hay kiểu dữ liệu.
