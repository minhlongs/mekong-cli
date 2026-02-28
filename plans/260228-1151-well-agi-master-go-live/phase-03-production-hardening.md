# Phase 03: Production Hardening

## Overview
- Priority: P2
- Status: Pending
- Description: Tăng cường bảo mật và cấu hình tối ưu cho môi trường production.

## Key Insights
- Cần đảm bảo các CSP headers được cấu hình chặt chẽ để ngăn chặn XSS.
- Các biến môi trường nhạy cảm không được lộ lọt vào client-side bundle trừ các biến `VITE_` cần thiết.

## Implementation Steps
1. Review `vercel.json` để kiểm tra cấu hình security headers.
2. Kiểm tra `SECURITY_AUDIT.md` (nếu có) để xem các lỗ hổng đã được báo cáo.
3. Chạy `npm audit` và xử lý các lỗi bảo mật nghiêm trọng.
4. Xác thực rằng `import.meta.env.PROD` được sử dụng đúng chỗ để bật/tắt các tính năng debug.

## Todo List
- [ ] Cấu hình Security Headers trong `vercel.json`.
- [ ] Chạy `npm audit`.
- [ ] Verify production environment variables.
- [ ] Kiểm tra Sentry integration cho production.
