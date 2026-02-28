# Phase 2: Cập Nhật Cấu Hình Cho 4 Apps Còn Lại

## Context Links
- Parent Plan: [plan.md](./plan.md)
- Dependency: Yêu cầu Phase 1 (đã có `tsconfig.base.json`).

## Overview
- **Priority**: P1
- **Status**: pending
- **Description**: Tiếp tục công việc chuẩn hoá bằng cách cập nhật 4 apps còn lại để kế thừa từ `tsconfig.base.json`.

## Key Insights
- Tuân thủ nghiêm ngặt giới hạn sửa đổi tối đa 5 file mỗi mission (Phase này sửa đúng 4 files).

## Requirements
- Các file `tsconfig.json` trong 4 apps được sửa đổi để có trường `"extends": "../../tsconfig.base.json"`.

## Architecture
- Kế thừa cấu hình từ Root `tsconfig.base.json`.

## Related Code Files
1. `apps/apex-os/tsconfig.json` (Update)
2. `apps/com-anh-duong-10x/tsconfig.json` (Update)
3. `apps/openclaw-worker/tsconfig.json` (Update)
4. `apps/sophia-proposal/tsconfig.json` (Update)

## Implementation Steps
1. Kiểm tra cấu hình hiện tại của 4 apps mục tiêu.
2. Cập nhật file `tsconfig.json` tại `apps/apex-os`.
3. Cập nhật file `tsconfig.json` tại `apps/com-anh-duong-10x`.
4. Cập nhật file `tsconfig.json` tại `apps/openclaw-worker`.
5. Cập nhật file `tsconfig.json` tại `apps/sophia-proposal`.
6. Ở mỗi file, xoá các config trùng lặp đã có ở base, thêm `"extends": "../../tsconfig.base.json"`.

## Todo List
- [ ] Cập nhật `apps/apex-os/tsconfig.json`
- [ ] Cập nhật `apps/com-anh-duong-10x/tsconfig.json`
- [ ] Cập nhật `apps/openclaw-worker/tsconfig.json`
- [ ] Cập nhật `apps/sophia-proposal/tsconfig.json`

## Success Criteria
- 4 file `tsconfig.json` được update thành công.
- Tối đa 5 files bị modify trong mission này.

## Risk Assessment
- Tương tự Phase 1, các thuộc tính riêng như `include`/`exclude` phải được giữ nguyên.
- Mitigation: Chỉ gộp chung `compilerOptions`.

## Security Considerations
- Không liên quan đến security.

## Next Steps
- Chuyển sang Phase 3 để chạy kiểm tra `tsc --noEmit`.
