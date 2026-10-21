---
title: "Phases 331-334: IALA AtoN, VNSW Single Window, IMSBC Group B & H&M Damage Survey Suite"
status: in_progress
created: 2026-10-09
author: Claude Fable 5 & Antigravity
architecture: Hybrid Unified Modular (< 200 LOC sub-modules + Central Facade)
---

# Kế hoạch Triển khai Chi tiết: Hàng hải & Cảng biển Phases 331–334

## 1. Mục tiêu Tổng quan
Triển khai hoàn chỉnh 4 phân hệ kỹ thuật hàng hải và cảng biển quốc tế theo chuẩn kiến trúc **Hybrid Modular Facade**:
- **Phase 331**: Báo hiệu Hàng hải IALA (MBS Region A/B, Cardinal/Lateral Marks) & AIS Message 21 AtoN Telemetry (Real/Synthetic/Virtual).
- **Phase 332**: Tự động hóa Khai báo Một cửa Quốc gia Hàng hải VNSW & IMO FAL 1–7 Declarations, Port Clearance Issuance.
- **Phase 333**: Kiểm soát An toàn Hàng rời Nguy hiểm Hóa học IMSBC Code Group B, Giám sát Khí độc/Cháy nổ Hầm hàng & Quy tắc Thông gió.
- **Phase 334**: Giám định Tổn thất Thân tàu & Máy tàu (H&M Damage Survey, Particular/General Average Apportionment, Deductibles & Depreciation).

## 2. Danh sách các Phase Kỹ thuật
- [ ] [Phase 01: Thiết kế Lõi Modular & Central Facade](phase-01-modular-core-engines.md)
- [ ] [Phase 02: Tích hợp CLI Commands & Bilingual Aliases](phase-02-cli-commands-wiring.md)
- [ ] [Phase 03: Đăng ký FastMCP Tools trong MCP Server](phase-03-fastmcp-tools.md)
- [ ] [Phase 04: Bộ kiểm thử Đơn vị & Tích hợp 100% Zero-Mock](phase-04-unit-integration-tests.md)
- [ ] [Phase 05: Cập nhật Roadmap & Persistent Memory](phase-05-roadmap-docs-sync.md)

## 3. Tiêu chí Thành công (Definition of Done)
1. Toàn bộ các file trong `src/core/maritime/` dưới 200 LOC.
2. File mặt tiền `src/core/maritime_aton_vnsw_imsbc_hm_engine.py` re-export đầy đủ và SHA-256 tamper-evident hash.
3. 4 nhóm lệnh CLI (`aton`, `vnsw`, `imsbc`, `hmsurvey`) và 8 alias tiếng Việt hoạt động trơn tru.
4. 4 tools FastMCP tích hợp đầy đủ schema, xử lý lỗi an toàn trong `scripts/mcp_server.py`.
5. Kiểm thử `pytest tests/test_maritime_aton_vnsw_imsbc_hm_suite.py` đạt 100% pass với $\ge 20$ bài test zero-mock.
6. `ruff check` không phát hiện lỗi cú pháp hay quy tắc formatting.
