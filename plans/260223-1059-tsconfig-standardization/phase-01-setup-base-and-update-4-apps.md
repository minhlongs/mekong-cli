# Phase 1: Thiết lập TSConfig Base và Cập nhật 4 Apps Đầu Tiên

## Context Links
- Parent Plan: [plan.md](./plan.md)
- Dependency: Yêu cầu tối đa 5 file/mission.

## Overview
- **Priority**: P1
- **Status**: completed
- **Description**: Tạo file cấu hình gốc `tsconfig.base.json` tại root của monorepo. Sau đó cập nhật `tsconfig.json` của 4 apps đầu tiên để kế thừa (extends) từ base config này.

## Key Insights
- File `tsconfig.base.json` chứa các tuỳ chọn compiler chung (`strict: true`, `esModuleInterop: true`, `skipLibCheck: true`, `forceConsistentCasingInFileNames: true`, ...).
- Giới hạn mission: Chỉ thao tác đúng 5 files để tuân thủ lệnh của Elite Commander.

## Requirements
- File `tsconfig.base.json` được tạo mới ở thư mục gốc.
- Các file `tsconfig.json` trong 4 apps được sửa đổi để có trường `"extends": "../../tsconfig.base.json"`.

## Architecture
- Root `tsconfig.base.json` -> Các app cụ thể kế thừa và ghi đè (nếu cần) thông qua `apps/<app-name>/tsconfig.json`.

## Related Code Files
1. `tsconfig.base.json` (Create)
2. `apps/84tea/tsconfig.json` (Update)
3. `apps/agencyos-landing/tsconfig.json` (Update)
4. `apps/agencyos-web/tsconfig.json` (Update)
5. `apps/anima119/tsconfig.json` (Update)

## Implementation Steps
1. Phân tích các file `tsconfig.json` hiện tại của 4 apps để trích xuất các config chung nhất.
2. Tạo file `tsconfig.base.json` ở root repository.
3. Thay thế nội dung của 4 file `tsconfig.json` tại các apps: `84tea`, `agencyos-landing`, `agencyos-web`, `anima119`. Xoá các config bị trùng lặp, thêm thuộc tính `"extends": "../../tsconfig.base.json"`.
4. Đảm bảo file cấu hình vẫn giữ lại các đường dẫn (`paths`), mảng `include`, `exclude` đặc thù của từng app.

## Todo List
- [x] Khởi tạo `tsconfig.base.json`
- [x] Cập nhật `apps/84tea/tsconfig.json`
- [x] Cập nhật `apps/agencyos-landing/tsconfig.json`
- [x] Cập nhật `apps/agencyos-web/tsconfig.json`
- [x] Cập nhật `apps/anima119/tsconfig.json`

## Success Criteria
- Tối đa 5 file bị ảnh hưởng.
- Các `tsconfig.json` không báo lỗi cú pháp.
- Mỗi file của app đều extends chính xác từ base.

## Risk Assessment
- Việc gộp config chung có thể làm sai lệch cấu hình biên dịch của một số app (ví dụ React vs Node.js).
- Mitigation: Base config chỉ chứa các compiler options an toàn, framework-agnostic. Frontend và Backend app có thể ghi đè `compilerOptions` như `jsx`, `lib`.

## Security Considerations
- Không liên quan đến security.

## Next Steps
- Chuyển sang Phase 2 để xử lý 4 apps còn lại.
