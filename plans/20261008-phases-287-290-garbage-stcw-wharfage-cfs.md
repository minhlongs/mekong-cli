# Kế hoạch Triển khai: Phases 287–290 Quản lý Rác MARPOL, Giờ nghỉ STCW/MLC, Cước Cầu bến & Hải quan CFS/E-Seal

## Tổng quan 4 Phân hệ
- **Phase 287**: Kế hoạch quản lý rác MARPOL Annex V, Giới hạn xả rác biển & Sổ nhật ký rác điện tử GRB Engine (MARPOL Annex V Regs 3-6, IMO MEPC.295(71), Bộ luật Hàng hải VN 2015, Thông tư 41/2020/TT-BGTVT).
- **Phase 288**: Giờ làm việc & Giờ nghỉ ngơi thuyền viên STCW 2010 Manila & MLC 2006 Standard A2.3 Engine (77h/tuần, 10h/ngày, 2 khoảng nghỉ, khoảng dài >=6h, giãn cách <=14h).
- **Phase 289**: Cước sử dụng cầu bến, phao neo & Quản lý thời gian lưu cầu cảng biển Thông tư 39/2023/TT-BGTVT & Thông tư 12/2024/TT-BGTVT Engine.
- **Phase 290**: Địa điểm thu gom hàng lẻ CFS, Chia tách/Đóng ghép LCL & Giám sát niêm phong định vị điện tử E-Seal Hải quan Engine (Luật Hải quan 2014 Điều 61-63, Nghị định 08/2015/NĐ-CP, Thông tư 38/2015/TT-BTC & 39/2018/TT-BTC).

## Các bước thực hiện
1. [x] Nghiên cứu cơ sở pháp lý & nghiệp vụ (`docs/plans/research/researcher-33-marpol-garbage-stcw-rest.md` & `researcher-34-wharfage-tariffs-cfs-eseal.md`).
2. [x] Kiến trúc kỹ thuật & Tech Stack (`docs/plans/tech-stack-garbage-stcw-wharfage-cfs.md`).
3. [x] Hướng dẫn thiết kế giao diện & Terminal Wireframes (`docs/design-guidelines-garbage-stcw-wharfage-cfs.md`).
4. [x] Xây dựng Engine lõi thuần Python (`src/core/maritime_garbage_stcw_wharfage_cfs_engine.py`):
   - Đầy đủ dataclass, validation rules, tính toán tiền tệ, xử lý vi phạm xả rác, thuật toán trượt 24h & 7 ngày giờ nghỉ, khung cước cầu bến và phụ phí overstay, theo dõi thời hạn CFS 90 ngày và phát hiện can thiệp E-Seal.
5. [x] Xây dựng Command CLI Typer (`src/cli/commands/maritime_garbage_stcw_wharfage_cfs_command.py`):
   - 4 ứng dụng Typer con, đăng ký trong `src/cli/app_setup.py` với 8 bí danh song ngữ.
6. [x] Tích hợp FastMCP Tools & Handlers (`scripts/mcp_server.py`):
   - 4 tools chuẩn hóa với các trường thông số rõ ràng, trả về chuỗi JSON đầy đủ.
7. [x] Xây dựng Bộ kiểm thử không dùng mock (`tests/test_maritime_garbage_stcw_wharfage_cfs_suite.py`):
   - Các bài test xác minh 100% xanh cho cả 4 phân hệ, CLI và FastMCP (25 tests passed).
8. [x] Cập nhật Tài liệu & Persistent Memory:
   - `docs/development-roadmap.md`, `docs/project-changelog.md`, `docs/system-architecture.md`, `MEMORY.md`.
