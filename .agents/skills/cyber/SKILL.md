---
name: cyber
description: Vietnamese Cybersecurity, Critical Information Infrastructure & Network Security Suite.
---

# mekong cyber — Autonomous Vietnamese Cybersecurity, Critical Infrastructure & Network Security Suite

## Căn Cứ Pháp Lý & Chuẩn Mực Nghiệp Vụ
1. **Luật An ninh mạng 2018 (Luật số 24/2018/QH14)**:
   - Thống nhất quản lý bảo vệ an ninh mạng, phòng ngừa ngăn chặn hành vi sử dụng không gian mạng xâm phạm an ninh quốc gia, trật tự an toàn xã hội.
   - Cơ quan chủ quản chuyên trách: **Cục An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao (A05) - Bộ Công an**.
2. **Nghị định số 53/2022/NĐ-CP (Quy định chi tiết Luật An ninh mạng)**:
   - **Lưu trữ dữ liệu tại Việt Nam (Data Localization - Điều 26)**:
     * Áp dụng đối với doanh nghiệp trong nước và doanh nghiệp nước ngoài cung cấp dịch vụ viễn thông, Internet, dịch vụ gia tăng trên không gian mạng tại Việt Nam.
     * Dữ liệu bắt buộc lưu trữ tại Việt Nam: Dữ liệu về thông tin cá nhân người sử dụng dịch vụ tại VN; Dữ liệu do người sử dụng tạo ra (tên tài khoản, thời gian sử dụng dịch vụ, thông tin thẻ tín dụng, IP, tin nhắn, cuộc gọi, tìm kiếm); Dữ liệu về mối quan hệ của người sử dụng (bạn bè, nhóm kết nối).
     * Thời gian lưu trữ dữ liệu tại Việt Nam: Tối thiểu $\ge 24\text{ tháng}$.
     * Yêu cầu đặt văn phòng đại diện / chi nhánh: Doanh nghiệp nước ngoài có các dịch vụ quy định khi có yêu cầu bằng văn bản của Bộ trưởng Bộ Công an phải hoàn tất thành lập chi nhánh hoặc văn phòng đại diện tại Việt Nam trong vòng 12 tháng.
3. **Nghị định số 85/2016/NĐ-CP (Bảo đảm an toàn hệ thống thông tin theo cấp độ)**:
   - Hệ thống thông tin tại Việt Nam được phân thành 5 cấp độ:
     * **Cấp độ 1**: Hệ thống thông tin nội bộ thông thường, kiểm tra định kỳ 24 tháng/lần.
     * **Cấp độ 2**: Hệ thống cung cấp dịch vụ công/thông tin công cộng cấp tỉnh, kiểm tra 12 tháng/lần.
     * **Cấp độ 3**: Hệ thống phục vụ người dân toàn quốc, cổng thanh toán quốc gia, TMĐT lớn, bí mật nhà nước độ Mật, kiểm tra 12 tháng/lần.
     * **Cấp độ 4**: Hệ thống thông tin điều khiển hạ tầng trọng yếu (lưới điện, viễn thông lõi, ngân hàng TW, bí mật Tối mật), kiểm tra 6 tháng/lần, cách ly Air-Gap.
     * **Cấp độ 5**: Hệ thống thông tin quan trọng đặc biệt về an ninh quốc gia (quốc phòng, an ninh, cơ yếu bí mật Tuyệt mật), kiểm tra 6 tháng/lần, mật mã chuyên dụng Ban Cơ yếu Chính phủ.
4. **Thông tư số 20/2017/TT-BTTTT (Ứng cứu sự cố an toàn thông tin mạng quốc gia)**:
   - Cơ quan điều phối quốc gia: **VNCERT/CC (Cục An toàn thông tin - Bộ Thông tin và Truyền thông)**.
   - Quy chuẩn báo cáo sự cố khẩn cấp: Mọi sự cố an toàn thông tin mạng nghiêm trọng phải được báo cáo bằng văn bản hoặc điện tử cho VNCERT/CC trong vòng $24\text{ giờ}$ kể từ khi phát hiện.
5. **Điều kiện kinh doanh dịch vụ an toàn thông tin mạng (Luật ATTTM 2015)**:
   - Doanh nghiệp kinh doanh dịch vụ giám sát ATTT (SOC), kiểm thử xâm nhập (Pentest), ứng cứu sự cố phải được Bộ TTTT cấp Giấy phép (thời hạn 10 năm).
   - Điều kiện: Tối thiểu 02 kỹ sư có chứng chỉ an toàn thông tin quốc tế (CISSP, CISA, CEH, CompTIA Security+...), cơ sở vật chất và phòng thí nghiệm (Lab) chuyên dụng.
6. **Lưu trữ SQLite WAL**: Bảng `data_localization_audits`, `security_level_assessments`, `cyber_incident_reports`, `cyber_service_licenses` tại `.mekong/cyber.db`.

---

## CLI Invocations

```bash
# Báo cáo tổng quan an ninh mạng, lưu trữ dữ liệu tại Việt Nam và sự cố
mekong cyber

# Thẩm định tuân thủ lưu trữ dữ liệu tại Việt Nam (Data Localization - Điều 26 Luật An ninh mạng & NĐ 53/2022)
mekong cyber localize "Mekong Cloud Services" --type FOREIGN_TECH_PLATFORM --personal --ugc --relationship --local-storage --retention 24 --branch

# Xác định và thẩm định cấp độ an toàn hệ thống thông tin (Cấp độ 1-5 theo Nghị định 85/2016/NĐ-CP)
mekong cyber level "Hệ thống Thanh toán Liên ngân hàng Quốc gia" --org "Ngân hàng Nhà nước" --data-class SECRET_TOIMAT --scale NATIONAL_CRITICAL

# Tiếp nhận và điều phối ứng cứu sự cố an toàn thông tin theo chuẩn 24h VNCERT/CC (Thông tư 20/2017)
mekong cyber incident "Sự cố Tấn công Ransomware Mã hóa Dữ liệu Máy chủ Cơ sở Dữ liệu" --system "Hệ thống Cổng Dịch vụ công" --severity HIGH --vector RANSOMWARE --hosts 20 --breach --reported-24h

# Thẩm tra điều kiện cấp Giấy phép kinh doanh dịch vụ an toàn thông tin mạng (Điều 41-44 Luật ATTTM 2015)
mekong cyber license "Công ty CP An ninh mạng Mekong CyberSec" --director "Nguyễn Văn Bảo" --engineers 4 --lab --scope "SECURITY_AUDIT_AND_MONITORING"

# Tra cứu lịch sử thẩm định và báo cáo sự cố an ninh mạng
mekong cyber list all --limit 20
```

---

## FastMCP & JSON-RPC Tools
- `mekong_cyber_localize(service_name, provider_type, stores_personal_data, stores_user_generated_data, stores_relationship_data, local_storage_active, retention_months, has_local_branch)`
- `mekong_cyber_level(system_name, organization, data_classification, service_scale)`
- `mekong_cyber_incident(incident_title, system_name, severity_level, attack_vector, affected_hosts_count, data_breached, reported_to_vncert_within_24h)`
- `mekong_cyber_license(firm_name, director_name, certified_engineers_count, has_specialized_lab, service_scope)`
- `mekong_cyber_list(category, limit)`
- `mekong_cyber_status()`
