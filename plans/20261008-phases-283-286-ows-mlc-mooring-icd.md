# Kế hoạch Triển khai: Phases 283–286 OWS 15 ppm, Lương Thuyền viên MLC, Cước Buộc Dây & Cảng Cạn ICD

## Tổng quan 4 Phân hệ
- **Phase 283**: Thiết bị phân ly dầu nước OWS 15 ppm & Nhật ký dầu điện tử ORB Engine (MARPOL Annex I Regs. 14-15, MEPC.107(49), Thông tư 41/2020/TT-BGTVT).
- **Phase 284**: Hợp đồng lao động thuyền viên, Bảng lương MLC 2006 & Ký quỹ bảo lãnh hồi hương Engine (MLC 2006 Standard A2.2 & A2.5, VMC 2015 Điều 58-64, Nghị định 121/2014/NĐ-CP).
- **Phase 285**: Dịch vụ buộc cởi dây tàu cảng biển Thông tư 39/2023/TT-BGTVT & Kiểm soát an toàn dây OCIMF MEG4 Engine.
- **Phase 286**: Cảng cạn ICD, Tờ khai vận chuyển độc lập OLA & Giám sát hải quan liên cảng Engine (Luật Hải quan 2014 Điều 42 & 51-53, Nghị định 08/2015/NĐ-CP, Thông tư 38/2015/TT-BTC).

## Các bước thực hiện
1. [x] Nghiên cứu cơ sở pháp lý & nghiệp vụ (`docs/plans/research/researcher-31-ows-bilge-marpol-mlc-wages.md` & `researcher-32-mooring-tariffs-icd-dryport.md`).
2. [x] Kiến trúc kỹ thuật & Tech Stack (`docs/plans/tech-stack-ows-mlc-mooring-icd.md`).
3. [x] Hướng dẫn thiết kế giao diện & Terminal Wireframes (`docs/design-guidelines-ows-mlc-mooring-icd.md`).
4. [x] Xây dựng Engine lõi thuần Python (`src/core/maritime_ows_mlc_mooring_icd_engine.py`):
   - Đầy đủ dataclass, validation rules, tính toán tiền tệ, xử lý vi phạm nồng độ, cơ chế ngắt van 3 ngả tự động, bảng lương MLC, khung cước dây neo, thời hạn vận chuyển ICD.
5. [x] Xây dựng Command CLI Typer (`src/cli/commands/maritime_ows_mlc_mooring_icd_command.py`):
   - 4 ứng dụng Typer con, đăng ký trong `src/cli/app_setup.py` với 8 bí danh song ngữ.
6. [x] Tích hợp FastMCP Tools & Handlers (`scripts/mcp_server.py`):
   - 4 tools chuẩn hóa với các trường thông số rõ ràng, trả về chuỗi JSON đầy đủ.
7. [x] Xây dựng Bộ kiểm thử không dùng mock (`tests/test_maritime_ows_mlc_mooring_icd_suite.py`):
   - 29 bài test xác minh 100% xanh.
8. [ ] Cập nhật Tài liệu & Persistent Memory:
   - `docs/development-roadmap.md`, `docs/project-changelog.md`, `docs/system-architecture.md`, `MEMORY.md`.
