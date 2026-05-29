# NHỊP ĐIỆU XANH INTEGRATION & DEPLOYMENT ORCHESTRATOR SHOWCASE

---

## SECTION 1: HERO (TIÊU ĐIỂM)

### Vietnamese
**Nhịp Điệu Xanh Orchestrator**
*Đóng gói, Vận hành và Giám sát tự động 20 module Proptech trên Kubernetes*
Một giải pháp hoàn chỉnh cho việc tự động hoá từ lập trình, kiểm thử tải, bảo mật đến triển khai thực tế. Cung cấp hạ tầng ổn định, không downtime, an toàn dữ liệu và cảnh báo sự cố thời gian thực cho sàn giao dịch bất động sản Cần Thơ.

### English
**Nhịp Điệu Xanh Orchestrator**
*Orchestrating, Deploying, and Monitoring 20 Proptech Modules on Kubernetes*
A unified infrastructure blueprint automating developer environments, E2E/load testing, image/web security scanning, and multi-namespace deployments. Ensuring zero-downtime rollouts, resilient data pipelines, and real-time incident alerting.

---

## SECTION 2: TOPOLOGY (KIẾN TRÚC MẠNG)

### Vietnamese
**Kiến trúc Gateway & Event Bus**
Hệ thống kết hợp giữa mô hình Client-Gateway-Service truyền thống và Kiến trúc Hướng Sự kiện (Event-Driven Architecture) thông qua **Apache Kafka**:
- **API Gateway (Nginx)**: Cổng vào bảo mật duy nhất cho hệ thống. Định tuyến thông minh, ngăn chặn tấn công DDoS, giới hạn tần suất request (rate limiting).
- **Service Discovery**: Các service tìm kiếm tự động lẫn nhau qua Kubernetes CoreDNS.
- **Event Bus (Apache Kafka & Zookeeper)**: Đảm bảo tính nhất quán dữ liệu cuối cùng (eventual consistency) giữa Backend, AI Service và các nút Blockchain Ledger/DAO.

### English
**Gateway & Event Bus Topology**
A hybrid network architecture bridging synchronous Client-Gateway routing with asynchronous Event-Driven dispatch:
- **API Gateway (Nginx)**: The single secure entry point. Features intelligent request routing, rate limiting, and standard CORS protection.
- **Service Discovery**: Internal pods automatically discover each other via Kubernetes CoreDNS.
- **Event Bus (Apache Kafka & Zookeeper)**: Coordinates data flow asynchronously between the Backend core, AI services, and private Blockchain ledgers.

---

## SECTION 3: CONTAINER & HELM (ĐÓNG GÓI & ĐIỀU PHỐI KHÔNG GIAN)

### Vietnamese
**Hạ tầng dưới dạng mã (IaC)**
Đóng gói tối ưu và quản lý vòng đời ứng dụng linh hoạt qua Kubernetes:
- **Dockerfiles đa tầng (Multi-stage)**: Giảm kích thước image, cô lập compiler, tăng tốc độ build và cải thiện bảo mật.
- **Docker Compose**: Đồng bộ toàn bộ DB, Kafka, Mock AI Service, Frontend và Monitoring trên Local chỉ bằng một lệnh duy nhất.
- **Helm Chart Độc Lập**: Định nghĩa Deployment, Service, PVC, Ingress cho mọi thành phần (Frontend, Backend, AI, Postgres, Kafka, Zookeeper, Geth Blockchain Node).

### English
**Infrastructure as Code (IaC)**
Standardizing staging and production environments using modern container orchestration:
- **Multi-stage Dockerfiles**: Lightweight, secure container images built without compile-time bloat.
- **Docker Compose**: Spawns Postgres, Kafka, AI Service, Frontend, and Prometheus on local dev machines with a single script execution.
- **Self-contained Helm Chart**: Manages manifests for all microservices, stateful databases, queues, and ingress configurations in staging/production namespaces.

---

## SECTION 4: CI/CD & SECURITY (TỰ ĐỘNG HÓA & BẢO MẬT)

### Vietnamese
**Pipeline Tích hợp & Triển khai liên tục**
Quy trình CI/CD thiết lập qua GitHub Actions tích hợp các rào chắn bảo mật nghiêm ngặt:
- **Trivy Scanner**: Quét lỗ hổng thư viện OS/Runtime trong Docker Image trước khi đẩy lên registry.
- **OWASP ZAP Dynamic Scan**: Quét lỗ hổng ứng dụng web động (DAST) chống SQL Injection, XSS trên Staging trước khi go-live.
- **Triển khai an toàn**: Tự động deploy lên Staging, kiểm duyệt thủ công (Manual Approval Gate) trước khi nâng cấp Rolling Update lên Production.

### English
**CI/CD Pipeline & Security Hardening**
Automated workflows via GitHub Actions enforcing security audits at every level:
- **Trivy Container Scanner**: Scans built images for known CVEs and OS packages vulnerability before registry pushes.
- **OWASP ZAP DAST Scan**: Runs dynamic application security tests on the live Staging url before production gates.
- **Gated Deployments**: Automatic staging push, followed by a manual approval checkpoint before executing rolling updates on Production.

---

## SECTION 5: QA & PERFORMANCE (KIỂM THỬ E2E & HIỆU NĂNG)

### Vietnamese
**Đảm bảo chất lượng hệ thống**
Đánh giá kỹ lưỡng độ tin cậy và sức chịu đựng của ứng dụng:
- **Playwright E2E**: Giả lập hành vi người dùng nhập form, chọn ngân sách, nhu cầu và khu vực, xác minh luồng đăng ký thành công trên UI.
- **k6 Load Testing**: Giả lập tăng dần lên **10,000 người dùng đồng thời** gửi request đăng ký Lead. Ràng buộc hiệu năng: 95% phản hồi < 500ms, tỷ lệ lỗi < 1%.

### English
**Quality Assurance & Performance Ingestion**
Validating platform logic and system endurance under heavy loads:
- **Playwright E2E**: Simulates end-to-end user actions (form fills, dropdown selections, lead creation) and asserts database synchronization.
- **k6 Performance Test**: Ramps up to **10,000 concurrent Virtual Users** targeting `/api/leads`. Performance constraints: p95 latency under 500ms, error rate under 1%.

---

## SECTION 6: OBSERVABILITY (GIÁM SÁT & CẢNH BÁO)

### Vietnamese
**Khả năng quan sát & Ứng phó sự cố**
Giám sát toàn diện hệ thống từ hạ tầng đến ứng dụng:
- **Prometheus & Grafana**: Thu thập metrics và trực quan hoá lượng request, latency, RAM/CPU.
- **Alertmanager**: Cảnh báo tức thời qua Slack & Email khi database down, đĩa đầy > 80% hoặc lỗi 500 tăng đột biến.
- **Promtail & Loki**: Gom log từ Docker containers thời gian thực để truy vết nguyên nhân gốc rễ (Root Cause Analysis).

### English
**Observability & Alerting Stack**
Comprehensive monitoring from low-level containers to application performance:
- **Prometheus & Grafana**: Collects and visualizes request volume, connection pool limits, and CPU/memory quotas.
- **Alertmanager Webhooks**: Delivers instant Slack and email alerts for database disconnects, disk exhaustion (> 80%), or HTTP 5xx spikes.
- **Promtail & Loki Log Aggregation**: Streams stdout/stderr from active containers for rapid root-cause debugging.
