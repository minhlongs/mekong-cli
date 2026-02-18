---
title: "CTO MISSION: Prepare mekong-cli for Open Source Publication + RaaS Foundation"
description: "Kế hoạch tổng thể để chuẩn bị mekong-cli cho việc public open source, bao gồm dọn dẹp, kiểm tra bảo mật, viết lại tài liệu và tối ưu hóa trải nghiệm developer."
status: in-progress
priority: P1
effort: 3h
branch: master
tags: [opensource, documentation, security, cleanup, raas]
created: 2026-02-15
---

# Kế Hoạch: Prepare mekong-cli for Open Source + RaaS Foundation

## 1. Tổng Quan
Nhiệm vụ này nhằm mục đích biến `mekong-cli` từ một internal tool thành một dự án Open Source chuyên nghiệp, đóng vai trò là nền tảng tham chiếu cho mô hình **Revenue-as-a-Service (RaaS)**. Chúng ta cần đảm bảo code sạch, không chứa thông tin nhạy cảm, tài liệu rõ ràng và dễ dàng để cộng đồng tiếp cận.

## 2. Các Phase Thực Hiện

### Phase 1: Security Audit & Cleanup (Ưu tiên cao nhất)
**Mục tiêu**: Loại bỏ hoàn toàn các file rác, file nội bộ, logs và đảm bảo không lộ secrets.
- [ ] **Scan Secrets**: Quét toàn bộ repo tìm API keys, passwords, internal URLs (dùng `grep`).
    - Keywords: `API_KEY`, `SECRET`, `PASSWORD`, `private_key`, `token`, `auth`, `credentials`.
- [ ] **Clean Internal Files**:
    - Xóa `RULES_*.md` cũ không dùng (nếu có).
    - Xóa các file logs `*.log`, `npm-debug.log`, `yarn-error.log`.
    - Xóa các file temporary, cache.
    - Kiểm tra `AGENTS.md`, `AUDIT.md`, `HANDOFF.md` và move vào `archive/` hoặc xóa.
    - Kiểm tra folder `plans/` và `apps/` để loại bỏ các nội dung internal-only.
- [ ] **Verify .gitignore**: Đảm bảo `.env`, `node_modules`, `dist`, `coverage`, logs được ignore chặt chẽ.

### Phase 2: Documentation Overhaul
**Mục tiêu**: Xây dựng bộ mặt chuyên nghiệp cho dự án.
- [ ] **README.md**: Viết lại theo chuẩn Open Source.
    - Giới thiệu RaaS là gì.
    - Architecture Diagram (Mermaid).
    - Quick Start (cho người mới).
    - Monetization Model (giải thích Antigravity Proxy).
- [ ] **README.vi.md**: Cập nhật bản tiếng Việt tương ứng.
- [ ] **CONTRIBUTING.md**: Hướng dẫn rõ ràng quy trình PR, setup môi trường dev.
- [ ] **Structure Docs**: Cập nhật `docs/project-overview-pdr.md` để phản ánh trạng thái hiện tại.

### Phase 3: Package Structure & DX Polish
**Mục tiêu**: Đảm bảo "It just works" khi người khác clone về.
- [ ] **Review package.json**:
    - Kiểm tra `scripts`: đảm bảo các lệnh `dev`, `build`, `test` chạy đúng.
    - Kiểm tra `dependencies`: loại bỏ các lib không dùng.
    - Thêm `keywords`, `author`, `repository` metadata chính xác.
- [ ] **Verify Workspace**: Kiểm tra cấu hình `pnpm-workspace.yaml` hoặc `turbo.json` (nếu có).
- [ ] **Task Examples**: Chuẩn hóa các file trong `tasks/examples/` để user dễ hình dung cách dùng.

### Phase 4: Monetization & Architecture Definition
**Mục tiêu**: Định hình rõ mô hình kinh doanh RaaS.
- [ ] **Update docs/raas-foundation.md**:
    - Giải thích sâu hơn về Antigravity Proxy layer.
    - Mô hình License (Community vs Enterprise).
- [ ] **Architecture Check**: Đảm bảo code phản ánh đúng tài liệu (vị trí của Proxy, Tôm Hùm Daemon).

## 3. Quy Tắc Thực Thi
- **Batching**: Mỗi mission xử lý tối đa 5 file để dễ review.
- **Verification**: Sau khi sửa, phải chạy `npm install` và `npm run build` (nếu có) để đảm bảo không break.
- **Language**: Tài liệu chính bằng Tiếng Anh (quốc tế hóa), có bản Tiếng Việt hỗ trợ. Commit message chuẩn Conventional Commits.

## 4. Unresolved Questions
- Có cần giữ lại folder `_bmad/` không? (Cần kiểm tra nội dung).
- Các file trong `apps/` có cái nào là private source không? (Cần review kỹ `apps/apex-os`, `apps/84tea`).

---
**Next Step**: Bắt đầu Phase 1 - Security Audit & Cleanup.
