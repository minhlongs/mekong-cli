# 🚀 Kế Hoạch Ra Mắt Nền Tảng Nhịp Điệu Xanh (Launch & Go-Live Plan)

Tài liệu này chi tiết hóa danh sách kiểm tra (checklists) kỹ thuật và chiến lược Go-to-Market (GTM) phục vụ việc triển khai thực tế hệ sinh thái Proptech Nhịp Điệu Xanh lên môi trường Production.

---

## 📋 1. Go-Live Checklist (Danh Sách Kiểm Tra Kỹ Thuật)

Nhằm đảm bảo hệ thống vận hành trơn tru và an toàn tuyệt đối khi tiếp cận người dùng, đội ngũ vận hành cần thực hiện kiểm tra theo checklist sau:

| Danh Mục | Tác Vụ Cần Thực Hiện | Trạng Thái | Người Chịu Trách Nhiệm | Ghi Chú |
| :--- | :--- | :---: | :---: | :--- |
| **Mạng & Domain** | Cấu hình bản ghi DNS A/CNAME trỏ về Ingress Controller IP (`nhipdieuxanh.vn`). | ⬜ | DevOps Lead | TTL 300s để cập nhật nhanh. |
| **Bảo Mật (SSL)** | Thiết lập chứng chỉ SSL/TLS Let's Encrypt tự động gia hạn qua cert-manager trên Kubernetes. | ⬜ | Security Eng | Hỗ trợ TLS 1.3 và cấu hình HSTS. |
| **Cơ Sở Dữ Liệu** | Thiết lập Backup tự động mỗi ngày (Daily CronJob) lên AWS S3 (hoặc Cloudflare R2), lưu giữ tối thiểu 30 ngày. | ⬜ | Database Admin | Thử nghiệm khôi phục từ bản backup trước ngày go-live. |
| **Tài Nguyên K8s** | Cấu hình Resource Limits/Requests cho tất cả Pods tránh tình trạng tranh chấp (OOMKilled). | ⬜ | K8s Admin | Thiết lập HPA (Horizontal Pod Autoscaler) cho Frontend/Backend. |
| **Sự Cố & Khôi Phục**| Kích hoạt cơ chế Circuit Breaker, xác minh kịch bản khôi phục thảm họa (Disaster Recovery). | ⬜ | SRE Team | Giả lập tình huống Kafka cluster ngưng kết nối. |
| **Giám Sát (Alerts)** | Kết nối Alertmanager đến kênh Slack `#ndx-alerts-prod` và email trực ban 24/7. | ⬜ | DevOps Lead | Kiểm tra Alert 500 error và Database Down. |
| **Tài Liệu Cẩm Nang** | Hoàn thành tài liệu hướng dẫn sử dụng (User Manual) và API Swagger docs. | ⬜ | Tech Writer | Cập nhật file Swagger docs tại `/api/docs`. |
| **Hỗ Trợ Khách Hàng**| Cấu hình Widget chat trực tuyến (Zalo/Chatwoot) trên Landing Page. | ⬜ | Support Team | Đường dây nóng hỗ trợ ký hợp đồng và thanh toán trực tuyến. |

---

## 🎯 2. Chiến Lược Go-to-Market (GTM)

Chiến lược ra mắt nền tảng Nhịp Điệu Xanh tuân theo nguyên tắc **Triển khai Từng Bước (Gradual Rollout)** nhằm giảm thiểu rủi ro kỹ thuật và tối ưu hóa trải nghiệm khách hàng tại khu vực Cần Thơ.

### 📍 Giai Đoạn 1: Thử Nghiệm Khép Kín (Private Beta)
- **Đối tượng mục tiêu:** 100 khách hàng VIP đầu tiên và các môi giới đối tác thân thiết tại TP. Cần Thơ.
- **Mục tiêu:**
  - Xác thực luồng nghiệp vụ chính trên thực tế: Đăng ký -> Nhận tư vấn -> Đặt lịch xem nhà -> Ký hợp đồng điện tử -> Thanh toán.
  - Đo lường và đánh giá các chỉ số kỹ thuật: Latency của Landing Page, độ trễ gửi tin nhắn SMS/Telegram thông báo, tốc độ phản hồi của Chatbot Mock AI.
- **Thu thập phản hồi:** Thiết lập biểu mẫu khảo sát trực tuyến qua email và gọi điện phỏng vấn trực tiếp sau mỗi giao dịch xem nhà/ký hợp đồng.

### 📈 Giai Đoạn 2: Mở Rộng Giới Hạn (Public Beta & Soft Launch)
- **Đối tượng mục tiêu:** Mở rộng tiếp cận lên khoảng 1.000 - 3.000 người dùng tự nhiên từ các chiến dịch SEO và Marketing địa phương.
- **Mục tiêu:**
  - Kích hoạt cơ chế Autoscaling trên Kubernetes để kiểm nghiệm khả năng chịu tải của hệ thống.
  - Phân tích hành vi người dùng qua các công cụ đo lường (PostHog/Hotjar) để tối ưu tỷ lệ chuyển đổi (CRO) trên Landing Page.
  - Điều chỉnh thuật toán gợi ý bất động sản của AI Service dựa trên dữ liệu tương tác thực tế đầu tiên.

### 🚀 Giai Đoạn 3: Ra Mắt Chính Thức (Grand Launch)
- **Chiến dịch truyền thông lớn:** Tổ chức sự kiện ra mắt trực tiếp tại Cần Thơ kết hợp chạy quảng cáo đa kênh (Facebook Ads, Google Search, Zalo Ads) hướng tới người mua nhà sinh sống tại Đồng bằng Sông Cửu Long.
- **Hạ tầng hỗ trợ:** Sẵn sàng chịu tải tối thiểu 10.000 người dùng đồng thời (đã được kiểm thử đạt chỉ tiêu bằng công cụ k6).

---

## 🚨 3. Quy Trình Ứng Phó Sự Cố (Runbook Cơ Bản)

Khi xảy ra sự cố đột xuất trong quá trình launch, đội ngũ kỹ thuật áp dụng quy trình khắc phục sau:

1. **Sự cố API Gateway trả về lỗi 500 liên tục:**
   - *Bước 1:* Kiểm tra logs của Nginx gateway: `kubectl logs -n ndx-prod deployment/gateway`.
   - *Bước 2:* Xác minh trạng thái kết nối giữa backend và database: Kiểm tra pod backend có bị treo do connection pool đầy hay không.
   - *Bước 3:* Thực hiện rollback nhanh về bản build ổn định trước đó bằng Helm: `helm rollback ndx-prod <revision-number>`.

2. **Cơ sở dữ liệu bị quá tải (CPU/Memory > 90%):**
   - *Bước 1:* Kiểm tra các câu lệnh query chậm (Slow Queries) bằng log của Postgres.
   - *Bước 2:* Tăng tài nguyên tài nguyên RAM/CPU cho Pod Postgres tạm thời, hoặc kích hoạt Read Replica để chia tải truy vấn tìm kiếm bất động sản.
