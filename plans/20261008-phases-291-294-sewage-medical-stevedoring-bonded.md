# Kế hoạch Triển khai: Phases 291–294 Xử lý Nước thải MARPOL IV, Giám định Sức khỏe Thuyền viên STCW/MLC, Cước Bốc dỡ Cảng biển & Kho Ngoại quan Hải quan

## Tổng quan 4 Phân hệ
- **Phase 291**: Tiêu chuẩn xả nước thải MARPOL Annex IV (Regs 9, 10, 11), Hệ thống xử lý nước thải STP IMO MEPC.227(64) & Giới hạn xả thải theo cự ly/vận tốc tàu Engine.
- **Phase 292**: Tiêu chuẩn giám định y tế, thị lực/thính lực, chứng nhận sức khỏe thuyền viên STCW Manila I/9, MLC 2006 Standard A1.2 & Thông tư 22/2017/TT-BYT Engine.
- **Phase 293**: Biểu khung giá cước dịch vụ bốc dỡ container & hàng hóa tại cảng biển Việt Nam Thông tư 39/2023/TT-BGTVT & Thông tư 12/2024/TT-BGTVT Engine.
- **Phase 294**: Quản lý vòng đời lưu kho, thời hạn 12 tháng + gia hạn 12 tháng, cảnh báo quá hạn và quy trình tịch thu/thanh lý Kho Ngoại quan Luật Hải quan 2014 & Nghị định 08/2015/NĐ-CP Engine.

## Các bước thực hiện
1. [x] Nghiên cứu cơ sở pháp lý & nghiệp vụ (`docs/plans/research/researcher-35-marpol-sewage-stcw-medical.md` & `researcher-36-stevedoring-bonded-warehouse.md`).
2. [x] Kiến trúc kỹ thuật & Tech Stack (`docs/plans/tech-stack-sewage-medical-stevedoring-bonded.md`).
3. [x] Hướng dẫn thiết kế giao diện & Terminal Wireframes (`docs/design-guidelines-sewage-medical-stevedoring-bonded.md`).
4. [ ] Xây dựng Engine lõi thuần Python (`src/core/maritime_sewage_medical_stevedoring_bonded_engine.py`):
   - Đầy đủ dataclass, validation rules, kiểm tra khoảng cách/tốc độ/nồng độ STP, phân loại thị lực/thính lực thuyền viên, tính toán khung cước bốc dỡ cảng biển theo vùng/loại cont/phụ phí IMDG & OOG, máy trạng thái theo dõi 12 tháng + 90 ngày tồn đọng kho ngoại quan.
5. [ ] Xây dựng Command CLI Typer (`src/cli/commands/maritime_sewage_medical_stevedoring_bonded_command.py`):
   - 4 ứng dụng Typer con, đăng ký trong `src/cli/app_setup.py` với 8 bí danh song ngữ (`sewage`/`nuocthai`, `seafarermedical`/`suckhoethuyenvien`, `stevedoretariff`/`bocdocangbien`, `bondedwh`/`khongoaiquan`).
6. [ ] Tích hợp FastMCP Tools & Handlers (`scripts/mcp_server.py`):
   - 4 tools chuẩn hóa với các trường thông số rõ ràng, trả về chuỗi JSON đầy đủ.
7. [ ] Xây dựng Bộ kiểm thử không dùng mock (`tests/test_maritime_sewage_medical_stevedoring_bonded_suite.py`):
   - Các bài test xác minh 100% xanh cho cả 4 phân hệ, CLI và FastMCP.
8. [ ] Cập nhật Tài liệu & Persistent Memory:
   - `docs/development-roadmap.md`, `docs/project-changelog.md`, `docs/system-architecture.md`, `MEMORY.md`.
