# Chính Sách Bảo Mật (Security Policy)

## Các Phiên Bản Được Hỗ Trợ

Chúng tôi cam kết hỗ trợ bảo mật cho các phiên bản mới nhất của Mekong CLI.

| Phiên Bản | Được Hỗ Trợ |
| --------- | ----------- |
| 2.1.x     | ✅          |
| 2.0.x     | ❌          |
| < 2.0     | ❌          |

## Báo Cáo Lỗ Hổng

Chúng tôi coi trọng sự an toàn của người dùng và hệ thống. Nếu bạn phát hiện một lỗ hổng bảo mật, vui lòng làm theo hướng dẫn sau:

**KHÔNG** báo cáo lỗ hổng công khai qua GitHub Issues.

Vui lòng gửi email chi tiết về lỗ hổng tới: **security@agencyos.dev**

### Quy trình xử lý:
1.  Chúng tôi sẽ xác nhận đã nhận được báo cáo trong vòng 48 giờ.
2.  Chúng tôi sẽ đánh giá mức độ nghiêm trọng và tác động.
3.  Nếu lỗ hổng được xác thực, chúng tôi sẽ phát hành bản vá trong thời gian sớm nhất.
4.  Chúng tôi sẽ công khai ghi nhận đóng góp của bạn (trừ khi bạn muốn ẩn danh) sau khi bản vá đã được phát hành.

## Các Biện Pháp Bảo Mật Chủ Động

Dự án này tuân thủ các nguyên tắc bảo mật "Binh Pháp":

1.  **Sandbox**: CC CLI chạy trong môi trường được kiểm soát.
2.  **No Secrets**: Binh Pháp Quality Gate tự động chặn các commit chứa API Key.
3.  **Proxy**: Mọi cuộc gọi LLM đều đi qua Antigravity Proxy để ẩn danh và bảo vệ quota.

---
*"Cẩn tắc vô ưu"*
