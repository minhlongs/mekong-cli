# Plan: Test Proxy Routing

1. **Kiểm tra trạng thái Antigravity Proxy**:
   - Dùng curl để gọi health check endpoint trên port 9191 (`http://localhost:9191/health` hoặc root).
   - Kiểm tra log của proxy nếu có.

2. **Test Routing (Gọi LLM API qua Proxy)**:
   - Thử gửi một request đơn giản đến proxy mô phỏng Anthropic API hoặc endpoint tương ứng.
   - Xác minh proxy route request thành công và trả về response hợp lệ.

3. **Phân tích kết quả**:
   - Dùng subagent để đọc log và phân tích quá trình routing.
   - Xác định xem failover hoặc load balancing có hoạt động đúng không (nếu có thể test).

4. **Báo cáo và Update**:
   - Ghi lại kết quả test.
   - Cập nhật `tasks/lessons.md` nếu phát hiện vấn đề và có bài học rút ra.
