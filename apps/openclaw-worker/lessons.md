# 📕 Lessons Learned — Tôm Hùm CTO
> **知己知彼百戰不殆** — Biết mình biết người, trăm trận không nguy.
> Mỗi thất bại = 1 bài học. Ghi nhận để KHÔNG lặp lại.

---

## Format
```
### [YYYY-MM-DD] [Task Name]
- **Failure Mode:** Mô tả lỗi
- **Root Cause:** Nguyên nhân gốc
- **Fix Applied:** Giải pháp
- **Prevention:** Phòng ngừa cho lần sau
```

---

### 2026-02-26 i18n Validator Refactor (Project Well)
- **Failure Mode:** i18n validator báo lỗi 1466 keys missing dù keys thực tế tồn tại.
- **Root Cause:** Script cũ dùng regex/eval không xử lý được cấu trúc locale dạng module (spread operator `...module`).
- **Fix Applied:** Viết lại validator sử dụng **TypeScript Compiler API** để phân tích AST, resolve imports và spread assignments một cách chính xác.
- **Prevention:** Luôn ưu tiên dùng static analysis tools (TS AST) thay vì regex khi làm việc với cấu trúc code phức tạp. Sử dụng `researcher` agent để tìm giải pháp tooling chuẩn trước khi sửa thủ công.
