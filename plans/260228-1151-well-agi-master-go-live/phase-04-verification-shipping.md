# Phase 04: Verification & Shipping

## Overview
- Priority: P1
- Status: Pending
- Description: Bước kiểm tra cuối cùng và thực hiện đẩy code lên production.

## Key Insights
- Tuân thủ ĐIỀU 49: Không báo cáo DONE khi chưa verify production GREEN.
- Cần chạy Smoke Test trên môi trường thực tế sau khi deploy.

## Implementation Steps
1. Chạy full pipeline: `npm run build` && `npm test`.
2. Thực hiện `git push origin master`.
3. Giám sát GitHub Actions cho đến khi đạt trạng thái SUCCESS.
4. Sử dụng `curl -sI` để kiểm tra HTTP 200 từ production URL.
5. Thực hiện manual smoke test trên trình duyệt.

## Todo List
- [ ] Full Build & Test pass.
- [ ] Git push.
- [ ] CI/CD Green (poll 5 mins).
- [ ] Production URL trả về 200 OK.
- [ ] Chụp ảnh/Screenshot verify checkout flow (nếu có thể).
